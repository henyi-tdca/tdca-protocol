# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3-7 扩展：沙盒四维取数只读接口）
# 目标函数:     NCA-SANDBOX-FEED-001——熔断事件／正和／MOU 锚定／化合链 四维只读读数
#               批量包 {generated_at, pool_ref, dimensions[4]}，供审计报告八维 3.2~3.5
# 约束矩阵:     交办令 §2 十字段契约（缺数据必为 null·⛔0；as_of 带时区；note ⛔ 留白）
#               + §3 停手五条（纯读·⛔ 写引擎·⛔ 造数·⛔ 凭据）+ 接口熵=0
# 先验分布:     routes/chem.py:81-89（只读 GET 先例）+ nca_logger.list_nca（append-only 账本）
# 配置权边界:    L2 层；只读遍历 store/nca_logger，绝不 build_nca/save_nca/save_sandbox
# 预期分配:     REST 端点；失败=500（单源异常时该维转 OUT-OF-LEDGER-NOT-CONNECTED 照常返回）
# 审计轨迹:      只读，不生成 NCA（读数不写存证，照 routes 只读先例）
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""沙盒四维取数只读 API（NCA-SANDBOX-FEED-001）。

制度锚定: FC-SBX-OPS-001 M3-7 | SPDX-License-Identifier: TDCA-Internal

口径纪律（⛔ 混算）：
- FUSE_EVENTS  单源＝NCA 存证账本（append-only，事件天然去重）；
- POSITIVE_SUM 单源＝沙盒 positive_sum_logs 中含 delta 的记录（交付确认记录无 delta，不计）；
- MOU_ANCHOR   单源＝沙盒 mou_logs；
- COMPOUND_CHAIN 单源＝沙盒 reactions。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import nca_logger, store
from ..models import Sandbox

router = APIRouter(
    prefix="/api/v1/sandbox-feed",
    tags=["沙盒四维取数（NCA-SANDBOX-FEED-001·纯读）"],
)

_MetricId = Literal["FUSE_EVENTS", "POSITIVE_SUM", "MOU_ANCHOR", "COMPOUND_CHAIN"]
_Unit = Literal["count", "pct", "ratio"]
_Space = Literal["NS", "SBX", "PCM"]
_Status = Literal["OK", "OUT-OF-LEDGER-NOT-CONNECTED", "PARTIAL"]


class MetricDimension(BaseModel):
    """单维读数十字段（交办令 §2.1 契约，字段不得增减）。"""

    metric_id: _MetricId
    value: Optional[Union[int, float]] = Field(description="读数；缺数据必为 null（⛔ 以 0 冒充）")
    unit: _Unit
    basis: str = Field(description="口径一句（⛔ 件数与事件数混算）")
    sample: Optional[int] = Field(description="分母")
    as_of: str = Field(description="数据时点（ISO 8601 带时区；无时区即不合规）")
    space: _Space
    source_module: List[str]
    status: _Status
    note: str = Field(description="缺数原因／口径限制（⛔ 留白）")


class SandboxFeed(BaseModel):
    """四维批量包（交办令 §2.2：pool_ref 锚生成时点；同 pool_ref 同口径同值）。"""

    generated_at: str
    pool_ref: str
    dimensions: List[MetricDimension]


def _pool_ref(sandboxes: List[Sandbox], nca_items: List[Dict[str, Any]]) -> str:
    """沙盒池快照哈希：池内全部沙盒内容（按 id 排序）＋NCA 链尾 content_hash。

    只锚数据内容、不含时间戳——数据不变则 pool_ref 不变（幂等锚）。
    """
    payload = {
        "pool": "tdca-sandbox-pool",
        "sandboxes": sorted(
            (s.model_dump(mode="json") for s in sandboxes),
            key=lambda d: d.get("sandbox_id", ""),
        ),
        "nca_tail": nca_items[-1].get("content_hash") if nca_items else None,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _dim_fuse(nca_items: List[Dict[str, Any]], nca_ok: bool, generated_at: str) -> MetricDimension:
    """熔断事件：NCA 账本 negative_space_check=='FUSE' 存证条数（事件数口径）。"""
    basis = (
        "事件数＝NCA 存证账本中 negative_space_check=='FUSE' 之存证条数"
        "（append-only 账本，一事一证天然去重；⛔ 与沙盒内嵌字段混算）"
    )
    if not nca_ok:
        return MetricDimension(
            metric_id="FUSE_EVENTS",
            value=None,
            unit="count",
            basis=basis,
            sample=None,
            as_of=generated_at,
            space="SBX",
            source_module=["nca_logger"],
            status="OUT-OF-LEDGER-NOT-CONNECTED",
            note="NCA 存证账本不可达（读取异常），无法计熔断事件；"
            "未以沙盒内嵌熔断字段替代（混算禁令），据实报缺",
        )
    fuses = [n for n in nca_items if n.get("negative_space_check") == "FUSE"]
    if fuses:
        as_of = str(fuses[-1].get("timestamp") or generated_at)
        note = f"账本在册 {len(nca_items)} 条存证，其中 FUSE {len(fuses)} 条；最近 FUSE 存证时点见 as_of"
    else:
        as_of = str(nca_items[-1].get("timestamp") or generated_at) if nca_items else generated_at
        note = f"账本在册 {len(nca_items)} 条存证，FUSE 0 条（事件数真实为零，非缺数据）"
    return MetricDimension(
        metric_id="FUSE_EVENTS",
        value=len(fuses),
        unit="count",
        basis=basis,
        sample=len(nca_items),
        as_of=as_of,
        space="SBX",
        source_module=["nca_logger"],
        status="OK",
        note=note,
    )


def _dim_positive_sum(sandboxes: List[Sandbox], generated_at: str) -> MetricDimension:
    """正和：池内最近一条含 delta 验证记录之协同剩余（delta＝联盟效用−独立效用和）。"""
    basis = (
        "最近一条含 delta 的正和验证记录之协同剩余"
        "（delta＝coalition_utility − Σindependent_utilities）；"
        "分母＝池内含 delta 的验证记录数（交付确认记录无 delta，⛔ 计入）"
    )
    entries: List[Tuple[Dict[str, Any], Sandbox]] = [
        (log, sb)
        for sb in sandboxes
        for log in (sb.positive_sum_logs or [])
        if isinstance(log, dict) and "delta" in log
    ]
    if not entries:
        return MetricDimension(
            metric_id="POSITIVE_SUM",
            value=None,
            unit="ratio",
            basis=basis,
            sample=0,
            as_of=generated_at,
            space="SBX",
            source_module=["utility_genie_adapter", "genie_callback", "sandbox_core"],
            status="OUT-OF-LEDGER-NOT-CONNECTED",
            note=f"沙盒池 {len(sandboxes)} 沙盒均无含 delta 的正和验证记录"
            "（F6 验证尚未运行），据实报缺（⛔ 回 0）",
        )

    # 键＝(时间戳, 池内序号)；秒级同戳时取后写者（append 序即时间序）
    def _key(item: Tuple[int, Dict[str, Any], Sandbox]) -> Tuple[str, int]:
        idx, log, sb = item
        return (str(log.get("timestamp") or sb.updated_at or ""), idx)

    indexed = [(i, log, sb) for i, (log, sb) in enumerate(entries)]
    _, log, sb = max(indexed, key=_key)
    note = f"判定 is_positive_sum={log.get('is_positive_sum')}；fuse={log.get('fuse')}"
    if "positive_sum_index" in log:
        note += f"；positive_sum_index={log.get('positive_sum_index')}"
    return MetricDimension(
        metric_id="POSITIVE_SUM",
        value=log["delta"],
        unit="ratio",
        basis=basis,
        sample=len(entries),
        as_of=str(log.get("timestamp") or sb.updated_at or generated_at),
        space="SBX",
        source_module=["utility_genie_adapter", "genie_callback", "sandbox_core"],
        status="OK",
        note=note,
    )


def _dim_mou(sandboxes: List[Sandbox], generated_at: str) -> MetricDimension:
    """MOU 锚定：池内 mou_logs 记录数（现全为模拟锚定）。"""
    basis = (
        "沙盒池 MOU 锚定记录数（CB-IF-001）；现全为模拟锚定"
        "（source=SIMULATED-TAX-AUTHORITY 显式标记），真实锚定永不在沙盒内发生"
    )
    anchors: List[Tuple[Dict[str, Any], Sandbox]] = [
        (log, sb)
        for sb in sandboxes
        for log in (sb.mou_logs or [])
        if isinstance(log, dict)
    ]
    if not anchors:
        return MetricDimension(
            metric_id="MOU_ANCHOR",
            value=None,
            unit="count",
            basis=basis,
            sample=len(sandboxes),
            as_of=generated_at,
            space="SBX",
            source_module=["cbdc_anchor", "sright"],
            status="OUT-OF-LEDGER-NOT-CONNECTED",
            note=f"沙盒池 {len(sandboxes)} 沙盒均无 MOU 锚定记录"
            "（CB-IF-001 尚未锚定），据实报缺（⛔ 回 0）",
        )
    verified = sum(1 for log, _ in anchors if log.get("verified"))
    as_of = max((str(sb.updated_at or "") for _, sb in anchors), default="") or generated_at
    return MetricDimension(
        metric_id="MOU_ANCHOR",
        value=len(anchors),
        unit="count",
        basis=basis,
        sample=len(sandboxes),
        as_of=as_of,
        space="SBX",
        source_module=["cbdc_anchor", "sright"],
        status="OK",
        note=f"已核 verified={verified}／总 {len(anchors)} 条；锚记录无内嵌时间戳，"
        "as_of 取最近回写沙盒 updated_at",
    )


def _dim_compound(sandboxes: List[Sandbox], generated_at: str) -> MetricDimension:
    """化合链：池内 reactions 反应轨迹记录数（正向＋反向合计）。"""
    basis = (
        "沙盒池化合反应轨迹记录数（F5：CHEM-001 正向 combined ＋"
        " CHEM-002 反向 pending_governance 合计，⛔ 去重）"
    )
    rxns: List[Tuple[Dict[str, Any], Sandbox]] = [
        (r, sb)
        for sb in sandboxes
        for r in (sb.reactions or [])
        if isinstance(r, dict)
    ]
    if not rxns:
        return MetricDimension(
            metric_id="COMPOUND_CHAIN",
            value=None,
            unit="count",
            basis=basis,
            sample=len(sandboxes),
            as_of=generated_at,
            space="SBX",
            source_module=["chem_engine", "sandbox_core"],
            status="OUT-OF-LEDGER-NOT-CONNECTED",
            note=f"沙盒池 {len(sandboxes)} 沙盒均无化合反应轨迹"
            "（F5 化合尚未运行），据实报缺（⛔ 回 0）",
        )
    kinds: Dict[str, int] = {}
    for r, _ in rxns:
        k = str(r.get("chem_type") or "UNKNOWN")
        kinds[k] = kinds.get(k, 0) + 1
    as_of = max((str(sb.updated_at or "") for _, sb in rxns), default="") or generated_at
    return MetricDimension(
        metric_id="COMPOUND_CHAIN",
        value=len(rxns),
        unit="count",
        basis=basis,
        sample=len(sandboxes),
        as_of=as_of,
        space="SBX",
        source_module=["chem_engine", "sandbox_core"],
        status="OK",
        note="构成 " + "；".join(f"{k}={v}" for k, v in sorted(kinds.items()))
        + "；反应记录无内嵌时间戳，as_of 取最近回写沙盒 updated_at",
    )


@router.get("", response_model=SandboxFeed, summary="沙盒四维取数批量包（纯读）")
def sandbox_feed() -> SandboxFeed:
    """四维只读读数（审计报告八维 3.2~3.5 供数源）。

    六要素声明:
    目标函数: NCA-SANDBOX-FEED-001 批量包（熔断／正和／MOU／化合链）
    约束矩阵: 十字段契约（缺数据 null·⛔0；as_of 带时区；note ⛔ 留白）；纯读——
              仅 list_sandboxes/list_nca 遍历，⛔ build_nca/save_nca/save_sandbox/ADAPTER
    先验分布: routes/chem.py 只读 GET 模式 + 交办令 §2
    配置权边界: L2；只读，无写副作用（数据目录的首建属存储层既有先例）
    预期分配: 200 + 批量包；单源异常时该维转 OUT-OF-LEDGER-NOT-CONNECTED 照常返回
    审计轨迹: 只读，不生成 NCA（读数不写存证）
    """
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sandboxes = store.list_sandboxes()  # 只读，不生成 NCA（store 层既有语义）
    try:
        nca_items = nca_logger.list_nca()
        nca_ok = True
    except OSError:
        nca_items, nca_ok = [], False
    return SandboxFeed(
        generated_at=generated_at,
        pool_ref=_pool_ref(sandboxes, nca_items),
        dimensions=[
            _dim_fuse(nca_items, nca_ok, generated_at),
            _dim_positive_sum(sandboxes, generated_at),
            _dim_mou(sandboxes, generated_at),
            _dim_compound(sandboxes, generated_at),
        ],
    )
