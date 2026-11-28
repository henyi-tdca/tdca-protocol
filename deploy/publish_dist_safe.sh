#!/bin/bash
# =============================================================================
# TDCA 制度水印
# FC-ID: TDCA-FC-OPS-001 | 目标函数: 前端 dist 安全发布（SITE-AUTH-TIER-001 S-C 三道防线）
# 约束矩阵: 创始人逐字「③ 下载件本来就不入仓」＋「按建议办」；⛔ 下载件入仓 ⛔ 应然件清单入仓
# 教训锚点: 2026-11-06 新构建 dist 只剩 4 包（downloads 被整目录替换清空）＋ mv 换目录致
#           nginx bind mount 悬空 403——本脚本两坑同修。
# 用法（站机上）: bash publish_dist_safe.sh <新dist.tgz路径> <发布名，如 usability4>
# =============================================================================
set -euo pipefail

TZ_DATE="$(date +%Y%m%d-%H%M%S)"
SITE="${TDCA_SITE_ROOT:-/root/tdca-site}"
DIST="$SITE/dist"
STAGING="$SITE/dist-staging-$TZ_DATE"
BACKUPS="$SITE/backups"
PUBLIC_BASE="${TDCA_PUBLIC_BASE:-https://127.0.0.1}"

[ $# -eq 2 ] || { echo "用法: $0 <新dist.tgz> <发布名>"; exit 64; }
TGZ="$1"; NAME="$2"
[ -f "$TGZ" ] || { echo "❌ tgz 不存在: $TGZ"; exit 66; }
[ -d "$DIST" ] || { echo "❌ dist 不存在: $DIST"; exit 66; }
command -v rsync >/dev/null || { echo "❌ 缺 rsync"; exit 69; }
mkdir -p "$BACKUPS"

echo "== [防线三 1/2] 发布前留存：downloads 打包 + dist 整备 =="
BEFORE_COUNT="$(find "$DIST/downloads" -maxdepth 1 -type f 2>/dev/null | wc -l)"
tar czf "$BACKUPS/downloads-backup-$NAME-$TZ_DATE.tgz" -C "$DIST" downloads
cp -r "$DIST" "$SITE/dist-backup-$NAME-$TZ_DATE"
echo "   downloads 备份: backups/downloads-backup-$NAME-$TZ_DATE.tgz（发布前 $BEFORE_COUNT 件）"
echo "   dist 整备:     dist-backup-$NAME-$TZ_DATE"

echo "== [防线一] 解包 staging + downloads 只增不删不覆盖并入 =="
rm -rf "$STAGING"; mkdir -p "$STAGING"
tar xzf "$TGZ" -C "$STAGING"
if [ -d "$DIST/downloads" ]; then
    # 线上已有件并入 staging（同名不覆盖：--ignore-existing，迭代＝新包名）
    rsync -a --ignore-existing "$DIST/downloads/" "$STAGING/downloads/"
fi
# 原位发布（⛔mv 整目录——bind mount 悬空事故锚点）：先换主体（--delete 同步构建产物），
# downloads 目录排除在外；downloads 单独增量同步（不删、不覆盖）。
rsync -a --delete --exclude='/downloads' "$STAGING/" "$DIST/"
rsync -a --ignore-existing "$STAGING/downloads/" "$DIST/downloads/"
rm -rf "$STAGING"
echo "   原位 rsync 完成（dist inode 未动，nginx 无需重启）"

echo "== [防线二] 发布后核对：downloads 件数 + 直链 200 全抽核 =="
AFTER_COUNT="$(find "$DIST/downloads" -maxdepth 1 -type f | wc -l)"
echo "   downloads 件数: 发布前 $BEFORE_COUNT → 发布后 $AFTER_COUNT（应不减）"
[ "$AFTER_COUNT" -ge "$BEFORE_COUNT" ] || { echo "❌ downloads 件数减少——停手核对"; exit 65; }

ok=0; bad=0
while IFS= read -r f; do
    b="$(basename "$f")"
    code="$(curl -sk -o /dev/null -w '%{http_code}' "$PUBLIC_BASE/downloads/$b")"
    if [ "$code" = "200" ]; then ok=$((ok+1)); else bad=$((bad+1)); echo "   ❌ $b → $code"; fi
done < <(find "$DIST/downloads" -maxdepth 1 -name '*.zip' -type f)
echo "   直链抽核: $ok 件 200 / 失败 $bad 件"
[ "$bad" -eq 0 ] || { echo "❌ 存在非 200 直链——停手核对"; exit 65; }

BUNDLE="$(grep -o 'index-[^"]*\.js' "$DIST/index.html" | head -1)"

echo "== [防线三 2/2] sitemap 同步（C-2 OPS-003：以仓为准·不随 dist 漂移）=="
SITEMAP_DIR="$SITE/ops-files/public-static"
SITEMAP_SRC="${TDCA_SITEMAP_SRC:-$SITE/sitemap-canonical.xml}"
if [ -f "$SITEMAP_SRC" ]; then
    if ! cmp -s "$SITEMAP_SRC" "$SITEMAP_DIR/sitemap.xml"; then
        cp "$SITEMAP_DIR/sitemap.xml" "$SITEMAP_DIR/sitemap.xml.bak-publish-$TZ_DATE"
        cp "$SITEMAP_SRC" "$SITEMAP_DIR/sitemap.xml"
        chmod 644 "$SITEMAP_DIR/sitemap.xml"
        echo "   sitemap 已同步为仓件（旧件备份 sitemap.xml.bak-publish-$TZ_DATE）"
    else
        echo "   sitemap 已与仓件逐字节一致（跳过）"
    fi
else
    echo "   ⚠️ 未供仓件 sitemap 源（TDCA_SITEMAP_SRC=$SITEMAP_SRC）——仅核对在役件，不同步"
fi
sm_code="$(curl -sk -o /dev/null -w '%{http_code}' "$PUBLIC_BASE/sitemap.xml")"
sm_sha="$(sha256sum "$SITEMAP_DIR/sitemap.xml" | cut -c1-16)"
sm_n="$(grep -c '<url>' "$SITEMAP_DIR/sitemap.xml")"
echo "   sitemap 在役: HTTP=$sm_code sha256_16=$sm_sha urls=$sm_n"
[ "$sm_code" = "200" ] || { echo "❌ sitemap 非 200——停手核对"; exit 65; }
em_code="$(curl -sk -o /dev/null -w '%{http_code}' "$PUBLIC_BASE/endpoint-map.json")"
echo "   endpoint-map 在役: HTTP=$em_code（C-3 OPS-003 同目录持久件，仅核不阻断）"
echo "== [防线二 3/3] 件面清单逐件核对（SITEFIX-007 块C：四件 200 阻断式）=="
surface_ok=0; surface_bad=0
for p in /404.html /curation.json /openapi.json /.well-known/agent.json; do
    scode="$(curl -sk -o /dev/null -w '%{http_code}' "$PUBLIC_BASE$p")"
    if [ "$scode" = "200" ]; then surface_ok=$((surface_ok+1)); else surface_bad=$((surface_bad+1)); echo "   ❌ $p → $scode"; fi
done
echo "   件面清单: $surface_ok/4 件 200，失败 $surface_bad"
[ "$surface_bad" -eq 0 ] || { echo "❌ 件面清单存在非 200——阻断（public-static 面须先恢复）"; exit 65; }


echo "== PASS：$NAME 发布完成（bundle $BUNDLE，downloads $AFTER_COUNT 件全通，sitemap urls=$sm_n） =="
exit 0
