"""ASP — 智能体调度协议适配层（M2，与 FC-012 9 Phase 同构）

硬约束（TDCA-PHASE-E-INT-1）:
  - ASP 状态机必须与 FC-012 的 9 Phase 流程一一映射（破例识别）
  - 禁止绕过 FC-012 直接调度智能体；核心迁移逻辑全部委托 FC-012 FlowEngine
  - 禁止修改 FC-012 已归档代码

本模块为纯适配层：ASP 状态名 ↔ FC-012 phase 映射 + 偏离检测。
"""

from enum import Enum


class ASPState(Enum):
    """ASP 调度状态（12 态，与 FC-012 ALL_STATES 一一映射）"""
    CREATED = "CREATED"        # P0 意图孕育
    PARSING = "PARSING"        # P1 意图编译
    COMPILING = "COMPILING"    # P2 协议编译
    VALIDATING = "VALIDATING"  # P3 沙盒验证
    ANCHORING = "ANCHORING"    # P4 节点锚定
    REGISTERING = "REGISTERING"  # P5 上链确权
    PUBLISHING = "PUBLISHING"  # P6 接口发布
    SOLVING = "SOLVING"        # P7 正和求解
    DELIVERING = "DELIVERING"  # P8 智能合约交付
    COMPLETED = "COMPLETED"
    FUSED = "FUSED"
    TERMINATED = "TERMINATED"


# ASP 状态 → FC-012 phase 映射（FC-012: PHASES=['P0'..'P8'] + FUSE/COMPLETED/TERMINATED）
ASP_TO_FC = {
    ASPState.CREATED: "P0",
    ASPState.PARSING: "P1",
    ASPState.COMPILING: "P2",
    ASPState.VALIDATING: "P3",
    ASPState.ANCHORING: "P4",
    ASPState.REGISTERING: "P5",
    ASPState.PUBLISHING: "P6",
    ASPState.SOLVING: "P7",
    ASPState.DELIVERING: "P8",
    ASPState.COMPLETED: "COMPLETED",
    ASPState.FUSED: "FUSE",
    ASPState.TERMINATED: "TERMINATED",
}
FC_TO_ASP = {v: k for k, v in ASP_TO_FC.items()}

# 合法迁移事件（继承 FC-012 PhaseMachine 事件集）
VALID_EVENTS = ("ADVANCE", "ROLLBACK", "FUSE", "HUMAN_APPROVE")


class ID38Exception(Exception):
    """破例识别触发：偏离 FC-012 9 Phase 的调度请求"""

    def __init__(self, reason: str, suggested: str = ""):
        self.reason = reason
        self.suggested = suggested
        super().__init__("[ID38-TRIGGER] %s%s" % (reason, " 建议: " + suggested if suggested else ""))


class ASPAdapter:
    """ASP 适配层：状态映射 + 偏离检测，调度委托 FC-012 FlowEngine"""

    def __init__(self, flow_engine=None):
        """flow_engine: FC-012 FlowEngine 实例（Phase C 已归档，依赖注入）"""
        self._engine = flow_engine  # 委托目标；None 时仅做映射校验（测试/契约校验模式）

    # ---- 状态映射 ----

    def to_fc(self, asp_state) -> str:
        """ASP 状态 → FC-012 phase（非法状态触发破例识别）"""
        if isinstance(asp_state, str):
            try:
                asp_state = ASPState(asp_state)
            except ValueError:
                raise ID38Exception(
                    "非法 ASP 状态: %s（不在 12 态映射表内）" % asp_state,
                    "合法状态: %s" % ", ".join(s.value for s in ASPState))
        if asp_state not in ASP_TO_FC:
            raise ID38Exception("状态无 FC-012 映射: %s" % asp_state)
        return ASP_TO_FC[asp_state]

    def from_fc(self, fc_phase: str) -> ASPState:
        """FC-012 phase → ASP 状态（未知 phase 触发破例识别）"""
        if fc_phase not in FC_TO_ASP:
            raise ID38Exception("FC-012 未知 phase: %s（与已归档状态集合不兼容）" % fc_phase)
        return FC_TO_ASP[fc_phase]

    # ---- 调度操作（委托 FC-012，含偏离检测） ----

    def advance(self, agent_id: str, context: dict):
        """推进：委托 FC-012 FlowEngine.advance（若已注入）"""
        if self._engine is None:
            raise ID38Exception("FC-012 FlowEngine 未注入，无法执行调度", "注入 Phase C 已归档 FlowEngine")
        return self._engine.advance(agent_id, context)

    def approve(self, agent_id: str, context: dict = None):
        """人类批准（P8→COMPLETED + MOU 闭环）

        context 至少包含 human_signature=True + tax_in/tax_out（mou_closed 条件）。
        """
        if self._engine is None:
            raise ID38Exception("FC-012 FlowEngine 未注入，无法执行人类批准")
        ctx = {"human_signature": True, "tax_in": 0, "tax_out": 0}
        if context:
            ctx.update(context)
        return self._engine.human_approve(agent_id, ctx)

    def rollback(self, agent_id: str, target_asp: ASPState):
        """回退到指定 ASP 状态（映射为 FC-012 phase 后委托）"""
        if self._engine is None:
            raise ID38Exception("FC-012 FlowEngine 未注入，无法执行回退")
        fc_target = self.to_fc(target_asp)
        return self._engine.rollback(agent_id, fc_target)

    def timeline(self, agent_id: str):
        """生命周期时间线（M5 看板数据源，委托 FC-012 trajectory）"""
        if self._engine is None:
            raise ID38Exception("FC-012 FlowEngine 未注入，无法获取时间线")
        return self._engine.trajectory(agent_id)

    # ---- 契约校验（无需引擎，供测试/审查） ----

    def validate_mapping(self) -> list:
        """校验 ASP↔FC-012 映射完整性（12 态双向一致）"""
        issues = []
        if len(ASP_TO_FC) != 12:
            issues.append("ASP 状态数 %d ≠ 12" % len(ASP_TO_FC))
        fc_set = set(ASP_TO_FC.values())
        expected = {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8",
                    "FUSE", "COMPLETED", "TERMINATED"}
        if fc_set != expected:
            issues.append("FC-012 映射集合偏离: %s" % sorted(fc_set ^ expected))
        return issues


if __name__ == "__main__":  # pragma: no cover（演示块，非交付逻辑）
    adapter = ASPAdapter()
    print("映射校验:", adapter.validate_mapping() or "12/12 一致")
    print("ASP.COMPILING → FC:", adapter.to_fc(ASPState.COMPILING))
    print("FC 'P5' → ASP:", adapter.from_fc("P5").value)
    try:
        adapter.to_fc("PAUSED")
    except ID38Exception as e:
        print("破例识别偏离检测:", e)
