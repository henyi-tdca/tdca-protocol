# SPDX-License-Identifier: Apache-2.0
"""tdca_ecoscan · 来源适配层（发现层扩源 W-1）

把 T-2~T-6 来源的记录翻成 ScanTarget 统一形状：
  T-2 dataset（数据集）／T-3 model（模型）／T-4 saas／T-5 portal／T-6 page（散页）

约束：
  · 纯函数、⛔ 无网络——T-4/T-5 抓取合规留白未开（S-4），调用方须自备原始记录；
  · 缺必填键 fail-closed 拒绝（ValueError），不静默丢弃；
  · ScanTarget 只增字段（source_type/evidence_ref/permalink），旧字段与既有调用不受影响。
"""
from __future__ import annotations

from typing import Dict, Optional

from .scanner import ScanTarget

SOURCE_GITHUB = "github"     # T-1（EcoScanner.scan_github 原生路径）
SOURCE_DATASET = "dataset"   # T-2
SOURCE_MODEL = "model"       # T-3
SOURCE_SAAS = "saas"         # T-4（抓取未开，仅适配自备记录）
SOURCE_PORTAL = "portal"     # T-5（抓取未开，仅适配自备记录）
SOURCE_PAGE = "page"         # T-6

SUPPORTED_SOURCES = (SOURCE_DATASET, SOURCE_MODEL, SOURCE_SAAS, SOURCE_PORTAL, SOURCE_PAGE)


def _need(rec: Dict, key: str, source: str) -> str:
    """必填键取值（fail-closed：缺失/空串即拒绝）。"""
    v = rec.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"[ADAPTER] {source} 记录缺必填键: {key}")
    return v.strip()


def _opt(rec: Dict, *keys: str) -> Optional[str]:
    for k in keys:
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _to_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def adapt_dataset(rec: Dict) -> ScanTarget:
    """T-2 数据集 → 统一形状（如数据卡片导出记录）。"""
    return ScanTarget(
        repo_full=_need(rec, "id", SOURCE_DATASET),
        stars=_to_int(rec.get("downloads")),
        license_spdx=_opt(rec, "license"),
        pushed_at=_opt(rec, "lastModified", "updated_at", "pushed_at"),
        description=(_opt(rec, "card_summary", "description") or "")[:200],
        keywords=list(rec.get("tags") or rec.get("keywords") or []),
        url=_need(rec, "url", SOURCE_DATASET),
        source_type=SOURCE_DATASET,
        evidence_ref=_opt(rec, "card_ref", "evidence_ref"),
        permalink=_opt(rec, "revision", "commit") or _opt(rec, "permalink"),
    )


def adapt_model(rec: Dict) -> ScanTarget:
    """T-3 模型 → 统一形状。"""
    return ScanTarget(
        repo_full=_need(rec, "id", SOURCE_MODEL),
        stars=_to_int(rec.get("likes") or rec.get("downloads")),
        license_spdx=_opt(rec, "license"),
        pushed_at=_opt(rec, "lastModified", "updated_at"),
        description=(_opt(rec, "card_summary", "description") or "")[:200],
        keywords=list(rec.get("tags") or rec.get("keywords") or []),
        url=_need(rec, "url", SOURCE_MODEL),
        source_type=SOURCE_MODEL,
        evidence_ref=_opt(rec, "card_ref", "evidence_ref"),
        permalink=_opt(rec, "revision", "commit", "permalink")
        or _opt(rec, "card_ref", "evidence_ref"),
    )


def adapt_saas(rec: Dict) -> ScanTarget:
    """T-4 SaaS 服务 → 统一形状（仅适配自备记录；抓取未开）。"""
    return ScanTarget(
        repo_full=_need(rec, "name", SOURCE_SAAS),
        stars=0,
        license_spdx=_opt(rec, "license"),   # 服务通常无 SPDX；无声明交许可分档器判不可判
        pushed_at=_opt(rec, "updated_at"),
        description=(_opt(rec, "summary", "description") or "")[:200],
        keywords=list(rec.get("keywords") or []),
        url=_need(rec, "url", SOURCE_SAAS),
        source_type=SOURCE_SAAS,
        evidence_ref=_opt(rec, "api_ref", "docs_ref", "evidence_ref"),
        permalink=_opt(rec, "tos_url", "permalink"),
    )


def adapt_portal(rec: Dict) -> ScanTarget:
    """T-5 门户/目录站 → 统一形状（仅适配自备记录；抓取未开）。"""
    return ScanTarget(
        repo_full=_need(rec, "name", SOURCE_PORTAL),
        stars=0,
        license_spdx=_opt(rec, "license"),
        pushed_at=_opt(rec, "updated_at"),
        description=(_opt(rec, "summary", "description") or "")[:200],
        keywords=list(rec.get("keywords") or []),
        url=_need(rec, "url", SOURCE_PORTAL),
        source_type=SOURCE_PORTAL,
        evidence_ref=_opt(rec, "catalog_ref", "entry_ref", "evidence_ref"),
        permalink=_opt(rec, "permalink") or _opt(rec, "catalog_ref", "entry_ref"),
    )


def adapt_page(rec: Dict) -> ScanTarget:
    """T-6 散页 → 统一形状。"""
    return ScanTarget(
        repo_full=_need(rec, "title", SOURCE_PAGE),
        stars=0,
        license_spdx=_opt(rec, "license"),
        pushed_at=_opt(rec, "updated_at", "retrieved_at"),
        description=(_opt(rec, "summary") or "")[:200],
        keywords=list(rec.get("keywords") or []),
        url=_need(rec, "url", SOURCE_PAGE),
        source_type=SOURCE_PAGE,
        evidence_ref=_opt(rec, "snapshot_ref", "evidence_ref"),
        permalink=_opt(rec, "permalink") or _opt(rec, "snapshot_ref"),
    )


_ADAPTERS = {
    SOURCE_DATASET: adapt_dataset,
    SOURCE_MODEL: adapt_model,
    SOURCE_SAAS: adapt_saas,
    SOURCE_PORTAL: adapt_portal,
    SOURCE_PAGE: adapt_page,
}


def adapt(source_type: str, rec: Dict) -> ScanTarget:
    """按来源类型分派适配（未知来源 fail-closed 拒绝）。"""
    fn = _ADAPTERS.get(source_type)
    if fn is None:
        raise ValueError(f"[ADAPTER] 未知来源类型: {source_type}（支持: {', '.join(SUPPORTED_SOURCES)}）")
    return fn(rec)
