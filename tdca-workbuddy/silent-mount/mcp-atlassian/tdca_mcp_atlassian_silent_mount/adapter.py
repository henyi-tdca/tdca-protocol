"""TDCA × mcp-atlassian 静默挂载适配器（样例 · 模拟态试点）。

定位：独立组件，协议层对接 sooperset/mcp-atlassian 公开接口语义
（MCP 服务器（Jira/Confluence 工具面）），不复制上游代码、不修改上游源码、
不真实连接 上游 API（静默挂载 = 对方零感知）。

full_pipeline() 五步：配置权坐标映射 → NSFL 预检 → NCA 存证 → MOU 锚定 → 正和放行。
全程零外部网络调用：请求载荷在本地构造并「模拟发送」（仅落日志，绝不传输）。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .mou import MouLedger
from .nca import derive_audit_step, generate_nca
from .nsfl import NsflChecker, NsflVerdict


class TdcaMcpatlSilentMount:
    """mcp-atlassian 静默挂载适配器（批1 严选挂载，仿 acps 六模块）。"""

    # ---- 挂载登记常量（源自 mounts/mcp-atlassian/NCA-MOUNT-20260929-003）----
    TARGET = "sooperset/mcp-atlassian"
    LICENSE = "MIT"
    INTERFACE = "MCP 服务器（Jira/Confluence 工具面）"
    MOUNT_NCA = "NCA-MOUNT-20260929-003"          # 挂载登记存证链
    NOTICE_NCA = "NCA-ECOACT-20260929-NTC-023"    # 告知函存证
    CATEGORY = "share-enabled"                     # 默认分润类
    TAX_RATE = 0.15                                # 15% 模拟态分润
    SIMULATED: bool = True                         # ID92 模拟态标注
    SILENT: bool = False                           # 静默挂载（大仓甲案）/告知函在架
    NETWORK_SEND: bool = False                     # 静默挂载·零感知硬开关

    def __init__(self, negative_space: Optional[List[str]] = None):
        self.nsfl = NsflChecker(negative_space)
        self.ledger = MouLedger(tax_rate=self.TAX_RATE)

    # ---- ① 配置权坐标映射 ----
    def map_config_coordinate(self, *, scenario: str = "silent-mount") -> Dict[str, Any]:
        """把上游目标 + 接口面映射为 TDCA 配置权坐标（本地构造，无网络）。"""
        return {
            "coordinate_id": "TDCA-COORD-SM-MCPATL",
            "target": self.TARGET,
            "license": self.LICENSE,
            "interface": self.INTERFACE,
            "category": self.CATEGORY,
            "scenario": scenario,
            "mount_nca": self.MOUNT_NCA,
            "derived_from": "mount-registry",  # 源自挂载登记，非实时拉取
        }

    # ---- ② 模拟上游请求载荷（绝不发送）----
    def simulate_upstream_payload(self, *, task: str, tags: List[str]) -> Dict[str, Any]:
        """本地构造一份「若实连上游将发出的挂载引用请求」载荷。仅返回，不传输。"""
        return {
            "_simulated": True,
            "_network_send": self.NETWORK_SEND,
            "target": self.TARGET,
            "action": "silent_mount_reference_only",
            "interface": self.INTERFACE,
            "task": task,
            "capability_tags": tags,
            "license": self.LICENSE,
            "mount_nca": self.MOUNT_NCA,
            "note": "协议层只读引用声明；不写入上游、不调用上游 API",
        }

    # ---- 正和放行（轻量本地校验）----
    @staticmethod
    def _positive_sum_ok(utility_weight: float, budget: float) -> bool:
        return (utility_weight - budget) > 0

    # ---- 端到端流水线 ----
    def full_pipeline(
        self,
        *,
        task: str,
        capability_tags: List[str],
        max_budget: float = 0.2,
        scenario: str = "silent-mount",
        base_utility: float = 1.0,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()

        # ① 配置权坐标映射
        coord = self.map_config_coordinate(scenario=scenario)

        # ② NSFL 预检（先于一切）
        proposal_text = (
            f"静默挂载 {self.TARGET}（{self.LICENSE}）于 {self.INTERFACE}；"
            f"只读引用声明；{self.CATEGORY}；分润 {int(self.TAX_RATE*100)}% 模拟态"
        )
        verdict = self.nsfl.check(proposal_text + " " + task + " " + " ".join(capability_tags))
        if verdict == NsflVerdict.BLOCK:
            return self._blocked(task, now, reason="negative-space")

        # ③ NCA 存证（六要素）
        nca = generate_nca(
            objective=f"静默挂载配置权调用：{task}",
            constraints=[
                "NSFL 负空间通过",
                "registered_only（登记态·不宣称已封装可用）",
                f"write=False upstream_code_change=False network_send=False",
                f"profit_sharing_mode=simulated tax_rate={self.TAX_RATE}",
            ],
            prior={"scenario": scenario, "mount_nca": self.MOUNT_NCA,
                   "license": self.LICENSE, "category": self.CATEGORY},
            config_boundary={
                "scope": "silent-mount-reference-only",
                "subject": self.TARGET,
                "write": False,
                "upstream_code_change": False,
                "network_send": False,
                "proposals_only": True,
                "profit_sharing_mode": "simulated",
                "tax_rate_simulated": self.TAX_RATE,
            },
            expected_allocation={
                "profit_sharing": f"{int(self.TAX_RATE*100)}% 模拟态反哺上游",
                "upstream_perception": "zero（静默挂载）",
            },
            audit_trail=[derive_audit_step("silent_mount", now,
                         f"nsfl=pass mount_nca={self.MOUNT_NCA}")],
        )

        # ④ MOU 锚定（15% 分润模拟态记账，无现金流）
        mou = self.ledger.record_profit_share(base_utility,
                                              note=f"mcp-atlassian 静默挂载 {nca['nca_id']}")

        # ⑤ 正和放行（本地轻量校验）
        ps_pass = self._positive_sum_ok(base_utility, max_budget)
        if not ps_pass:
            return self._blocked(task, now, reason="not-positive-sum")

        # 模拟构造上游请求载荷（绝不发送）
        payload = self.simulate_upstream_payload(task=task, tags=capability_tags)

        # 硬断言：静默挂载不得产生任何外部写入/网络发送
        assert self.NETWORK_SEND is False, "静默挂载硬纪律：network_send 必须为 False"
        assert payload["_network_send"] is False

        return {
            "target": self.TARGET,
            "license": self.LICENSE,
            "interface": self.INTERFACE,
            "coordinate": coord,
            "nsfl_verdict": verdict,
            "nca": nca,
            "mou": {
                "mou_id": mou.mou_id,
                "tax_out": mou.tax_out,
                "total": mou.total,
                "simulated": True,
                "tax_rate": self.TAX_RATE,
            },
            "positive_sum_pass": ps_pass,
            "simulated": True,
            "upstream_notified": False,           # 对方零感知
            "upstream_payload_simulated": payload,  # 仅构造，未发送
            "silent_mount_ok": True,
            "mount_nca": self.MOUNT_NCA,
        }

    # ---- 内部：熔断结果 ----
    def _blocked(self, task: str, now: str, *, reason: str) -> Dict[str, Any]:
        nca = generate_nca(
            objective=f"被拒静默挂载：{task}",
            constraints=[f"reason={reason}"],
            prior={"mount_nca": self.MOUNT_NCA},
            config_boundary={"scope": "none", "subject": self.TARGET},
            expected_allocation={},
            audit_trail=[derive_audit_step("blocked", now, reason)],
        )
        return {
            "target": self.TARGET,
            "license": self.LICENSE,
            "coordinate": self.map_config_coordinate(),
            "nsfl_verdict": NsflVerdict.BLOCK,
            "nca": nca,
            "mou": {},
            "positive_sum_pass": False,
            "simulated": True,
            "upstream_notified": False,
            "silent_mount_ok": False,
            "mount_nca": self.MOUNT_NCA,
        }
