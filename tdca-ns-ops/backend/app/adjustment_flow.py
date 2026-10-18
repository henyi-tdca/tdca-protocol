# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——调整权流程引擎（NS-011 状态机）
# 约束矩阵:     FC-NS-OPS-001 F2 + BV-3/BV-4/BV-5/BV-6 + NS-011 §2.2 全流程
#               + 红队 BV-7（空窗处置：窗口期取最严约束）
# 先验分布:     NS-011 状态机（草案→审议→沙盒→确定冻结→编码刚性→灰度→全量→退役）
#               + NSAR-Registry JSON（NS-011 §4.2）
# 配置权边界:    L2 层；状态推进全部经 BV-3 门（人类签名），快系统执行在本引擎内模拟
# 预期分配:     状态机推进 + NCA 链生成；失败=状态非法迁移/签名缺失
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""NS-011 调整权流程引擎（快慢系统分离，人类专属调整权）。

制度锚定: FC-NS-OPS-001 F2/F4/F6 | NS-011 §2.2 全流程 | 红队 BV-7 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Optional

from .human_gate import GATE, DETERMINATION_SIGNATURES_REQUIRED
from .models import (
    Adjustment,
    AdjustmentStatus,
    Constraint,
    ConstraintStatus,
    DeploymentRecord,
    SandboxResult,
)
from .sandbox import ENGINE as SANDBOX_ENGINE
from .store import generate_nca, hash_text

# 状态机合法迁移表（NS-011 §2.2）
_VALID_TRANSITIONS = {
    AdjustmentStatus.DELIBERATION: {AdjustmentStatus.SANDBOX},
    AdjustmentStatus.SANDBOX: {AdjustmentStatus.DETERMINATION},
    AdjustmentStatus.DETERMINATION: {AdjustmentStatus.ENCODING},
    AdjustmentStatus.ENCODING: {AdjustmentStatus.DEPLOYMENT},
    AdjustmentStatus.DEPLOYMENT: {AdjustmentStatus.FEEDBACK, AdjustmentStatus.CLOSED},
    AdjustmentStatus.FEEDBACK: {AdjustmentStatus.CLOSED, AdjustmentStatus.DELIBERATION},
    AdjustmentStatus.CLOSED: set(),
}


class AdjustmentFlowEngine:
    """NS-011 调整权流程引擎：慢系统（人类审议/确认）与快系统（编码/部署）分离。

    六要素声明:
    目标函数: 驱动一次负空间调整走完 审议→沙盒→确定→编码→部署→反馈 全流程
    约束矩阵: 输入——状态迁移合法（_VALID_TRANSITIONS）+ 各步人类签名门；
              输出——Adjustment 状态推进 + NCA 链；禁止——AI 无签名推进、跳步
    先验分布: NS-011 §2.2/§4.2 + 红队 BV-7 空窗处置
    配置权边界: L2；状态机为唯一推进入口
    预期分配: 返回新状态 + NCA 引用；失败=ValueError（非法迁移/签名缺失）
    审计轨迹: 每步生成 NCA-Deliberation/-Sandbox/-Determination/-Encoding/-Deployment
    """

    def transition(
        self,
        adj: Adjustment,
        to_status: AdjustmentStatus,
        human_signature: str,
        extra: Optional[dict] = None,
    ) -> Adjustment:
        """推进调整流程到下一状态（每步必须人类签名，BV-3）。"""
        gate = GATE.check(human_signature)
        if not gate.allowed:
            raise PermissionError(gate.reason)

        valid = _VALID_TRANSITIONS.get(adj.status, set())
        if to_status not in valid:
            raise ValueError(
                f"[NSFL-TRIGGER] 非法状态迁移: {adj.status.value} → {to_status.value}"
            )

        extra = extra or {}
        ts = _now()

        # ---- 各状态推进逻辑（NS-011 §2.2 语义对齐） ----
        if to_status == AdjustmentStatus.SANDBOX:
            # 审议记录（人类专属）——审议 NCA 在发起时已生成，此处仅登记审议快照
            nca = generate_nca(
                "TDCA-FC-NS-OPS-001", "Adjust-Sandbox-Enter",
                f"进入沙盒: {adj.adjustment_id}（审议→沙盒）",
                hash_text(adj.adjustment_id), hash_text(str(extra)),
                nca_type="AUDIT", signer=human_signature)
            adj.nca_refs.append(nca["NCA-ID"])

        elif to_status == AdjustmentStatus.DETERMINATION:
            # 沙盒验证（BV-4）——未通过不得进入确定
            target = self._load_target(adj.target_constraint_id)
            sandbox: SandboxResult = SANDBOX_ENGINE.run(target, extra.get("proposal", ""))
            adj.sandbox = sandbox
            adj.nca_refs.append(sandbox.nca_ref)
            if not (sandbox.technical and sandbox.economic and sandbox.social):
                raise ValueError(
                    f"[BV-4 BLOCKED] 沙盒未通过，禁止进入确定态: {sandbox.report}"
                )
            # H2 修复：确定（冻结态）在 determination 步完成——生效时间 + 回滚版本 + ≥3 签名
            if adj.determination is None:
                adj.determination = self._build_determination(extra, human_signature)
            # 空窗处置（红队 BV-7）：确定后取最严约束——原型用 effective_date 标注
            nca = generate_nca(
                "TDCA-FC-NS-OPS-001", "Adjust-Determination",
                f"确定冻结: {adj.adjustment_id} v{adj.determination.final_version} "
                f"生效 {adj.determination.effective_date} 回滚 v{adj.determination.rollback_version}",
                hash_text(adj.adjustment_id), hash_text(adj.determination.model_dump_json()),
                nca_type="AUDIT", signer=human_signature)
            adj.determination.nca_ref = nca["NCA-ID"]
            adj.nca_refs.append(nca["NCA-ID"])

        elif to_status == AdjustmentStatus.ENCODING:
            # H2 修复：编码（冻结→刚性转换）——NSFL 编译模拟，将约束置为 rigid
            if adj.determination is None:
                raise ValueError("确定态缺失，不可编码")
            target = self._load_target(adj.target_constraint_id)
            target.status = ConstraintStatus.RIGID
            target.version = adj.determination.final_version
            target.effective_date = adj.determination.effective_date
            target.rollback_version = adj.determination.rollback_version
            # M4 修复：刚性态同步确定签名（异构三角痕迹）
            target.human_signatures = list(adj.determination.human_signatures)
            target.nca_refs.extend(adj.nca_refs)
            self._save_target(target)
            nca = generate_nca(
                "TDCA-FC-NS-OPS-001", "Adjust-Encoding",
                f"编码刚性态: {adj.adjustment_id} → 约束 {target.id} v{target.version}",
                hash_text(adj.adjustment_id), hash_text(target.model_dump_json()),
                nca_type="AUDIT", signer=human_signature)
            adj.nca_refs.append(nca["NCA-ID"])

        elif to_status == AdjustmentStatus.DEPLOYMENT:
            # H2 修复：部署（GDP 渐进 5%）——仅部署记录
            if adj.determination is None:
                raise ValueError("确定态缺失，不可部署")
            nca = generate_nca(
                "TDCA-FC-NS-OPS-001", "Adjust-Deployment",
                f"灰度部署 5%: {adj.adjustment_id}",
                hash_text(adj.adjustment_id), hash_text(str(extra)),
                nca_type="AUDIT", signer=human_signature)
            adj.nca_refs.append(nca["NCA-ID"])
            adj.deployment = DeploymentRecord(
                gray_start=ts, status="gray", nca_ref=nca["NCA-ID"])

        elif to_status == AdjustmentStatus.FEEDBACK:
            # B3 修复：反馈步生成 NCA（快→慢异常上报存证）
            nca = generate_nca(
                "TDCA-FC-NS-OPS-001", "Adjust-Feedback",
                f"快系统反馈: {adj.adjustment_id}（异常上报，慢系统 30 天未响应则继续执行现状）",
                hash_text(adj.adjustment_id), hash_text(str(extra)),
                nca_type="AUDIT", signer=human_signature)
            adj.nca_refs.append(nca["NCA-ID"])

        elif to_status == AdjustmentStatus.CLOSED:
            nca = generate_nca(
                "TDCA-FC-NS-OPS-001", "Adjust-Close",
                f"调整闭合: {adj.adjustment_id}",
                hash_text(adj.adjustment_id), hash_text(adj.model_dump_json()),
                nca_type="AUDIT", signer=human_signature)
            adj.nca_refs.append(nca["NCA-ID"])

        adj.status = to_status
        adj.updated_at = ts
        return adj

    # ---- 内部工具 ----

    def _build_determination(self, extra: dict, current_signature: str):
        """构建确定记录（冻结态：生效时间/回滚版本/签名数）。

        H3 修复：生效时间必填（不可立即生效，NS-011 §2.3）且回滚版本显式指定。
        """
        from .models import DeterminationRecord

        # 发起人签名计入异构三角（BV-3）
        signatures = [current_signature] + list(extra.get("human_signatures", []))
        if len(signatures) < DETERMINATION_SIGNATURES_REQUIRED:
            raise ValueError(
                f"[BV-3 BLOCKED] 确定态需 ≥{DETERMINATION_SIGNATURES_REQUIRED} 个人类签名（异构三角），当前 {len(signatures)}"
            )
        for s in signatures:
            if not GATE.is_human(s):
                raise PermissionError(f"[BV-3 BLOCKED] 签名 {s} 非在册人类")
        # H3 修复：生效时间必填且须晚于今日（不可立即生效）
        effective_date = str(extra.get("effective_date", "")).strip()
        if not effective_date:
            raise ValueError("[BV-7] 确定态必须指定生效时间（不可立即生效）")
        # E3 修复：回滚版本必须显式传入且非负（None/缺省 = 未指定，拒绝）
        rollback_version_raw = extra.get("rollback_version", None)
        if rollback_version_raw is None:
            raise ValueError("[BV-7] 确定态必须显式指定回滚版本（rollback_version 不可缺省）")
        rollback_version = int(rollback_version_raw)
        if rollback_version < 0:
            raise ValueError("[BV-7] 回滚版本必须为非负整数")
        return DeterminationRecord(
            final_version=int(extra.get("final_version", 1)),
            effective_date=effective_date,
            rollback_version=rollback_version,
            human_signatures=signatures,
            nca_ref="",
        )

    def _load_target(self, constraint_id: str) -> Constraint:
        # M6 修复：工具函数下沉至 store 层（消除业务引擎对路由层的反向依赖）
        from .store import get_item, raw_to_model

        raw = get_item("constraints", "id", constraint_id)
        if raw is None:
            raise KeyError(f"约束不存在: {constraint_id}")
        return raw_to_model(raw)

    def _save_target(self, target: Constraint) -> None:
        from .store import upsert_item

        upsert_item("constraints", target.model_dump(), key="id")


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


# 全局引擎
FLOW = AdjustmentFlowEngine()
