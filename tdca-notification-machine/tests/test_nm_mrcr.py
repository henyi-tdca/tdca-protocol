# -*- coding: utf-8 -*-
"""通知机层 3 场景化合 + MRCR 接入测试（FC-SPEC §3 + §九 验收项 3）。

模拟态标注: 本测试为模拟数据验证（MOU 锚定 D-011），不构成真实配置权执行路径；通知机硬件未投产部署。

覆盖:
  1. scene-phy-notification 场景制度六文件齐全 + DUAL 编译器同构校验通过
  2. 最小化合三条件（不可拆分/涌现价值/非线性）判定通过
  3. NM-Operator/Gov/Fin/Med 四角色 MRCR 注册 + 场景隔离
  4. 权限检查（注册角色有权限 / 未注册 TDID 拒绝 / 禁止项阻断）
  5. 引擎 MRCR 接入：注册 TDID → APPROVED；未注册 TDID → REJECTED（fail-closed）
  6. NODE_AUTH 登记路径豁免 MRCR 检查
"""
import sys
from pathlib import Path

import pytest

_NM = Path(__file__).resolve().parent.parent          # tdca-notification-machine/
_WS = _NM.parent
_DUAL = _WS / "tdca-dual-protocol-package"
for _p in (str(_NM), str(_DUAL / "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from engine.nm_mrcr import NmMrcrManager, HW_ACTION_MAP  # noqa: E402
from engine.notification_machine_engine import (          # noqa: E402
    HardwareCall,
    HardwareCallType,
    NotificationMachineEngine,
)


# ---- 1. 场景制度六文件齐全 ----

def test_scene_files_present():
    scene_dir = _NM / "scenes" / "scene-phy-notification"
    required = ["scene-constitution.md", "scene-constraints.md", "scene-nsfl.md",
                "scene-terms.md", "scene-review.md", "scene-pricing.md"]
    for f in required:
        assert (scene_dir / f).exists(), "缺失场景文件: {}".format(f)


# ---- 2. DUAL 编译器同构校验 + 最小化合三条件 ----

def test_dual_isomorphism():
    from dual_protocol_compiler import DualProtocolCompiler
    comp = DualProtocolCompiler(
        tdca_path=str(_DUAL / "tdca-public"),
        scene_path=str(_NM / "scenes" / "scene-phy-notification"),
        scene_name="scene-phy-notification")
    assert comp.validate_isomorphism() is True
    assert comp.validation_errors == []


def test_dual_minimal_compound():
    from dual_protocol_compiler import DualProtocolCompiler
    comp = DualProtocolCompiler(
        tdca_path=str(_DUAL / "tdca-public"),
        scene_path=str(_NM / "scenes" / "scene-phy-notification"),
        scene_name="scene-phy-notification")
    passed, message = comp.check_minimal_compound()
    assert passed is True, "最小化合判定失败: {}".format(message)
    # 三条件全过
    assert "不可拆分性" in message and "涌现价值" in message and "非线性" in message
    assert all(k in message for k in ("通过", "通过", "通过"))


# ---- 3. NM 四角色注册 + 场景隔离 ----

def test_nm_roles_registered():
    m = NmMrcrManager()
    for role in ("NM-Operator", "NM-Gov", "NM-Fin", "NM-Med"):
        m.register_tdid("TDID-{}".format(role), role)
        assert m.get_role("TDID-{}".format(role), "scene-phy-notification") == role
    # 场景隔离
    assert "TDID-NM-Operator" in m.scene_users("scene-phy-notification")


# ---- 4. 权限检查 ----

def test_permission_granted():
    m = NmMrcrManager()
    m.register_tdid("TDID-OP", "NM-Operator")
    assert m.check_call_permission("TDID-OP", "fact_chain") is True
    assert m.check_call_permission("TDID-OP", "auth_confirm") is True


def test_permission_denied_unregistered():
    m = NmMrcrManager()
    # 未注册 TDID → 无权限（fail-closed）
    assert m.check_call_permission("TDID-NOPE", "fact_chain") is False


def test_prohibition_blocks():
    m = NmMrcrManager()
    m.register_tdid("TDID-OP", "NM-Operator")
    # 信任锚底线禁止项：PUF 密钥导出 / TDID 伪造 / 物理拆解
    assert m.check_permission("TDID-OP", "scene-phy-notification", "puf_key_export") is False
    assert m.check_permission("TDID-OP", "scene-phy-notification", "tdid_forge") is False
    assert m.check_permission("TDID-OP", "scene-phy-notification", "physical_tamper") is False


def test_action_map_complete():
    for hw in HardwareCallType:
        assert hw.value in HW_ACTION_MAP, "HW_ACTION_MAP 缺少映射: {}".format(hw.value)


# ---- 5. 引擎 MRCR 接入 ----

def _call(hw_type, tdid="TDID-OP", value=1000.0, tax=100.0, compound=False):
    return HardwareCall(
        hw_type=hw_type, tdid=tdid, scene="scene-phy-notification",
        payload="payload-{}".format(hw_type.value),
        call_value=value, tax_receipt=tax,
        indivisibility=compound, emergence=compound, nonlinearity=compound,
    )


def test_engine_mrcr_approved():
    m = NmMrcrManager()
    m.register_tdid("TDID-OP", "NM-Operator")
    eng = NotificationMachineEngine(tdid="TDID-OP", mrcr=m)
    rec = eng.execute(_call(HardwareCallType.FACT_CHAIN))
    assert rec.metering["verdict"] == "APPROVED"
    assert rec.metering["call_type"] == "disposable"


def test_engine_mrcr_rejected_unregistered():
    m = NmMrcrManager()
    eng = NotificationMachineEngine(tdid="TDID-NOPE", mrcr=m)
    rec = eng.execute(_call(HardwareCallType.FACT_CHAIN, tdid="TDID-NOPE"))
    assert rec.metering["verdict"] == "REJECTED"          # fail-closed
    assert rec.metering["call_type"] == "mrcr_rejected"
    assert rec.metering["net_value"] == 0.0
    assert rec.nca_lite["type"] == "fact"                  # 拒绝亦留痕（NCA-Lite）
    assert rec.state_snapshot["state"] == "UNREGISTERED"   # 状态不推进


def test_engine_mrcr_node_auth_exempt():
    m = NmMrcrManager()
    eng = NotificationMachineEngine(tdid="TDID-NEW", mrcr=m)
    # NODE_AUTH 登记路径豁免权限检查（注册本身即授权过程）
    rec = eng.execute(_call(HardwareCallType.NODE_AUTH, tdid="TDID-NEW"))
    assert rec.metering["verdict"] == "APPROVED"
    assert rec.metering["call_type"] == "service"


def test_engine_mrcr_role_isolated():
    # 角色场景隔离：Gov 角色可做合规审查动作（无 HW 映射，直接查权限表）
    m = NmMrcrManager()
    m.register_tdid("TDID-GOV", "NM-Gov")
    assert m.check_permission("TDID-GOV", "scene-phy-notification", "compliance_review") is True
    # 未注册的 Operator 无 Gov 专属权限
    m.register_tdid("TDID-OP", "NM-Operator")
    assert m.check_permission("TDID-OP", "scene-phy-notification", "compliance_review") is False


# ---- 6. 引擎带真实 DUAL 场景路径的化合（层 3 端到端）----

def test_engine_dual_scene_compound():
    """化合调用（AUTH_CONFIRM）提供真实 scene-phy-notification 场景路径时，
    走 DUAL 编译器 check_minimal_compound（三条件全过）→ compound_ref 生成。"""
    m = NmMrcrManager()
    m.register_tdid("TDID-OP", "NM-Operator")
    eng = NotificationMachineEngine(
        tdid="TDID-OP", mrcr=m,
        dual_tdca_path=str(_DUAL / "tdca-public"),
        dual_scene_path=str(_NM / "scenes" / "scene-phy-notification"))
    rec = eng.execute(_call(HardwareCallType.AUTH_CONFIRM, compound=True))
    assert rec.metering["verdict"] == "APPROVED"
    assert rec.metering["call_type"] == "compound"
    assert rec.compound_ref is not None and rec.compound_ref.startswith("dual-")

