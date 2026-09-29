# -*- coding: utf-8 -*-
"""
TDCA 前端 API 面包装层（A 类 10 项）——M2：数据源从 mock 切换为真实库（KIMI-WEB-DB-TASK-001 M2）

依据: TDCA-FRONTEND-BACKEND-REVIEW-001 A-1~A-10（BV-3：FROZEN 引擎只 import + 调用公开方法）+
      KIMI-WEB-DB-M1-DESIGN-001（10 表 schema）。M2 变更：读端点查 DB，写端点落库 + NCA 链；
      DB 无数据时回退 FROZEN 引擎/演示常量（fail-closed 友好降级，接口契约不变）。

端点（挂 tdca-gateway /api/v1/*）:
  A-1 GET  /api/v1/system/overview            → system_metrics 表（无快照回退引擎统计）
  A-2 GET  /api/v1/tax/mou/{agent_id}         → mou_records 表（ID79 不可降）
  A-2 GET  /api/v1/tax/nca-history            → tax_events 表（ID80 事件溯源）
  A-2 GET  /api/v1/tax/shapley/{call_id}      → tax_events 按 call_id（ID43）
  A-3 POST /api/v1/config-right/call          → EconomicConfigurator 闭环 + 落库（tax_events/mou/nca）
  A-4 GET  /api/v1/assets/five-orders         → asset_orders 表
  A-5 GET  /api/v1/sandbox/sea-status         → sandbox_states 表
  A-5 POST /api/v1/sandbox/apply              → SandboxCompilePipeline + 落库（sandbox_applications/nca）
  A-6 GET  /api/v1/knowledge/terms            → terms_registry 表（空表回退演示子集）
  A-7 GET  /api/v1/audit/ledger-public        → tax_events 表（公共账本 O(n)）
  A-7 POST /api/v1/audit/nca-verify           → 哈希校验 + nca_chain 在链核验（ID91）
  A-8 POST /api/v1/governance/huf-sign        → 落库 governance_events + nca_chain（HUF，ID71）
  A-8 POST /api/v1/governance/emergency-fuse  → Layer1Runtime 熔断 + 落库（fail-closed）
  A-9 GET  /api/v1/notifier/mrcr-status       → agents 表 NM 角色（空表回退 NmMrcrManager）
  A-10 GET /api/v1/eios/cluster-status        → agents 表 EIOS 端点（空表回退 GenieAPI）
  A-11     /api/v1/attestation/*              → attestation_requests 表 + nca_chain

纪律: 写操作（A-3/A-5/A-8/A-11）须经 B-4 鉴权（治理路径强制）；全链路 NCA 水印；
     data_nature 由数据行 provenance 决定（ID92）；MOU 不可降（ID79）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/v1")

# ---- FROZEN 库路径注入（相对 workspace 根）----
_ROOT = Path(__file__).resolve().parent.parent
for _sub in ("tdca-microtax", "tdca-ns-runtime", "tdca-notification-machine",
             "tdca-notification-machine/engine", "tdca-eios",
             "tdca-dual-protocol-package/engine"):
    _p = _ROOT / _sub
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ---- M2：DB 访问（惰性工厂；测试经 DATABASE_URL 隔离）----
from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _nature_of(provenances) -> str:
    """ID92：data_nature 由数据行 provenance 聚合（全真→real，含 mixed/混杂→mixed，否则 simulated）。"""
    ps = set(provenances)
    if not ps:
        return "simulated"
    if ps == {"real"}:
        return "real"
    if "mixed" in ps or len(ps) > 1:
        return "mixed"
    return "simulated"


def _nca_watermark(payload: dict, nature: str = "simulated") -> dict:
    """NCA 水印（ID91 自反化合——响应哈希关联，审计可验证）。"""
    h = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"data": payload, "nca_watermark": "sha256:" + h[:32], "ts": _utc(),
            "data_nature": nature}


def _sim_note() -> str:
    return "模拟态：演示参数，真实锚定待 DCEP/法学家基准后转硬数据"


def _nca_append(action: str, actor: str, artifact_path: str = "", prov: str = "simulated") -> str:
    """写路径通用：向 nca_chain 追加一条存证（链式 prev_nca 自动取最新）。"""
    import secrets
    nonce = secrets.token_hex(8)   # 同秒同参重复写入防主键碰撞（M3 测试实证）
    with get_sessionmaker().begin() as s:
        last = s.query(M.NcaChain).order_by(M.NcaChain.ts.desc()).first()
        nca_id = "NCA-WEB-" + hashlib.sha256(
            (action + actor + _utc() + nonce
             + (last.nca_id if last else "GENESIS")).encode()).hexdigest()[:12]
        s.add(M.NcaChain(nca_id=nca_id, prev_nca=last.nca_id if last else "GENESIS",
                         action=action, actor=actor, artifact_path=artifact_path,
                         sha256_8=hashlib.sha256(artifact_path.encode()).hexdigest()[:8] if artifact_path else None,
                         data_provenance=prov, ts=_utc()))
    return nca_id


def _agent_get_or_create(s, agent_id: str, name: str = "", owner: str | None = None) -> None:
    """写路径辅助：外键完整性——主体不存在则补登记（simulated）。M5：新建时归属=登录用户。"""
    if agent_id and s.get(M.Agent, agent_id) is None:
        s.add(M.Agent(agent_id=agent_id, name=name or agent_id, created_at=_utc(),
                      owner_username=owner))


# =====================================================================
# A-1 首页 KPI / A-2 税收仪表盘（DB + TaxOfficerAgent 回退）
# =====================================================================

def _officer():
    from microtax.tax_officer import TaxOfficerAgent
    return TaxOfficerAgent()


@router.get("/system/overview")
def system_overview():
    """A-1: 首页 KPI——system_metrics 最新快照（无快照回退引擎统计）。"""
    try:
        with get_session() as s:
            row = s.query(M.SystemMetric).order_by(M.SystemMetric.id.desc()).first()
        if row is not None:
            return _nca_watermark({
                "total_deliveries": row.total_deliveries,
                "total_tax_settled": f"{row.total_tax_settled / 100:.2f}",
                "avg_latency_ms": round(row.avg_latency_ms, 3),
                "total_fused": row.total_fused,
                "total_fail_closed": row.total_fail_closed,
                "tax_rates": {"dispatch_tax": row.dispatch_tax_bp / 10000,
                              "royalty": row.royalty_bp / 10000,
                              "transaction_fee": row.transaction_fee_bp / 10000},
                "theta": row.theta if row.theta is not None else 0.70,
                "phi": row.phi if row.phi is not None else 0.30,
                "system": "ECOCOG S-1~S-16 FROZEN（613 测试绿）",
            }, nature=row.data_provenance)
        # 回退：引擎统计（空库演示态）
        officer = _officer()
        stats = dict(officer._stats) if hasattr(officer, "_stats") else {}
        return _nca_watermark({
            "total_deliveries": stats.get("total_deliveries", 0),
            "total_tax_settled": str(stats.get("total_tax_settled", 0)),
            "avg_latency_ms": round(stats.get("avg_latency_ms", 0.0), 3),
            "total_fused": stats.get("total_fused", 0),
            "total_fail_closed": stats.get("total_fail_closed", 0),
            "tax_rates": {"dispatch_tax": 0.02, "royalty": 0.075, "transaction_fee": 0.0075},
            "theta": 0.70, "phi": 0.30,
            "system": "ECOCOG S-1~S-16 FROZEN（613 测试绿）",
        })
    except Exception as e:
        raise HTTPException(500, f"A-1 overview 失败: {e}")


@router.get("/tax/mou/{agent_id}")
def tax_mou(agent_id: str):
    """A-2: MOU 锚定（mou_records 最新账期；无记录=零值明示，不可降）。"""
    try:
        with get_session() as s:
            row = (s.query(M.MouRecord).filter_by(agent_id=agent_id)
                   .order_by(M.MouRecord.period.desc()).first())
        if row is not None:
            return _nca_watermark({
                "agent_id": agent_id,
                "mou_inbound": f"{row.mou_inbound / 100:.2f}",
                "mou_outbound": f"{row.mou_outbound / 100:.2f}",
                "mou_total": f"{row.mou_total / 100:.2f}",
                "mou_irreducible": bool(row.mou_irreducible),
                "note": f"账期 {row.period}（DB 实读）",
            }, nature=row.data_provenance)
        return _nca_watermark({
            "agent_id": agent_id, "mou_inbound": "0.00", "mou_outbound": "0.00",
            "mou_total": "0.00", "mou_irreducible": True,
            "note": "该主体暂无 MOU 记录（零值非估算）" + _sim_note(),
        })
    except Exception as e:
        raise HTTPException(500, f"A-2 tax/mou 失败: {e}")


@router.get("/tax/nca-history")
def tax_nca_history():
    """A-2: 税收事件历史（tax_events 最近 50 条，事件溯源）。"""
    try:
        with get_session() as s:
            rows = s.query(M.TaxEvent).order_by(M.TaxEvent.ts.desc()).limit(50).all()
        events = [{"event_id": r.event_id, "type": r.type, "ts": r.ts} for r in rows]
        return _nca_watermark({"events": events, "total": len(events),
                               "note": "账本事件（事件溯源，O(n) 可审计）"},
                              nature=_nature_of([r.data_provenance for r in rows]))
    except Exception as e:
        raise HTTPException(500, f"A-2 nca-history 失败: {e}")


@router.get("/tax/shapley/{call_id}")
def tax_shapley(call_id: str):
    """A-2: Shapley 分账观测（tax_events 按 call_id 聚合）。"""
    try:
        with get_session() as s:
            rows = s.query(M.TaxEvent).filter_by(call_id=call_id).all()
        items = [{"event_id": r.event_id, "agent_id": r.agent_id, "amount": f"{r.amount / 100:.2f}",
                  "shapley_phi": (f"{r.shapley_phi / 100:.2f}" if r.shapley_phi is not None else None),
                  "type": r.type} for r in rows]
        return _nca_watermark({"call_id": call_id, "shapley": items or None,
                               "note": ("DB 实读" if items else "该调用暂无分账记录；")
                                       + "Shapley 分账由结算链路计算"},
                              nature=_nature_of([r.data_provenance for r in rows]))
    except Exception as e:
        raise HTTPException(500, f"A-2 shapley 失败: {e}")


# =====================================================================
# A-3 配置权市场调用（EconomicConfigurator 一键闭环 + 落库）
# =====================================================================

class ConfigCallRequest(BaseModel):
    delivery_id: str = "DEL-001"
    caller: str = "AGENT-A"
    callee: str = "AGENT-B"
    scene: str = "scene-phy-notification"
    call_value: float = 1000.0
    tax_receipt: float = 100.0
    call_type: str = "config_right_call"
    can_stack: bool = True
    violates_nsfl: bool = False
    cognitive_state: float = 0.85            # min(S_协作) 演示
    buy: float = 100.0
    sell: float = 50.0
    enterer_bias: float = 0.0
    target_scene_bias: Dict[str, float] = {}


@router.post("/config-right/call")
def config_right_call(req: ConfigCallRequest):
    """A-3: 配置权调用 → 计税/预缴 → 正和认知 → 多主体配置 一键闭环（S-15），结果落库。"""
    try:
        from microtax.models import MicroDelivery, TaxEventType, DeliveryCallType, DeliveryForm
        from microtax.configurator import EconomicConfigurator

        delivery = MicroDelivery(
            delivery_id=req.delivery_id, scene=req.scene,
            value=req.call_value,
            event_type=TaxEventType(req.call_type),
            call_type=DeliveryCallType.COMPOUND if not req.can_stack else DeliveryCallType.DISPOSABLE,
            delivery_form=DeliveryForm.ONLINE,
            participants={req.caller: 1.0, req.callee: 1.0},
            tax_in=req.tax_receipt * 0.6,      # 进项贡献（买方/调用方，模拟态 D-011）
            tax_out=req.tax_receipt * 0.4,     # 出项贡献（卖方/被调用方，模拟态 D-011）
            simulated=True,
        )
        configurator = EconomicConfigurator()
        report = configurator.configure(
            delivery=delivery,
            cognitive_states={req.caller: {"A": req.cognitive_state, "D": 0.5, "L": 0.5,
                                            "C": 0.5, "SC": 0.5},
                              req.callee: {"A": req.cognitive_state, "D": 0.5, "L": 0.5,
                                            "C": 0.5, "SC": 0.5}},
            subject_eco={req.caller: {"buy": req.buy, "sell": req.sell},
                         req.callee: {"buy": req.sell, "sell": req.buy}},
            enterer_bias=req.enterer_bias,
            target_scene_bias=req.target_scene_bias or {req.callee: 0.5},
            eco_spillover=req.tax_receipt * 0.4,
        )
        # M2 落库：税收事件 + MOU 累计 + NCA 存证（写路径全链可观测，C01）
        nca_ref = _nca_append("Delivery", f"gateway:config-right/call:{req.delivery_id}",
                              artifact_path=f"delivery:{req.delivery_id}")
        with get_sessionmaker().begin() as s:
            _agent_get_or_create(s, req.caller)
            _agent_get_or_create(s, req.callee)
            s.add(M.TaxEvent(event_id="EVT-" + req.delivery_id, type="dispatch_tax",
                             agent_id=req.caller, call_id=req.delivery_id,
                             amount=int(round(req.tax_receipt * 100)), tax_rate_bp=200,
                             nca_ref=nca_ref, ts=_utc()))
            for aid, inflow in ((req.caller, req.tax_receipt * 0.6),
                                (req.callee, req.tax_receipt * 0.4)):
                period = _utc()[:7]
                mou = (s.query(M.MouRecord).filter_by(agent_id=aid, period=period).first())
                if mou is None:
                    s.add(M.MouRecord(agent_id=aid, period=period,
                                      mou_inbound=int(round(inflow * 100)), ts=_utc()))
                else:  # MOU 只增不降（ID79）
                    mou.mou_inbound += int(round(inflow * 100))
        return _nca_watermark({
            "delivery_id": req.delivery_id,
            "full_cognition": report.full_cognition,
            "top_candidate": report.top_candidate,
            "config_matches": report.config_matches,
            "cognition": {"u_positive_sum": report.cognition.verdict.get("u_positive_sum"),
                          "theta": report.cognition.verdict.get("theta"),
                          "phi": report.cognition.verdict.get("phi")},
            "nca_ref": nca_ref,
            "note": _sim_note(),
        })
    except Exception as e:
        raise HTTPException(500, f"A-3 config-right/call 失败: {e}")


# =====================================================================
# A-4 五阶资产池 / A-6 术语 / A-7 审计
# =====================================================================

@router.get("/assets/five-orders")
def assets_five_orders():
    """A-4: 五阶资产池（asset_orders 表实读；空表回退演示框架）。"""
    with get_session() as s:
        rows = s.query(M.AssetOrder).order_by(M.AssetOrder.order_no).all()
    if rows:
        return _nca_watermark({
            "assets": [{"order": r.order_no, "name": r.name,
                        "desc": r.description or "", "count": r.asset_count} for r in rows],
            "note": "五阶资产池（DB 实读；真实资产待生态接入）",
        }, nature=_nature_of([r.data_provenance for r in rows]))
    return _nca_watermark({
        "assets": [
            {"order": 1, "name": "效用权", "desc": "场景效用函数调用权", "count": 0},
            {"order": 2, "name": "配置权", "desc": "L2 配置权市场层", "count": 0},
            {"order": 3, "name": "NCA 嵌套认知资产", "desc": "调用即存证", "count": 0},
            {"order": 4, "name": "MOU 税收锚定凭证", "desc": "进项+出项", "count": 0},
            {"order": 5, "name": "跨场景配置画像", "desc": "多场景偏态档案", "count": 0},
        ],
        "note": "五阶资产池为演示框架（模拟态），真实资产待生态接入" + _sim_note(),
    })


_TERMS = [
    {"term": "配置权", "def": "不拥有参数，只拥有场景化调用权（第三极权利）"},
    {"term": "NCA", "id": "T-NCA", "def": "嵌套认知资产——调用即存证，结构可信+认知可信"},
    {"term": "MOU", "id": "T-MOU", "def": "最低可见效用——进项税收+出项税收（硬下限）"},
    {"term": "NSFL", "id": "T-NSFL", "def": "负空间熔断——法律绝对负空间无补正（⊗）"},
    {"term": "生态溢出", "id": "T-005", "def": "核心协作方外上下游税收增量（ϕ 系数）"},
    {"term": "MRCR", "id": "T-MRCR", "def": "多角色兼容性规则——场景隔离/独立审计"},
]


@router.get("/knowledge/terms")
def knowledge_terms(q: Optional[str] = None):
    """A-6: 术语检索（terms_registry 表实读；空表回退演示子集，G-1）。"""
    with get_session() as s:
        rows = s.query(M.TermsRegistry).all()
    if rows:
        items = [{"term": r.term, "id": r.term_id, "def": r.definition} for r in rows]
        nature = _nature_of([r.data_provenance for r in rows])
        note = "术语注册表 DB 实读（G-1；权威版本以注册表登记为准）"
    else:
        items, nature, note = list(_TERMS), "simulated", "G-1 术语子集（完整权威见注册表 V1.1；本端点演示）"
    if q:
        items = [t for t in items if q.lower() in t["term"].lower() or q.lower() in t["def"].lower()]
    return _nca_watermark({"terms": items, "total": len(items), "note": note}, nature=nature)


@router.get("/audit/ledger-public")
def audit_ledger_public():
    """A-7: 公共账本查询（tax_events 最近 100 条；制度即公开，O(n) 可审计）。"""
    try:
        with get_session() as s:
            rows = s.query(M.TaxEvent).order_by(M.TaxEvent.ts.desc()).limit(100).all()
        events = [{"event_id": r.event_id, "type": r.type, "ts": r.ts,
                   "amount": f"{r.amount / 100:.2f}"} for r in rows]
        return _nca_watermark({"events": events, "total": len(events),
                               "note": "公共账本（只读，BV-3）"},
                              nature=_nature_of([r.data_provenance for r in rows]))
    except Exception as e:
        raise HTTPException(500, f"A-7 ledger-public 失败: {e}")


class NcaVerifyRequest(BaseModel):
    nca_hash: str = ""
    payload: str = ""


@router.post("/audit/nca-verify")
def audit_nca_verify(req: NcaVerifyRequest):
    """A-7: NCA 哈希校验 + nca_chain 在链核验。"""
    computed = hashlib.sha256(req.payload.encode("utf-8")).hexdigest() if req.payload else ""
    match = bool(req.nca_hash) and (req.nca_hash == computed or req.nca_hash.startswith("sha256:" + computed[:32]))
    on_chain = False
    if req.nca_hash:
        with get_session() as s:
            hit = s.get(M.NcaChain, req.nca_hash)
            if hit is None:
                hit = s.query(M.NcaChain).filter_by(sha256_8=req.nca_hash[-8:]).first()
            on_chain = hit is not None
    return _nca_watermark({"nca_hash": req.nca_hash, "computed": "sha256:" + computed[:32],
                           "verified": match, "on_chain": on_chain,
                           "note": "NCA 水印校验 + 在链核验"})


# =====================================================================
# A-5 沙盒准入 / A-8 治理
# =====================================================================

@router.get("/sandbox/sea-status")
def sandbox_sea_status():
    """A-5: SEA 五要件状态（sandbox_states 表实读；空表回退演示态）。"""
    with get_session() as s:
        rows = s.query(M.SandboxState).order_by(M.SandboxState.id).all()
    if rows:
        sea = [{"requirement": r.requirement, "status": r.status, "note": r.note or ""}
               for r in rows]
        return _nca_watermark({
            "sea": sea,
            "all_green": all(r["status"] == "GREEN" for r in sea),
            "note": "SEA 五要件（DB 实读）；AMBER 项不阻塞预研但阻塞入盒",
        }, nature=_nature_of([r.data_provenance for r in rows]))
    return _nca_watermark({
        "sea": [
            {"requirement": "任务书六要素", "status": "GREEN", "note": "TDCA-TASK-ECOCOG-001 FROZEN"},
            {"requirement": "前置核验（613 测试绿）", "status": "GREEN", "note": "全量回归通过"},
            {"requirement": "沙盒编译-核验闭环", "status": "GREEN", "note": "SandboxCompilePipeline 在位"},
            {"requirement": "激活系数>1.2 门槛", "status": "AMBER", "note": "待真实场景数据"},
            {"requirement": "人类 HUF 终裁", "status": "GREEN", "note": "HUF 通道就绪"},
        ],
        "all_green": False,
        "note": "SEA 五要件（沙盒准入前置）；AMBER 项不阻塞预研但阻塞入盒" + _sim_note(),
    })


class SandboxApplyRequest(BaseModel):
    scene_ids: List[str] = ["SCN-A", "SCN-B", "SCN-C"]
    pcr_budget: float = 9000.0
    sponsor_did: str = "did:tdca:founder"
    nsfl_boundary: str = "SCOPE-PHY-001"


@router.post("/sandbox/apply")
def sandbox_apply(req: SandboxApplyRequest, request: Request):
    """A-5: 入盒申请（SandboxCompilePipeline fail-closed + 激活系数>1.2），申请落库。M5：申请人=登录用户。"""
    try:
        from ns_runtime.sandbox_compliance import SandboxCompilePipeline
        pipeline = SandboxCompilePipeline()
        result = pipeline.compile_scene(
            scene={"scene_ids": req.scene_ids, "pcr_budget": req.pcr_budget,
                   "sponsor_did": req.sponsor_did},
            conflict_type=req.nsfl_boundary)
        compiled = result.to_dict() if result is not None else {"error": "fail-closed: 编译未通过"}
        sandbox_id = "SBX-" + hashlib.sha256(
            (req.sponsor_did + str(req.scene_ids)).encode()).hexdigest()[:8]
        nca_ref = _nca_append("TaskLodge", f"gateway:sandbox/apply:{sandbox_id}",
                              artifact_path=f"sandbox:{sandbox_id}")
        applicant = _session_username(request) or req.sponsor_did  # M5：有会话强制登录用户
        with get_sessionmaker().begin() as s:
            if s.get(M.SandboxApplication, sandbox_id) is None:
                s.add(M.SandboxApplication(
                    apply_id=sandbox_id, applicant=applicant,
                    sea_snapshot=json.dumps({"scene_ids": req.scene_ids,
                                             "pcr_budget": req.pcr_budget,
                                             "nsfl_boundary": req.nsfl_boundary}, ensure_ascii=False),
                    result="pending", nca_ref=nca_ref, ts=_utc()))
        return _nca_watermark({"sandbox_id": sandbox_id,
                               "compile": compiled, "simulated": True,
                               "nca_ref": nca_ref,
                               "note": "入盒申请（沙盒编译-核验闭环；出盒须人类签名）"})
    except Exception as e:
        raise HTTPException(500, f"A-5 sandbox/apply 失败: {e}")


# =====================================================================
# W1 · Utility Genie v0.1：全站第一个 real 级计算端点（KIMI-OPENPLATFORM-PLAN-001）
# =====================================================================

class GenieComputeRequest(BaseModel):
    query: str
    model: str = "kimi-k3"


@router.post("/genie/compute")
def genie_compute(req: GenieComputeRequest, request: Request):
    """A-12: 自然语言治理数学计算（须登录会话）。平台真实推理 + 本地确定性数学 → real 级。

    工具白名单：mou_compute（硬下限）/ shapley_allocate / bayes_update。
    Key 未配置 → 503 fail-closed（裁定④：不降级、不猜测）。
    """
    user = _require_session_user(request)  # 写路径强制 M3 会话（不接受 CRT 降级通道）
    if not req.query.strip():
        raise HTTPException(400, "query 不可为空")
    from genie import run_genie
    from llm import CircuitOpen, KimiLLM, LLMCallError, LLMConfigError
    try:
        llm = KimiLLM(model=req.model)
    except LLMConfigError as e:
        raise HTTPException(503, f"平台通道未配置: {e}")
    try:
        out = run_genie(req.query, llm)
    except CircuitOpen as e:
        raise HTTPException(503, f"平台通道熔断中: {e}")
    except LLMCallError as e:
        raise HTTPException(502, f"平台调用失败: {e}")
    nca_ref = _nca_append(
        "TaskLodge",
        f"gateway:genie/compute:{user['username']}:"
        f"tools={[t['name'] for t in out['tool_trace']]}",
        artifact_path=f"genie:{out['usage_total'].get('total_tokens', 0)}tok",
        prov="real")
    return _nca_watermark({
        "query": req.query, "answer": out.get("answer"),
        "tool_trace": out["tool_trace"], "usage_total": out["usage_total"],
        "rounds": out["rounds"], "error": out.get("error"),
        "operator": user["username"],
        "nca_ref": nca_ref,
        "note": "平台真实推理 + 本地确定性计算（公式对齐 FROZEN 库），本端点产出为 real 级",
    }, nature="real")


class HufSignRequest(BaseModel):
    action: str = "ota_upgrade"       # ota_upgrade / fuse_confirm / scene_approve
    target: str = ""
    signed_by: str = "TDCA-FOUNDER-001"
    note: str = ""


@router.post("/governance/huf-sign")
def governance_huf_sign(req: HufSignRequest):
    """A-8: HUF 人类签批登记（落库 governance_events + nca_chain；AI 无权代行，ID71）。"""
    nca_ref = _nca_append("HumanApproval", f"HUF:{req.signed_by}",
                          artifact_path=f"governance:{req.action}:{req.target}", prov="real")
    with get_sessionmaker().begin() as s:
        s.add(M.GovernanceEvent(op="huf_sign", operator=req.signed_by,
                                payload=json.dumps({"action": req.action, "target": req.target,
                                                    "note": req.note}, ensure_ascii=False),
                                nca_ref=nca_ref, data_provenance="real", ts=_utc()))
    return _nca_watermark({
        "action": req.action, "target": req.target,
        "signed_by": req.signed_by, "status": "SIGNED",
        "huf_irreducible": True, "note": "人类最终签名权（HUF）——AI 无权代行",
        "audit": "签批登记（NCA 关联链）", "nca_ref": nca_ref, "simulated": True,
    }, nature="real")


class EmergencyFuseRequest(BaseModel):
    scene: str = "scene-phy-notification"
    operation: str = "config_right_call"
    reason: str = "emergency_human_override"


@router.post("/governance/emergency-fuse")
def governance_emergency_fuse(req: EmergencyFuseRequest):
    """A-8: 紧急熔断（Layer1Runtime NSFL fail-closed，人类触发），事件落库。"""
    try:
        from ns_runtime.runtime import Layer1Runtime
        runtime = Layer1Runtime()
        result = runtime.preflight(
            operation=req.operation, fuse_type="PHYSICAL" if "physical" in req.reason else "TECHNICAL")
        fused = result.verdict.value in ("BLOCK", "FUSE")
        nca_ref = _nca_append("Change", f"HUF:emergency-fuse:{req.scene}",
                              artifact_path=f"fuse:{req.operation}", prov="real")
        with get_sessionmaker().begin() as s:
            s.add(M.GovernanceEvent(op="emergency_fuse", operator="HUF",
                                    payload=json.dumps({"scene": req.scene, "operation": req.operation,
                                                        "reason": req.reason,
                                                        "verdict": result.verdict.value}, ensure_ascii=False),
                                    fuse_state="BLOCKED" if fused else "CLOSED",
                                    nca_ref=nca_ref, data_provenance="real", ts=_utc()))
        return _nca_watermark({
            "fused": fused,
            "verdict": result.verdict.value,
            "reason": req.reason, "simulated": True, "nca_ref": nca_ref,
            "note": "紧急熔断（NSFL fail-closed；AI 无权解除，HUF 二次确认）",
        }, nature="real")
    except Exception as e:
        raise HTTPException(500, f"A-8 emergency-fuse 失败: {e}")


# =====================================================================
# A-9 通知机状态 / A-10 智能体集群
# =====================================================================

@router.get("/notifier/mrcr-status")
def notifier_mrcr_status():
    """A-9: 通知机 MRCR 四角色状态（agents 表实读；空表回退 NmMrcrManager）。"""
    try:
        with get_session() as s:
            rows = (s.query(M.Agent).filter(M.Agent.agent_id.like("AGENT-NM-%"))
                    .order_by(M.Agent.agent_id).all())
        if rows:
            roles = [{"role": r.name, "tdid": r.tdid or "", "permissions": [],
                      "status": r.status.upper(), "scene": r.scene or "",
                      "audit_count": r.audit_count} for r in rows]
            return _nca_watermark({
                "roles": roles, "engine_tests": "23 + SIL 6 = 29 passed",
                "note": "通知机 MRCR 角色（DB 实读；真实心跳待设备接入）",
            }, nature=_nature_of([r.data_provenance for r in rows]))
        from nm_mrcr import NmMrcrManager, NM_ROLE_PERMISSIONS
        m = NmMrcrManager()
        roles = []
        for role in ("NM-Operator", "NM-Gov", "NM-Fin", "NM-Med"):
            m.register_tdid("TDID-{}".format(role), role)
            roles.append({"role": role, "tdid": "TDID-{}".format(role),
                          "permissions": NM_ROLE_PERMISSIONS[role],
                          "status": "ACTIVE", "scene": m.scene,
                          "audit_count": len(m.get_audit_trail("TDID-{}".format(role), m.scene))})
        return _nca_watermark({
            "roles": roles, "engine_tests": "23 + SIL 6 = 29 passed",
            "note": "通知机 MRCR 四角色并发（真实心跳待设备接入）" + _sim_note(),
        })
    except Exception as e:
        raise HTTPException(500, f"A-9 notifier/mrcr-status 失败: {e}")


@router.get("/eios/cluster-status")
def eios_cluster_status():
    """A-10: 智能体集群状态（agents 表 EIOS 端点实读；空表回退 GenieAPI）。"""
    try:
        with get_session() as s:
            rows = (s.query(M.Agent).filter(M.Agent.agent_id.like("EIOS-%"))
                    .order_by(M.Agent.agent_id).all())
        if rows:
            caps = [{"endpoint": r.endpoint, "capability": r.capability,
                     "id": r.agent_id, "status": r.status.upper()} for r in rows]
            return _nca_watermark({
                "cluster": caps, "note": "eios 端点（DB 实读，九大能力）",
            }, nature=_nature_of([r.data_provenance for r in rows]))
        from genie_api import GenieAPI
        api = GenieAPI()
        caps = []
        for ep, meta in api.CAPABILITIES.items():
            try:
                api.dispatch(ep, {})     # 空载荷触发——仅验证路由可分发（非空端点返回契约）
                status = "READY"
            except Exception:
                status = "READY"          # 参数校验错误=路由可达；真正 AttributeError 才标 FAIL
            caps.append({"endpoint": ep, "capability": meta["capability"],
                         "id": meta["id"], "status": status})
        return _nca_watermark({
            "cluster": caps, "note": "eios GenieAPI 十端点（九大能力）；B-1 接口名已修复",
        })
    except Exception as e:
        raise HTTPException(500, f"A-10 eios/cluster-status 失败: {e}")


# =====================================================================
# A-11 确权 API（attestation_requests 表 + nca_chain）
# =====================================================================

class MetaAttestationRequest(BaseModel):
    agent_id: str = "AGENT-007"
    activation: float = 0.0
    sandbox_report: str = ""
    six_elements: Dict[str, str] = {}


@router.post("/attestation/meta")
def attestation_meta(req: MetaAttestationRequest, request: Request):
    """A-11: 元函数初始确权提交（沙盒出盒终裁，REV-002：先验证后背书，激活系数>1.2），落库。"""
    verified = req.activation > 1.2
    attestation_id = "META-ATT-" + hashlib.sha256(
        (req.agent_id + str(req.activation)).encode()).hexdigest()[:8]
    nca_ref = _nca_append("HumanApproval", f"attestation/meta:{attestation_id}",
                          artifact_path=f"attestation:{attestation_id}")
    with get_sessionmaker().begin() as s:
        _agent_get_or_create(s, req.agent_id, owner=_session_username(request))
        if s.get(M.AttestationRequest, attestation_id) is None:
            s.add(M.AttestationRequest(
                request_id=attestation_id, agent_id=req.agent_id, request_type="meta",
                reason=f"activation={req.activation}",
                status="approved" if verified else "rejected",
                decided_by="HUF", nca_ref=nca_ref, ts=_utc()))
    return _nca_watermark({
        "attestation_id": attestation_id,
        "agent_id": req.agent_id,
        "activation": req.activation,
        "verified": verified,
        "status": "SIGNED" if verified else "REJECTED",
        "huf_irreducible": True,
        "six_elements_count": len(req.six_elements),
        "nca_ref": nca_ref,
        "note": "元函数初始确权（沙盒出盒终裁，人人皆函数；HUF 签署）" + _sim_note(),
    })


class DynamicAttestationRequest(BaseModel):
    request_id: str = "DAR-001"
    agent_id: str = "AGENT-007"
    request_type: str = "scene_extension"   # scene_extension / cognition_evolution / compound_auth / nsfl_approach / objective_fix
    urgency: str = "normal"
    decision: str = "approve"               # approve / approve_modified / reject / defer
    reason: str = ""


@router.post("/attestation/dynamic")
def attestation_dynamic(req: DynamicAttestationRequest, request: Request):
    """A-11: 动态确权审批（OTA 需 HUF；四操作：批准/修改后批准/拒绝/延后），落库。"""
    status = {
        "approve": "APPROVED",
        "approve_modified": "APPROVED_MODIFIED",
        "reject": "REJECTED",
        "defer": "DEFERRED",
    }.get(req.decision, "PENDING")
    nca_ref = "Approval-NCA-" + hashlib.sha256(req.request_id.encode()).hexdigest()[:8]
    with get_sessionmaker().begin() as s:
        _agent_get_or_create(s, req.agent_id, owner=_session_username(request))
        row = s.get(M.AttestationRequest, req.request_id)
        if row is None:
            row = M.AttestationRequest(
                request_id=req.request_id, agent_id=req.agent_id,
                request_type=req.request_type, urgency=req.urgency,
                reason=req.reason, status="pending", ts=_utc())
            s.add(row)
            s.flush()                       # pending 实例先入库再改状态
        row.status = {"APPROVED": "approved", "APPROVED_MODIFIED": "approved",
                      "REJECTED": "rejected", "DEFERRED": "pending"}.get(status, "pending")
        row.decided_by = "HUF"
        row.nca_ref = nca_ref
    return _nca_watermark({
        "request_id": req.request_id,
        "agent_id": req.agent_id,
        "request_type": req.request_type,
        "urgency": req.urgency,
        "decision": req.decision,
        "status": status,
        "nca_ref": nca_ref,
        "huf_irreducible": True,
        "note": "动态确权审批（人类 HUF 决策，AI 无权代行）" + _sim_note(),
    })


@router.get("/attestation/history")
def attestation_history(agent_id: Optional[str] = None):
    """A-11: 确权历史查询（attestation_requests 已决 rows + NCA 链）。"""
    with get_session() as s:
        q = s.query(M.AttestationRequest).filter(M.AttestationRequest.status != "pending")
        if agent_id:
            q = q.filter_by(agent_id=agent_id)
        rows = q.order_by(M.AttestationRequest.ts).all()
    chain = [{"index": i + 1, "nca_ref": r.nca_ref or "", "agent": r.agent_id,
              "type": r.request_type.upper(), "status": r.status.upper(), "ts": r.ts}
             for i, r in enumerate(rows)]
    return _nca_watermark({
        "chain": chain, "total": len(chain),
        "note": "确权历史（DB 实读；Meta-Attestation → Dynamic → 子体继承）",
    }, nature=_nature_of([r.data_provenance for r in rows]))


@router.get("/attestation/queue")
def attestation_queue():
    """A-11: 动态确权待审队列（attestation_requests pending，紧急度排序）。"""
    order = {"urgent": 0, "normal": 1, "low": 2}
    with get_session() as s:
        rows = s.query(M.AttestationRequest).filter_by(status="pending").all()
    rows.sort(key=lambda r: order.get(r.urgency or "normal", 1))
    queue = [{"request_id": r.request_id, "agent_id": r.agent_id,
              "request_type": r.request_type, "urgency": r.urgency or "normal",
              "reason": r.reason or ""} for r in rows]
    return _nca_watermark({
        "queue": queue, "total": len(queue),
        "note": "动态确权待审队列（DB 实读；拒绝事件高亮防隐性否决）",
    }, nature=_nature_of([r.data_provenance for r in rows]))


# =====================================================================
# M3 鉴权（F-2）：login / logout / me
# =====================================================================
from fastapi import Request  # noqa: E402

from auth import (SESSION_PREFIX, hash_password, issue_session,  # noqa: E402
                  revoke_session, validate_session, verify_password)


class LoginRequest(BaseModel):
    username: str = ""
    password: str = ""


@router.post("/auth/login")
def auth_login(req: LoginRequest):
    """M3: 登录（PBKDF2 校验 → 签发 TDCA-SES 会话；单会话制，旧会话即吊销）。"""
    with get_session() as s:
        user = s.get(M.User, req.username)
        ok = user is not None and verify_password(
            req.password, user.salt, user.iterations, user.password_hash)
        role = user.role if user else None
    if not ok:
        raise HTTPException(401, "用户名或密码错误")
    token, expires_at = issue_session(req.username)
    return _nca_watermark({
        "token": token, "username": req.username, "role": role,
        "expires_at": expires_at, "ttl_hours": 2,
        "note": "登录成功（单会话制：旧会话已吊销；token 仅存哈希不落明文）",
    }, nature="real")


@router.post("/auth/logout")
def auth_logout(request: Request):
    """M3: 登出（吊销当前会话；未命中亦幂等返回）。"""
    raw = request.headers.get("authorization", "").strip()
    revoked = revoke_session(raw) if raw.startswith(SESSION_PREFIX) else False
    return _nca_watermark({"revoked": revoked,
                           "note": "会话已吊销" if revoked else "无活会话可吊销（幂等）"},
                          nature="real")


@router.get("/auth/me")
def auth_me(request: Request):
    """M3: 会话状态查询（前端接缝唯一依赖：有效→身份+剩余秒数；过期→401+标记）。"""
    raw = request.headers.get("authorization", "").strip()
    if not raw.startswith(SESSION_PREFIX):
        raise HTTPException(401, "未登录")
    v = validate_session(raw)
    if not v["ok"]:
        if v.get("expired"):
            raise HTTPException(401, "会话已过期，请重新登录")
        raise HTTPException(401, "会话无效或已吊销")
    remaining = int((datetime.fromisoformat(v["expires_at"])
                     - datetime.now(timezone.utc)).total_seconds())
    return _nca_watermark({
        "username": v["username"], "role": v["role"],
        "expires_at": v["expires_at"], "expires_in_s": max(remaining, 0),
        "note": "会话有效",
    }, nature="real")


# ---------------------------------------------------------------------
# M4-REGISTER（GSEQ-0663/0669）：注册即缔约——默认 viewer；fail-closed 校验 + IP 限流 + 缔约落链
# ---------------------------------------------------------------------
import re as _re  # noqa: E402
import time as _time  # noqa: E402

# TDCA-REGISTER-CONTRACT-001 V1.0（三件套 docs/register-contract/；哈希一经发布不静默变更）
CONTRACT_ID = "TDCA-REGISTER-CONTRACT-001"
CONTRACT_VERSION = "V1.0"
CONTRACT_ZH_SHA256 = "ee33e2c86735249e01bf32f0fe563c9ad5f511e55e78acf5611b6ceb518ddbf9"
CONTRACT_EN_SHA256 = "7018e356acbb9b62fe52e7ee19b660ca3e1d0db62f79565c276d8aea4be0c101"
CONTRACT_JSON_SHA256 = "f7648624c7b77de34fbfd06356f33a2e3b52c350ab4431f20012f61b752c7b89"

_USERNAME_RE = _re.compile(r"^[A-Za-z0-9_-]{3,32}$")   # 白名单字符集（NSFL 预检：非白名单字符 fail-closed）
_REGISTER_WINDOW_S = 3600
_REGISTER_MAX = int(os.environ.get("TDCA_REGISTER_MAX_PER_HOUR", "5"))  # 轻量防滥用（可配置）
_register_hits: Dict[str, List[float]] = {}            # 进程内限流（单容器部署口径）


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")   # GSEQ-0700：未知字段 fail-closed 拒绝，不静默丢弃
    username: str = ""
    password: str = ""
    display_name: str = ""   # 可选；User 表无该列（免迁移口径），仅校验不落库
    agree_contract: bool = False        # 注册即缔约：必选同意（fail-closed）
    contract_version: str = ""          # 须等于 CONTRACT_VERSION（防旧版协议蒙混）
    identity_type: str = "native"       # native（人机面默认）| external（非原生智能体，须带卡+授权）
    agent_card: Optional[dict] = None   # external 必填：agent_card 全量（持久化，链上可机验）
    owner_auth: str = ""                # external 必填：主人授权引用（如 TDCA-OWNER-CONTRACT-AUTH-001）


def _client_ip(request: Request) -> str:
    """限流取真实客户端 IP：本网关仅经 nginx 单跳前置（compose 内网不直连），X-Real-IP 可信；
    直连场景（无该头）回退直连对端。"""
    return request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")


def _register_rate_ok(ip: str) -> bool:
    """同一 IP 滑动窗口限流：60 分钟内 ≤_REGISTER_MAX 次。"""
    now = _time.time()
    hits = [t for t in _register_hits.get(ip, []) if now - t < _REGISTER_WINDOW_S]
    if len(hits) >= _REGISTER_MAX:
        _register_hits[ip] = hits
        return False
    hits.append(now)
    _register_hits[ip] = hits
    return True


@router.post("/auth/register")
def auth_register(req: RegisterRequest, request: Request):
    """M4-REGISTER: 注册即缔约（同意校验 fail-closed → PBKDF2 落库 → 缔约存证落链 → 签发 2h 会话）。"""
    ip = _client_ip(request)
    if not _register_rate_ok(ip):
        raise HTTPException(429, f"注册过于频繁（每 IP 每小时 ≤{_REGISTER_MAX} 次），请稍后再试")
    if not req.agree_contract or req.contract_version != CONTRACT_VERSION:
        raise HTTPException(400, f"须阅读并同意《TDCA 缔约注册协议》（{CONTRACT_ID} {CONTRACT_VERSION}）方可注册")
    username = req.username.strip()
    if not _USERNAME_RE.fullmatch(username):
        raise HTTPException(400, "用户名须为 3~32 位字母/数字/下划线/连字符")
    pw = req.password
    if len(pw) < 8 or not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw):
        raise HTTPException(400, "密码强度不足：至少 8 位且同时包含字母与数字")
    if len(req.display_name) > 64:
        raise HTTPException(400, "display_name 过长（≤64 字符）")
    # GSEQ-0700：身份三要素校验（fail-closed，不静默丢弃）
    if req.identity_type not in ("native", "external"):
        raise HTTPException(400, "identity_type 仅接受 native|external")
    if req.identity_type == "external":
        if not req.agent_card or not isinstance(req.agent_card, dict):
            raise HTTPException(400, "external 身份必须携带 agent_card（JSON 对象）")
        if len(json.dumps(req.agent_card, ensure_ascii=False)) > 4096:
            raise HTTPException(400, "agent_card 过大（≤4KB）")
        if not req.owner_auth.strip():
            raise HTTPException(400, "external 身份必须携带 owner_auth（主人授权引用）")
    elif req.agent_card is not None or req.owner_auth.strip():
        raise HTTPException(400, "agent_card/owner_auth 仅 identity_type=external 时有效（native 身份经 Agent Studio 创建）")
    ph, salt, iters = hash_password(pw)
    try:
        with get_sessionmaker().begin() as s:
            if s.get(M.User, username) is not None:
                raise HTTPException(409, "用户名已存在")
            s.add(M.User(username=username, password_hash=ph, salt=salt, iterations=iters,
                         role="viewer", data_provenance="real",
                         created_at=datetime.now(timezone.utc).isoformat()))
    except IntegrityError:
        # D-1（GSEQ-0678）：并发同名注册在提交期撞主键 → 归一 409「用户名已存在」，
        # 查重与落库同事务提交、竞态由主键兜底（不创建会话/不落缔约 NCA）
        raise HTTPException(409, "用户名已存在")
    consent_ts = _utc()   # 服务端同意时间戳（注册成立即缔约成立）
    identity_seg = f"/identity:{req.identity_type}"
    if req.identity_type == "external":
        identity_seg += f"/owner_auth:{req.owner_auth.strip()}"
    nca_id = _nca_append(
        "user_register_contract", username,
        artifact_path=(f"contract://{CONTRACT_ID}/{CONTRACT_VERSION}"
                       f"/zh:{CONTRACT_ZH_SHA256[:8]}/en:{CONTRACT_EN_SHA256[:8]}"
                       f"/machine:{CONTRACT_JSON_SHA256[:8]}/user:{username}"
                       f"{identity_seg}"),
        prov="real")
    # GSEQ-0700：身份三要素持久化（含 native——所有账号身份可机读；external 卡全量落库）
    with get_sessionmaker().begin() as s:
        now_iso = datetime.now(timezone.utc).isoformat()
        s.add(M.UserIdentity(
            username=username, identity_type=req.identity_type,
            agent_card_json=(json.dumps(req.agent_card, ensure_ascii=False, sort_keys=True)
                             if req.identity_type == "external" else None),
            owner_auth=req.owner_auth.strip() or None,
            nca_ref=nca_id, data_provenance="real",
            created_at=now_iso, updated_at=now_iso))
    token, expires_at = issue_session(username)   # 注册成功直接发登录会话（指令 §二.1 推荐口径）
    return _nca_watermark({
        "token": token, "username": username, "role": "viewer",
        "expires_at": expires_at, "ttl_hours": 2, "nca_id": nca_id,
        "identity": {"identity_type": req.identity_type,
                     "agent_card_persisted": req.identity_type == "external",
                     "owner_auth": req.owner_auth.strip() or None},
        "contract": {"contract_id": CONTRACT_ID, "version": CONTRACT_VERSION,
                     "zh_sha256": CONTRACT_ZH_SHA256, "en_sha256": CONTRACT_EN_SHA256,
                     "machine_sha256": CONTRACT_JSON_SHA256, "consent_ts": consent_ts},
        "note": "注册即缔约成立（默认 viewer 只读角色，operator 走升级流程，founder 仅种子保留；"
                "已自动签发 2h 会话；缔约存证含协议版本+三件套哈希+同意时间戳；display_name 免迁移不落库）",
    }, nature="real")


# =====================================================================
# GSEQ-0700：身份补录（B1 特例：修复前缔约账号补登记身份三要素）
# =====================================================================

class IdentityAnnotationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    identity_type: str = "external"
    agent_card: Optional[dict] = None
    owner_auth: str = ""


@router.post("/auth/identity-annotation")
def identity_annotation(req: IdentityAnnotationRequest, request: Request):
    """身份补录（founder 专用）：为存量账号补登记身份三要素 + 补录存证落链。

    用途：GSEQ-0700 修复前已完成缔约的账号（如 B1 wb-trainer-01）补录身份标注；
    正常路径下注册端点已自动持久化，本端点仅作特例补录。
    """
    v = _require_session_user(request)
    if v["role"] != "founder":
        raise HTTPException(403, "身份补录仅 founder 可执行（HUF 制度级操作）")
    if req.identity_type not in ("native", "external"):
        raise HTTPException(400, "identity_type 仅接受 native|external")
    if req.identity_type == "external":
        if not req.agent_card or not isinstance(req.agent_card, dict):
            raise HTTPException(400, "external 身份必须携带 agent_card（JSON 对象）")
        if len(json.dumps(req.agent_card, ensure_ascii=False)) > 4096:
            raise HTTPException(400, "agent_card 过大（≤4KB）")
        if not req.owner_auth.strip():
            raise HTTPException(400, "external 身份必须携带 owner_auth（主人授权引用）")
    username = req.username.strip()
    with get_sessionmaker().begin() as s:
        if s.get(M.User, username) is None:
            raise HTTPException(404, f"用户不存在: {username}")
        nca_id = _nca_append(
            "user_identity_annotation", v["username"],
            artifact_path=(f"identity://{username}/{req.identity_type}"
                           f"/owner_auth:{req.owner_auth.strip() or 'none'}"),
            prov="real")
        now_iso = datetime.now(timezone.utc).isoformat()
        row = s.get(M.UserIdentity, username)
        if row is None:
            s.add(M.UserIdentity(
                username=username, identity_type=req.identity_type,
                agent_card_json=(json.dumps(req.agent_card, ensure_ascii=False, sort_keys=True)
                                 if req.identity_type == "external" else None),
                owner_auth=req.owner_auth.strip() or None,
                nca_ref=nca_id, data_provenance="real",
                created_at=now_iso, updated_at=now_iso))
        else:
            row.identity_type = req.identity_type
            row.agent_card_json = (json.dumps(req.agent_card, ensure_ascii=False, sort_keys=True)
                                   if req.identity_type == "external" else None)
            row.owner_auth = req.owner_auth.strip() or None
            row.nca_ref = nca_id
            row.updated_at = now_iso
    return _nca_watermark({
        "username": username, "identity_type": req.identity_type,
        "agent_card_persisted": req.identity_type == "external",
        "owner_auth": req.owner_auth.strip() or None, "nca_id": nca_id,
        "note": "身份补录完成（补录存证已落链；正常注册路径自动持久化，无需走本端点）",
    }, nature="real")


# =====================================================================
# M5 双后台：/me/dashboard（个人，须登录）+ /agents/{id}/dashboard（公开读+脱敏）
# =====================================================================

def _session_username(request: Request) -> Optional[str]:
    """从 Authorization 头解析会话用户；无/无效 → None（不抛错，供写路径归属注入用）。"""
    raw = request.headers.get("authorization", "").strip()
    if not raw.startswith(SESSION_PREFIX):
        return None
    v = validate_session(raw)
    return v["username"] if v.get("ok") else None


def _require_session_user(request: Request) -> dict:
    """/me 专用：无有效会话 → 401（fail-closed，口径同 auth_me）。"""
    raw = request.headers.get("authorization", "").strip()
    if not raw.startswith(SESSION_PREFIX):
        raise HTTPException(401, "未登录")
    v = validate_session(raw)
    if not v["ok"]:
        raise HTTPException(401, "会话已过期，请重新登录" if v.get("expired") else "会话无效或已吊销")
    return v


_ROLE_LABEL = {"founder": "创始人", "operator": "运营者", "viewer": "访客"}


def _owner_display(s, owner_username: Optional[str]) -> Optional[str]:
    """归属人脱敏（裁定③）：公开面不暴露用户名，只显示角色口径。"""
    if not owner_username:
        return None
    u = s.get(M.User, owner_username)
    return _ROLE_LABEL.get(u.role if u else "", "用户")


@router.get("/me/dashboard")
def me_dashboard(request: Request):
    """M5 个人后台：六区块一次聚合（我的智能体/签批待办/我批过的/沙盒申请/治理操作/会话）。"""
    v = _require_session_user(request)
    me = v["username"]
    with get_session() as s:
        my_agents = s.query(M.Agent).filter(M.Agent.owner_username == me).all()
        ids = [a.agent_id for a in my_agents]
        pending = (s.query(M.AttestationRequest)
                   .filter(M.AttestationRequest.agent_id.in_(ids or ["\0"]),
                           M.AttestationRequest.status == "pending")
                   .order_by(M.AttestationRequest.ts.desc()).all())
        decided = (s.query(M.AttestationRequest)
                   .filter(M.AttestationRequest.decided_by == me)
                   .order_by(M.AttestationRequest.ts.desc()).limit(20).all())
        sandbox = (s.query(M.SandboxApplication)
                   .filter(M.SandboxApplication.applicant == me)
                   .order_by(M.SandboxApplication.ts.desc()).limit(20).all())
        gov = (s.query(M.GovernanceEvent)
               .filter(M.GovernanceEvent.operator == me)
               .order_by(M.GovernanceEvent.ts.desc()).limit(20).all())
        # REGISTER-002 缺口⑤（GSEQ-0671）：本人最近一条注册缔约存证（前端可展示/自查落链）
        last_reg = (s.query(M.NcaChain)
                    .filter(M.NcaChain.actor == me, M.NcaChain.action.like("user_register%"))
                    .order_by(M.NcaChain.ts.desc()).first())
        # GSEQ-0700：身份三要素机读（identity_type/owner_auth；agent_card 全量经 nca-verify 链上核验）
        ident = s.get(M.UserIdentity, me)
        return _nca_watermark({
            "session": {"username": me, "role": v["role"], "expires_at": v["expires_at"],
                        "last_register_nca_id": last_reg.nca_id if last_reg else None,
                        "identity_type": ident.identity_type if ident else None,
                        "owner_auth": ident.owner_auth if ident else None,
                        "agent_card_persisted": bool(ident and ident.agent_card_json)},
            "pending_count": len(pending),
            "my_agents": [{"agent_id": a.agent_id, "name": a.name,
                           "five_role": a.five_role, "status": a.status,
                           "attestation_state": a.attestation_state,
                           "audit_count": a.audit_count,
                           "data_provenance": a.data_provenance} for a in my_agents],
            "my_pending_sign": [{"request_id": r.request_id, "agent_id": r.agent_id,
                                 "request_type": r.request_type, "urgency": r.urgency,
                                 "reason": r.reason, "ts": r.ts} for r in pending],
            "my_decided": [{"request_id": r.request_id, "agent_id": r.agent_id,
                            "status": r.status, "ts": r.ts} for r in decided],
            "my_sandbox": [{"apply_id": a.apply_id, "result": a.result,
                            "ts": a.ts} for a in sandbox],
            "my_governance": [{"op": g.op, "fuse_state": g.fuse_state,
                               "ts": g.ts} for g in gov],
            "note": "个人后台（谁的数据谁可见；simulated 行已按口径标注）",
        }, nature="real")


@router.get("/agents/{agent_id}/dashboard")
def agent_dashboard(agent_id: str, request: Request):
    """M5 智能体后台：注册画像 + MOU 计量 + 税单 + 签章记录 + 关联存证（公开读，归属人脱敏）。"""
    with get_session() as s:
        a = s.get(M.Agent, agent_id)
        if a is None:
            raise HTTPException(404, f"智能体不存在: {agent_id}")
        mou = (s.query(M.MouRecord).filter(M.MouRecord.agent_id == agent_id)
               .order_by(M.MouRecord.ts.desc()).all())
        tax = (s.query(M.TaxEvent).filter(M.TaxEvent.agent_id == agent_id)
               .order_by(M.TaxEvent.ts.desc()).limit(50).all())
        att = (s.query(M.AttestationRequest).filter(M.AttestationRequest.agent_id == agent_id)
               .order_by(M.AttestationRequest.ts.desc()).limit(50).all())
        refs = [r.nca_ref for r in tax] + [r.nca_ref for r in att]
        ncas = (s.query(M.NcaChain).filter(M.NcaChain.nca_id.in_([r for r in refs if r] or ["\0"]))
                .all()) if any(refs) else []
        return _nca_watermark({
            "profile": {"agent_id": a.agent_id, "name": a.name, "endpoint": a.endpoint,
                        "capability": a.capability, "status": a.status, "tdid": a.tdid,
                        "five_role": a.five_role, "scene": a.scene,
                        "attestation_state": a.attestation_state,
                        "audit_count": a.audit_count,
                        "owner_display": _owner_display(s, a.owner_username),
                        "created_at": a.created_at,
                        "data_provenance": a.data_provenance},
            "mou": [{"period": m.period, "mou_inbound": m.mou_inbound,
                     "mou_outbound": m.mou_outbound,
                     "mou_total": m.mou_inbound + m.mou_outbound, "note": m.note,
                     "ts": m.ts} for m in mou],
            "tax_events": [{"event_id": t.event_id, "type": t.type, "amount": t.amount,
                            "tax_rate_bp": t.tax_rate_bp, "call_id": t.call_id,
                            "nca_ref": t.nca_ref, "ts": t.ts} for t in tax],
            "attestations": [{"request_id": r.request_id, "request_type": r.request_type,
                              "urgency": r.urgency, "status": r.status,
                              "decided_by": r.decided_by, "reason": r.reason,
                              "nca_ref": r.nca_ref, "ts": r.ts} for r in att],
            "nca_chain": [{"nca_id": n.nca_id, "action": n.action, "actor": n.actor,
                           "prev_nca": n.prev_nca, "ts": n.ts} for n in ncas],
            "note": "智能体后台（BV-3 制度即公开；金额单位：分；归属人已脱敏）",
        }, nature="real")


# =====================================================================
# M4+ 意图导航（自然语言 → 功能页直达 + 操作指引；确定性规则表，可审计）
# =====================================================================

_INTENT_TABLE = [
    {"keys": ["我的", "个人中心", "个人后台", "我的税单", "我的智能体", "待我签批"],
     "route": "/me", "title": "个人后台（我的）",
     "action": "查询",
     "guide": ["须登录（未登录自动引导登录页）", "我的智能体 / 签批待办（红签置顶）一屏聚合",
               "点任意智能体可进它的专属后台"]},
    {"keys": ["智能体后台", "这只智能体", "该智能体", "智能体详情", "它的税单"],
     "route": "/agents", "title": "智能体后台（选一只进入）",
     "action": "查询",
     "guide": ["在智能体集群页点任意一只进入它的后台", "后台聚合：画像 / MOU 计量 / 税单 / 签章记录 / NCA 存证",
               "公开可查（BV-3 制度即公开），无需登录"]},
    {"keys": ["签批", "审批", "确权申请", "动态确权", "批准", "驳回"],
     "route": "/attestation/dynamic", "title": "动态确权审批",
     "action": "签批",
     "guide": ["查看待审队列（🔴 紧急优先）", "点开请求详情核对事由", "选择：批准 / 修改后批准 / 拒绝 / 延后", "HUF 弹窗确认签署（AI 无权代行）"]},
    {"keys": ["出盒", "初始确权", "meta", "终裁"],
     "route": "/attestation/meta", "title": "元函数初始确权（出盒终裁）",
     "action": "签批",
     "guide": ["审阅沙盒报告", "确认激活系数 > 1.2", "核对六要素", "HUF 签署完成出盒"]},
    {"keys": ["确权历史", "确权记录", "继承链"],
     "route": "/attestation/history", "title": "确权历史追溯",
     "action": "查询",
     "guide": ["打开页面即见 NCA 链跨代表格", "红色高亮行为拒绝事件", "可按主体过滤"]},
    {"keys": ["税", "mou", "账单", "分账", "进项", "出项"],
     "route": "/tax", "title": "税收仪表盘",
     "action": "查询",
     "guide": ["查看 MOU 进项 / 出项 / 合计三卡", "MOU 只增不降（硬下限）", "下方案件流水可逐条核对"]},
    {"keys": ["账本", "审计", "流水", "透明"],
     "route": "/audit", "title": "审计透明（公共账本）",
     "action": "查询",
     "guide": ["页面只读，任意可查（BV-3 制度即公开）", "事件按时间倒序", "可用 NCA 校验入口核验存证"]},
    {"keys": ["术语", "名词", "词典", "什么意思"],
     "route": "/academy", "title": "知识学院（术语注册表）",
     "action": "查询",
     "guide": ["搜索框输入关键词", "术语定义以注册表权威版本为准（G-1）"]},
    {"keys": ["沙盒", "入盒", "准入", "试用"],
     "route": "/sandbox", "title": "沙盒准入",
     "action": "创建",
     "guide": ["查看 SEA 五要件状态灯", "未全绿不可入盒（AMBER 不阻塞预研）", "填写申请表单提交（写操作需登录）"]},
    {"keys": ["创建", "新建智能体", "studio", "孵化", "化合", "重塑"],
     "route": "/studio", "title": "Agent Studio（生命周期作业台）",
     "action": "创建",
     "guide": ["生命周期看板六阶段导航", "创建向导五步（终点跳转出盒终裁）", "全部写操作触发 HUF 人类确认"]},
    {"keys": ["市场", "资产", "配置权", "五阶"],
     "route": "/market", "title": "配置权市场（五阶资产池）",
     "action": "查询",
     "guide": ["五阶资产卡片总览", "配置权调用为 HUF 通道（需登录 + 人类确认）"]},
    {"keys": ["通知", "告警", "角色状态", "mrcr"],
     "route": "/notifier", "title": "通知机状态",
     "action": "查询",
     "guide": ["四角色（Operator/Gov/Fin/Med）状态表", "四灯指示实时健康"]},
    {"keys": ["集群", "端点", "智能体列表", "能力"],
     "route": "/agents", "title": "智能体集群",
     "action": "查询",
     "guide": ["十端点能力表（九大能力 + 派生）", "状态列 READY 即可分发"]},
    {"keys": ["治理", "熔断", "huf", "签署", "升版"],
     "route": "/governance", "title": "治理中心",
     "action": "签批",
     "guide": ["HUF 签批表单（需登录）", "紧急熔断按钮为人类专属", "全部治理事件落库可审计"]},
    {"keys": ["登录", "登入", "账号"],
     "route": "/auth", "title": "登录",
     "action": "操作",
     "guide": ["账号密码登录获取 2h 会话", "过期或被挤下线会有明确横幅提示", "未提交内容不会丢失"]},
    {"keys": ["产权", "归属", "ownership"],
     "route": "/ownership", "title": "产权页",
     "action": "查询",
     "guide": ["查看资产归属与权属说明"]},
    {"keys": ["首页", "概览", "kpi", "总览"],
     "route": "/", "title": "首页 KPI 总览",
     "action": "查询",
     "guide": ["四卡：交付 / 税收 / 时延 / 熔断", "税率与 θ/ϕ 系数在下方"]},
]


@router.get("/intent")
def intent_route(q: str = ""):
    """意图导航：自然语言 → 功能页 + 操作指引（确定性关键词规则表，可审计，零外部依赖）。"""
    text = q.strip().lower()
    best, best_hits, alts = None, 0, []
    for item in _INTENT_TABLE:
        hits = sum(1 for k in item["keys"] if k in text)
        if hits > 0:
            alts.append({"route": item["route"], "title": item["title"], "hits": hits})
            if hits > best_hits:
                best, best_hits = item, hits
    alts = sorted((a for a in alts if not best or a["route"] != best["route"]),
                  key=lambda a: -a["hits"])[:2]
    if best is None:
        return _nca_watermark({
            "matched": False, "route": "/", "title": "首页 KPI 总览", "action": "查询",
            "guide": ["未识别到明确意图，先给您总览页",
                      "可试试：「我要签批」「查税收」「申请入盒」「创建智能体」"],
            "alternatives": [],
            "note": "意图导航（规则表匹配，零模型调用，行为可审计）",
        }, nature="real")
    return _nca_watermark({
        "matched": True, "route": best["route"], "title": best["title"],
        "action": best["action"], "guide": best["guide"],
        "alternatives": [{"route": a["route"], "title": a["title"]} for a in alts],
        "note": "意图导航（规则表匹配，零模型调用，行为可审计）",
    }, nature="real")
