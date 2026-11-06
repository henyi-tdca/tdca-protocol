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
echo "== PASS：$NAME 发布完成（bundle $BUNDLE，downloads $AFTER_COUNT 件全通） =="
exit 0
