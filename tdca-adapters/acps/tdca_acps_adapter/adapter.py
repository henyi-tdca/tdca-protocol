"""TDCA × ACPs 适配器主入口。

将 ACPs 的 AIC 身份 / ACS 能力 / ADP 发现升级为 TDCA 配置权调用：
发现 → 配置权坐标 → 效用函数 → NSFL 检查 → 正和验证 → NCA 生成 → MOU 记账。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from .mapper import confidence_of, coordinate_of, kind_of, utility_of
from .models import ACS, AIC, AllocationConfig, AllocationResult, DiscoveryQuery, NsflVerdict
from .mou import MouLedger
from .nca import derive_audit_step, generate_nca
from .nsfl import NsflChecker
from .positivesum import PositiveSumValidator


class TdcaAcpsAdapter:
    """ACPs → TDCA 制度层适配器（样板 1，Apache-2.0）。"""

    def __init__(
        self,
        negative_space: Optional[Sequence[str]] = None,
        scenario_base: str = "default",
    ):
        self.nsfl = NsflChecker(negative_space)
        self.validator = PositiveSumValidator()
        self.ledger = MouLedger()
        self.scenario = scenario_base

    # ---- 映射层 ----
    def map_aic(self, aic: AIC, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        return coordinate_of(aic, tags or [])

    def describe_utility(self, acs: ACS) -> Dict[str, Any]:
        return utility_of(acs)

    # ---- 配置权调用 ----
    def allocate(self, config: AllocationConfig) -> AllocationResult:
        """执行一次配置权调用（替代 ACPs 的纯发现）。"""
        now = datetime.now(timezone.utc).isoformat()
        # 1. 解析查询 → 实体与标签
        tags = self._extract_tags(config)
        aic = AIC(oid="", aic=config.requester_aic)
        # 2. NSFL 负空间检查（先于一切）
        verdict = self.nsfl.check(config.query.text + " " + " ".join(tags))
        if verdict == NsflVerdict.BLOCK:
            return self._blocked_result(config, now, tags, reason="negative-space")
        # 3. 配置权坐标 + 效用函数
        coord = coordinate_of(aic, tags)
        acs = ACS(capability_tags=tags, service_endpoints=[])
        util = utility_of(acs)
        conf = confidence_of(acs)
        # 4. 正和验证
        cost = config.max_budget
        ps = self.validator.validate(util_weight_of(util), cost, config.scenario, conf)
        if not ps.passed:
            return self._blocked_result(config, now, tags, reason="not-positive-sum", ps_surplus=ps.surplus)
        # 5. NCA 生成
        nca = generate_nca(
            objective=f"配置权调用：{config.query.text or '无描述'}",
            constraints=["NSFL 负空间通过", "正和验证通过", f"预算上限 {cost}"],
            prior={"scenario": config.scenario, "confidence": conf},
            config_boundary={"scope": "single-scenario", "subject": config.requester_aic},
            expected_allocation={"profit_sharing": "15% 模拟态", "tax_in": round(ps.surplus * 0.1, 6)},
            audit_trail=[derive_audit_step("allocate", now, "nsfl=pass,positive_sum=pass")],
        )
        # 6. MOU 记账（模拟态）
        tax_in = round(ps.surplus * 0.1, 6)
        mou = self.ledger.record(tax_in, 0.0, note=f"ACPs 配置权调用 {nca['nca_id']}")
        return AllocationResult(
            coordinate=coord,
            utility_function=util,
            positive_sum=ps.surplus,
            positive_sum_pass=True,
            nca=nca,
            nsfl_verdict=NsflVerdict.PASS,
            mou={"mou_id": mou.mou_id, "total": mou.total, "simulated": True},
            allocation_id=f"ALLOC-{nca['nca_id'].split('-')[-1]}",
        )

    # ---- 端到端流水线（发现 → 配置 → 存证 → 记账）----
    def full_pipeline(
        self,
        *,
        task: str,
        capability_tags: List[str],
        aic: str,
        max_budget: float = 0.2,
        scenario: Optional[str] = None,
    ) -> AllocationResult:
        cfg = AllocationConfig(
            query=DiscoveryQuery(text=task, structured_filters={"capability_tags": capability_tags}),
            requester_aic=aic,
            max_budget=max_budget,
            scenario=scenario or self.scenario,
        )
        return self.allocate(cfg)

    # ---- 内部 ----
    @staticmethod
    def _extract_tags(config: AllocationConfig) -> List[str]:
        tags = list(config.query.structured_filters.get("capability_tags", []))
        if not tags:
            # 从查询文本提取粗略标签（词袋简化，非上游代码）
            for kw in ("code", "analysis", "security", "ops", "search", "api", "agent"):
                if kw in (config.query.text or "").lower():
                    tags.append(kw)
        return tags or ["generic"]

    def _blocked_result(
        self, config: AllocationConfig, now: str, tags: List[str], *,
        reason: str, ps_surplus: float = 0.0,
    ) -> AllocationResult:
        aic = AIC(oid="", aic=config.requester_aic)
        nca = generate_nca(
            objective=f"被拒调用：{config.query.text or '无描述'}",
            constraints=[f"reason={reason}"],
            prior={"scenario": config.scenario},
            config_boundary={"scope": "none", "subject": config.requester_aic},
            expected_allocation={},
            audit_trail=[derive_audit_step("blocked", now, reason)],
        )
        return AllocationResult(
            coordinate=coordinate_of(aic, tags),
            utility_function={},
            positive_sum=ps_surplus,
            positive_sum_pass=False,
            nca=nca,
            nsfl_verdict=NsflVerdict.BLOCK,
            mou={},
            allocation_id="",
        )


def util_weight_of(util: Dict[str, Any]) -> float:
    """效用函数 → 权重（简化：能力数量加权）。"""
    n = len(util.get("capabilities", []) or [])
    return round(min(2.0, 0.5 + 0.25 * n), 3)
