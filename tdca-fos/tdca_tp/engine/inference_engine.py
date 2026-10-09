# -*- coding: utf-8 -*-
"""
TDCA-TP 思维协议推理机 — M2 完整实现
制度锚定: TDCA-KG-001 §2.3 | ID38 破例识别 | ID79 MOU | ID82 接口熵 | ID54 MRCR | SPEC-002
版本: V1.0 | 状态: M2-CODED | FC: TDCA-FC-20260804-006-M2

职责: TDCA-KG-001 §2.3 五条核心规则全部可自动触发。
  快系统路径：非 CRITICAL 自动执行（毫秒级）
  慢系统路径：CRITICAL 级触发 NSFL 熔断并上报人类（ID71）
  所有触发动作生成 NCA（ID91）
NSFL-Declaration:
  - CRITICAL 级事件必须经慢系统，不可在快系统中自动恢复
  - 不执行任何 ⊗ 禁止操作符语义
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time


class AlertSeverity(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3  # 触发 NSFL 熔断


@dataclass
class InferenceResult:
    """规则执行结果"""
    rule_name: str
    triggered: bool
    severity: AlertSeverity
    alert: Dict[str, Any]
    nca_reference: str
    action_taken: str
    timestamp: int


class TDCATPReasoner:
    """
    TDCA 思维协议推理机 — M2 完整实现
    五条核心规则全部可自动触发
    依赖注入：graph_engine 提供图数据查询；测试可用 InMemoryGraphAdapter
    """

    def __init__(self, graph_engine=None, nca_generator=None, nsfl_engine=None,
                 mou_validator=None):
        self.graph = graph_engine
        self.nca = nca_generator
        self.nsfl = nsfl_engine
        self.mou = mou_validator
        self.rule_registry: Dict[str, Dict] = {}
        self._register_all_rules()

    # ==================== 规则注册 ====================

    def _register_all_rules(self):
        """注册 TDCA-KG-001 五条核心规则 + 运行时逻辑"""
        # 规则 1: 破例识别自动触发 — ID38
        self.rule_registry["ExceptionDetection"] = {
            "name": "ExceptionDetection",
            "description": "要求'破例'即伪创新信号",
            "principle": "ID38",
            "severity": AlertSeverity.CRITICAL,
            "trigger": self._trigger_exception_detection,
            "action": self._action_block_and_escalate,
        }
        # 规则 2: 接口熵=0 验证 — ID82
        self.rule_registry["InterfaceEntropyZero"] = {
            "name": "InterfaceEntropyZero",
            "description": "编译产物接口熵必须为 0",
            "principle": "TDCA-PRINCIPLE-INTERFACE-ENTROPY-001",
            "severity": AlertSeverity.CRITICAL,
            "trigger": self._trigger_interface_entropy,
            "action": self._action_block_deployment,
        }
        # 规则 3: MRCR 场景隔离检查 — ID54
        self.rule_registry["MRCRSceneIsolation"] = {
            "name": "MRCRSceneIsolation",
            "description": "同一主体在不同场景的角色必须隔离",
            "principle": "ID54",
            "severity": AlertSeverity.WARNING,
            "trigger": self._trigger_mrcr_isolation,
            "action": self._action_warn_and_audit,
        }
        # 规则 4: MOU 连续验证 — ID79
        self.rule_registry["MOUContinuousVerification"] = {
            "name": "MOUContinuousVerification",
            "description": "MOU 锚定必须连续，缺失率 < 7%",
            "principle": "ID79",
            "severity": AlertSeverity.WARNING,
            "trigger": self._trigger_mou_continuous,
            "action": self._action_warn_and_request_mou,
        }
        # 规则 5: NCA 嵌套深度检查 — SPEC-002
        self.rule_registry["NCANestingDepth"] = {
            "name": "NCANestingDepth",
            "description": "NCA 嵌套层级不得超过 10",
            "principle": "SPEC-002",
            "severity": AlertSeverity.INFO,
            "trigger": self._trigger_nesting_depth,
            "action": self._action_log_and_monitor,
        }

    # ==================== 执行入口 ====================

    def execute(self, rule_name: str, context: Dict[str, Any]) -> InferenceResult:
        """
        执行单条推理规则
        快系统路径：自动执行，毫秒级
        慢系统路径：CRITICAL 级触发 NSFL 熔断，上报人类
        """
        rule = self.rule_registry.get(rule_name)
        if not rule:
            raise ValueError(f"未知规则: {rule_name}")

        # 1. 执行触发器
        triggered, evidence = rule["trigger"](context)

        if not triggered:
            return InferenceResult(
                rule_name=rule_name, triggered=False,
                severity=AlertSeverity.INFO, alert={},
                nca_reference="", action_taken="NO_ACTION",
                timestamp=int(time.time()),
            )

        # 2. 执行动作处理器
        alert = rule["action"](evidence)

        # 3. 生成 NCA（内容哈希封印）
        nca_ref = self._generate_nca(rule_name, rule, evidence, alert)

        # 4. CRITICAL 级触发 NSFL 熔断（慢系统路径）
        if rule["severity"] == AlertSeverity.CRITICAL:
            fuse_id = self._trigger_nsfl_fuse(rule, alert, nca_ref)
            action_taken = f"NSFL_FUSE_TRIGGERED:{fuse_id}" if fuse_id else "NSFL_FUSE_TRIGGERED"
        else:
            action_taken = alert.get("action", "LOGGED")

        return InferenceResult(
            rule_name=rule_name, triggered=True,
            severity=rule["severity"], alert=alert,
            nca_reference=nca_ref, action_taken=action_taken,
            timestamp=int(time.time()),
        )

    def get_rule(self, rule_name: str) -> Optional[Dict]:
        """获取规则注册信息"""
        return self.rule_registry.get(rule_name)

    def list_rules(self) -> List[str]:
        return sorted(self.rule_registry.keys())

    # ==================== 规则 1: 破例识别（ID38）====================

    def _trigger_exception_detection(self, context: Dict) -> tuple:
        """破例识别：检测文本中是否包含绕过宪法级原理的语义"""
        draft_text = context.get("draft_text", "")
        principle_id = context.get("principle_id", "")

        # 查询该原理的优先级（context 优先，graph 兜底）
        priority = context.get("principle_priority", None)
        if priority is None and self.graph is not None:
            priority = self._graph_call("get_principle_priority", principle_id)
        if priority is None:
            priority = 0
        if priority != 5:
            return False, {}

        # 检测破例语义模式
        bypass_patterns = ["绕过", "破例", "例外处理", "特殊通道", "不走", "跳过"]
        detected = [p for p in bypass_patterns if p in draft_text]

        if not detected:
            return False, {}

        return True, {
            "principle_id": principle_id,
            "principle_name": self._graph_call("get_principle_name", principle_id)
                               if self.graph else "",
            "detected_patterns": detected,
            "draft_snippet": draft_text[:200],
        }

    def _action_block_and_escalate(self, evidence: Dict) -> Dict:
        """破例识别动作：阻断并上报慢系统"""
        return {
            "type": "PSEUDO_INNOVATION", "severity": 3, "rule": "ID38",
            "action": "BLOCK_AND_ESCALATE",
            "reason": f"检测到试图绕过宪法级制度原理 {evidence.get('principle_id', '')}",
            "alt_path": "在正空间内重新设计，产生可税收硬效用",
            "evidence": evidence,
        }

    # ==================== 规则 2: 接口熵=0（ID82）====================

    def _trigger_interface_entropy(self, context: Dict) -> tuple:
        """接口熵验证：检测编译产物接口熵是否为 0"""
        code_module_id = context.get("code_module_id", "")
        compiler = context.get("compiler", "")

        if compiler != "DeepSeek-V4":
            return False, {}

        entropy = context.get("calculated_entropy", None)
        if entropy is None and self.graph is not None:
            entropy = self._graph_call("calculate_interface_entropy", code_module_id)
        if entropy is None:
            entropy = 0.0

        return entropy > 0, {
            "code_module_id": code_module_id,
            "compiler": compiler,
            "calculated_entropy": float(entropy),
        }

    def _action_block_deployment(self, evidence: Dict) -> Dict:
        """接口熵违规动作：阻断部署"""
        return {
            "type": "INTERFACE_ENTROPY_VIOLATION", "severity": 3,
            "rule": "TDCA-PRINCIPLE-INTERFACE-ENTROPY-001",
            "action": "BLOCK_DEPLOYMENT",
            "reason": f"编译产物接口熵={evidence.get('calculated_entropy', 0)} > 0，违反制度同构跃进原则",
            "alt_path": "重新编译，确保接口熵=0（检查配置权边界七元组完整性）",
            "evidence": evidence,
        }

    # ==================== 规则 3: MRCR 场景隔离（ID54）====================

    def _trigger_mrcr_isolation(self, context: Dict) -> tuple:
        """MRCR 场景隔离检查"""
        agent_id = context.get("agent_id", "")
        scenes = context.get("scenes", None)
        if scenes is None and self.graph is not None:
            scenes = self._graph_call("get_agent_scenes", agent_id)
        if scenes is None:
            scenes = []

        if len(scenes) <= 1:
            return False, {}

        isolated = self._check_isolation(agent_id, scenes, context)
        return not isolated, {
            "agent_id": agent_id,
            "scenes": scenes,
            "isolated": isolated,
        }

    def _check_isolation(self, agent_id: str, scenes: List[str], context: Dict) -> bool:
        """检查场景间是否满足隔离条件"""
        # context 可显式提供隔离结论（测试/预计算）
        if "isolation_verified" in context:
            return bool(context["isolation_verified"])
        if self.graph is None:
            return False  # 无图数据时默认视为未隔离（保守）
        for i, s1 in enumerate(scenes):
            for s2 in scenes[i + 1:]:
                ok = self._graph_call("verify_scene_isolation", agent_id, s1, s2)
                if ok is not True:
                    return False
        return True

    def _action_warn_and_audit(self, evidence: Dict) -> Dict:
        return {
            "type": "MRCR_VIOLATION", "severity": 2, "rule": "ID54",
            "action": "WARN_AND_AUDIT",
            "reason": f"主体 {evidence.get('agent_id', '')} 在多场景间未满足隔离条件",
            "alt_path": "分离角色或提交场景隔离证明",
            "evidence": evidence,
        }

    # ==================== 规则 4: MOU 连续验证（ID79）====================

    def _trigger_mou_continuous(self, context: Dict) -> tuple:
        """MOU 连续验证：30 天内缺失率 < 7%"""
        window_days = int(context.get("window_days", 30))
        window_start = int(time.time()) - window_days * 86400
        window_end = int(time.time())

        mou_count = context.get("mou_count", None)
        if mou_count is None and self.graph is not None:
            mou_count = self._graph_call("count_mou_in_window", window_start, window_end)
        if mou_count is None:
            mou_count = 0

        threshold = window_days * 0.93
        missing_rate = (window_days - mou_count) / window_days

        return mou_count < threshold, {
            "window_days": window_days,
            "mou_count": mou_count,
            "threshold": threshold,
            "missing_rate": missing_rate,
        }

    def _action_warn_and_request_mou(self, evidence: Dict) -> Dict:
        return {
            "type": "MOU_INSUFFICIENT", "severity": 2, "rule": "ID79",
            "action": "WARN_AND_REQUEST_MOU",
            "reason": f"MOU 缺失率 {evidence.get('missing_rate', 0) * 100:.1f}% 超过阈值 7%",
            "alt_path": "补充税收锚定数据或提交 MOU 豁免申请（慢系统）",
            "evidence": evidence,
        }

    # ==================== 规则 5: NCA 嵌套深度（SPEC-002）====================

    def _trigger_nesting_depth(self, context: Dict) -> tuple:
        """NCA 嵌套深度检查"""
        nca_id = context.get("nca_id", "")
        max_depth = int(context.get("max_depth", 10))

        depth = context.get("nesting_depth", None)
        if depth is None and self.graph is not None:
            depth = self._graph_call("calculate_nesting_depth", nca_id)
        if depth is None:
            depth = 0

        return depth > max_depth, {
            "nca_id": nca_id, "depth": depth, "max_depth": max_depth,
        }

    def _action_log_and_monitor(self, evidence: Dict) -> Dict:
        return {
            "type": "NESTING_TOO_DEEP", "severity": 1, "rule": "SPEC-002",
            "action": "LOG_AND_MONITOR",
            "reason": f"NCA {evidence.get('nca_id', '')} 嵌套深度 {evidence.get('depth', 0)} > {evidence.get('max_depth', 10)}",
            "alt_path": "考虑 NCA 扁平化或拆分",
            "evidence": evidence,
        }

    # ==================== 内部工具 ====================

    def _graph_call(self, method: str, *args):
        """安全调用图引擎方法（鸭子类型）"""
        fn = getattr(self.graph, method, None)
        if fn is None:
            return None
        try:
            return fn(*args)
        except Exception:
            return None

    def _generate_nca(self, rule_name: str, rule: Dict, evidence: Dict,
                      alert: Dict) -> str:
        """生成规则执行 NCA — ID91"""
        if self.nca is None:
            return ""
        if hasattr(self.nca, "generate"):
            nca = self.nca.generate(
                type="INSTITUTIONAL", layer=2,
                content={
                    "rule": rule_name, "principle": rule["principle"],
                    "severity": rule["severity"].name,
                    "evidence": evidence, "alert": alert,
                },
            )
            return nca.nca_id
        if hasattr(self.nca, "record_inference"):
            return self.nca.record_inference(
                rule_name=rule_name, principle=rule["principle"],
                trigger_params=evidence, alert=alert)
        return ""

    def _trigger_nsfl_fuse(self, rule: Dict, alert: Dict, nca_ref: str) -> Optional[str]:
        """CRITICAL 级触发 NSFL 熔断 — ID85/ID86"""
        if self.nsfl is None:
            return None
        if hasattr(self.nsfl, "trigger"):
            return self.nsfl.trigger(
                rule_id=f"TDCA-RULE-{rule['name']}",
                severity=3,
                reason=alert.get("reason", ""),
                alt_path=alert.get("alt_path", "人工审查"),
                nca_ref=nca_ref,
            )
        if hasattr(self.nsfl, "trigger_fuse"):
            return self.nsfl.trigger_fuse(
                rule_id=f"TDCA-RULE-{rule['name']}",
                reason=alert.get("reason", ""),
                alt_path=alert.get("alt_path", "人工审查"),
            )
        return None
