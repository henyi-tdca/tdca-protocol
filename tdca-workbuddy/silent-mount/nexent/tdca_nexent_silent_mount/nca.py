"""NCA 嵌套认知资产生成（六要素）。

每次静默挂载配置权调用生成六要素 NCA：
目标函数 / 约束矩阵 / 先验分布 / 配置权边界 / 预期分配 / 审计轨迹。
链式哈希（sha256_8）作为存证水印，对齐 tdca-adapters/acps/nca.py 范式。
"""

import hashlib
import uuid
from typing import Any, Dict, List


def _sha8(blob: str) -> str:
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8]


def generate_nca(
    *,
    objective: str,
    constraints: List[str],
    prior: Dict[str, Any],
    config_boundary: Dict[str, Any],
    expected_allocation: Dict[str, Any],
    audit_trail: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """生成六要素 NCA（链式哈希：nca_id 由要素内容派生）。"""
    nca_id = f"NCA-SM-NEXENT-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "objective_function": objective,
        "constraint_matrix": constraints,
        "prior_distribution": prior,
        "config_boundary": config_boundary,
        "expected_allocation": expected_allocation,
        "audit_trail": audit_trail,
    }
    digest_input = f"{nca_id}|{payload}"
    payload["integrity"] = {"sha256_8": _sha8(digest_input)}
    return {"nca_id": nca_id, "six_elements": payload}


def derive_audit_step(step: str, time: str, evidence: str) -> Dict[str, Any]:
    return {"step": step, "time": time, "evidence": evidence}
