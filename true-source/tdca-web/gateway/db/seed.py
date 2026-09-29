# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M1 | 目标函数: 种子数据（幂等，可重复执行）
# 约束矩阵: ID92——种子来源与 provenance 严格按设计包 §三：五面板 simulated / 205 元案例 mixed / 术语 real
# 先验分布: 前端 mock 常量（agents.tsx 五面板 / sandbox.tsx SEA）+ CASE-002 教学视频案例（205 元复算一致）
# 预期分配: agents×5 + NM×4 + EIOS×10 + mou×1 + nca×3（链）+ tax_events×3 + sandbox_states×5
#           + metrics×1 + asset_orders×5 + terms×8 + attestation×7（pending3+history4）
# 审计轨迹: NCA-KIMIWEB-003/004
# =============================================================================
"""种子数据：自然键查重幂等。重复执行不产生重复行。"""
import datetime

from db import get_session
from db.models import (
    Agent, AssetOrder, AttestationRequest, GovernanceEvent, MouRecord, NcaChain,
    SandboxApplication, SandboxState, SystemMetric, TaxEvent, TermsRegistry, User,
)

_NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

# 幂等策略：自然键查重（存在即跳过）——自增主键表无唯一约束可用，统一走查重，通用且可审计
_KEYS = {
    Agent: ["agent_id"],
    NcaChain: ["nca_id"],
    TaxEvent: ["event_id"],
    MouRecord: ["agent_id", "period"],
    SandboxState: ["requirement"],
    SandboxApplication: ["apply_id"],
    SystemMetric: [],  # 快照表：仅当表为空时种首条
    AttestationRequest: ["request_id"],
    AssetOrder: ["order_no"],
    TermsRegistry: ["term_id"],
    GovernanceEvent: [],
    User: ["username"],
}


def _ins(session, model, rows):
    keys = _KEYS[model]
    for row in rows:
        if not keys:
            if session.query(model).first() is not None:
                continue
        else:
            probe = {k: row[k] for k in keys}
            if session.query(model).filter_by(**probe).first() is not None:
                continue
        session.add(model(**row))


def seed():
    s = get_session()
    with s.begin():
        _ins(s, Agent, [
            dict(agent_id="AGENT-TRAINER", name="Trainer 培训导师", endpoint="tdca-trainer",
                 capability="学术交流/考核测评/学习路径", tdid="tdid:trainer", five_role="M",
                 scene="academy", attestation_state="valid", created_at=_NOW),
            dict(agent_id="AGENT-EXECUTOR", name="Executor 执行官", endpoint="tdca-executor",
                 capability="任务执行/交付闭环", tdid="tdid:executor", five_role="M",
                 scene="studio", attestation_state="valid", created_at=_NOW),
            dict(agent_id="AGENT-AUDITOR", name="Auditor 审查官", endpoint="tdca-code-reviewer",
                 capability="代码审查/合规审计", tdid="tdid:auditor", five_role="G",
                 scene="governance", attestation_state="valid", created_at=_NOW),
            dict(agent_id="AGENT-SERVICE", name="Service 服务官", endpoint="tdca-industry-advisor",
                 capability="行业顾问/落地匹配", tdid="tdid:service", five_role="L",
                 scene="market", attestation_state="expiring", created_at=_NOW),
            dict(agent_id="AGENT-GENIE", name="Genie 效用精灵", endpoint="tdca-utility-genie",
                 capability="正和满意解/效用计量", tdid="tdid:genie", five_role="mu",
                 scene="tax", attestation_state="valid", created_at=_NOW),
        ])
        _ins(s, NcaChain, [
            dict(nca_id="NCA-SEED-001", prev_nca="GENESIS", action="TaskLodge",
                 actor="seed", artifact_path="db/seed.py", sha256_8="seed0001", ts=_NOW),
            dict(nca_id="NCA-SEED-002", prev_nca="NCA-SEED-001", action="Delivery",
                 actor="seed", artifact_path="db/seed.py", sha256_8="seed0002", ts=_NOW),
            dict(nca_id="NCA-SEED-003", prev_nca="NCA-SEED-002", action="HumanApproval",
                 actor="HUMAN-FOUNDER-001", artifact_path="db/seed.py", sha256_8="seed0003",
                 data_provenance="real", ts=_NOW),
        ])
        # CASE-002 教学视频案例：205 元 = 40 + 150 + 15（复算一致口径，机制真实/税率模拟 → mixed）
        _ins(s, TaxEvent, [
            dict(event_id="EVT-CASE002-01", type="dispatch_tax", agent_id="AGENT-EXECUTOR",
                 call_id="TDCA-FC-20260813-VIDEO-TEACH-001", amount=4000, tax_rate_bp=200,
                 nca_ref="NCA-SEED-001", data_provenance="mixed", ts=_NOW),
            dict(event_id="EVT-CASE002-02", type="royalty", agent_id="AGENT-GENIE",
                 call_id="TDCA-FC-20260813-VIDEO-TEACH-001", amount=15000, tax_rate_bp=750,
                 nca_ref="NCA-SEED-002", data_provenance="mixed", ts=_NOW),
            dict(event_id="EVT-CASE002-03", type="transaction_fee", agent_id="AGENT-GENIE",
                 call_id="TDCA-FC-20260813-VIDEO-TEACH-001", amount=1500, tax_rate_bp=75,
                 nca_ref="NCA-SEED-003", data_provenance="mixed", ts=_NOW),
        ])
        _ins(s, MouRecord, [
            dict(agent_id="AGENT-GENIE", period="2026-08", mou_inbound=19000,
                 mou_outbound=1500, note="CASE-002 口径演示（205 元=40+150+15）",
                 data_provenance="mixed", ts=_NOW),
        ])
        _ins(s, SandboxState, [
            dict(requirement="SEA-1 准入声明", status="GREEN", note="五要件演示态", checked_at=_NOW),
            dict(requirement="SEA-2 负空间声明", status="GREEN", note="五要件演示态", checked_at=_NOW),
            dict(requirement="SEA-3 存证承诺", status="GREEN", note="五要件演示态", checked_at=_NOW),
            dict(requirement="SEA-4 熔断联动", status="GREEN", note="五要件演示态", checked_at=_NOW),
            dict(requirement="SEA-5 人类签批位", status="GREEN", note="五要件演示态", checked_at=_NOW),
        ])
        _ins(s, SystemMetric, [
            dict(total_deliveries=128, total_tax_settled=20500, avg_latency_ms=5.2,
                 total_fused=3, total_fail_closed=7, theta=0.65, phi=0.5, ts=_NOW),
        ])
        _ins(s, AssetOrder, [
            dict(order_no=1, name="效用权", description="场景效用函数调用权", asset_count=0),
            dict(order_no=2, name="配置权", description="L2 配置权市场层（ID76）", asset_count=0),
            dict(order_no=3, name="NCA 嵌套认知资产", description="调用即存证（ID91）", asset_count=0),
            dict(order_no=4, name="MOU 税收锚定凭证", description="进项+出项（ID79）", asset_count=0),
            dict(order_no=5, name="跨场景配置画像", description="多场景偏态档案（L-6 演进）", asset_count=0),
        ])
        # M2 扩充：通知机 MRCR 四角色 + eios 十端点（A-9/A-10 DB 实读数据源）
        _ins(s, Agent, [
            dict(agent_id="AGENT-NM-01", name="NM-Operator", tdid="TDID-NM-Operator",
                 scene="notification", status="active", created_at=_NOW),
            dict(agent_id="AGENT-NM-02", name="NM-Gov", tdid="TDID-NM-Gov",
                 scene="notification", status="active", created_at=_NOW),
            dict(agent_id="AGENT-NM-03", name="NM-Fin", tdid="TDID-NM-Fin",
                 scene="notification", status="active", created_at=_NOW),
            dict(agent_id="AGENT-NM-04", name="NM-Med", tdid="TDID-NM-Med",
                 scene="notification", status="active", created_at=_NOW),
        ])
        import sys as _sys
        from pathlib import Path as _Path
        _eios = str(_Path(__file__).resolve().parents[2] / "tdca-eios")
        if _eios not in _sys.path:
            _sys.path.insert(0, _eios)
        from genie_api import GenieAPI
        _caps = GenieAPI().CAPABILITIES
        _ins(s, Agent, [
            dict(agent_id=f"EIOS-{i:02d}", name=meta["capability"], endpoint=ep,
                 capability=meta["capability"], status="active", created_at=_NOW)
            for i, (ep, meta) in enumerate(_caps.items(), start=1)
        ])
        # M2 扩充：确权待审队列 3 条（紧急度 urgent/normal/low）+ 已决历史 4 条
        _ins(s, AttestationRequest, [
            dict(request_id="DAR-001", agent_id="AGENT-GENIE", request_type="scene_extension",
                 urgency="urgent", reason="申请扩展至跨场景配置画像场景（L-6 演进前置）",
                 status="pending", ts=_NOW),
            dict(request_id="DAR-002", agent_id="AGENT-SERVICE", request_type="compound_auth",
                 urgency="normal", reason="行业顾问场景申请复合授权（通知机+翻译市场）",
                 status="pending", ts=_NOW),
            dict(request_id="DAR-003", agent_id="AGENT-TRAINER", request_type="cognition_evolution",
                 urgency="low", reason="培训导师认知演进备案（教学语料扩充）",
                 status="pending", ts=_NOW),
            dict(request_id="META-ATT-SEED-01", agent_id="AGENT-GENIE", request_type="meta",
                 reason="activation=1.35（CASE-002 出盒终裁演示）", status="approved",
                 decided_by="HUF", nca_ref="NCA-SEED-001", ts=_NOW),
            dict(request_id="DAR-H-001", agent_id="AGENT-EXECUTOR", request_type="objective_fix",
                 urgency="normal", reason="目标函数固化申请", status="approved",
                 decided_by="HUF", nca_ref="NCA-SEED-002", ts=_NOW),
            dict(request_id="DAR-H-002", agent_id="AGENT-SERVICE", request_type="nsfl_approach",
                 urgency="urgent", reason="逼近法律绝对负空间边界（⊗）", status="rejected",
                 decided_by="HUF", nca_ref="NCA-SEED-003", ts=_NOW),
            dict(request_id="DAR-H-003", agent_id="AGENT-TRAINER", request_type="meta_child",
                 urgency="low", reason="子体继承确权（ID91 跨代链）", status="approved",
                 decided_by="HUF", nca_ref="NCA-SEED-003", ts=_NOW),
        ])
        _ins(s, TermsRegistry, [
            dict(term_id="T-NCA", term="NCA", definition="嵌套认知资产（Nested Cognitive Asset）"),
            dict(term_id="T-NSFL", term="NSFL", definition="负空间函数语言（Negative Space Function Language）"),
            dict(term_id="T-MOU", term="MOU", definition="最低可见效用 = 进项税收 + 出项税收（税收锚定硬下限）"),
            dict(term_id="T-SI", term="SI", definition="会话索引文件（Session Index）"),
            dict(term_id="T-FC", term="FC", definition="函数调用任务（Function Call）"),
            dict(term_id="T-MRCR", term="MRCR", definition="多角色兼容性规则（Multi-Role Compatibility Rule）"),
            dict(term_id="T-PUCR", term="PUCR", definition="配置权预售（Pre-sale of Configuration Rights）"),
            dict(term_id="T-TDCA", term="TDCA", definition="可信数字协作架构 ⟨ℑ, 𝒯, ℰ, 𝒫, 𝒦⟩"),
        ])
        # M3：founder 账号——口令只从环境变量 TDCA_FOUNDER_PASSWORD 读（人肉直给→环境变量→不落盘），
        # 缺省拒种（fail-closed：绝不种默认/硬编码口令）；库内仅存 PBKDF2 哈希+盐
        import os as _os
        _pw = _os.environ.get("TDCA_FOUNDER_PASSWORD", "")
        if _pw:
            from auth import hash_password as _hp
            _ph, _salt, _it = _hp(_pw)
            _ins(s, User, [dict(username="founder", password_hash=_ph, salt=_salt,
                                iterations=_it, role="founder", created_at=_NOW)])
            print("founder 种子已种（哈希+盐，无明文）")
        else:
            print("founder 种子跳过：TDCA_FOUNDER_PASSWORD 未设置（fail-closed，不种默认口令）")
        # M5：存量智能体归属回填（幂等——仅回填 NULL，重跑不回改）
        n_bf = s.query(Agent).filter(Agent.owner_username.is_(None)).update(
            {Agent.owner_username: "founder"})
        if n_bf:
            print(f"owner 回填 {n_bf} 行 → founder（仅 NULL 行，幂等）")
    s.close()
    print("seed OK（幂等，可重复执行）")


if __name__ == "__main__":
    seed()
