#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# 交付:        通知机规范包（层 3 场景化合 · MRCR 扩展）
# 目标函数:     通知机 NM-* 四角色 MRCR 注册扩展（TDID ↔ 场景角色，FC-SPEC §3.2）
# 约束矩阵:     五元拓扑 + 最小化合（日抛优先） + NSFL-V0.2 + FC-SPEC 澄清 C（物理/制度负空间区分）
# 先验分布:     MRCRManager（DUAL-PROTOCOL V1.1，FROZEN）+ scene-phy-notification 场景制度
# 配置权边界:    L2 配置权市场层；Config-Right-Token 不上芯片（澄清 A）；人类签批归 TCN 慢系统
# 预期分配:     NM-Operator/Gov/Fin/Med 角色注册 + 权限检查 + 审计轨迹
# 审计轨迹:      通知机审计序列（2026-08-11 起）
# 模拟态标注: 本模块为规则工具实现，不构成真实配置权执行路径；SE 签名为 mock 占位；通知机硬件未投产部署，本实现为模拟（SIL）
# 版本:          V1.0.0（L-7 通知机接入恢复，2026-08-12）
# =============================================================================
"""通知机 MRCR 多角色扩展（FC-SPEC §3.2）。

角色: NM-Operator（通用）/ NM-Gov（政务）/ NM-Fin（金融）/ NM-Med（医疗）。
权限: 场景隔离 + 独立审计 + 独立演化（继承 DUAL-PROTOCOL MRCRManager，
不改 FROZEN 基座——BV-3 只读，仅子类扩展 ROLE_PERMISSIONS）。

对齐: tdca-notification-machine/scenes/scene-phy-notification/scene-constraints.md §三/§五
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

# ---- 基座复用路径（相对 workspace 根）----
_ENGINE_DIR = Path(__file__).resolve().parent
_BASE = _ENGINE_DIR.parent.parent
for _sub in ("tdca-dual-protocol-package/engine",):
    _p = _BASE / _sub
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from mrcr_manager import MRCRManager  # noqa: E402


# NM-* 角色权限（FC-SPEC §3.2 角色矩阵 + scene-constraints.md §三 配置权边界）
NM_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "NM-Operator": ["fact_hash_upload", "call_authorization", "telemetry_collect"],
    "NM-Gov": ["fact_hash_upload", "call_authorization", "compliance_review"],
    "NM-Fin": ["fact_hash_upload", "call_authorization", "risk_validation"],
    "NM-Med": ["fact_hash_upload", "call_authorization", "privacy_review"],
}

# NM-* 角色禁止项（全部共享信任锚底线禁止 + 行业特有禁止；场景负空间 SCENE-PHY-001/002/003）
NM_ROLE_PROHIBITIONS: Dict[str, List[str]] = {
    "NM-Operator": ["puf_key_export", "tdid_forge", "config_right_mutation",
                    "physical_tamper", "firmware_unapproved"],
    "NM-Gov": ["puf_key_export", "tdid_forge", "config_right_mutation",
               "physical_tamper", "firmware_unapproved", "compliance_bypass"],
    "NM-Fin": ["puf_key_export", "tdid_forge", "config_right_mutation",
               "physical_tamper", "firmware_unapproved", "risk_bypass"],
    "NM-Med": ["puf_key_export", "tdid_forge", "config_right_mutation",
               "physical_tamper", "firmware_unapproved", "privacy_violation"],
}

# 硬件调用类型 → MRCR 动作（引擎接入映射）
HW_ACTION_MAP = {
    "fact_chain": "fact_hash_upload",
    "auth_confirm": "call_authorization",
    "migration": "call_authorization",
    "node_auth": "node_auth",          # 登记类：以 register 权限为准（引擎侧另处理）
}


class NmMrcrManager(MRCRManager):
    """通知机 MRCR 管理器（子类扩展，BV-3 不改基座）。"""

    # 扩展角色权限表：基座 ROLE_PERMISSIONS + NM-* 四角色（仅本类生效）
    ROLE_PERMISSIONS = {
        **MRCRManager.ROLE_PERMISSIONS,
        **NM_ROLE_PERMISSIONS,
    }
    SCENE_PROHIBITION_KEYS = {
        **MRCRManager.SCENE_PROHIBITION_KEYS,
        "NM-Operator": "nm_prohibitions",
        "NM-Gov": "nm_gov_prohibitions",
        "NM-Fin": "nm_fin_prohibitions",
        "NM-Med": "nm_med_prohibitions",
    }

    def __init__(self, scene: str = "scene-phy-notification"):
        super().__init__()
        self.scene = scene
        # 预载场景负空间（SCENE-PHY-001~003 → 共享信任锚底线禁止）
        self.set_scene_prohibitions(scene, {
            "nm_prohibitions": NM_ROLE_PROHIBITIONS["NM-Operator"],
            "nm_gov_prohibitions": NM_ROLE_PROHIBITIONS["NM-Gov"],
            "nm_fin_prohibitions": NM_ROLE_PROHIBITIONS["NM-Fin"],
            "nm_med_prohibitions": NM_ROLE_PROHIBITIONS["NM-Med"],
        })

    def register_tdid(self, tdid: str, role: str) -> dict:
        """注册 TDID 到场景角色（TDID ↔ 场景角色，场景隔离）。"""
        if role not in self.ROLE_PERMISSIONS:
            raise ValueError("未知 NM 角色: {!r}".format(role))
        self.register_role(tdid, role, self.scene)
        return self.role_registry[tdid][self.scene]

    def check_call_permission(self, tdid: str, hw_type_value: str) -> bool:
        """引擎接入：按硬件调用类型检查 TDID 权限。"""
        action = HW_ACTION_MAP.get(hw_type_value)
        if action is None:
            return False
        return self.check_permission(tdid, self.scene, action)
