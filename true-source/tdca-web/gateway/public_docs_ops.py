# -*- coding: utf-8 -*-
"""
公开只读制度件取得面（丙案 · L1SI151-PUBLIC-ROUTE-001）。

口径（入站判据 P-1~P-5之前置 · TDCA-RULING-SITE-INGEST-DEFINITION-001）：
  - 入站＝公网可取得件：本面即「可发现（P-1）＋可取得（P-2）」之公开承载面；
  - 匿名只读：仅 GET；写方法一律不开放（未定义即 405 fail-closed）；
  - 只列已入站公开件：以在册公开清单为准（regulation 17 · whitepapers 2 · papers 13 · L1SI154-010 扩面），
    ⛔ 未入站件不出现、⛔ 乙类存证件永不出现（fail-closed：越界取件 404，
    ⛔ 不借 404/200 之差泄露在仓与否之外的信息——统一 404）；
  - 单一事实源：件即容器内只读文件（docs/regulations/），sha256 由文件现算，
    ⛔ 不另建库表副本、⛔ 不双源各算；
  - 不带私域：⛔ 内部编号（件内若残留编号属内容本身，照实返回——入站核验另扫）、
    ⛔ 运维字段、⛔ 他人数据、⛔ 计量与额度；
  - 限流：60 次/分/IP（滑动窗口，防枚举）；
  - 别名：旧 /api/site/docs/* 指向同一实现（⛔ 不双实现），仅为前端不改。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from error_codes import with_code  # L1SI153 段一：拒绝体仅增设 code 字段

router = APIRouter(prefix="/api/public", tags=["public-docs"])
# 别名路由：与主路由同一实现（同一处理函数），仅为前端不改（施工令 §二）
alias_router = APIRouter(prefix="/api/site", tags=["public-docs-alias"])

# ---------------------------------------------------------------------
# 在册公开清单（三族 57 件 · regulation 42／whitepapers 2／papers 13 · L1SI154-010 扩面 + L1SI154-028 九件 + L1SI155-INGEST-002 十六件）
# ⛔ 未入站件与乙类 2 件（签批记录／生效注记）一律不得列入；
# 更新本清单须另有在册依据（入站批次放行件），⛔ 不得随代码静默扩面。
# ---------------------------------------------------------------------
_FAMILY = "regulation"  # 默认族：裸 /api/public/docs 兼容行为（仍列 regulation）
# L1SI154-010：多族承载——族 → 容器内目录（/docs/<dir>，只读挂载）
_FAMILY_DIRS = {"regulation": "regulations", "whitepapers": "whitepapers", "papers": "papers"}
_PUBLIC_DOCS = {
    "regulation": (
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版V0.1-DRAFT）.yaml",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版V0.1-DRAFT）.yaml",
    "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V0.9-DRAFT·待签批）.md",
    "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V0.9-DRAFT）.yaml",
    "TDCA-PUB-CORPUS-017-可信协作宪法（对外可读版·V0.1草案候选·十条与序言四支柱）.md",
    "TDCA-PUB-CORPUS-043-Constitution-EN-可信协作宪法英文人读版（V0.1·十条与四支柱·逐条对应中文）.md",
    "TDCA-PUB-CORPUS-044-Constitution-MACHINE-可信协作宪法机读版（V0.1·十条与四支柱·与中文英文互见）.yaml",
    "TDCA-PUB-CORPUS-029-卷二纯版第二批清理版重出-身份可信等级认定条例对外版（仅去符号·语义同028·六检通过）.md",
    "TDCA-PUB-CORPUS-045-IdentityTier-EN-身份可信等级认定条例英文人读版（十六条·V1.0·逐条对应中文）.md",
    "TDCA-PUB-CORPUS-046-IdentityTier-MACHINE-身份可信等级认定条例机读版（四档与判定次序与三态·V1.0·互见）.yaml",
    "TDCA-PUB-CORPUS-030-卷二纯版第三批-智能体定义条例对外版（二十一条·V1.0已生效·六检通过·引用不重写）.md",
    "TDCA-PUB-CORPUS-047-AgentDefinition-EN-智能体定义条例英文人读版（二十一条·V1.0·逐条对应中文）.md",
    "TDCA-PUB-CORPUS-048-AgentDefinition-MACHINE-智能体定义条例机读版（本体与创世与主体与效用与生命周期·V1.0互见）.yaml",
    "TDCA-PUB-CORPUS-083-流程环节卡发现（五问·六类失败·第4张卡）.md",
    "TDCA-PUB-CORPUS-084-流程环节卡相遇（五问·六类失败·第5张卡）.md",
    "TDCA-PUB-CORPUS-085-流程环节卡握手（五问·七类失败·第6张卡）.md",
    "TDCA-PUB-CORPUS-086-流程环节卡签约（五问·七类失败·第7张卡）.md",
    "TDCA-PUB-CORPUS-087-流程环节卡交付（五问·七类失败·第8张卡）.md",
    "TDCA-PUB-CORPUS-088-流程环节卡验收（五问·七类失败·第9张卡）.md",
    "TDCA-PUB-CORPUS-090-卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md",
    "TDCA-PUB-CORPUS-091-卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md",
    "TDCA-PUB-CORPUS-092-卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md",
    # L1SI155-INGEST-002：十五件入册（A 三已生效条例 ＋ B 治理规范 ＋ E 卷三卡十一）＋ AMEND-1 授权件模板对外版（第 16 件）
    "TDCA-PUB-CORPUS-069-惩罚三态与守门器对外纯版（二十五条与AB九条·V1.0已生效2026-10-16）.md",
    "TDCA-PUB-CORPUS-070-租户与环境作用域凭证绑定条例对外纯版（三规则一通路一分层·V1.0已生效2026-09-25）.md",
    "TDCA-PUB-CORPUS-071-IP版权资产评估管理办法对外纯版（三十一条齐·V1.0已生效2026-09-30）.md",
    "TDCA-PUB-CORPUS-074-制度治理规范对外纯版（六判据链·英文待补）.md",
    "TDCA-PUB-CORPUS-058-流程环节卡注册缔约（五问·七类失败·三句固定·第三张卡）.md",
    "TDCA-PUB-CORPUS-101-流程环节卡授权配置（五问·七类失败·第1张卡补五问版）.md",
    "TDCA-PUB-CORPUS-102-流程环节卡结算计税（五问·七类失败·第2张卡补五问版）.md",
    "TDCA-PUB-CORPUS-097-流程环节卡谈判（五问·七类失败·第10张卡）.md",
    "TDCA-PUB-CORPUS-098-流程环节卡试错（五问·七类失败·第11张卡）.md",
    "TDCA-PUB-CORPUS-099-流程环节卡验证（五问·七类失败·第12张卡）.md",
    "TDCA-PUB-CORPUS-100-流程环节卡履约准备（五问·七类失败·第13张卡）.md",
    "TDCA-PUB-CORPUS-093-流程环节卡履约（五问·七类失败·第14张卡）.md",
    "TDCA-PUB-CORPUS-094-流程环节卡结算分配（五问·七类失败·第15张卡）.md",
    "TDCA-PUB-CORPUS-095-流程环节卡信用及遗产管理（五问·七类失败·第16张卡）.md",
    "TDCA-PUB-CORPUS-096-流程环节卡争议裁决（五问·七类失败·第17张卡）.md",
    "TDCA-PUB-CORPUS-103-授权件模板对外版（中文人读·V1.0-FROZEN按签批更正版本面貌·八字段与四要件）.md",
    # L1SI164-NCA-EXT-INSITE-001（AMEND-2 授权追加）：存证（NCA）制度对外节选版 R2 件——regulation 42→43
    "TDCA-PUB-NCA-STD-001-EXT-V1.1-存证（NCA）制度对外节选版（已生效·与内部V1.1同版·差异清单）-R2.md",
    # L1SI164-NCA-GENESIS-REG-INSITE-001（授权追加）：官方可信认知资产登记件（对外节选版）——regulation 43→44
    "TDCA-PUB-NCA-GENESIS-REG-001-TDCA官方可信认知资产登记·创世认知资产区块（人读·已登记·对外节选版）.md",
    # L1SI164-NCA-GENESIS-REG-INSITE-001-AMEND-1（授权追加）：创世区块完整证据件（对外版）——regulation 44→45
    "TDCA-PUB-NCA-GENESIS-EVID-001-官方可信认知资产·创世区块完整证据（三块·算法·签批·自验）-对外版.md",
    ),
    # L1SI154-010：白皮书 2 件全量（已全量扫六类内部编号零命中）
    "whitepapers": (
    "TDCA-AI-GOVERNANCE-WP-001.md",
    "TDCA-COG-WP-001.md",
    ),
    # L1SI154-010：论文顶层正文 13 件（README/.gitattributes 元数据件不入；evidence/ 默认排除）
    "papers": (
    "TDCA-FUNCTION-WP-002-APPX-G-附录G-制度大模型与制度孪生函数化登记.md",
    "TDCA-FUNCTION-WP-002-函数白皮书.md",
    "TDCA-MATH-WP-REV-001-数学基础白皮书修订本.md",
    "TDCA-MONOGRAPH-COP-001.md",
    "TDCA-MONOGRAPH-IT-001.md",
    "TDCA-PAPER-ENGINEERING-PHILOSOPHY-001-工程哲学-English-V1.0.md",
    "TDCA-PAPER-ENGINEERING-PHILOSOPHY-001-工程哲学-中文版-V1.0.md",
    "TDCA-PAPER-FUNCTIONAL-LM-001.md",
    "TDCA-PAPER-PHILOSOPHY-001-制度哲学-English-V1.0.md",
    "TDCA-PAPER-PHILOSOPHY-001-制度哲学-中文版-V1.0.md",
    "TDCA-WP-MATERIALISM-001.md",
    "TDCA-paper-CN.md",
    "TDCA-paper-EN.md",
    ),
}
_PUBLIC_SET = frozenset(n for names in _PUBLIC_DOCS.values() for n in names)
_PUBLIC_FAMILY = {n: fam for fam, names in _PUBLIC_DOCS.items() for n in names}

# L1SI154-011 段C：清单显示名映射（⛔ 只改显示名，路径与 slug 一字不改，防断链）。
# 背景：008 段A 只换了六件内容、件名未变，文件名里的 V0.1-DRAFT 与内容面貌（V1.0-FROZEN已生效）
# 不符；相遇专章两版内容仍为真草案，去 DRAFT 字样但保留「待签批」真实状态。
# 键必须是 _PUBLIC_SET 内的在册件名；未映射件显示名=文件名（默认行为不变）。
_DISPLAY_NAME = {
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V0.1-DRAFT）.md":
        "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版V0.1-DRAFT）.md":
        "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版V0.1-DRAFT）.yaml":
        "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版·V1.0-FROZEN已生效）.yaml",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V0.1-DRAFT）.md":
        "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版V0.1-DRAFT）.md":
        "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版V0.1-DRAFT）.yaml":
        "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版·V1.0-FROZEN已生效）.yaml",
    "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V0.9-DRAFT·待签批）.md":
        "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V1.0已生效）.md",
    "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V0.9-DRAFT）.yaml":
        "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V1.0已生效）.yaml",
    # L1SI154-081：去内部批次字样（卷二纯版第N批…），显示名规则＝制度名（形态·版本）；slug/路径不动
    "TDCA-PUB-CORPUS-029-卷二纯版第二批清理版重出-身份可信等级认定条例对外版（仅去符号·语义同028·六检通过）.md":
        "TDCA-PUB-CORPUS-029-身份可信等级认定条例对外版（V1.0已生效）.md",
    "TDCA-PUB-CORPUS-030-卷二纯版第三批-智能体定义条例对外版（二十一条·V1.0已生效·六检通过·引用不重写）.md":
        "TDCA-PUB-CORPUS-030-智能体定义条例对外版（V1.0已生效·二十一条）.md",
    # L1SI154-028：六卡三卷入册（显示名加「流程卡 ·」「说明卷 ·」前缀；slug/路径不动）
    "TDCA-PUB-CORPUS-083-流程环节卡发现（五问·六类失败·第4张卡）.md":
        "流程卡 · 发现（五问 · 六类失败）.md",
    "TDCA-PUB-CORPUS-084-流程环节卡相遇（五问·六类失败·第5张卡）.md":
        "流程卡 · 相遇（五问 · 六类失败）.md",
    "TDCA-PUB-CORPUS-085-流程环节卡握手（五问·七类失败·第6张卡）.md":
        "流程卡 · 握手（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-086-流程环节卡签约（五问·七类失败·第7张卡）.md":
        "流程卡 · 签约（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-087-流程环节卡交付（五问·七类失败·第8张卡）.md":
        "流程卡 · 交付（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-088-流程环节卡验收（五问·七类失败·第9张卡）.md":
        "流程卡 · 验收（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-090-卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md":
        "说明卷 · 卷四 治理卷（谁定规则／怎么改／怎么监督／争议边界）.md",
    "TDCA-PUB-CORPUS-091-卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md":
        "说明卷 · 卷五 同构卷（制度与技术同构／本体同构／场景嵌套）.md",
    "TDCA-PUB-CORPUS-092-卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md":
        "说明卷 · 卷六 助手与入口（三类入口／助手四步接入／代签红线）.md",
}
assert all(n in _PUBLIC_SET for n in _DISPLAY_NAME), "显示名映射键必须是在册件名"

_RATE_LIMIT_PER_MIN = 60

# ---------------------------------------------------------------------
# 限流（进程内滑动窗口；单 worker 部署下足够，防枚举非防攻击）
# ---------------------------------------------------------------------
_hits: dict[str, list] = {}
_hits_lock = threading.Lock()


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    with _hits_lock:
        lst = _hits.setdefault(ip, [])
        cutoff = now - 60.0
        while lst and lst[0] < cutoff:
            lst.pop(0)
        if len(lst) >= _RATE_LIMIT_PER_MIN:
            return True
        lst.append(now)
        return False


# ---------------------------------------------------------------------
# 件目录解析：容器内只读挂载（/docs/<族目录>）为单一事实源；
# 本地/测试可用 TDCA_PUBLIC_DOCS_DIR 指向等价目录（⛔ 生产不设）
# ---------------------------------------------------------------------
def _docs_dir(family: str = _FAMILY) -> Path | None:
    override = os.environ.get("TDCA_PUBLIC_DOCS_DIR", "").strip()
    if override:
        # 测试覆盖：所有族共用一个等价目录（夹具平铺全部在册件）
        p = Path(override)
        return p if p.is_dir() else None
    sub = _FAMILY_DIRS.get(family)
    if not sub:
        return None
    here = Path(__file__).resolve()
    for parent in (here.parents[3], here.parents[2], here.parents[1]):
        cand = parent / "docs" / sub
        if cand.is_dir():
            return cand
    return None


def _read_doc(filename: str) -> tuple[bytes, str] | None:
    """读在册公开件（⛔ 绝不越出清单）；返回 (bytes, sha256) 或 None。"""
    if filename not in _PUBLIC_SET:
        return None
    d = _docs_dir(_PUBLIC_FAMILY.get(filename, _FAMILY))
    if d is None:
        return None
    fpath = d / filename
    try:
        raw = fpath.read_bytes()
    except OSError:
        return None
    if not fpath.is_file() or fpath.parent != d:  # 纵深防御（防路径穿越）
        return None
    return raw, hashlib.sha256(raw).hexdigest()


_VERSION_RE = re.compile(r"V\d+\.\d+(?:-[A-Z0-9.]+)*")
_YAML_VERSION_RE = re.compile(r"^version:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.M)


def _version_of(filename: str, text: str) -> str | None:
    """版本读件内真实值（best-effort；⛔ 不硬编码）。"""
    if filename.endswith(".yaml"):
        m = _YAML_VERSION_RE.search(text[:2000])
        if m:
            return m.group(1).strip()
    head = "\n".join(text.splitlines()[:30])
    m = _VERSION_RE.search(head)
    return m.group(0) if m else None


def _entry(filename: str, raw: bytes, sha: str, family: str) -> dict:
    text = raw.decode("utf-8", "replace")
    return {
        "family": family,
        "slug": filename,
        "filename": filename,
        "display_name": _DISPLAY_NAME.get(filename, filename),  # 仅显示层；路径/slug 不改
        "version": _version_of(filename, text),
        "bytes": len(raw),
        "sha256": sha,
        "sha256_16": sha.upper()[:16],
    }


def _list_docs(family: str = _FAMILY) -> JSONResponse:
    entries = []
    for name in _PUBLIC_DOCS.get(family, ()):  # 未知族：空清单（路由层已 404，纵深防御）
        got = _read_doc(name)
        if got is None:
            # 已入站件缺失＝容器件异常：不静默减项，明示 fail-closed
            # L1SI153 段三②：error 机器字段设过渡期（两存：error＋detail＋code）——
            # DEPRECATED，下版删除；新判据一律读 code，⛔ 勿为新代码依赖 error
            return JSONResponse(
                with_code({"error": "DOC_SOURCE_UNAVAILABLE",
                           "detail": f"在册公开件暂不可读：{name}（文档源异常，已按 fail-closed 暂停列出）"}, 503),
                status_code=503)
        raw, sha = got
        entries.append(_entry(name, raw, sha, family))
    return JSONResponse({
        "family": family,
        "count": len(entries),
        "source": f"docs/{_FAMILY_DIRS.get(family, family)}（只读容器件·单一事实源）",
        "principle": "只列已入站公开件；未入站与存证件不出现（fail-closed）",
        "documents": entries,
    })


def _get_doc(slug: str) -> JSONResponse:
    got = _read_doc(slug)
    if got is None:
        # 统一 404：未入站件／乙类件／不存在件，对外不可分辨（fail-closed）
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    raw, sha = got
    entry = _entry(slug, raw, sha, _PUBLIC_FAMILY.get(slug, _FAMILY))
    entry["content"] = raw.decode("utf-8", "replace")
    return JSONResponse(entry)


def _guard(request: Request) -> JSONResponse | None:
    if _rate_limited(request.client.host if request.client else "unknown"):
        # L1SI153 段二②：裸英文退役 → 码表口径中文短句（RES-RES-001）
        return JSONResponse(with_code({"detail": "操作过于频繁，请稍后再试（限流 60 次/分钟/同一地址）"}, 429), status_code=429)
    return None


# ---------------------------------------------------------------------
# 主路由：GET /api/public/docs[/regulation[/slug]]
# ---------------------------------------------------------------------
@router.get("/docs")
def public_docs_list(request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    return _list_docs()


@router.get("/docs/{family}")
def public_docs_family(family: str, request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    if family not in _PUBLIC_DOCS:
        # L1SI154-010：族按公开清单判定（⛔ 非清单族一律 fail-closed 404）
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    return _list_docs(family)


@router.get("/docs/{family}/{slug:path}")
def public_docs_get(family: str, slug: str, request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    if family not in _PUBLIC_DOCS:
        # L1SI154-010：族按公开清单判定（⛔ 非清单族一律 fail-closed 404）
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    return _get_doc(slug)


# ---------------------------------------------------------------------
# 别名：旧 /api/site/docs/* —— 同一实现，⛔ 不双实现（施工令 §二）
# ---------------------------------------------------------------------
@alias_router.get("/docs")
def alias_docs_list(request: Request):
    return public_docs_list(request)


@alias_router.get("/docs/{family}")
def alias_docs_family(family: str, request: Request):
    return public_docs_family(family, request)


@alias_router.get("/docs/{family}/{slug:path}")
def alias_docs_get(family: str, slug: str, request: Request):
    return public_docs_get(family, slug, request)
