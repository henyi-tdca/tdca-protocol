# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-20260811-002-DUAL-PROTOCOL
# 目标函数:     MRCR 多角色兼容性管理器（场景隔离/独立审计/独立演化）
# 约束矩阵:     MRCR 多角色兼容性规则 + NSFL-V0.2 + 配置权边界
# 先验分布:     TDCA-DUAL-PROTOCOL-001-V1.0 设计稿
# 配置权边界:    L2 配置权市场层；角色权限按场景隔离
# 预期分配:     角色注册 / 权限检查 / 审计轨迹
# 审计轨迹:      TDCA-NCA-20260811-006-DUAL-PROTOCOL
# 开发者:       [人类签批人]
# 模拟态标注（ID92）: 本引擎为工具实现，不构成真实配置权执行路径
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
"""MRCR 多角色兼容性管理器 V1.0.0

实现场景隔离、独立审计、独立演化——用户在不同场景下持有不同层级配置权角色。
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional


class MRCRManager:
    """多角色兼容性规则管理器。"""

    ROLE_PERMISSIONS = {
        "Developer": ["code_generation", "testing", "documentation"],
        "Financial-Engineer": ["code_generation", "testing", "risk_validation"],
        "Medical-Engineer": ["code_generation", "testing", "clinical_review"],
        "Gov-Engineer": ["code_generation", "testing", "compliance_review"],
        "Auditor": ["review_all", "approve", "reject"],
        "Admin": ["all_permissions"],
    }

    SCENE_PROHIBITION_KEYS = {
        "Developer": "developer_prohibitions",
        "Financial-Engineer": "financial_prohibitions",
        "Medical-Engineer": "medical_prohibitions",
        "Gov-Engineer": "gov_prohibitions",
    }

    def __init__(self):
        self.role_registry: Dict[str, Dict[str, dict]] = {}
        self.scene_isolation: Dict[str, List[str]] = {}
        self.scene_nsfl_cache: Dict[str, dict] = {}

    # ---- 注册 ----

    def register_role(self, user_id: str, role: str, scene: str) -> None:
        """注册用户在特定场景下的角色（场景隔离）。"""
        if user_id not in self.role_registry:
            self.role_registry[user_id] = {}
        self.role_registry[user_id][scene] = {
            "role": role,
            "permissions": self._get_role_permissions(role),
            "prohibitions": self._get_role_prohibitions(role, scene),
            "audit_trail": [],
        }
        self.scene_isolation.setdefault(scene, []).append(user_id)

    def _get_role_permissions(self, role: str) -> List[str]:
        """获取角色权限。"""
        return self.ROLE_PERMISSIONS.get(role, [])

    def _get_role_prohibitions(self, role: str, scene: str) -> List[str]:
        """获取角色在场景下的禁止事项（从场景负空间加载）。"""
        scene_nsfl = self._load_scene_nsfl(scene)
        key = self.SCENE_PROHIBITION_KEYS.get(role)
        return scene_nsfl.get(key, []) if key else []

    def _load_scene_nsfl(self, scene: str) -> dict:
        """加载场景负空间规则（缓存）。"""
        if scene not in self.scene_nsfl_cache:
            self.scene_nsfl_cache[scene] = {}
        return self.scene_nsfl_cache[scene]

    def set_scene_prohibitions(self, scene: str, prohibitions: dict) -> None:
        """设置场景负空间规则（供测试/接入使用）。"""
        self.scene_nsfl_cache[scene] = prohibitions

    # ---- 权限 ----

    def check_permission(self, user_id: str, scene: str, action: str) -> bool:
        """检查用户在场景下是否有权限执行操作。"""
        user_roles = self.role_registry.get(user_id, {})
        scene_role = user_roles.get(scene)
        if not scene_role:
            return False
        if action in scene_role["prohibitions"]:
            return False
        if action in scene_role["permissions"] or "all_permissions" in scene_role["permissions"]:
            return True
        return False

    # ---- 审计 ----

    def audit_action(self, user_id: str, scene: str, action: str, result: bool) -> dict:
        """审计用户操作（独立审计）。"""
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "scene": scene,
            "action": action,
            "result": result,
            "role": self.role_registry.get(user_id, {}).get(scene, {}).get("role", "unknown"),
        }
        if user_id in self.role_registry and scene in self.role_registry[user_id]:
            self.role_registry[user_id][scene]["audit_trail"].append(audit_record)
        return audit_record

    # ---- 查询 ----

    def get_audit_trail(self, user_id: str, scene: str) -> List[dict]:
        """获取用户在场景下的审计轨迹（独立审计）。"""
        return self.role_registry.get(user_id, {}).get(scene, {}).get("audit_trail", [])

    def get_role(self, user_id: str, scene: str) -> Optional[str]:
        """获取用户在场景下的角色。"""
        return self.role_registry.get(user_id, {}).get(scene, {}).get("role")

    def scene_users(self, scene: str) -> List[str]:
        """获取场景内用户（场景隔离视图）。"""
        return self.scene_isolation.get(scene, [])
