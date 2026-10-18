# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     沙盒生命周期状态机（F1）——Phase0→P0→P1→Exit/Closed 全流程 CRUD
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 开发纪律 6 项 + 宪法十六条（可观测）
# 先验分布:     任务书 §二 F1 + §3.2 数据模型 + §五 SV-1~7
# 配置权边界:    L2 层；所有操作生成 NCA 存证（F8）
# 预期分配:     沙盒创建/配置/运行/评估/出盒/关闭 + NCA 链；失败=状态非法拒绝
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""沙盒生命周期状态机（F1，SV-1~7 执行中枢）。

制度锚定: FC-SBX-OPS-001 F1 / SV-1~7 | SPDX-License-Identifier: TDCA-Internal

状态转移:
  Phase0(准入) → P0(实验) → P1(评估) → Exit(出盒) / Closed(关闭·熔断/终止)
任意非终态 → Closed（负空间熔断 SV-3 / 三方终止 SV-4，人类裁决）
每个操作强制 NCA 存证（SV-7）；出盒强制 SV-1（α>1.2）+ SV-6（三方签名）。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from . import multisig
from .activation_engine import ACTIVATION_THRESHOLD, check_exit_eligibility, compute_activation
from .chem_engine import (
    chem_combine as _chem_combine,
    chem_separate as _chem_separate,
    eng003_min_compound_check,
)
from .models import Phase, Sandbox
from .nca_logger import build_nca, save_nca
from .sright import allocate_sright, escalate_gradient, pucr_presale
from .trinity import TRINITY_ROLES, TrinityCoordinator
from . import utility_genie_adapter as genie

FC_ID = "TDCA-FC-SBX-OPS-001"

# 五主体发起方（任务书 §二 F1 沙盒创建）
INITIATOR_ROLES = {"innovator", "investor", "government", "platform", "service"}

# 状态机合法转移表（不可绕过）
_TRANSITIONS: Dict[Phase, set[Phase]] = {
    Phase.PHASE0: {Phase.P0, Phase.CLOSED},
    Phase.P0: {Phase.P1, Phase.CLOSED},
    Phase.P1: {Phase.EXIT, Phase.CLOSED},
    Phase.EXIT: set(),
    Phase.CLOSED: set(),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SandboxCore:
    """沙盒生命周期操作引擎（F1 CRUD + 状态机 + NCA 全操作存证）。"""

    def create(
        self,
        name: str,
        initiator_did: str,
        initiator_role: str,
        six_elements: Dict[str, str],
    ) -> Sandbox:
        """创建沙盒（准入 Phase0）。

        六要素声明:
        目标函数: 创建沙盒实例并进入准入阶段（F1-C）
        约束矩阵: 输入——name/initiator_did/initiator_role/six_elements 必填；
                  输出——Sandbox（Phase0）；禁止——空六要素（宪法可观测）、非法发起方
        先验分布: 任务书 §二 F1 沙盒创建（五主体发起，六要素声明）
        配置权边界: L2；创建操作生成 NCA（SV-7）
        预期分配: 返回新建沙盒；失败=ValueError
        审计轨迹: NCA Operation=SBX_CREATE
        """
        if not name or not initiator_did or not initiator_role:
            raise ValueError("name / initiator_did / initiator_role 必填")
        if initiator_role not in INITIATOR_ROLES:
            raise ValueError(f"initiator_role 必须为五主体之一 {'/'.join(sorted(INITIATOR_ROLES))}，收到 {initiator_role!r}")
        if not six_elements or not all(
            k in six_elements for k in ("目标函数", "约束矩阵", "先验分布", "配置权边界", "预期分配", "审计轨迹")
        ):
            raise ValueError("六要素声明不完整（工作规范 §2.2：目标函数/约束矩阵/先验分布/配置权边界/预期分配/审计轨迹）")

        from . import store

        sb = Sandbox(
            sandbox_id=store.new_sandbox_id(),
            name=name,
            phase=Phase.PHASE0,
            initiator_did=initiator_did,
            initiator_role=initiator_role,
            six_elements=six_elements,
            created_at=_now_iso(),
            updated_at=_now_iso(),
        )
        nca = build_nca(
            operation="SBX_CREATE",
            operator=initiator_did,
            pre_state="NONE",
            post_state=Phase.PHASE0.value,
            audit_trail=f"name={name}; initiator_role={initiator_role}",
        )
        sb.nca_ids.append(save_nca(nca))
        store.save_sandbox(sb)
        return sb

    def configure(
        self,
        sandbox_id: str,
        pucr: Optional[Dict[str, Any]] = None,
        s_rights: Optional[List[Dict[str, Any]]] = None,
    ) -> Sandbox:
        """沙盒配置（准入期）：场景配置权预埋 + PUCR 预售/质押记录（SV-2）。

        六要素声明:
        目标函数: 配置沙盒（F1-配置）——PUCR 预售/质押与 S-Right 场景配置权记录
        约束矩阵: 输入——sandbox_id、pucr/s_rights；输出——更新后 Sandbox；
                  禁止——非准入期配置、PUCR 无数据性质标注（开发纪律 2）
        先验分布: 任务书 §二 F1 沙盒配置（SV-2 PUCR 预售须可验证）
        配置权边界: L2；配置记录随 NCA 存证
        预期分配: 返回更新后沙盒；失败=状态非法/记录缺失
        审计轨迹: NCA Operation=SBX_CONFIGURE
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.PHASE0, "沙盒配置")

        if pucr is not None:
            if "amount" not in pucr or pucr.get("amount", 0) <= 0:
                raise ValueError("PUCR 预售/质押须含正数 amount（SV-2 可验证硬数据）")
            if pucr.get("data_nature", "simulated") not in {"real", "simulated"}:
                raise ValueError("data_nature 必须为 real/simulated（开发纪律 2：数据性质不可伪造）")
            pucr = dict(pucr)
            pucr.setdefault("data_nature", "simulated")  # M1 模拟合约数据显式标注（开发纪律 2）
            pucr.setdefault("mou_anchor", "")  # MOU 税收锚定验证位（M2 落地）
            sb.pucr = pucr
        if s_rights is not None:
            sb.s_rights = list(s_rights)

        nca = build_nca(
            operation="SBX_CONFIGURE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"pucr={pucr is not None}; s_rights={len(sb.s_rights)}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def start_experiment(self, sandbox_id: str, operator_did: str) -> Sandbox:
        """准入完成 → 进入实验阶段（Phase0→P0）。

        六要素声明:
        目标函数: 沙盒由准入进入实验（F1-运行前置）——状态机推进 Phase0→P0
        约束矩阵: 输入——sandbox_id、operator_did；输出——P0 沙盒；禁止——非法转移
        先验分布: 任务书 §3.2 Phase 0→P0
        配置权边界: L2
        预期分配: 返回 P0 沙盒；失败=状态非法
        审计轨迹: NCA Operation=SBX_START
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.PHASE0, "进入实验")
        nca = build_nca(
            operation="SBX_START",
            operator=operator_did,
            pre_state=sb.phase.value,
            post_state=Phase.P0.value,
            audit_trail=f"operator={operator_did}",
        )
        sb.nca_ids.append(save_nca(nca))
        self._advance(sb, Phase.P0)
        return sb

    def run_iteration(self, sandbox_id: str, iteration: Dict[str, Any]) -> Sandbox:
        """实验迭代（P0）：数据收集 + ENG-003 最小化合检查日志预埋。

        六要素声明:
        目标函数: 执行一次实验迭代并记录数据（F1-运行）+ ENG-003 检查日志（F5 预埋）
        约束矩阵: 输入——sandbox_id、iteration（非空）；输出——迭代记录写入 eng003_log；
                  禁止——非实验期运行、空迭代
        先验分布: 任务书 §二 F5（ENG-003 最小化合检查器）+ 开发纪律 5（ENG-003 日志）
        配置权边界: L2；日志随沙盒存证
        预期分配: 返回更新后沙盒；失败=状态非法
        审计轨迹: NCA Operation=SBX_RUN_ITERATION
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.P0, "实验运行")
        if not iteration:
            raise ValueError("iteration 不可为空")

        # ENG-003 最小化合检查日志（M1 预埋位：物理叠加是否足够判定，F5 落地完整判定）
        sb.eng003_log.append(
            {
                "iteration": len(sb.eng003_log) + 1,
                "timestamp": _now_iso(),
                "physically_composable": True,  # M1 预埋：假定物理叠加优先成立，F5 落地三条件检验
                "check": "ENG-003 最小化合预检（M1 预埋，F5 落地）",
                "iteration_data": iteration,
            }
        )
        nca = build_nca(
            operation="SBX_RUN_ITERATION",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"iteration={len(sb.eng003_log)}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def evaluate(
        self,
        sandbox_id: str,
        pcr_input: float,
        tax_revenue: float,
        employment_ss: float,
        data_nature: str = "simulated",
    ) -> Sandbox:
        """沙盒评估（P0→P1）：激活系数计算（F3）+ 过程 NCA 存证（F8）。

        六要素声明:
        目标函数: 计算激活系数并推进评估阶段（F1-评估 + F3 + F8）
        约束矩阵: 输入——pcr/tax/ss/data_nature（activation_engine 校验）；
                  输出——P1 沙盒 + activation_log；禁止——α 计算 mock、负数输入
        先验分布: 任务书 §二 F3 + KB-ECON-001 §7 + 开发纪律 1（不可 mock）
        配置权边界: L2；计算输入输出全部 NCA 存证（可审计）
        预期分配: 返回 P1 沙盒（含激活系数记录）；失败=输入非法/状态非法
        审计轨迹: NCA Operation=SBX_EVALUATE（含输入哈希）
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.P0, "沙盒评估")

        result = compute_activation(pcr_input, tax_revenue, employment_ss, data_nature)
        from hashlib import sha256
        import json as _json

        input_hash = sha256(
            _json.dumps({"pcr": pcr_input, "tax": tax_revenue, "ss": employment_ss}, sort_keys=True).encode()
        ).hexdigest()

        log_entry = {
            "timestamp": _now_iso(),
            **result,
            "input_hash": input_hash,
        }
        sb.activation_logs.append(log_entry)

        nca = build_nca(
            operation="SBX_EVALUATE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=Phase.P1.value,
            audit_trail=f"coefficient={result['coefficient']}; input_hash={input_hash[:16]}",
            negative_space_check="FUSE" if result["status"] == "财政不可持续" else "PASS",
        )
        sb.nca_ids.append(save_nca(nca))
        self._advance(sb, Phase.P1)
        return sb

    def exit(
        self,
        sandbox_id: str,
        signatures: List[Dict[str, str]],
        human_signatory: str,
    ) -> Sandbox:
        """沙盒出盒（P1→Exit）：SV-1（α>1.2）+ SV-6（三方签名）硬校验，人类签批。

        六要素声明:
        目标函数: 沙盒出盒（F1-出盒）——正和交付确认 + 资产确权前置
        约束矩阵: 输入——signatures（异构三角）、human_signatory；
                  禁止——α≤1.2 出盒（SV-1）、三方签名不足出盒（SV-6）、无人类签批
        先验分布: 任务书 §五 SV-1/SV-6 + §七（出盒评估须人类最终签名）
        配置权边界: L2；出盒为终态操作，须人类签批
        预期分配: 返回 Exit 沙盒；失败=资格不满足（列明原因）
        审计轨迹: NCA Operation=SBX_EXIT（Human-Signature 字段）
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.P1, "沙盒出盒")

        if not human_signatory:
            raise ValueError("human_signatory 不可为空——出盒须人类最终签名（任务书 §七：智能体可推荐，人类裁决）")

        latest = sb.activation_logs[-1] if sb.activation_logs else None
        if latest is None:
            raise ValueError("出盒前必须先评估（SBX_EVALUATE）生成激活系数记录")

        activation = {
            "coefficient": latest["coefficient"],
            "exit_required": latest["exit_required"],
            "status": latest["status"],
        }
        # 签名结构硬校验（R6/V2：collect 收口——逐签校验 role/did/signature，杜绝任意 dict 旁路）
        for sig in signatures:
            multisig.collect_signature(sig.get("role", ""), sig.get("did", ""), sig.get("signature", ""))
        # 达数判定（SV-6 异构三角 ≥3，三方各 ≥1；同角色不重复计票）
        sig_result = multisig.verify_trinity_signatures(signatures)
        eligibility = check_exit_eligibility(activation, sig_result)
        if not eligibility["eligible"]:
            reasons = eligibility["reasons"] + sig_result.get("reasons", [])
            raise ValueError("出盒资格不满足: " + "; ".join(reasons))

        nca = build_nca(
            operation="SBX_EXIT",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=Phase.EXIT.value,
            human_signature=human_signatory,
            audit_trail=f"coefficient={activation['coefficient']}; signatures={sig_result['count']}/3",
            negative_space_check="PASS",
        )
        sb.nca_ids.append(save_nca(nca))
        self._advance(sb, Phase.EXIT)
        return sb

    def close(
        self,
        sandbox_id: str,
        trigger_role: str,
        reason: str,
        human_signatory: str,
    ) -> Sandbox:
        """沙盒关闭（任意非终态→Closed）：负空间熔断（SV-3）/三方终止（SV-4），人类裁决。

        六要素声明:
        目标函数: 沙盒关闭（F1-关闭）——负空间熔断 / 三方终止 / 资产清算 / 审计归档
        约束矩阵: 输入——trigger_role（三方之一）、reason、human_signatory；
                  禁止——非三方角色触发终止（SV-4）、无人类裁决关闭、终态再关闭
        先验分布: 任务书 §二 F1 沙盒关闭 + §五 SV-3/SV-4 + §七（出盒人类最终签名）
        配置权边界: L2；关闭为终态操作，人类裁决
        预期分配: 返回 Closed 沙盒；失败=角色非法/状态非法
        审计轨迹: NCA Operation=SBX_CLOSE
        """
        sb = self._require(sandbox_id)
        if sb.phase in (Phase.EXIT, Phase.CLOSED):
            raise ValueError(f"沙盒已处终态（{sb.phase.value}），不可关闭")
        if not multisig.can_trigger_termination(trigger_role):
            raise ValueError(f"trigger_role 必须为三位一体之一（SV-4），收到 {trigger_role!r}")
        if not reason or not human_signatory:
            raise ValueError("reason 与 human_signatory 必填（人类裁决关闭）")

        # SV-3 熔断标记：结构化继承最近激活系数判定 + 最近正和验证 FUSE（#3）
        fuse = "负空间" in reason or "熔断" in reason
        if sb.activation_logs and sb.activation_logs[-1].get("status") == "财政不可持续":
            fuse = True
        if sb.positive_sum_logs and sb.positive_sum_logs[-1].get("fuse"):
            fuse = True

        nca = build_nca(
            operation="SBX_CLOSE",
            operator=trigger_role,
            pre_state=sb.phase.value,
            post_state=Phase.CLOSED.value,
            human_signature=human_signatory,
            audit_trail=f"reason={reason}; trigger_role={trigger_role}",
            negative_space_check="FUSE" if fuse else "PASS",
        )
        sb.nca_ids.append(save_nca(nca))
        self._advance(sb, Phase.CLOSED)
        return sb

    def get(self, sandbox_id: str) -> Sandbox:
        """公开读取沙盒（路由层用；不存在抛 KeyError）。

        六要素声明:
        目标函数: 沙盒详情读取（F1-R 路由入口）
        约束矩阵: 输入——sandbox_id；输出——Sandbox；禁止——不存在放行
        先验分布: _require 内部实现
        配置权边界: L2
        预期分配: 返回沙盒；失败=KeyError
        审计轨迹: 只读，不生成 NCA
        """
        return self._require(sandbox_id)

    # ============================================================ M2 扩展区

    def configure_trinity(
        self,
        sandbox_id: str,
        profiles: List[Dict[str, Any]],
    ) -> Sandbox:
        """F2 三位一体配置：注册创新者/投资者/政府三方（M2）。

        六要素声明:
        目标函数: 三方注册入沙盒（F2）——创新者/投资者/政府配置 + Shapley 分配位
        约束矩阵: 输入——profiles（role/did/contribution/reservation_utility）；输出——更新后 Sandbox；
                  禁止——角色重复、非法角色（trinity 模块校验）
        先验分布: 任务书 §二 F2 + §3.2 TrinityConfig
        配置权边界: L2；配置随 NCA 存证
        预期分配: 返回含 trinity 配置的沙盒；失败=ValueError
        审计轨迹: SBX_TRINITY_CONFIGURE NCA 存证
        """
        sb = self._require(sandbox_id)
        if sb.trinity and set(sb.trinity.get("profiles", {}).keys()) == set(TRINITY_ROLES):
            raise ValueError("三方已配置齐，禁止覆盖（如需调整走 DCD/三方重配流程）")
        # P3-4: 部分覆盖窗口——已注册角色不可重提交（防静默覆盖旧值）
        if sb.trinity.get("profiles"):
            existing = set(sb.trinity["profiles"].keys())
            for p in profiles:
                if p["role"] in existing:
                    raise ValueError(f"角色 {p['role']} 已注册，禁止覆盖（走 DCD 调整）")
        self._assert_phase(sb, Phase.PHASE0, "三方配置")
        coord = TrinityCoordinator()
        for p in profiles:
            coord.register(
                p["role"], p["did"], p.get("contribution", {}), float(p.get("reservation_utility", 0.0))
            )
        sb.trinity = {
            "profiles": coord.profiles(),
            "shapley_weights": {},  # F2 分配结果位（shapley_allocate 填充）
            "status": "configured",
        }
        nca = build_nca(
            operation="SBX_TRINITY_CONFIGURE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"roles={'/'.join(sorted(coord.profiles().keys()))}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def shapley_allocate(self, sandbox_id: str) -> Sandbox:
        """F2 Shapley 分配（三方收益分配，KB-ECON-001 §4）。

        六要素声明:
        目标函数: 计算三方 Shapley 分配并写入沙盒（F2）
        约束矩阵: 输入——sandbox_id（须已配置三方）；输出——更新后 Sandbox（shapley_weights）；
                  禁止——三方未配置齐
        先验分布: KB-ECON-001 §4（φ_i 公式 + 四性质）
        配置权边界: L2
        预期分配: 返回含分配结果的沙盒；失败=ValueError
        审计轨迹: SBX_SHAPLEY_ALLOCATE NCA 存证（含 coalition 价值表）
        """
        sb = self._require(sandbox_id)
        if not sb.trinity or not sb.trinity.get("profiles"):
            raise ValueError("先执行 SBX_TRINITY_CONFIGURE 配置三方")
        if sb.phase in (Phase.EXIT, Phase.CLOSED):
            raise ValueError(f"终态（{sb.phase.value}）不可 Shapley 分配")
        coord = TrinityCoordinator()
        for role, p in sb.trinity["profiles"].items():
            coord.register(role, p["did"], p.get("contribution", {}), float(p.get("reservation_utility", 0.0)))

        # 联合价值函数：v(S) = 基础投入和 + 协同因子（M2 简化；M4 接真实正和解）
        def coalition_value(s: frozenset) -> float:
            base = sum(
                float(sb.trinity["profiles"][r].get("contribution", {}).get("value", 0.0))
                for r in s if r in sb.trinity["profiles"]
            )
            synergy = 1.0 + 0.15 * len(s)
            return base * synergy if s else 0.0

        result = coord.shapley_allocate(coalition_value)
        sb.trinity["shapley_weights"] = result["allocations"]
        sb.trinity["shapley_properties"] = result["properties"]
        sb.trinity["status"] = "allocated"
        nca = build_nca(
            operation="SBX_SHAPLEY_ALLOCATE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"allocations={result['allocations']}; props={result['properties']}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def allocate_sright(
        self,
        sandbox_id: str,
        scene: str,
        holder_did: str,
        gradient: str = "L0",
    ) -> Sandbox:
        """F4 S-Right 场景配置权分配（M2）。

        六要素声明:
        目标函数: S-Right 分配（F4）——场景配置权 + 制度梯度
        约束矩阵: 输入——scene/holder_did/gradient；输出——更新后 Sandbox（s_rights）；
                  禁止——非法梯度、空场景
        先验分布: 任务书 §二 F4
        配置权边界: L2；宪法 C13（配置权非占有权）
        预期分配: 返回含 S-Right 的沙盒；失败=ValueError
        审计轨迹: SBX_SRIGHT_ALLOCATE NCA 存证
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.PHASE0, "S-Right 分配")
        sright = allocate_sright(scene, holder_did, gradient)
        sb.s_rights.append(sright)
        nca = build_nca(
            operation="SBX_SRIGHT_ALLOCATE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"scene={scene}; gradient={gradient}; holder={holder_did}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def pucr_presale(
        self,
        sandbox_id: str,
        amount: float,
        data_nature: str = "simulated",
        mou_anchor: str = "",
    ) -> Sandbox:
        """F4/SV-2 PUCR 预售（零数据企业第一笔可验证硬数据）。

        六要素声明:
        目标函数: PUCR 预售记录（F4/SV-2）——配置权预售产生可验证数据
        约束矩阵: 输入——amount>0、data_nature；输出——更新后 Sandbox（pucr）；
                  禁止——amount≤0、数据性质伪造
        先验分布: 任务书 §二 F4 + SV-2 + KB-ECON-001 §5
        配置权边界: L2；MOU 锚定验证位（M4 接真实税务）
        预期分配: 返回含 pucr 的沙盒；失败=ValueError
        审计轨迹: SBX_PUCR_PRESALE NCA 存证（含 amount/data_nature）
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.PHASE0, "PUCR 预售")
        holder = sb.s_rights[0]["holder_did"] if sb.s_rights else sb.initiator_did
        sright_ref = {"holder_did": holder}
        pucr_record = pucr_presale(sright_ref, amount, data_nature, mou_anchor)["pucr"]
        sb.pucr = pucr_record
        nca = build_nca(
            operation="SBX_PUCR_PRESALE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"amount={amount}; data_nature={data_nature}; mou_anchor={mou_anchor or 'pending'}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def chem_combine(
        self,
        sandbox_id: str,
        assets: List[str],
        conditions: Dict[str, bool],
        justification: str,
        catalyst: bool = False,
    ) -> Sandbox:
        """F5 正向化合（CHEM-001 + ENG-003 检查 + F6 正和门槛）。

        六要素声明:
        目标函数: 五阶资产正向化合（F5/CHEM-001）——ENG-003 前置 + 正和门槛（绑定最近正和验证）+ NCA 产出
        约束矩阵: 输入——assets/conditions/justification/catalyst；
                  禁止——ENG-003 判定物理叠加优先（SV-5）、无正和验证记录（须先 SBX_POSITIVE_SUM）、
                  正和增量≤0（CHEM-004）；surplus 由服务端取自 positive_sum_logs（不接受客户端自报）
        先验分布: 任务书 §二 F5 + KB-ECON-001 §8 + F6 正和验证
        配置权边界: L2；化合调用随 NCA 存证
        预期分配: 返回含反应记录/ENG-003 日志的沙盒；失败=ValueError
        审计轨迹: SBX_CHEM_COMBINE NCA 存证（含 eng003 判定 + surplus 来源）
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.P0, "正向化合")
        if not sb.positive_sum_logs:
            raise ValueError("化合前必须先正和验证（SBX_POSITIVE_SUM），surplus 不可自报")
        # P3-3: 取最近一条含 delta 的正和验证记录（兼容 DELIVERY_CONFIRM 记录无 delta）
        surplus = next(
            (float(log["delta"]) for log in reversed(sb.positive_sum_logs) if "delta" in log),
            None,
        )
        if surplus is None:
            raise ValueError("化合前必须先正和验证（SBX_POSITIVE_SUM），surplus 不可自报")
        eng003 = eng003_min_compound_check(assets, conditions, justification)
        rx = _chem_combine(
            sandbox_id, assets, f"cfg-right:{sandbox_id}", eng003, surplus, catalyst=catalyst
        )
        # ENG-003 日志落地（M1 预埋位启用，格式向后兼容）
        sb.eng003_log.append(
            {
                "iteration": len(sb.eng003_log) + 1,
                "timestamp": _now_iso(),
                "physically_composable": eng003["physically_composable"],
                "check": f"ENG-003 {eng003['decision']}",
                "conditions": eng003["conditions"],
                "justification": justification,
                "iteration_data": {"reaction": rx["reaction_id"], "assets": assets},
            }
        )
        rx["product_nca"] = None  # 出盒时经 F8 生成产品 NCA（M2 记录反应轨迹）
        sb.reactions.append(rx)
        nca = build_nca(
            operation="SBX_CHEM_COMBINE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"reaction={rx['reaction_id']}; eng003={eng003['required']}; surplus={surplus}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def chem_separate(
        self,
        sandbox_id: str,
        nca_id: str,
        governance_ref: str,
        separation_cost: float,
    ) -> Sandbox:
        """F5 反向分离（CHEM-002：NCA 析构，需治理介入）。

        六要素声明:
        目标函数: 反向分离（F5/CHEM-002）——高成本析构，治理介入
        约束矩阵: 输入——nca_id/governance_ref/separation_cost；禁止——无治理引用
        先验分布: 任务书 §二 F5（反向分离高成本，需法律仲裁/治理介入）
        配置权边界: L2；分离为高成本操作
        预期分配: 返回含分离记录的沙盒；失败=ValueError
        审计轨迹: SBX_CHEM_SEPARATE NCA 存证
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.P0, "反向分离")
        sep = _chem_separate(sandbox_id, nca_id, governance_ref, separation_cost)
        sb.reactions.append(sep)
        nca = build_nca(
            operation="SBX_CHEM_SEPARATE",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"separation={sep['reaction_id']}; governance={governance_ref}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    def verify_positive_sum(
        self,
        sandbox_id: str,
        coalition_utility: float,
        independent_utilities: List[float],
    ) -> Sandbox:
        """F6 正和博弈实时验证（KB-ECON-001 §3：S_synergy > 0）。

        六要素声明:
        目标函数: 正和验证（F6）——S_synergy > 0，非正和 → FUSE 熔断标记
        约束矩阵: 输入——coalition_utility/independent_utilities；输出——更新后 Sandbox（positive_sum_logs）；
                  禁止——非正和判通过（熔断）
        先验分布: KB-ECON-001 §3 + 任务书 §二 F6
        配置权边界: L2；验证随 NCA 存证
        预期分配: 返回含正和验证记录的沙盒；失败=ValueError（非正和）
        审计轨迹: SBX_POSITIVE_SUM NCA 存证（negative_space_check=FUSE 若非正和）
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.P0, "正和验证")
        result = genie.positive_sum_check(coalition_utility, independent_utilities)
        sb.positive_sum_logs.append(
            {
                "timestamp": _now_iso(),
                **result,
            }
        )
        nca = build_nca(
            operation="SBX_POSITIVE_SUM",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"delta={result['delta']}; index={result['positive_sum_index']}",
            negative_space_check="FUSE" if result["fuse"] else "PASS",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        if result["fuse"]:
            # SV-3: 非正和方向自动阻断（任务书 F6）——记录 FUSE 存证后阻断，须人类裁决
            raise ValueError("非正和 → 负空间熔断（SV-3），沙盒须人类裁决后方可继续实验")
        return sb

    def delivery_confirm(
        self,
        sandbox_id: str,
        contract_id: str,
        target_utility: Dict[str, float],
        actual_mou: Dict[str, float],
        token_ref: str,
    ) -> Sandbox:
        """F6 出盒正和交付确认（效用精灵 + NCA 存证 SV-7）。

        六要素声明:
        目标函数: 出盒交付确认（F6/任务书 §6.3）——MOU 税收锚定硬验证 + NCA 存证
        约束矩阵: 输入——contract_id/target_utility/actual_mou/token_ref；输出——更新后 Sandbox + 确认记录；
                  禁止——效用精灵缺失降级（RuntimeError）
        先验分布: 任务书 §6.3 + tdca-utility-genie ContractDeliveryValidator
        配置权边界: L2；确认报告随 SBX_DELIVERY_CONFIRM NCA 存证（SV-7）
        预期分配: 返回含交付确认记录的沙盒；失败=RuntimeError/ValueError
        审计轨迹: SBX_DELIVERY_CONFIRM NCA 存证（含确认报告哈希）
        """
        sb = self._require(sandbox_id)
        self._assert_phase(sb, Phase.P1, "出盒交付确认")  # P3-2: 交付确认须评估期（SV-1 出盒语义）
        report = genie.delivery_confirm(contract_id, target_utility, actual_mou, token_ref)
        sb.positive_sum_logs.append({"timestamp": _now_iso(), "delivery_confirm": report, "operation": "DELIVERY_CONFIRM"})
        nca = build_nca(
            operation="SBX_DELIVERY_CONFIRM",
            operator=sb.initiator_did,
            pre_state=sb.phase.value,
            post_state=sb.phase.value,
            audit_trail=f"contract={contract_id}; tax_verified={report.get('tax_anchor_verification')}",
        )
        sb.nca_ids.append(save_nca(nca))
        sb.updated_at = _now_iso()
        self._save(sb)
        return sb

    # ------------------------------------------------------------------ 内部

    def _require(self, sandbox_id: str) -> Sandbox:
        from . import store

        try:
            sb = store.load_sandbox(sandbox_id)
        except (ValueError, json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"沙盒数据损坏或 ID 非法: {e}") from e
        if sb is None:
            raise KeyError(f"沙盒不存在: {sandbox_id}")
        return sb
    def _save(self, sb: Sandbox) -> None:
        from . import store

        store.save_sandbox(sb)

    @staticmethod
    def _assert_phase(sb: Sandbox, expected: Phase, action: str) -> None:
        if sb.phase != expected:
            raise ValueError(f"{action}要求阶段 {expected.value}，当前 {sb.phase.value}（非法状态转移）")

    def _advance(self, sb: Sandbox, target: Phase) -> None:
        """状态机推进（合法转移表校验，非法转移拒绝）。

        六要素声明:
        目标函数: 状态机核心——校验并执行阶段转移
        约束矩阵: 输入——sb、target；输出——sb.phase 更新 + 持久化；禁止——非法转移
        先验分布: 任务书 §3.2 Phase 0→P0→P1→Exit
        配置权边界: L2
        预期分配: 转移成功；失败=ValueError（非法转移）
        审计轨迹: NCA 由调用方先行存证
        """
        allowed = _TRANSITIONS.get(sb.phase, set())
        if target not in allowed:
            raise ValueError(f"非法状态转移: {sb.phase.value} → {target.value}（允许: {sorted(p.value for p in allowed)}）")
        sb.phase = target
        sb.updated_at = _now_iso()
        self._save(sb)
