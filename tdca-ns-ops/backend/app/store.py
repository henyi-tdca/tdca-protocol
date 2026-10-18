# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——约束存储层（JSON 持久化）+ NCA 存证引擎
# 约束矩阵:     宪法十六条 + BV-5（全操作 NCA 存证）+ BV-3（人类写权门校验在路由层）
# 先验分布:     MEMO-006 附录 C NCA 11 字段规范 | 论丛 NS-011 §4.2 NSAR-Registry
# 配置权边界:    L2 层；存储层仅读写本工程数据目录，不触碰权威空间
# 预期分配:     JSON 文件持久化（data/）+ NCA YAML 生成；失败=文件锁/IO 异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""NS-OPS M1 存储与 NCA 存证层。

制度锚定: FC-NS-OPS-001 F6（NCA 存证）/ MEMO-006 附录 C | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 数据目录（工程内，绝不触碰权威空间 tdca-official-kb）
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_NCA_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".tdca-nca"

_lock = threading.RLock()


# ---------------------------------------------------------------------------
# 存储基座
# ---------------------------------------------------------------------------


def _ensure_dirs() -> None:
    """确保数据目录存在。"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _NCA_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    """UTC 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def load_collection(name: str) -> list[dict]:
    """读取 JSON 集合（约束/调整）。"""
    _ensure_dirs()
    path = _DATA_DIR / f"{name}.json"
    if not path.exists():
        return []
    with _lock:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def save_collection(name: str, items: list[dict]) -> None:
    """原子写入 JSON 集合（临时文件+rename，防写坏）。"""
    _ensure_dirs()
    path = _DATA_DIR / f"{name}.json"
    tmp = path.with_suffix(".json.tmp")
    with _lock:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        tmp.replace(path)


def get_item(name: str, key: str, value: str) -> dict | None:
    """按键查单条。"""
    for item in load_collection(name):
        if item.get(key) == value:
            return item
    return None


def upsert_item(name: str, item: dict, key: str = "id") -> dict:
    """按主键插入或更新。返回写入后的条目。"""
    items = load_collection(name)
    for i, it in enumerate(items):
        if it.get(key) == item.get(key):
            items[i] = item
            save_collection(name, items)
            return item
    items.append(item)
    save_collection(name, items)
    return item


def raw_to_model(raw: dict):
    """JSON dict → Constraint 模型（供业务引擎复用，M6：消除对路由层依赖）。"""
    from .models import Constraint

    return Constraint.model_validate(raw)


def hash_text(data: str | bytes) -> str:
    """SHA-256 摘要（审计轨迹用）。"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# NCA 存证引擎（BV-5 / MEMO-006 附录 C 11 字段）
# ---------------------------------------------------------------------------


def generate_nca(
    fc_id: str,
    operation: str,
    scope: str,
    pre_hash: str,
    post_hash: str,
    operator: str = "Reasonix",
    human_signature_required: bool = True,
    nca_type: str = "CODE",
    signer: str | None = None,
    nsfl_triggered: bool = False,
    nsfl_reason: str | None = None,
) -> dict:
    """生成 NCA 记录（MEMO-006 附录 C 11 字段），写 YAML 并返回记录。

    六要素声明:
    目标函数: 为一次受控操作生成不可篡改的 NCA 存证
    约束矩阵: 输入——fc_id/operation 非空，前后哈希为 64 位 hex；输出——YAML 落盘 + 返回 dict；
              禁止——不触碰权威空间、不伪造人类签名
    先验分布: MEMO-006 附录 C 字段规范 | .tdca-nca/ 既有 NCA 文件序列
    配置权边界: L2 层；存证仅追加，不修改既有 NCA
    预期分配: 返回 NCA dict；副作用=写 YAML；失败=IO 异常
    审计轨迹: 输入哈希=scope；输出哈希=post_hash；时间戳；NCA-ID 自引用
    """
    _ensure_dirs()
    ts = _now()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"TDCA-{operator.upper()}"
    # M1/E4/T-3 修复：seq 计算（按最大序号而非数量，防空洞复用覆盖）+ 文件写入在同一锁区间
    with _lock:
        existing = [p for p in _NCA_DIR.glob(f"NCA-{prefix}-{date_str}-*.yaml")]
        seqs = []
        for p in existing:
            try:
                seqs.append(int(p.stem.split("-")[-1]))
            except ValueError:
                continue
        seq = (max(seqs) if seqs else 0) + 1
        nca_id = f"{prefix}-{date_str}-{seq:03d}"
        yaml_path = _NCA_DIR / f"NCA-{nca_id}.yaml"
        # T-3 防御：目标路径已存在则继续递增，绝不覆盖既有存证
        while yaml_path.exists():
            seq += 1
            nca_id = f"{prefix}-{date_str}-{seq:03d}"
            yaml_path = _NCA_DIR / f"NCA-{nca_id}.yaml"

        record = {
            "NCA-ID": nca_id,
            "Function-Call-ID": fc_id,
            "Operation-Type": operation,
            "Operator": operator,
            "Timestamp": ts,
            "Scope": scope,
            "Pre-State": {"Hash": pre_hash, "Size": len(pre_hash)},
            "Post-State": {"Hash": post_hash, "Size": len(post_hash)},
            "Config-Right-Token": {
                "Scope": scope,
                "Rollback": "回退至上一次通过版本",
                "Audit-Trail": f"NCA {nca_id} 文件记录",
                "Human-Signature-Required": human_signature_required,
                "Max-Retry": 0,
                "Granted-By": "TDCA-MEMO-006",
                "Expires": None,
            },
            "Audit-Trail": [{"Step": f"操作执行: {operation}", "Time": ts, "Evidence": post_hash}],
            "Human-Signature": {
                "Status": "Signed" if signer else ("Pending" if human_signature_required else "NotRequired"),
                "Signed-By": signer,
                "Signed-At": ts if signer else None,
            },
            "Negative-Space-Check": {
                "NSFL-Version": "V0.1",
                "Triggered": nsfl_triggered,
                "Trigger-Reason": nsfl_reason,
                "NCA-Type": nca_type,
            },
        }

        # YAML 输出（不依赖 pyyaml 的工程内 NCA——统一用 JSON 兼容格式写 YAML 风格文件）
        _write_nca_file(yaml_path, record)
    return record


def _write_nca_file(path: Path, record: dict[str, Any]) -> None:
    """以 YAML 风格写 NCA 文件（缩进 2 空格，unicode 直出）。"""
    lines: list[str] = []
    for k, v in record.items():
        _dump_pair(lines, k, v, 0)
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def _dump_pair(lines: list[str], key: str, value: Any, indent: int) -> None:
    """YAML 风格键值序列化（支持 dict/list 嵌套）。"""
    pad = "  " * indent
    if isinstance(value, dict):
        lines.append(f"{pad}{key}:")
        for k, v in value.items():
            _dump_pair(lines, k, v, indent + 1)
    elif isinstance(value, list):
        lines.append(f"{pad}{key}:")
        for item in value:
            if isinstance(item, dict):
                for i, (k, v) in enumerate(item.items()):
                    if i == 0:
                        lines.append(f"{pad}- {k}: {_scalar(v)}")
                    else:
                        lines.append(f"{pad}  {k}: {_scalar(v)}")
            else:
                lines.append(f"{pad}- {_scalar(item)}")
    else:
        lines.append(f"{pad}{key}: {_scalar(value)}")


def _scalar(v: Any) -> str:
    """标量序列化。"""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if ":" in s or s.startswith((" ", "-", "?", "#", "'", '"')):
        return f"'{s}'"
    return s
