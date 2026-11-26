# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 内容区文库（/api/v1/library/*）
# 约束矩阵: 站点入站令·甲（whitepapers/papers 批 1 入站）＋乙（cop-library 说明件
#           与代表性子库）——内容区只读面；以在册仓库为唯一权威源，本站只作内部阅读索引
# 口径: 只读（无写端点）；family 闭集机验（whitepaper/paper/terms/kg/cop-library/laws/law-notes）；
#       登录 DID 会话鉴权（与 P3~P9 各面一致）；docs 表缺失即 503 fail-closed
# 匿名放行: TDCA-RULING-SITE-COP-LIB-OPEN-001（2026-10-21，创始人取甲）——
#           仅 cop-library 一族三端点匿名只读；其余族仍须会话；⛔ 不改 _require_session_user 本体
# 匿名放行追加: LAWINGEST-001（2026-10-23，批C-C2）——laws/law-notes 两族并入匿名只读
#           （法律原文属公域材料；适用说明标「本侧解读·非官方意见」）；制度族（regulation）
#           归 /api/site/docs 维持原口径不变，⛔ 借机改动
# 匿名放行追加: ANON-READ-001（2026-11-08，依 TDCA-RULING-PUBLIC-CORPUS-055·治理件库·
#           decisions——「对外公开制度不需要注册可见」取甲）——制度族正文匿名只读：
#           白名单＝/api/public/docs 在册 49 件（slug＋sha256_16 逐件固定，⛔ 泛化）；
#           件即容器只读文件 docs/regulations/（与 public_docs_ops 同一事实源，⛔ 另建副本）；
#           fail-closed：白名单外／哈希不符／非 GET／路径穿越一律拒绝；⛔ 改 _require_session_user 本体
# 匿名放行追加: CONTENT-LIVE-ALL-001（2026-11-10，TDCA-HANDOFF-EXEC-L1SI206-CONTENT-LIVE-ALL-001
#           §二取甲＋L1SI189 在册裁定）——whitepaper/paper 两族并入匿名只读（六族）；两族源件
#           已过在册净名批与 S-2 复扫（凭据／自然人 0；4 处 NCA/GSEQ 为论文正文概念引用非工作件号）
# 族名两写追加: FAMNAME-011（2026-11-23，TDCA-HANDOFF-EXEC-L1SI227-FAMNAME-011 窄令放行）——
#           别名 301 层仅 #1~#5 五对（regulations/helps/coplib/ops-guide/term → 主名）；
#           #6/#7 未放行另案；⛔ 动存储 family 值、⛔ 动 _FAMILIES/_OPEN_FAMILIES 闭集、
#           ⛔ 入 /families 响应（⛔ 留双入口）
# 族名两写追加: FAMNAME-013（2026-11-23，创始人「同意」取乙案＋标准 V1.1 主名归单数）——
#           #6 papers→paper、#7 whitepapers→whitepaper 复名别名 301 补入（站上主名未变，
#           存储与前端 ⛔ 动，只补两条跳转）；本令取代 FAMNAME-011 之「#6/#7 不放行」结论
# =============================================================================
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from api_v1 import _nca_watermark, _require_session_user  # noqa: E402
from db import get_session  # noqa: E402
# TWO-001 B-1：脱敏单一真源——一处定义、多处调用（library 与 toolshelf 两处公开面同扫）
from public_sanitize import CATALOG_SENSITIVE as _CATALOG_SENSITIVE  # noqa: E402

router = APIRouter(prefix="/api/v1/library", tags=["library"])

# family 闭集：LIB-DOCS-SCOPE-001 新口径——知识库＝理论/白皮书/文献/术语/知识图谱/思维协议产物；
# regulation（制度类）归文档库 /api/site/docs（两闭集各自定义 ⛔ 不互取，零重叠）；
# terms/kg 新族位零行只建位 ⛔ 不造数据
# ANON-READ-001：制度族（regulation）正文匿名只读面（依 TDCA-RULING-PUBLIC-CORPUS-055·
# 治理件库·decisions——「对外公开制度不需要注册可见」取甲）。
# 白名单＝/api/public/docs 在册公开清单 regulation 49 件（2026-11-08 实测固化：
# slug＋sha256_16 逐件固定，⛔ 以族目录通配代替逐件；同日 NET-001 净面纳回后匿名面 49 件）；
# 件即容器只读文件
# docs/regulations/（与 public_docs_ops 同一事实源，⛔ 另建库表副本、⛔ 双源各算）。
# fail-closed：白名单外 slug／文件哈希与固化值不符／非 GET／路径穿越——一律 404 或 403。
_REG_DIR = Path("/docs/regulations")
_REG_WHITELIST = {
    # GENESIS-006（2026-11-08，依 HANDOFF-EXEC-L1SI204-RIGHTS-GENESIS-006）：4 件纯改名
    # （创世登记件乙案登记编号保留；第11号补净名＋同类扫净 3 件），slug 更新、哈希不变。
    # GENESIS-005（2026-11-08，依 HANDOFF-EXEC-L1SI204-RIGHTS-GENESIS-005）：44 件净名改名
    # （A 档 41 照 NETNAME-001 + B 档 3 照 NETNAME-002），slug 与固化哈希同步更新；
    # GENESIS-REG-001 登记编号缠判性 S-1 停手不动（照实回报候裁）。
    '配置权市场规范（单一权威稿·中文人读版V1.0（现行））.md': 'F514ED7DBB7B90FA',
    '配置权市场规范（英文人读版V1.0（现行））.md': '37CDC83B02DB9D09',
    '配置权市场规范（机读版V1.0（现行））.yaml': '25933FA0C805AFB8',
    'TDCA注册登记制度（中文人读版V1.0（现行））.md': 'DE9A9C992F36B1F3',
    'TDCA注册登记制度（英文人读版V1.0（现行））.md': 'C51CA0EE8F99486E',
    'TDCA注册登记制度（机读版V1.0（现行））.yaml': '108301077D9B021C',
    '场景线相遇专章对外版单独件（V1.0已生效·十七条）.md': '13A5CA0D77BC05BB',
    '可信协作宪法（对外可读版·V0.1·十条与序言四支柱）.md': '7C737861AEDF1CB3',
    '可信协作宪法英文人读版（V0.1·十条与四支柱·逐条对应中文）.md': '453750FC41E03B2E',
    '可信协作宪法机读版（V0.1·十条与四支柱·与中文英文互见）.yaml': 'D6704C36439CB154',
    # REGDETAIL-ALIGN-001（2026-11-26，依 TDCA-RULING-L1SI230-EXECRET-002 项一＋
    # TDCA-HANDOFF-EXEC-L1SI230-SITEGO-001 §五：准、免签批）：九键校验值按容器在役目录
    # /docs/regulations 现行净版逐件重算对齐（sha256_16 同算法）；⛔ 改键名/结构/机制、
    # ⛔ 改件面。逐件旧值见回报 -606；九件全同版、差异仅脱敏净版＋效力横幅。
    '身份可信等级认定条例对外版.md': '9893D771CEFC457A',
    '身份可信等级认定条例英文人读版（十六条·V1.0·逐条对应中文）.md': 'C0AF241A2A344ED8',
    '身份可信等级认定条例机读版（四档与判定次序与三态·V1.0·互见）.yaml': '0D749A0B90CAA6FD',
    '智能体定义条例对外版（二十一条·V1.0已生效）.md': 'BDBCB7488E3C7A7E',
    '智能体定义条例英文人读版（二十一条·V1.0·逐条对应中文）.md': 'D00FFC7A868E2B6D',
    '智能体定义条例机读版（本体与创世与主体与效用与生命周期·V1.0互见）.yaml': '4AD1F660193B3774',
    '流程环节卡发现（五问·六类失败·第4张卡）.md': 'DC61A25C04873379',
    '流程环节卡相遇（五问·六类失败·第5张卡）.md': 'EA6CA8CAE362C3CE',
    '流程环节卡握手（五问·七类失败·第6张卡）.md': '7014DBBA4BEAE18D',
    '流程环节卡签约（五问·七类失败·第7张卡）.md': 'AEBFBEFA3948D111',
    '流程环节卡交付（五问·七类失败·第8张卡）.md': '4565A45DEF19264C',
    '流程环节卡验收（五问·七类失败·第9张卡）.md': 'F1C7BD3E1340BE3E',
    '卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md': '9D1BF9EFE6305853',
    '卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md': 'BA29E5FA778C2415',
    '卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md': 'B2456EFDB79E6E8F',
    '惩罚三态与守门器对外纯版（二十五条与AB九条·V1.0已生效2026-10-16）.md': '9C0339D306B5F49F',
    '租户与环境作用域凭证绑定条例对外纯版（三规则一通路一分层·V1.0已生效2026-09-25）.md': '04C650A874D7C072',
    'IP版权资产评估管理办法对外纯版（三十一条齐·V1.0已生效2026-09-30）.md': 'EBA307DA2D181FEA',
    '制度治理规范对外纯版（六判据链）.md': '707BBFCFF9DA1480',
    '流程环节卡注册缔约（五问·七类失败·三句固定·第三张卡）.md': 'B76EFF232CD52920',
    '流程环节卡授权配置（五问·七类失败·第1张卡）.md': '27D00C5318B986DC',
    '流程环节卡结算计税（五问·七类失败·第2张卡）.md': 'BAB64CB43B38903C',
    '流程环节卡谈判（五问·七类失败·第10张卡）.md': '5B4C8D8F00563F25',
    '流程环节卡试错（五问·七类失败·第11张卡）.md': 'C8BD1B82A45C3ED9',
    '流程环节卡验证（五问·七类失败·第12张卡）.md': '3C52B10D1011DDC3',
    '流程环节卡履约准备（五问·七类失败·第13张卡）.md': 'C3ACF286D451FD22',
    '流程环节卡履约（五问·七类失败·第14张卡）.md': 'C6CF733FA9022077',
    '流程环节卡结算分配（五问·七类失败·第15张卡）.md': '43E95D6E7AD6C51B',
    '流程环节卡信用及遗产管理（五问·七类失败·第16张卡）.md': 'D590B9578341BE02',
    '流程环节卡争议裁决（五问·七类失败·第17张卡）.md': 'FFFA025E9A5F4DE7',
    '授权件模板对外版（中文人读·V1.0（现行）·八字段与四要件）.md': '83D3AAA832B44DEE',
    '存证（NCA）制度·对外节选版（V1.1）.md': '05F316A0915631EC',
    '官方可信认知资产登记·创世认知资产区块（V1.0·已登记）.md': 'FDAC3FCC24336316',
    'TDCA-PUB-NCA-GENESIS-EVID-001-官方可信认知资产·创世区块完整证据（三块·算法·签批·自验）-对外版.md': 'CCF73FCCA298C37A',
    # 2026-11-08 智库核证（WITNESS-ANONREAD-S2-001）暂剔一件：SIGNOFF-CONFIGMARKET-AUTH-001
    # 追认附记（正文含内部件号引用），49→48；候创始人明示（备忘 M-10），谁都不许代改。
    # TDCA-HANDOFF-EXEC-L1SI204-ANONREAD-NET-001（创始人「按推荐进行」）：净面后纳回 48→49——
    # 题名净名《配置权市场授权追认附记》、内部标识处置、句意零改动（三扫描零命中）、件改名净名；
    # 原 slug TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-追认附记.md（原固化哈希 3BAC791DDF8DFA87，原件 .bak 在同目录）。
    '配置权市场授权追认附记.md': 'FE13C218D8C41965',
    'TDCA-SIGNOFF-SCENE-ENCOUNTER-001-场景线·相遇专章·签批记录（条例·创始人签批·V1.0生效）.md': '78E74B3A96DDF87A',
    'TDCA-TEMPLATE-AUTH-001-生效注记.md': '16C538A9E1853FC2',
    '业务端节点接入与同构契约条例（对外公开版·V1.0）.md': '9E02C58A29F1B6CB',
    '业务端节点接入与同构契约条例（机读版·对外公开版·V1.0）.yaml': 'BF2BC5C35B986E05',
    # REGFACE-001（L1SI213，依 TDCA-HANDOFF-EXEC-L1SI213-SITE2-REGFACE-001）：
    # 读取面 49→55 补齐六件；固化值照令面实算表逐位核过（以容器在役目录
    # /docs/regulations 实算为准，六件全符）；⛔ 改既有 49 项、⛔ 动 _reg_read 逻辑
    # ENCNAME-002（L1SI226，创始人取甲）：EN/机读两件改净名（新件同内容同 sha），
    # 旧名退出扫描面（白名单除名＝不再服务）；README 因 L67/L68 随改自身 sha 变，固化值重算同步。
    'README.md': 'E4D68F6BE0922438',
    'TDCA-NSFL-COLLAB-NOTICE-V0.3.md': '926B1A1EFA2A776F',
    'TDCA-RELEASE-ENCOUNTER-001-相遇·公开说明（中文人读版·对外·脱敏）.md': '97D7F39F4560B0EF',
    'regulation-相遇公开说明-en.md': '530ECAC210AB45CA',
    'regulation-相遇公开说明.yaml': '8825B7253D954174',
    '人机协作工作条例.md': '69D9F6D44E139BC9',
    # CONTENT-CLOSE-001（L1SI224，依 TDCA-HANDOFF-EXEC-L1SI224-CONTENT-CLOSE-001 甲块）：
    # 五件入站（机读/英文对等在册对等版，同件多版本应齐）；固化值以容器在役目录
    # /docs/regulations 实算为准、逐位核过（043 经两地三读对齐 453750FC41E03B2E）；
    # ⛔ 改既有 55 项、⛔ 动 _reg_read 逻辑
    'TDCA-PUB-CORPUS-043-Constitution-EN-可信协作宪法英文人读版（V0.1·十条与四支柱·逐条对应中文）.md': '453750FC41E03B2E',
    'TDCA-PUB-CORPUS-044-Constitution-MACHINE-可信协作宪法机读版（V0.1·十条与四支柱·与中文英文互见）.yaml': 'D6704C36439CB154',
    'TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V1.0已生效）.yaml': 'F29F724A919BFC9F',
    'TDCA-TEMPLATE-AUTH-001-授权件模板（机读版V1.0-FROZEN）.yaml': 'F470E950E2C3E9EF',
    'TDCA-TEMPLATE-AUTH-001-授权件模板（英文人读版V1.0-FROZEN）.md': 'C2ACA45FB8A8B5F8',
}


# ── SITETRIO-001 S-3（GSEQ-9149，2026-11-26）：族内 slug 形制——对外 slug 去 .md 后缀 ──
# 白名单键（文件名＋固化哈希）不动：_reg_read 仍以文件名现算哈希 fail-closed 读原文；
# 仅对外呈现之 slug/title 去 .md（令面点名 50 条；.yaml 10 条带后缀属令面未点名，保留原样）。
# 旧 slug（带 .md）→ 新 slug 之 301 见 library_detail（照 _FAMILY_ALIASES 先例：路由面跳转非内容响应）。
def _reg_display_slug(fname: str) -> str:
    """文件名 → 对外 slug：仅去 .md 后缀（⛔ 动 .yaml；⛔ 动白名单键）。"""
    return fname[:-3] if fname.endswith(".md") else fname


_REG_DISPLAY: dict[str, str] = {}  # 对外 slug（去 .md）→ 白名单文件名
for _fname in _REG_WHITELIST:
    _dslug = _reg_display_slug(_fname)
    if _dslug in _REG_DISPLAY:
        raise RuntimeError(f"SITETRIO-001 S-3: 去 .md 后 slug 冲突 {_dslug!r}（fail-closed，⛔ 静默覆盖）")
    _REG_DISPLAY[_dslug] = _fname


def _reg_read(slug: str):
    """制度族白名单读路径：仅白名单 slug；文件现算哈希须与固化值一致（fail-closed）。"""
    if (not slug or "/" in slug or "\\" in slug or ".." in slug
            or slug not in _REG_WHITELIST):
        raise HTTPException(404, "DOC_NOT_FOUND: 件不存在或未入站")
    path = _REG_DIR / slug
    try:
        body = path.read_bytes()
    except OSError:
        raise HTTPException(404, "DOC_NOT_FOUND: 件不存在或未入站")
    digest = hashlib.sha256(body).hexdigest().upper()[:16]
    if digest != _REG_WHITELIST[slug]:
        raise HTTPException(404, "DOC_NOT_FOUND: 件不存在或未入站")
    return body.decode("utf-8", "replace")


_FAMILIES: dict[str, str] = {
    "whitepaper": "白皮书（理论／白皮书）",
    "paper": "文献（papers）",
    "terms": "术语（terms）",
    "kg": "知识图谱（kg）",
    "cop-library": "思维协议产物（cop-library）",
    "laws": "法律原文（laws）",
    "law-notes": "适用说明（law-notes）",
    # ANON-READ-001（依 TDCA-RULING-PUBLIC-CORPUS-055·治理件库·decisions——
    # 「对外公开制度不需要注册可见」取甲）：制度族入闭集，匿名只读面见下
    "regulation": "制度（regulation）",
    # SITE2-LIBOPEN-001（L1SI213，依 TDCA-WITNESS-L1SI213-SITE2-G2-001 §四取「改」）：
    # help/ops-guides 两族入资料库闭集（名与索引族名一致：帮助／操作指引）
    "help": "帮助",
    "ops-guides": "操作指引",
}

_SEL_LIST = text("SELECT slug, title, synced_at, LENGTH(body_md) AS body_chars"
                 " FROM docs WHERE family = :family ORDER BY slug")
_SEL_DETAIL = text("SELECT slug, title, body_md, source_path, data_nature, synced_at"
                   " FROM docs WHERE family = :family AND slug = :slug")
_SEL_COUNTS = text("SELECT family, COUNT(*) AS n FROM docs GROUP BY family")
_SEL_PAPER_CATALOG = text("SELECT slug, title, body_md, synced_at FROM docs"
                          " WHERE family = 'paper' ORDER BY slug")

# L1SI175-B1 S1-4：匿名摘要面脱敏——正则本体已并入单一真源 public_sanitize
# （TWO-001 B-1/B-2：凭据八形态＋内部编号族两族同扫），此处仅保留别名与长度口径
_SUMMARY_LEN = 200


def _first_prose_paragraph(body_md: str) -> str:
    """取正文首个说明性段落：跳过 Markdown 标题/引用块记号线/分隔线/代码围栏，截 200 字。"""
    for block in re.split(r"\n\s*\n", body_md or ""):
        lines = []
        for ln in block.splitlines():
            s = ln.strip()
            if not s or s.startswith(("#", "---", "```")):
                continue
            s = re.sub(r"^>\s?", "", s).strip()   # 去引用块记号
            if s:
                lines.append(s)
        if lines:
            return " ".join(lines)[:_SUMMARY_LEN]
    return ""


@router.get("/paper/catalog")
def paper_catalog(request: Request):
    """纸族匿名目录＋摘要（L1SI175-B1 S1-4）。

    匿名只返 slug/title/摘要（正文首段截 200 字）；正文端点 /paper/{slug} 仍 401 不动；
    摘要或标题命中脱敏正则者 fail-closed（摘要置 null 标「待核定」，标题命中整件不列）。"""
    try:
        with get_session() as s:
            rows = s.execute(_SEL_PAPER_CATALOG).all()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    items = []
    for r in rows:
        if _CATALOG_SENSITIVE.search(r.title or ""):
            continue
        summary = _first_prose_paragraph(r.body_md or "")
        if _CATALOG_SENSITIVE.search(summary):
            items.append({"slug": r.slug, "title": r.title,
                          "summary": None, "summary_note": "摘要待核定"})
        else:
            items.append({"slug": r.slug, "title": r.title, "summary": summary})
    return _nca_watermark(
        {"family": "paper", "count": len(items), "items": items,
         "note": "文献族公开目录＋摘要（正文须登录；摘要不构成全文替代）"},
        nature="real")


# COP-LIB-OPEN-001 + TERMS-OPEN-001：匿名放行两族（2026-10-21 并入同轮）
# LAWINGEST-001（批C-C2）：追加 laws/law-notes 两族匿名只读（法律原文属公域材料）
# CONTENT-LIVE-001（2026-11-10，依 TDCA-HANDOFF-EXEC-L1SI206-CONTENT-LIVE-ALL-001 §二取甲
#           ＋在册 L1SI189「论文与白皮书须可见」＋GSEQ-3694/3695 四族入站放行口径）：
#           追加 whitepaper/paper 两族匿名只读（目录＋正文同 cop-library 口径：只读、
#           ⛔ 下载原件若在册另有约束则照旧）；weekly 无此族端点（不存在悬空 401 待处置项）
# SITE2-LIBOPEN-001（L1SI213）：追加 help/ops-guides 两族匿名只读（与既有六族同列；
# docs 表 help 5／ops-guides 17 行已在位，公开面经 /api/public/docs 同族同件）
# TITLE-FAMILY-FIX-001（L1SI224，GSEQ-8823）：追加 regulation 入匿名开放面（族索引可见
#           = 本令目标；族内件目/正文仍走本文件 regulation 专属分支——件目白名单 49 件、
#           正文 _reg_read 白名单＋sha256 固化 fail-closed——不随本追加改变）
_OPEN_FAMILIES = ("cop-library", "terms", "laws", "law-notes", "whitepaper", "paper",
                  "help", "ops-guides", "regulation")

# FAMNAME-011（L1SI227，2026-11-23，依 TDCA-HANDOFF-EXEC-L1SI227-FAMNAME-011 窄令放行）：
# 族名两写·别名 301 层——仅 #1~#5 五对（#6 paper/papers、#7 whitepaper/whitepapers
# 未放行，另呈创始人裁；⛔ 动存储 family 值、⛔ 动 _FAMILIES 闭集、⛔ 入 _OPEN_FAMILIES、
# ⛔ 入 /families 响应——别名仅作路由面跳转落主名，⛔ 留双入口）。
# 判位：别名判定须在 _session_or_open 与 regulation 专属分支之前——匿名别名 URL
# 一律 301（不经鉴权：301 为路由面跳转非内容响应），落点保留子路径与 query。
# FAMNAME-013（L1SI227，2026-11-23，依 TDCA-HANDOFF-EXEC-L1SI227-FAMNAME-013）：
# 复名别名跳转——#6 papers→paper、#7 whitepapers→whitepaper 补入（创始人「同意」取乙案；
# 标准 V1.1 主名归单数，站上主名未变，存储与前端 ⛔ 动，只补两条别名 301）。
_FAMILY_ALIASES = {
    "regulations": "regulation",
    "helps": "help",
    "coplib": "cop-library",
    "ops-guide": "ops-guides",
    "term": "terms",
    "papers": "paper",
    "whitepapers": "whitepaper",
}


def _alias_redirect(family: str, tail: str, query: str):
    """别名→主名 301（FAMNAME-011）；非别名返 None。tail 为子路径（含前导 / 或空串）。"""
    main = _FAMILY_ALIASES.get(family)
    if main is None:
        return None
    qs = f"?{query}" if query else ""
    return RedirectResponse(f"/api/v1/library/{main}{tail}{qs}", status_code=301)


def _session_or_open(request: Request, family: str = "") -> None:
    """会话要求分派：_OPEN_FAMILIES 九族（cop-library/terms/laws/law-notes/whitepaper/paper
    ／help/ops-guides／regulation）匿名放行；其余（含未点名）照旧会话鉴权。
    ⛔ 不改 _require_session_user 本体（不动其签名与行为），仅在本族分支不调用之。"""
    if family in _OPEN_FAMILIES:
        return
    _require_session_user(request)


def _counts() -> dict[str, int]:
    try:
        with get_session() as s:
            rows = s.execute(_SEL_COUNTS).all()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    return {r.family: r.n for r in rows}


def _check_family(family: str) -> None:
    if family not in _FAMILIES:
        raise HTTPException(404, f"FAMILY_UNKNOWN: family 须为 {' / '.join(_FAMILIES)}")


@router.get("/families")
def library_families(request: Request):
    """文库族列表。匿名仅返 _OPEN_FAMILIES 九族（⛔ 泄他族名）；
    会话通过则返全闭集（回归照旧）。"""
    try:
        _require_session_user(request)
        authed = True
    except HTTPException:
        authed = False
    counts = _counts()
    if not authed:
        items = [{"family": f, "name": _FAMILIES[f],
                  "count": counts.get(f, 0)} for f in _OPEN_FAMILIES]
        return _nca_watermark(
            {"items": items, "total": len(items),
             "note": "匿名只读面：cop-library＋terms＋laws＋law-notes＋whitepaper＋paper "
                                     "＋help＋ops-guides＋regulation 九族开放（COP-LIB-OPEN-001／TERMS-OPEN-001／LAWINGEST-001／"
                                     "CONTENT-LIVE-ALL-001 案甲／TITLE-FAMILY-FIX-001）"},
            nature="real")
    items = [{"family": k, "name": v, "count": counts.get(k, 0)} for k, v in _FAMILIES.items()]
    # API-SHAPE F-3 兼容期：新增 data.items/data.total 统一形态，旧键 families 保留 ≥1 版
    return _nca_watermark({"families": items, "items": items, "total": len(items),
                           "note": "内容区只读面；以在册仓库为唯一权威源"},
                          nature="real")


@router.get("/{family}")
def library_list(family: str, request: Request):
    """族内件目（slug/title/synced_at；正文经 /{slug} 读取）。_OPEN_FAMILIES 九族匿名可读。

    ANON-READ-001（依 TDCA-RULING-PUBLIC-CORPUS-055·治理件库·decisions——「对外公开
    制度不需要注册可见」取甲）：制度族匿名可读，件目即白名单 49 件（slug 固定；
    2026-11-08 暂剔一件（WITNESS-ANONREAD-S2-001）后 NET-001 净面纳回，49→48→49）。"""
    redir = _alias_redirect(family, "", request.url.query)
    if redir is not None:
        return redir
    if family == "regulation":
        # SITETRIO-001 S-3：slug/title 去 .md 后缀呈现（白名单键不动；count 仍＝在册 60）
        items = [{"slug": _reg_display_slug(slug), "title": _reg_display_slug(slug),
                  "synced_at": None, "has_content": True}
                 for slug in sorted(_REG_WHITELIST)]
        return _nca_watermark(
            {"family": "regulation", "name": _FAMILIES["regulation"], "count": len(items),
             "items": items,
             "note": "制度族匿名只读面（ANON-READ-001）：白名单 49 件，正文经 /regulation/{slug} 读取"},
            nature="real")
    _session_or_open(request, family)
    _check_family(family)
    try:
        with get_session() as s:
            rows = s.execute(_SEL_LIST, {"family": family}).all()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    return _nca_watermark(
        {"family": family, "name": _FAMILIES[family],
         "items": [{"slug": r.slug, "title": r.title, "synced_at": r.synced_at,
                    "has_content": bool(r.body_chars and r.body_chars > 0)} for r in rows]},
        nature="real")


@router.get("/{family}/{slug}")
def library_detail(family: str, slug: str, request: Request):
    """单件正文（body_md 原文直出；不复制不改写；权威源在册）。_OPEN_FAMILIES 九族匿名可读。

    ANON-READ-001（依 TDCA-RULING-PUBLIC-CORPUS-055·治理件库·decisions——「对外公开
    制度不需要注册可见」取甲）：制度族白名单 49 件匿名可读正文（fail-closed 见 _reg_read）。"""
    redir = _alias_redirect(family, f"/{slug}", request.url.query)
    if redir is not None:
        return redir
    if family == "regulation":
        # SITETRIO-001 S-3：旧 slug（带 .md，白名单键形）→ 新 slug 301（旧 URL 保可用；
        # 照 _FAMILY_ALIASES 先例：301 为路由面跳转非内容响应，落点保留 query）。
        if slug.endswith(".md") and slug in _REG_WHITELIST:
            qs = f"?{request.url.query}" if request.url.query else ""
            return RedirectResponse(f"/api/v1/library/regulation/{_reg_display_slug(slug)}{qs}",
                                    status_code=301)
        body_md = _reg_read(_REG_DISPLAY.get(slug, slug))
        return _nca_watermark(
            {"family": "regulation", "slug": slug, "title": slug, "body_md": body_md,
             "source_path": f"docs/regulations/{_REG_DISPLAY.get(slug, slug)}", "synced_at": None,
             "note": "本站为内部阅读面；⛔ 不复制正文另存、⛔ 不改一字；权威源以在册仓库为准"},
            nature="real")
    _session_or_open(request, family)
    _check_family(family)
    try:
        with get_session() as s:
            row = s.execute(_SEL_DETAIL, {"family": family, "slug": slug}).first()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    if row is None:
        raise HTTPException(404, "DOC_NOT_FOUND: 件不存在或未入站")
    return _nca_watermark(
        {"family": family, "slug": row.slug, "title": row.title, "body_md": row.body_md,
         "source_path": row.source_path, "synced_at": row.synced_at,
         "note": "本站为内部阅读面；⛔ 不复制正文另存、⛔ 不改一字；权威源以在册仓库为准"},
        nature=row.data_nature if row.data_nature in ("real", "simulated") else "real")


# ANON-READ-001 写方法守卫：制度族匿名只读，写方法一律 403（fail-closed）；
# 其余族保持原状（405 Method Not Allowed，Allow: GET——与未定义方法时同状态）。
_WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def _write_guard(family: str):
    if family == "regulation":
        raise HTTPException(403, "REGULATION_READ_ONLY: 制度族匿名只读，写方法一律拒绝")
    raise HTTPException(405, "METHOD_NOT_ALLOWED: 该族只定义 GET", headers={"Allow": "GET"})


@router.api_route("/{family}/{slug}", methods=_WRITE_METHODS)
def library_detail_write_guard(family: str, slug: str, request: Request):
    _write_guard(family)


@router.api_route("/{family}", methods=_WRITE_METHODS)
def library_list_write_guard(family: str, request: Request):
    _write_guard(family)
