# -*- coding: utf-8 -*-
"""批 1 端点对照表对账脚本（L1SI143-SITE-BATCH1-ENDPOINT-MAP-001）

三源自动对账：
  源 A = 前端路由（解析 src/App.tsx 的 path="..."）
  源 B = 后端 /api/site 端点（解析 gateway/tdca_site_routes.py 的 @router 装饰器）
  源 C = CI 判态（status/fullrun-last.json，只读引用，脚本内不取机——由执行侧回读填入 ci_head/ci_verdict）
  源 D = 平台面 /api/v1（批 3 补全：解析同仓 tdca-web/gateway 各路由器件，绑回站点页调用）
合成 = 14 环 ↔ 制度条映射（批 1 令面随附，原样采用）+ 页面绑定 + 工件路径（人工定位件，如实标注）

可复跑：纯本地解析，同一提交上两跑 diff 为空即证。零凭据、零网络、零仓内改动。
"""
import json
import re
import sys
from pathlib import Path

# 站点树定位：默认取本脚本所在仓库中的站点树（docs/site/endpoint-map/ → 站点树根上三级），
# 可用环境变量 TDCA_SITE_ROOT 覆盖；--out 指定产物目录（默认与本脚本同目录）。
import argparse
import os

_here = Path(__file__).resolve()
SITE = Path(os.environ.get("TDCA_SITE_ROOT") or _here.parents[3])
OUT = Path(os.environ.get("TDCA_SITE_OUT") or _here.parent)
# 平台面网关在仓内兄弟树 tdca-web/gateway（批 3 完整面纳入 /api/v1）
PLATFORM_GW = Path(os.environ.get("TDCA_PLATFORM_GW") or _here.parents[3].parent / "tdca-web" / "gateway")
PLATFORM_OPS = ["api_v1", "workbuddy_ops", "cluster_ops", "formal_ops", "toolshelf_ops",
                "ci_ops", "anchor_ops", "ops_ops", "ownership_ops", "regulations_ops",
                "market_sim_ops", "library_ops", "announcements_ops", "authorization_ops",
                "market_admin_ops"]

def _parse_args(argv):
    p = argparse.ArgumentParser(description="批 1 端点对照表对账")
    p.add_argument("--site", default=None, help="站点树根目录（默认：脚本位置上三级 / TDCA_SITE_ROOT）")
    p.add_argument("--out", default=None, help="产物输出目录（默认：脚本同目录 / TDCA_SITE_OUT）")
    return p.parse_args(argv)

# CI 判态由执行侧经 ci_exec.py 回读（head / verdict / 计数），此处只登记引用值。
CI_STATE = {
    "head": "aa8217873fc4456b856fb02eb790453ad275cdfc",
    "compared_at": "20261014-130845",
    "passed": 3106, "failed": 0, "suites": 58,
    "source": "CI 机 /home/ci/tdca/status/fullrun-last.json（ci_exec.py 回读）",
}

def parse_routes(app_tsx: str):
    return re.findall(r'path="([^"]+)"', app_tsx)

def parse_endpoints(routes_py: str):
    """返回 [(method, path)]；path 为 router 相对路径（不含 /api/site 前缀）。"""
    eps = []
    for m in re.finditer(r'@router\.(get|post|put|delete)\("([^"]+)"', routes_py):
        eps.append((m.group(1).upper(), m.group(2)))
    return eps

# 14 环映射：令面随附（对外通俗名／内部件名），原样采用；页面与端点绑定为执行侧实测归因。
RINGS = [
    {"no": 1, "ring": "发现", "inst": "生态雷达·相遇线专章",
     "pages": ["/agents", "/agent-shelf"],
     "endpoints": ["GET /directory", "GET /weekly"],
     "endpoints_note": "名册摘要/周刊存档（公开只读面，无前端消费页，Home 以文档表呈现）；生态雷达＝ecoscan 机对机流水线",
     "artifacts": ["ecoscan/README.md（生态雷达流水线）", "docs/regulations/TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V0.9-DRAFT·待签批）.md"],
     "b1": "✓", "b2": "✓（只读出参结构确定）", "b3": "半（页有呈现、端点为公开读面无消费页）",
     "freq": "高", "freq_why": "名册页用户直达；生态扫描为制度硬核面",
     "gap": "相遇专章无专属呈现页（制度有、站点面无）——候选缺口"},
    {"no": 2, "ring": "相遇", "inst": "相遇线专章·身份管理制度",
     "pages": ["/about", "/announcements", "/pages"],
     "endpoints": [], "endpoints_note": "无专属端点（呈现面）",
     "artifacts": ["docs/regulations/TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V0.9-DRAFT·待签批）.md",
                   "governance/decisions/TDCA-AMEND-SRTA-IDMODES-001-身份管理四分法与兼容双向承认口径件（内部互认·外进内需内部承认·内出外需外部承认·兼容则双方都承认·护照免承认·含对前件之更正）.md"],
     "b1": "N/A", "b2": "N/A", "b3": "半（页呈现制度、无端点配对）",
     "freq": "中", "freq_why": "公告/站点地图中频",
     "gap": "身份管理制度四分法无专页；相遇专章签批记录件未在站点呈现——缺口"},
    {"no": 3, "ring": "握手", "inst": "双轨身份·身份可信等级条例·智能体身份锚定通知机令牌",
     "pages": ["/join", "/"],
     "endpoints": ["POST /agent-card/handshake", "GET /agent-card/{card_id}", "POST /notify-token"],
     "endpoints_note": "对接卡握手/查询＋通知机令牌登记（智能体通道；通知机令牌登记即「智能体身份锚定通知机令牌」之端点落点）",
     "artifacts": ["governance/decisions/TDCA-AGENT-DUAL-IDENTITY-001-智能体双轨身份与界面区分原则.md",
                   "governance/documents/TDCA-REG-IDENTITY-TIER-001-《身份可信等级认定条例》（人读版·V1.0·待签批·四步齐备）.md",
                   "governance/decisions/TDCA-SIGNOFF-REG-IDENTITY-TIER-001-《身份可信等级认定条例》生效签批落地件（V1.0-FROZEN·含V0.2至V0.4追加件并入·创始人逐字生效·对外仍待明示）.md"],
     "b1": "✓", "b2": "✓（pydantic AgentCard 模型，出入参确定）", "b3": "半（对接卡端点无前端消费页，Home 以文档表呈现）",
     "freq": "高", "freq_why": "缔约入口全站核心；握手为智能体首呼必经",
     "gap": ""},
    {"no": 4, "ring": "谈判", "inst": "场景配置权调用接口规范·配置权市场规范",
     "pages": ["/market", "/market-sim"],
     "endpoints": [], "endpoints_note": "市场页调平台 /api/v1/market-admin/* 与 /api/v1/market-sim/*（非 /api/site）",
     "artifacts": ["docs/regulations/TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V0.1-DRAFT）.md",
                   "docs/regulations/TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-签批落地件（配置权市场规范与授权件模板生效·V1.0-FROZEN）.md"],
     "b1": "✓（页调平台端点在册）", "b2": "半（平台端点非本批 /api/site 范围，结构以平台侧为准）", "b3": "✓（页有调用、端有实现）",
     "freq": "高", "freq_why": "市场面用户高频；配置权为制度硬核",
     "gap": "「场景配置权调用接口规范」件未定位（仓内仅见配置权市场规范）——工件缺口"},
    {"no": 5, "ring": "试错", "inst": "沙盒宪法化·动态安全三空间循环机制",
     "pages": ["/sandbox"],
     "endpoints": [], "endpoints_note": "沙盒页调平台 /api/v1/sandbox/sea-status、/api/v1/sandbox/apply",
     "artifacts": ["docs/sbx-ops/TDCA-PRINCIPLE-DSA-001-动态安全三空间循环机制.md",
                   "docs/papers/TDCA-MONOGRAPH-IT-001.md（专著内沙盒宪法化论述）"],
     "b1": "✓（页调平台端点在册）", "b2": "半（平台端点非本批范围）", "b3": "✓（页有调用、端有实现）",
     "freq": "高", "freq_why": "沙盒页用户高频；负空间三阶为合规硬核",
     "gap": "「沙盒宪法化」无独立制度件文件名（散见专著/DSA 件）——工件组织缺口（非缺失）"},
    {"no": 6, "ring": "验证", "inst": "制度治理判据链·转正四步之沙盒验证",
     "pages": ["/sandbox", "/attestation"],
     "endpoints": [], "endpoints_note": "验证页调平台 /api/v1/attestation/*",
     "artifacts": ["governance/decisions/TDCA-ASSERT-SRTA-IDENTITY-TIER-001-转正步三断言集与校验器件（Q-1至Q-21可机验断言·21条·合规集全过·对抗集21比21命中·含暴露力与可重复性）.md（转正四步之实作例）"],
     "b1": "✓（页调平台端点在册）", "b2": "半（平台端点非本批范围）", "b3": "✓",
     "freq": "中", "freq_why": "验证队列中频；判据链为制度硬核",
     "gap": "「制度治理判据链」无独立在册件名（判据链实作散见断言集/相遇专章）——工件组织缺口（非缺失）"},
    {"no": 7, "ring": "签约", "inst": "注册登记制度·授权件模板·缔约注册协议",
     "pages": ["/join", "/register", "/docs"],
     "endpoints": ["POST /join", "GET /join/status", "GET /join/list", "POST /join/review",
                   "GET /docs/{family}", "GET /docs/{family}/{slug}"],
     "endpoints_note": "缔约申请/进度/审核列表/三阶流转（页↔端全勾稽）；文档目录两件为制度文本公开读面（Docs 页实调）",
     "artifacts": ["docs/regulations/TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V0.1-DRAFT）.md",
                   "docs/regulations/TDCA-TEMPLATE-AUTH-001-授权件模板（中文人读版V0.1-DRAFT·四要件与固定格式八字段）.md",
                   "docs/register-contract/TDCA-REGISTER-CONTRACT-001-zh.md（缔约注册协议）"],
     "b1": "✓", "b2": "✓（JoinRequest/StageAdvance pydantic 模型）", "b3": "✓（Join/Review/Docs 页实调）",
     "freq": "高", "freq_why": "缔约与注册为全站主链；登记制度为硬核",
     "gap": ""},
    {"no": 8, "ring": "履约准备", "inst": "编排存证·集群·运行环境与数据通约",
     "pages": ["/cluster", "/ops", "/agents/:id"],
     "endpoints": [], "endpoints_note": "集群页调平台 /api/v1/cluster/*；编排＝GK-11 编排闭环＋flow-orchestrator",
     "artifacts": ["gov-kit/GK-11-编排闭环.md", "tdca-eios/docs/ASP-001.md（智能体调度协议·集群）", "tdca-eios/docs/EIOS-ARCH-001.md"],
     "b1": "✓（页调平台端点在册）", "b2": "半（平台端点非本批范围）", "b3": "✓",
     "freq": "中", "freq_why": "集群/运维中频；编排存证为硬核",
     "gap": "「运行环境与数据通约」件未定位（仓内仅见编排闭环与调度协议）——工件缺口"},
    {"no": 9, "ring": "履约", "inst": "协作规范·执行令牌（人类签发）",
     "pages": ["/agents/:id", "/studio"],
     "endpoints": [], "endpoints_note": "执行令牌＝网关 B-4 写鉴权 TDCA-CRT（gateway 中间件，人类签发通道）",
     "artifacts": [],
     "b1": "N/A", "b2": "N/A", "b3": "✗（执行令牌签发无页面承载；B-4 中间件为代码落点）",
     "freq": "中", "freq_why": "履约面中频；令牌签发为制度硬核",
     "gap": "「协作规范」与「执行令牌签发」均无在册制度件名、无签发 UI 页——双缺口（制度件＋页面）"},
    {"no": 10, "ring": "交付", "inst": "NCA 登记合一版（存证）",
     "pages": ["/attestation", "/audit"],
     "endpoints": [], "endpoints_note": "存证/台账页调平台 /api/v1/attestation/*、/api/v1/audit/ledger-public",
     "artifacts": ["nca-generator/（NCA 生成器）", "docs/register-contract/TDCA-REGISTER-CONTRACT-001-machine.json（机读登记件实例）"],
     "b1": "✓（页调平台端点在册）", "b2": "半（平台端点非本批范围）", "b3": "✓",
     "freq": "中", "freq_why": "存证台账中频；登记合一为硬核",
     "gap": "「NCA 登记合一版」正本未定位（仓内见生成器与机读实例，合一版文本件未定位）——工件缺口"},
    {"no": 11, "ring": "验收", "inst": "判据链·断言与校验器·四要件判定",
     "pages": ["/formal", "/authorization-registry"],
     "endpoints": [], "endpoints_note": "形式化页调平台 /api/v1/formal/*、/api/v1/ci/badge",
     "artifacts": ["governance/decisions/TDCA-ASSERT-SRTA-IDENTITY-TIER-001-转正步三断言集与校验器件（Q-1至Q-21可机验断言·21条·合规集全过·对抗集21比21命中·含暴露力与可重复性）.md",
                   "docs/regulations/TDCA-TEMPLATE-AUTH-001-授权件模板（中文人读版V0.1-DRAFT·四要件与固定格式八字段）.md（四要件来源）"],
     "b1": "✓（页调平台端点在册）", "b2": "半（平台端点非本批范围）", "b3": "✓",
     "freq": "中", "freq_why": "验收/授权登记中频；四要件为硬核",
     "gap": ""},
    {"no": 12, "ring": "结算分配", "inst": "统一结算规则·闭环结算·微交付税收",
     "pages": ["/tax"],
     "endpoints": ["POST /meter", "POST /credits", "GET /credits/{member_id}"],
     "endpoints_note": "调用计量＋积分台账（仅智能体通道；积分＝模拟记账单位非法偿，期 1 不结算）；税页另调平台 /api/v1/tax/mou/*",
     "artifacts": ["gov-kit/GK-04-统一结算.md", "docs/settlement/insurance/TDCA-INSURANCE-RULES-001-闭环结算保险金机制公开规则草案.md", "true-source/tdca-web/tdca-microtax/README.md（微交付税收实作）"],
     "b1": "✓（页调平台端点在册；/api/site credits 在网关）", "b2": "✓（CreditEvent pydantic 模型）", "b3": "✓（税页实调；credits 为智能体通道无页）",
     "freq": "中", "freq_why": "税收页中频；结算闭环为硬核",
     "gap": ""},
    {"no": 13, "ring": "争议裁决", "inst": "裁决权属司法（平台不代裁）",
     "pages": [],
     "endpoints": [], "endpoints_note": "制度性无落点：裁决权属司法，平台不代裁（令面原文）；工程侧仅争议痕迹零动作（G3 联动件）",
     "artifacts": ["governance/decisions/TDCA-G3-IDENTITY-LINK-SYNC-001-身份桥接联动交付记录.md（AMEND-2：争议痕迹＋无司法文件⇒零动作，载体而非裁决落点）"],
     "b1": "N/A", "b2": "N/A", "b3": "✗（无页面无端点，属制度性留白，非工程缺口）",
     "freq": "低", "freq_why": "低频事件；但制度定位须如实呈现",
     "gap": "制度性无落点（如实，非缺口）"},
    {"no": 14, "ring": "信用及遗产管理", "inst": "智能体治理（遗产继承与创建人消亡处置）·NCA 永续",
     "pages": ["/ownership", "/ownership-registry"],
     "endpoints": [], "endpoints_note": "权属页调平台 /api/v1/ownership/*",
     "artifacts": ["governance/decisions/TDCA-G3-IDENTITY-LINK-SYNC-001-身份桥接联动交付记录.md（消亡/继承联动实作＋存证）"],
     "b1": "✓（页调平台端点在册）", "b2": "半（平台端点非本批范围）", "b3": "半（联动实作为机通道，页仅权属呈现）",
     "freq": "中", "freq_why": "权属页中频；遗产处置为硬核但低频",
     "gap": "TDCA-STD-AGENT-ID-002（遗产继承与创建人消亡处置·引用称在册生效）正本未定位于本仓——工件缺口；「NCA 永续」文本件未定位"},
]

def parse_platform_endpoints():
    """批 3 完整面：枚举平台面 /api/v1（api_v1.py + 业务路由器），返回 [{method,path,file}]。"""
    out = []
    for name in PLATFORM_OPS:
        src = (PLATFORM_GW / f"{name}.py").read_text(encoding="utf-8")
        m = re.search(r'APIRouter\((?:[^)]*?prefix="([^"]+)")?', src)
        prefix = (m.group(1) if m and m.group(1) else "")
        for d in re.finditer(r'@router\.(get|post|put|delete)\(\s*"([^"]+)"', src):
            out.append({"method": d.group(1).upper(),
                        "path": f"{prefix}{d.group(2)}", "file": name})
    return out

def page_bindings():
    """站点页 → /api/v1 调用前缀绑定：{前缀: [页面件名]}（逐页 grep 归因）。"""
    bind = {}
    for f in sorted((SITE / "src" / "pages").glob("*.tsx")):
        for m in set(re.findall(r"/api/v1/[a-z0-9/{}_.-]+", f.read_text(encoding="utf-8"))):
            key = re.sub(r"[{}].*$", "*", m).rstrip("/")
            bind.setdefault(key, set()).add(f.stem)
    return {k: sorted(v) for k, v in bind.items()}

def main():
    app = (SITE / "src" / "App.tsx").read_text(encoding="utf-8")
    gw = (SITE / "gateway" / "tdca_site_routes.py").read_text(encoding="utf-8")
    routes = parse_routes(app)
    eps = parse_endpoints(gw)
    binds = page_bindings()
    plat = parse_platform_endpoints()
    for e in plat:
        cand = [k for k in binds if e["path"].startswith(k)]
        e["pages"] = sorted({p for k in cand for p in binds[k]})

    # 校验一：端点真存在（凡 RINGS 里列到的 /api/site 端点必须在网关解析结果内）
    ep_set = {f"{m} {p}" for m, p in eps}
    claimed = [e for r in RINGS for e in r["endpoints"]]
    missing = [e for e in claimed if e not in ep_set]
    # 校验二：页面真存在（路由表按段匹配，:id 等参数段归一）
    def norm(p):
        return re.sub(r":[^/]+", "*", p)
    route_norm = {norm(p) for p in routes}
    miss_pages = []
    for r in RINGS:
        for pg in r["pages"]:
            if norm(pg) not in route_norm:
                miss_pages.append(f"环{r['no']}:{pg}")

    table = {
        "meta": {
            "task": "L1SI143-SITE-BATCH1-ENDPOINT-MAP-001",
            "generated_by": Path(__file__).name,
            "site_head": CI_STATE["head"],
            "ci": CI_STATE,
            "counts": {"routes_total": len(routes), "routes_business": len([p for p in routes if p != "*"]),
                       "api_site_endpoints": len(eps),
                       "platform_endpoints_total": len(plat),
                       "platform_endpoints_page_bound": sum(1 for e in plat if e["pages"]),
                       "platform_endpoints_unbound": sum(1 for e in plat if not e["pages"])},
            "criteria": {"B-1": "端点真存在", "B-2": "接口熵=0（出入参结构确定）", "B-3": "两面成套（页↔端勾稽）"},
            "completeness": "批 3 补全：完整面＝站点面 /api/site（14）＋平台面 /api/v1（见 platform_endpoints）",
        },
        "routes": routes,
        "api_site_endpoints": [f"{m} /api/site{p}" for m, p in eps],
        "platform_endpoints": plat,
        "rings": RINGS,
        "self_check": {"claimed_endpoints_missing": missing, "pages_missing": miss_pages},
    }
    (OUT / "端点对照表.json").write_text(
        json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")

    # 人读五列表
    md = ["# 制度条款 → 代码落点 · 端点对照表（批 1＋批 3 补全·完整面）", "",
          f"站点源提交 `{CI_STATE['head']}`｜CI {CI_STATE['passed']} passed / {CI_STATE['failed']} failed / {CI_STATE['suites']} suites｜"
          f"路由 {table['meta']['counts']['routes_total']} 条（业务 {table['meta']['counts']['routes_business']}）｜/api/site 端点 {len(eps)} 个", "",
          "| 制度条款（业务语言） | 页面（路由） | 端点 | 工件（仓内路径） | 状态（B-1／B-2／B-3） |",
          "|---|---|---|---|---|"]
    for r in RINGS:
        pages = " ".join(r["pages"]) or "—"
        eps_s = "<br>".join(r["endpoints"]) if r["endpoints"] else ("—" if not r["endpoints_note"] else "—（" + r["endpoints_note"] + "）")
        arts = "<br>".join(r["artifacts"]) if r["artifacts"] else "无落点"
        st = f"B-1 {r['b1']}<br>B-2 {r['b2']}<br>B-3 {r['b3']}"
        md.append(f"| {r['no']} {r['ring']}（{r['inst']}） | {pages} | {eps_s} | {arts} | {st} |")
    md += ["", "## 高频列（批 2 排序输入）",
           "| 环 | 频次 | 依据（用户可达频次＋制度硬核度） |", "|---|---|---|"]
    for r in RINGS:
        md.append(f"| {r['no']} {r['ring']} | {r['freq']} | {r['freq_why']} |")
    md += ["", "## 缺口清单"]
    for r in RINGS:
        if r["gap"]:
            md.append(f"- 环{r['no']} {r['ring']}：{r['gap']}")
    pb = sum(1 for e in plat if e["pages"])
    md += ["", "## 平台面 /api/v1 候选端点清单（批 3 补全·完整面）",
           f"端点总数 **{len(plat)}**；页↔端绑定 **{pb}**；无页绑定 **{len(plat) - pb}**（内部/智能体通道，如实标）",
           "；".join(f"{name}×{sum(1 for e in plat if e['file'] == name)}" for name in PLATFORM_OPS), "",
           "| 端点 | 源件 | 调用页面 |", "|---|---|---|"]
    for e in plat:
        md.append(f"| {e['method']} `{e['path']}` | {e['file']} | {'、'.join(e['pages']) or '—'} |")
    md += ["", "## 自检",
           f"- 所引 /api/site 端点未在网关解析命中：{missing or '无'}",
           f"- 所引页面未在路由表命中：{miss_pages or '无'}",
           f"- /api/site 端点全量（{len(eps)}）：" + "、".join(f"{m} /api/site{p}" for m, p in eps)]
    (OUT / "端点对照表.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"routes": len(routes), "endpoints": len(eps),
                      "platform_total": len(plat), "platform_bound": pb,
                      "missing_eps": missing, "missing_pages": miss_pages}, ensure_ascii=False))

if __name__ == "__main__":
    _args = _parse_args(sys.argv[1:])
    if _args.site:
        SITE = Path(_args.site)
    if _args.out:
        OUT = Path(_args.out)
    sys.exit(main())
