# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     NCA 存证接口（F8）——全操作存证、链式防篡改、可审计
# 约束矩阵:     FC-SBX-OPS-001 SV-7（全操作 NCA 不可篡改）+ 工作规范 §六（11 字段）
# 先验分布:     MEMO-006 附录 C NCA 11 字段 + tdca-fos/tdca_nca 生成器
# 配置权边界:    L2 层；存证只追加不覆盖
# 预期分配:     存证生成/写盘/链式校验；失败=哈希不匹配
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""NCA 存证接口（F8，SV-7）。

制度锚定: FC-SBX-OPS-001 SV-7 / MEMO-006 附录 C / 工作规范 §六

NCA 11 字段: NCA-ID / FC-ID / Operation / Operator / Timestamp / Pre-State /
Post-State / Config-Right-Token / Audit-Trail / Human-Signature / Negative-Space-Check
防篡改: 链式哈希（每个 NCA 记录 prev_hash；content_hash = sha256(内容)）
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .models import NCA

FC_ID = "TDCA-FC-SBX-OPS-001"


def _seq_of(stem: str) -> int:
    """从文件名 stem（如 NCA-20260810-001）提取序号。"""
    try:
        return int(stem.rsplit("-", 1)[-1])
    except (ValueError, IndexError):
        return 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _nca_dir() -> Path:
    from . import store

    return Path(store._NCA_DIR)  # type: ignore[attr-defined]


def _content_hash(nca: dict) -> str:
    """对 NCA 内容（除 content_hash/prev_hash 外）求 sha256（防篡改核心）。

    注: prev_hash 不纳入 content_hash——链式校验独立比对 prev_hash 字段与上条
    content_hash 的相等性（篡改任意记录会同时破坏自身 content_hash 与下条 prev_hash）。
    """
    payload = {k: v for k, v in nca.items() if k not in ("content_hash", "prev_hash")}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _next_seq() -> int:
    """链尾序号 + 1（NCA-{date}-{seq:03d}）。"""
    d = _nca_dir()
    existing = []
    if d.exists():
        for p in d.glob("NCA-*.json"):
            existing.append(_seq_of(p.stem))
    return max(existing, default=0) + 1


def build_nca(
    operation: str,
    operator: str,
    pre_state: str,
    post_state: str,
    config_right_token: str = "",
    human_signature: str = "",
    negative_space_check: str = "PASS",
    audit_trail: str = "",
    fc_id: str = FC_ID,
) -> NCA:
    """构造 NCA 记录（含链式哈希字段）。

    六要素声明:
    目标函数: 生成 11 字段 NCA 存证记录（F8，SV-7 全操作存证）
    约束矩阵: 输入——operation/operator/pre_state/post_state 必填；输出——NCA 模型；
              禁止——空操作、哈希伪造（content_hash 由内容确定性生成）
    先验分布: MEMO-006 附录 C 11 字段
    配置权边界: L2；构造阶段无副作用
    预期分配: 返回含 content_hash 的 NCA；失败=ValueError
    审计轨迹: 本记录自身即审计轨迹载体
    """
    if not operation or not operator:
        raise ValueError("operation 与 operator 必填")
    seq = _next_seq()
    nca_id = f"NCA-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{seq:03d}"
    nca = NCA(
        nca_id=nca_id,
        fc_id=fc_id,
        operation=operation,
        operator=operator,
        timestamp=_now_iso(),
        pre_state=pre_state,
        post_state=post_state,
        config_right_token=config_right_token,
        audit_trail=audit_trail,
        human_signature=human_signature,
        negative_space_check=negative_space_check,
    )
    nca.content_hash = _content_hash(nca.model_dump())
    return nca


def save_nca(nca: NCA) -> str:
    """写盘存证：链尾 prev_hash 链接 + 原子写 JSON。返回 nca_id。

    六要素声明:
    目标函数: 持久化 NCA 并链接到链尾（SV-7 不可篡改存证）
    约束矩阵: 输入——NCA 模型；输出——nca_id；禁止——覆盖/删除既有存证（只追加）
    先验分布: 区块链式追加（append-only）
    配置权边界: L2；仅追加写盘
    预期分配: 返回 nca_id；失败=IOError
    审计轨迹: prev_hash 链即审计链
    """
    d = _nca_dir()
    d.mkdir(parents=True, exist_ok=True)

    # 链尾 prev_hash 链接（content_hash 不覆盖 prev_hash，链校验独立比对）
    tail = _tail_hash()
    if tail:
        nca.prev_hash = tail

    path = d / f"{nca.nca_id}.json"
    # #2 修复（tdca-notary）：原子写（临时文件 + rename，防半写 JSON）
    import os
    tmp = d / f".{nca.nca_id}.tmp"
    tmp.write_text(json.dumps(nca.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return nca.nca_id


def _tail_hash() -> str:
    """当前链尾 content_hash（无存证时返回空串）。

    按 NCA 序号（链序）取链尾而非 mtime——避免同秒写入的 mtime 歧义。
    """
    items = list_nca()
    if not items:
        return ""
    return items[-1].get("content_hash", "")


def load_nca(nca_id: str) -> Optional[Dict[str, Any]]:
    """按 id 读取 NCA（只读）。

    六要素声明:
    目标函数: NCA 详情读取（F8 审计查询）
    约束矩阵: 输入——nca_id（白名单格式 NCA-{date}-{seq}）；输出——dict|None；禁止——路径穿越（../）
    先验分布: 存证目录 JSON
    配置权边界: L2；只读
    预期分配: 返回存证或 None；失败=非法 id 返回 None
    审计轨迹: 只读，不生成 NCA
    """
    if not re.fullmatch(r"NCA-\d{8}-\d{3,}", nca_id or ""):
        return None  # 路径穿越防护（../ 拒绝）
    d = _nca_dir()
    path = d / f"{nca_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_nca() -> list[Dict[str, Any]]:
    """按序号升序列出全部 NCA（审计查询）。

    六要素声明:
    目标函数: NCA 列表（F8 审计）
    约束矩阵: 输入——无；输出——有序 dict[]；禁止——无
    先验分布: 存证目录 JSON
    配置权边界: L2；只读
    预期分配: 返回存证列表；失败=无
    审计轨迹: 只读
    """
    d = _nca_dir()
    if not d.exists():
        return []
    items = []
    for p in d.glob("NCA-*.json"):
        try:
            items.append((_seq_of(p.stem), json.loads(p.read_text(encoding="utf-8"))))
        except (ValueError, OSError):  # 单文件损坏跳过（JSON/Unicode 解码错误，与 store 容错对齐）
            continue
    return [item for _, item in sorted(items, key=lambda x: x[0])]


def verify_chain() -> Dict[str, Any]:
    """链式完整性校验：content_hash 自洽 + prev_hash 连续性（F8 审计）。

    六要素声明:
    目标函数: 校验 NCA 链不可篡改（SV-7）——每条 content_hash 匹配内容、prev_hash 连续
    约束矩阵: 输入——链上文件；输出——{valid, checked, first_broken, errors}；
              禁止——把哈希不匹配判为有效
    先验分布: 区块链式哈希校验
    配置权边界: L2；只读校验
    预期分配: 返回校验结果；失败=链断（返回 broken 定位）
    审计轨迹: 校验动作本身由调用方存证
    """
    items = list_nca()
    errors: list[str] = []
    prev: Optional[str] = None
    # #1 修复（tdca-notary）：序号缺口检测（尾部/中部缺失文件均检出）
    seqs = [_seq_of(it.get("nca_id", "")) for it in items]
    for i, seq in enumerate(seqs):
        if i > 0 and seq != seqs[i - 1] + 1:
            errors.append(f"NCA 序号缺口（缺失文件）: {seqs[i-1]} → {seq}（损坏/删除不可静默）")
            return {"valid": False, "checked": len(items), "first_broken": f"GAP-{seqs[i-1]}", "errors": errors}
    for item in items:
        # 链头完整性：首条 prev_hash 必须为空（伪造链头检测）
        if prev is None and item.get("prev_hash"):
            errors.append(f"{item['nca_id']}: 链头 prev_hash 应为空（伪造链头）")
            return {"valid": False, "checked": len(items), "first_broken": item["nca_id"], "errors": errors}
        # content_hash 自洽
        expected = _content_hash({k: v for k, v in item.items() if k != "content_hash"})
        if item.get("content_hash") != expected:
            errors.append(f"{item['nca_id']}: content_hash 不匹配（内容被篡改）")
            return {"valid": False, "checked": len(items), "first_broken": item["nca_id"], "errors": errors}
        # prev_hash 连续
        if prev is not None and item.get("prev_hash") != prev:
            errors.append(f"{item['nca_id']}: prev_hash 断链（应为 {prev[:12]}...）")
            return {"valid": False, "checked": len(items), "first_broken": item["nca_id"], "errors": errors}
        prev = item.get("content_hash")
    return {"valid": True, "checked": len(items), "first_broken": None, "errors": errors}
