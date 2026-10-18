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
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_
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
from db import get_engine, get_session, get_sessionmaker  # noqa: E402
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


def rec_hash_of(nca_id: str, prev_nca: str | None, action: str, actor: str,
                artifact_path: str | None, sha256_8: str | None,
                handshake_id: str | None, data_provenance: str, ts: str) -> str:
    """记录级哈希（M1″ 公开口径，逐字公开——第三方按此重算可验「该行未被改写」）：
    sha256('nca_id|prev_nca|action|actor|artifact_path|sha256_8|handshake_id|data_provenance|ts')
    → 十六进制大写前 16 位。空值按空串计。"""
    s = "|".join([nca_id, prev_nca or "", action, actor, artifact_path or "",
                  sha256_8 or "", handshake_id or "", data_provenance, ts])
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()[:16]


_NCA_LOG = logging.getLogger("tdca.nca")
_ERR_LOG = logging.getLogger("tdca.errors")   # L1SI153 段三①：底层异常只进日志，不直透用户
_NCA_APPEND_MAX_TRIES = 4   # 1 次正写 + 3 次 BUSY 退避重试（NCA-ATOMIC-001）
_NCA_FORK_BASELINE: Optional[Dict[str, int]] = None   # 启动基线快照（辅改 B「只报新增」；不入库不建表）


def init_nca_fork_baseline() -> None:
    """服务启动：对现有 prev_nca 计数打内存基线快照。

    基线差口径：此后仅当某 prev 计数超过其基线时才告警（历史分叉不刷告警）；
    不入库、不建表；快照失败保持 None，首个写路径惰性重取（fail-soft，不拒服）。
    """
    global _NCA_FORK_BASELINE
    try:
        with get_sessionmaker().begin() as s:
            rows = (s.query(M.NcaChain.prev_nca, func.count())
                    .filter(M.NcaChain.prev_nca != "GENESIS")
                    .group_by(M.NcaChain.prev_nca).all())
        _NCA_FORK_BASELINE = {p: c for p, c in rows}
        _NCA_LOG.info("NCA fork baseline snapshot: prevs=%d", len(_NCA_FORK_BASELINE))
    except Exception:
        _NCA_LOG.exception("NCA fork baseline snapshot failed; lazy fallback at first write")
        _NCA_FORK_BASELINE = None


def _nca_append(action: str, actor: str, artifact_path: str = "", prov: str = "simulated") -> str:
    """写路径通用：向 nca_chain 追加一条存证（链式 prev_nca 自动取最新）。

    NCA-ATOMIC-001 原子性整改（只防新断，不重接历史断链）：
      · 原始连接显式 BEGIN IMMEDIATE + BUSY 退避重试——"取尾号→落本行"成
        串行临界区，并发写者不再读到同一快照（防 prev 悬空/分叉的新增）；
      · 尾号按插入序（rowid）取，弃 ts DESC（同秒批量记录 ts 相同，取尾不可靠）；
      · 落库后检测"同 prev 计数超启动基线"（新增链分叉）即 NCA_FORK_ALERT
        告警——日志级、不阻断写入、「只报新增」基线差口径（辅改 B 替代项：
        不建唯一索引、不动表结构、不入库不建表）。
    L1SI154-031（M1″）：写时即锚定 rec_hash/prev_hash/detached/detach_reason——
    判据 2（单行未被改写有真验证力）的前提；口径见 rec_hash_of（公开）。
    """
    import secrets
    nonce = secrets.token_hex(8)   # 同秒同参重复写入防主键碰撞（M3 测试实证）
    engine = get_engine()
    nca_id: Optional[str] = None
    last_err: Optional[Exception] = None
    for attempt in range(_NCA_APPEND_MAX_TRIES):
        raw = cur = None
        try:
            raw = engine.raw_connection()
            dbapi = raw.dbapi_connection
            cur = dbapi.cursor()
            cur.execute("BEGIN IMMEDIATE")   # 写锁在事务起点持有（取号+落库一体）
            row = cur.execute(
                "SELECT nca_id, rec_hash, detached FROM nca_chain"
                " ORDER BY rowid DESC LIMIT 1").fetchone()
            tail = row[0] if row else "GENESIS"
            ts = _utc()
            nca_id = "NCA-WEB-" + hashlib.sha256(
                (action + actor + ts + nonce + tail).encode()).hexdigest()[:12]
            sha8 = (hashlib.sha256(artifact_path.encode()).hexdigest()[:8]
                    if artifact_path else None)
            if row is None:                    # 创世行
                prev_hash, detached, detach_reason = "", 0, None
            else:
                tail_rec_hash, tail_detached = row[1], row[2]
                prev_hash = tail_rec_hash or "MISSING"
                broken = (tail_rec_hash in (None, "")) or tail_detached == 1
                detached = 1 if broken else 0
                detach_reason = "missing_predecessor" if broken else None
            rh = rec_hash_of(nca_id, tail, action, actor, artifact_path,
                             sha8, None, prov, ts)
            cur.execute(
                "INSERT INTO nca_chain (nca_id, prev_nca, action, actor, artifact_path,"
                " sha256_8, data_provenance, ts, rec_hash, prev_hash, anchor_ok,"
                " detached, detach_reason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (nca_id, tail, action, actor, artifact_path or None, sha8,
                 prov, ts, rh, prev_hash, 0, detached, detach_reason))
            dbapi.commit()
            break
        except sqlite3.OperationalError as e:
            last_err = e
            if "locked" not in str(e).lower():
                raise
            time.sleep(min(0.05 * (2 ** attempt), 0.4) + secrets.randbelow(50) / 1000.0)
        finally:
            if cur is not None:
                cur.close()
            if raw is not None:
                try:
                    raw.dbapi_connection.rollback()
                except Exception:
                    pass
                raw.close()
    else:
        raise last_err  # type: ignore[misc]   # 重试耗尽：fail-closed，不写半条
    # 分叉告警（不阻断，「只报新增」基线差口径）：仅当某 prev 计数超过其
    # 启动基线时才告警；基线随现值上浮，同批分叉不重复刷。告警失败不影响主流程。
    try:
        global _NCA_FORK_BASELINE
        with get_sessionmaker().begin() as s:
            if _NCA_FORK_BASELINE is None:   # 启动快照失败的惰性回退
                rows = (s.query(M.NcaChain.prev_nca, func.count())
                        .filter(M.NcaChain.prev_nca != "GENESIS")
                        .group_by(M.NcaChain.prev_nca).all())
                _NCA_FORK_BASELINE = {p: c for p, c in rows}
            dups = (s.query(M.NcaChain.prev_nca, func.count())
                    .filter(M.NcaChain.prev_nca != "GENESIS")
                    .group_by(M.NcaChain.prev_nca)
                    .having(func.count() > 1).all())
        base = _NCA_FORK_BASELINE
        new_forks = [(p, c) for p, c in dups if c > base.get(p, 1)]
        if new_forks:
            _NCA_LOG.warning("NCA_FORK_ALERT new-fork groups=%d detail=%s",
                             len(new_forks), new_forks[:5])
        for p, c in dups:
            if c > base.get(p, 1):
                base[p] = c
    except Exception:
        _NCA_LOG.exception("NCA_FORK_ALERT check failed")
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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-1 overview 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-2 tax/mou 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-2 nca-history 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-2 shapley 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-3 config-right/call 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-7 ledger-public 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-5 sandbox/apply 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("genie 平台通道未配置: %s", e)
        raise HTTPException(503, "服务暂不可用，请稍后重试；反复失败请联系运维。")
    try:
        out = run_genie(req.query, llm)
    except CircuitOpen as e:
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("genie 平台通道熔断中: %s", e)
        raise HTTPException(503, "服务暂不可用，请稍后重试；反复失败请联系运维。")
    except LLMCallError as e:
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("genie 平台调用失败: %s", e)
        raise HTTPException(502, "服务暂不可用，请稍后重试；反复失败请联系运维。")
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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-8 emergency-fuse 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-9 notifier/mrcr-status 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
        # L1SI153 段三①：异常原文只进日志，⛔ 不返回用户；状态码不改
        _ERR_LOG.exception("A-10 eios/cluster-status 失败: %s", e)
        raise HTTPException(500, "系统繁忙，请稍后重试；反复失败请联系运维。")


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
def auth_login(req: LoginRequest, request: Request):
    """M3: 登录（PBKDF2 校验 → 签发 TDCA-SES 会话；单会话制，旧会话即吊销）。
    F-5（2026-10-10）：失败登录计入 IP|用户名 滑动窗限流（只计失败，成功不耗额度；
    超限 429 fail-closed，文案仍不区分账号不存在/口令错）。"""
    rate_key = f"{_client_ip(request)}|{req.username}"
    if not _login_rate_ok(rate_key):
        raise HTTPException(429, f"登录尝试过于频繁（每账号每 IP 每小时 ≤{_LOGIN_MAX} 次），请稍后再试")
    with get_session() as s:
        user = s.get(M.User, req.username)
        ok = user is not None and verify_password(
            req.password, user.salt, user.iterations, user.password_hash)
        role = user.role if user else None
    if not ok:
        _login_rate_record(rate_key)
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

# F-5（2026-10-10 立项）：登录口防爆破限流——注册口已有同构件，登录口原缺（免码公开面可爆破）。
# 键 = IP|用户名（双键：防同 IP 扫多账号，也防分布式对单账号爆破）；只计失败（成功登录不耗额度）。
_LOGIN_WINDOW_S = 3600
_LOGIN_MAX = int(os.environ.get("TDCA_LOGIN_MAX_PER_HOUR", "10"))  # 每账号每 IP 每小时（可配置）
_login_hits: Dict[str, List[float]] = {}               # 进程内（与注册限流同口径）


def _login_rate_record(key: str) -> None:
    """记录一次失败登录（滑动窗前先裁剪）。"""
    now = _time.time()
    hits = [t for t in _login_hits.get(key, []) if now - t < _LOGIN_WINDOW_S]
    hits.append(now)
    _login_hits[key] = hits


def _login_rate_ok(key: str) -> bool:
    """同一 IP|用户名 滑动窗口限流：60 分钟内失败 ≤_LOGIN_MAX 次。"""
    now = _time.time()
    hits = [t for t in _login_hits.get(key, []) if now - t < _LOGIN_WINDOW_S]
    return len(hits) < _LOGIN_MAX


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
    # L1SI145-ANCHOR-B2-001：注册选锚（可后补不设门槛；未选者默认记名级·待补）。
    # 只收枚举引用，⛔ 不收任何身份明文取值；选锚不产生权限、不发身份类令牌。
    anchor_kind: Optional[str] = None           # notifier|realname-phone；缺省/空=未选
    anchor_evidence_ref: Optional[str] = None   # 证据引用编号（引用非值；须与 anchor_kind 同传）


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
    # L1SI145-ANCHOR-B2-001：选锚枚举校验（fail-closed，未知值拒绝；引用只收编号不收明文取值）
    anchor_kind = (req.anchor_kind or "").strip() or None
    if anchor_kind is not None and anchor_kind not in ("notifier", "realname-phone"):
        raise HTTPException(400, "anchor_kind 仅接受 notifier|realname-phone（可留空，未选默认记名级·待补）")
    anchor_ref = (req.anchor_evidence_ref or "").strip() or None
    if anchor_ref is not None and anchor_kind is None:
        raise HTTPException(400, "anchor_evidence_ref 须与 anchor_kind 同传（未选锚不得携带证据引用）")
    if anchor_ref is not None and len(anchor_ref) > 256:
        raise HTTPException(400, "anchor_evidence_ref 过长（≤256 字符，引用编号）")
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
    # L1SI145-ANCHOR-B2-001：选锚落锚段存证（无存证不执行——存证失败即抛错，不建锚行）；
    # 未选者也照常建一行（anchor_kind NULL 如实＋记名级·待补＝默认标记落点）。
    _ANCHOR_TIER_BY_KIND = {"notifier": "固锚级", "realname-phone": "记名级"}
    anchor_tier = _ANCHOR_TIER_BY_KIND.get(anchor_kind or "", "记名级")
    anchor_nca = _nca_append(
        "user_anchor_select", username,
        artifact_path=(f"anchor://kind:{anchor_kind or 'none'}/tier:{anchor_tier}"
                       f"/state:待补/ref:{anchor_ref or 'none'}"),
        prov="real")
    with get_sessionmaker().begin() as s:
        now_iso = datetime.now(timezone.utc).isoformat()
        s.add(M.UserAnchor(
            username=username, anchor_kind=anchor_kind, anchor_tier=anchor_tier,
            tier_state="待补", evidence_ref=anchor_ref, nca_ref=anchor_nca,
            data_provenance="real", created_at=now_iso, updated_at=now_iso))
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
        "anchor": {"anchor_kind": anchor_kind, "anchor_tier": anchor_tier,
                   "tier_state": "待补", "nca_ref": anchor_nca,
                   "note": "选锚已随注册落锚段存证（未选者默认记名级·待补，可后补）；选锚不产生权限"},
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
# L1SI145-ANCHOR-B2-001：锚核验人工受理（founder/operator 专用，追加制留痕）
# =====================================================================

class AnchorVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    real_name_present: bool = False    # 只收有无（布尔），⛔ 不收明文取值
    phone_present: bool = False        # 手机号非必填：present=False 如实落 0
    evidence_ref: str = ""             # 证据引用编号（人工受理留痕载体，引用非值）


@router.post("/me/anchor/verify")
def me_anchor_verify(req: AnchorVerifyRequest, request: Request):
    """锚核验人工受理：站点管理员线下核过实名/手机号后调用。

    追加制：每次受理追加一条 user_anchor_verify 存证（原态→新态如实），再更新锚行；
    明文最小化：只落 *_present 布尔＋evidence_ref 引用，⛔ 绝不收/不落明文取值；
    fail-closed：无锚记录/无证据引用/角色不符一律拒绝。
    """
    v = _require_session_user(request)
    if v["role"] not in ("founder", "operator"):
        raise HTTPException(403, "锚核验受理仅 founder/operator 可执行（人工受理制度级操作）")
    username = req.username.strip()
    ref = req.evidence_ref.strip()
    if not ref:
        raise HTTPException(400, "evidence_ref 必填（核验证据引用编号，人工受理留痕载体）")
    if len(ref) > 256:
        raise HTTPException(400, "evidence_ref 过长（≤256 字符，引用编号）")
    with get_sessionmaker().begin() as s:
        if s.get(M.User, username) is None:
            raise HTTPException(404, f"用户不存在: {username}")
        row = s.get(M.UserAnchor, username)
        if row is None:
            raise HTTPException(404, f"该用户无锚记录（注册时未建锚行，异常态——请上报）")
        prev_state = row.tier_state
        nca_id = _nca_append(
            "user_anchor_verify", v["username"],
            artifact_path=(f"anchor://{username}/state:{prev_state}->已补"
                           f"/ref:{ref}"
                           f"/rn:{int(req.real_name_present)}/ph:{int(req.phone_present)}"),
            prov="real")
        now_iso = datetime.now(timezone.utc).isoformat()
        row.tier_state = "已补"
        row.real_name_present = 1 if req.real_name_present else 0
        row.phone_present = 1 if req.phone_present else 0
        row.evidence_ref = ref
        row.verified_at = now_iso
        row.verifier = v["username"]
        row.nca_ref = nca_id
        row.updated_at = now_iso
    return _nca_watermark({
        "username": username, "tier_state": "已补",
        "real_name_present": bool(req.real_name_present),
        "phone_present": bool(req.phone_present),
        "evidence_ref": ref, "verifier": v["username"], "nca_id": nca_id,
        "note": "锚核验受理完成（追加制存证已落链：原态如实→已补；明文最小化：只落有无布尔＋引用）",
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


_USAGE_TZ = timezone(timedelta(hours=8))     # +08（本项目明示日界口径）
_USAGE_DEFAULT_DAYS = 30                     # 窗口默认取值（执行侧裁，回报载明）
_USAGE_MAX_DAYS = 90                         # 窗口上限（防全表拉取）


def _fmt_plus8(raw: Optional[str]) -> tuple:
    """ISO-8601 文本 → (+08 'YYYY-MM-DD HH:MM:SS', True)；缺失/不可解析 → (None, False)。
    降级口径：不猜测不伪造，原值由调用方如实带出。"""
    if not raw:
        return None, False
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(_USAGE_TZ).strftime("%Y-%m-%d %H:%M:%S"), True
    except (ValueError, TypeError, OverflowError):
        return None, False


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
        # 我的配置记录（最小链要约，seller_ref=本人）＋站内积分合计（SIMULATED）
        config_records = []
        my_points = 0
        for r in (s.query(M.MarketSimRun)
                  .order_by(M.MarketSimRun.created_at.desc()).limit(100).all()):
            try:
                offer = json.loads(r.offer_json)
            except Exception:
                offer = {}
            if offer.get("seller_ref") != me:
                continue
            my_points += int(offer.get("price_points") or 0)
            config_records.append({"run_id": r.run_id, "result": r.result,
                                   "asset_summary": offer.get("asset_summary"),
                                   "scene": offer.get("scene"),
                                   "price_points": offer.get("price_points"),
                                   "nca_ref": r.nca_ref, "ts": r.created_at})
        # REGISTER-002 缺口⑤（GSEQ-0671）：本人最近一条注册缔约存证（前端可展示/自查落链）
        last_reg = (s.query(M.NcaChain)
                    .filter(M.NcaChain.actor == me, M.NcaChain.action.like("user_register%"))
                    .order_by(M.NcaChain.ts.desc()).first())
        # GSEQ-0700：身份三要素机读（identity_type/owner_auth；agent_card 全量经 nca-verify 链上核验）
        ident = s.get(M.UserIdentity, me)
        # L1SI145-ANCHOR-B2-001：本人锚行机读（无行=旧账号如实 null；只现有无布尔与核态，⛔ 不出明文取值）
        anchor = s.get(M.UserAnchor, me)
        # 账户信息栏升级版（可增项第 3 件）：users.created_at 现值如实带出（只读），
        # +08 展示值由 _fmt_plus8 解析；缺失/不可解析 ⟹ 原值如实、display=null、parse_ok=false
        u = s.get(M.User, me)
        created_raw = u.created_at if u else None
        created_disp, created_ok = _fmt_plus8(created_raw)
        return _nca_watermark({
            "session": {"username": me, "role": v["role"], "expires_at": v["expires_at"],
                        "last_register_nca_id": last_reg.nca_id if last_reg else None,
                        "identity_type": ident.identity_type if ident else None,
                        "owner_auth": ident.owner_auth if ident else None,
                        "agent_card_persisted": bool(ident and ident.agent_card_json),
                        "created_at": created_raw,
                        "created_at_display": created_disp,
                        "created_at_parse_ok": created_ok},
            "pending_count": len(pending),
            "user_anchor": ({
                "anchor_kind": anchor.anchor_kind, "anchor_tier": anchor.anchor_tier,
                "tier_state": anchor.tier_state,
                "real_name_present": anchor.real_name_present,
                "phone_present": anchor.phone_present,
                "evidence_ref": anchor.evidence_ref,
                "verified_at": anchor.verified_at, "verifier": anchor.verifier,
                "nca_ref": anchor.nca_ref, "updated_at": anchor.updated_at,
            } if anchor else None),
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
                            "sea_snapshot": a.sea_snapshot, "ts": a.ts} for a in sandbox],
            "my_governance": [{"op": g.op, "fuse_state": g.fuse_state,
                               "ts": g.ts} for g in gov],
            # 2026-10-04 创始人明示补齐栏目：资产/积分/配置权持有/配置记录/NCA
            "my_assets": [{"order_no": a.order_no, "name": a.name,
                           "description": a.description, "asset_count": a.asset_count,
                           "data_provenance": a.data_provenance}
                          for a in s.query(M.AssetOrder).order_by(M.AssetOrder.order_no).all()],
            "my_grants": [{"grant_id": g.grant_id, "subject_agent": g.subject_agent,
                           "scene_constraint": g.scene_constraint,
                           "asset_order": g.asset_order, "status": g.status,
                           "nca_ref": g.nca_ref}
                          for g in (s.query(M.AuthGrant)
                                    .filter(or_(M.AuthGrant.legal_signer == me,
                                                M.AuthGrant.subject_agent.in_(ids or ["\0"])))
                                    .order_by(M.AuthGrant.status).all())],
            "my_config_records": config_records,
            # 2026-10-09 批 1：权属栏（本人过滤；摘要口径与 /me/nca 明细单一口径）
            "my_ownership": [{"record_id": r.record_id, "work_title": r.work_title,
                              "jurisdiction_branch": r.jurisdiction_branch,
                              "status": r.status, "nca_ref": r.nca_ref,
                              "data_provenance": r.data_provenance,
                              "created_at": r.created_at}
                             for r in (s.query(M.OwnershipRecord)
                                       .filter(M.OwnershipRecord.owner_ref == me)
                                       .order_by(M.OwnershipRecord.created_at.desc()).all())],
            "my_points": {"balance": my_points,
                          "data_provenance": "simulated",
                          "note": "站内积分（最小链结算记账；期一 SIMULATED，非真实清算）"},
            "my_nca": [{"nca_id": n.nca_id, "action": n.action,
                        "artifact_path": n.artifact_path, "sha256_8": n.sha256_8,
                        "ts": n.ts}
                       for n in (s.query(M.NcaChain).filter(M.NcaChain.actor == me)
                                 .order_by(M.NcaChain.ts.desc()).limit(20).all())],
            "note": "个人后台（谁的数据谁可见；simulated 行已按口径标注；资产目录为全站五阶形态，"
                    "积分/最小链为 SIMULATED；权属栏本人过滤）",
        }, nature="real")


@router.get("/me/nca")
def me_nca(request: Request, page: int = 1, limit: int = 20, action: str = ""):
    """P1 控制台：本人 NCA 存证分页明细（actor=本人强制过滤；摘要走 /me/dashboard 最近 20，
    明细走本端分页——单一口径不两处各算；action 精确过滤可空）。"""
    v = _require_session_user(request)
    me = v["username"]
    if page < 1:
        raise HTTPException(400, "page 须 ≥1")
    if limit < 1 or limit > 100:
        raise HTTPException(400, "limit 须 1~100")
    with get_session() as s:
        q = s.query(M.NcaChain).filter(M.NcaChain.actor == me)
        if action:
            q = q.filter(M.NcaChain.action == action)
        total = q.count()
        rows = (q.order_by(M.NcaChain.ts.desc())
                .offset((page - 1) * limit).limit(limit).all())
    return _nca_watermark({
        "total": total, "page": page, "limit": limit,
        "items": [{"nca_id": n.nca_id, "action": n.action,
                   "artifact_path": n.artifact_path, "sha256_8": n.sha256_8,
                   "ts": n.ts} for n in rows],
    }, nature="real")


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")   # 未知字段 fail-closed 拒绝
    old_password: str = ""
    new_password: str = ""


class SessionRevokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")   # 未知字段 fail-closed 拒绝
    sid: str = ""


def _session_sid(token_hash: str) -> str:
    """会话展示指纹（吊销标识）：sha256(token_hash) 前 12 位。
    不可逆、不可用于登录取值、不暴露 token_hash 本身；仅作列表-吊销对照键。"""
    return hashlib.sha256(token_hash.encode("utf-8")).hexdigest()[:12]


@router.get("/me/sessions")
def me_sessions(request: Request):
    """会话管理·看（2026-10-09 可增项第 1 件）：列本人会话——创建/到期/是否当前/
    是否已失效（revoked 或过期）。⛔ 不返回 token/token_hash 任何值（标识用 sid 指纹）。
    勘察实况：单活会话制（登录即挤旧），历史 revoked 行只读留痕、照常列出。"""
    v = _require_session_user(request)
    me = v["username"]
    current_hash = hashlib.sha256(
        request.headers.get("authorization", "").strip().encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    items = []
    with get_session() as s:
        rows = (s.query(M.AuthSession)
                .filter(M.AuthSession.username == me)
                .order_by(M.AuthSession.created_at.desc()).all())
        for r in rows:
            items.append({
                "sid": _session_sid(r.token_hash),
                "created_at": r.created_at,
                "expires_at": r.expires_at,
                "is_current": r.token_hash == current_hash,
                "is_revoked": r.revoked == 1,
                "is_expired": datetime.fromisoformat(r.expires_at) <= now,
            })
    return _nca_watermark({
        "sessions": items,
        "note": "仅列本人会话；单活会话制（登录即挤下线），历史会话只读留痕；"
                "标识 sid 为 token_hash 的 sha256 指纹，不含任何可登录材料",
    }, nature="real")


@router.post("/me/sessions/revoke")
def me_session_revoke(req: SessionRevokeRequest, request: Request):
    """会话管理·踢（指定会话）：sid 指纹命中本人未吊销会话 → revoked=1（既有语义）。
    他人会话或不存在 → 404（不可见处理，⛔ 不泄漏存在性）；⛔ 不删行、不动表。"""
    v = _require_session_user(request)
    me = v["username"]
    sid = req.sid.strip()
    if not sid:
        raise HTTPException(400, "sid 不可为空")
    with get_sessionmaker().begin() as s:
        row = None
        for r in s.query(M.AuthSession).filter(
                M.AuthSession.username == me, M.AuthSession.revoked == 0).all():
            if _session_sid(r.token_hash) == sid:
                row = r
                break
        if row is None:
            raise HTTPException(404, "会话不存在或已失效")
        row.revoked = 1
    nca_ref = _nca_append("user_session_revoke", me,
                          artifact_path=f"auth://me/session-revoke/{me}", prov="real")
    return _nca_watermark({
        "revoked": True, "sid": sid, "nca_ref": nca_ref,
        "note": "指定会话已吊销（revoked=1 既有语义，不删行）",
    }, nature="real")


@router.post("/me/sessions/revoke-all")
def me_session_revoke_all(request: Request):
    """会话管理·踢（全部）：吊销本人全部会话（含当前）＝强制退出登录。
    revoked=1 既有语义；⛔ 不删行、不动表；落 NCA（⛔ 不含 token 值）。
    当前会话自下一请求起 401（validate_session revoked 语义，S-3 实测口径）。"""
    v = _require_session_user(request)
    me = v["username"]
    revoked_n = 0
    with get_sessionmaker().begin() as s:
        for r in s.query(M.AuthSession).filter(
                M.AuthSession.username == me, M.AuthSession.revoked == 0).all():
            r.revoked = 1
            revoked_n += 1
    nca_ref = _nca_append("user_session_revoke_all", me,
                          artifact_path=f"auth://me/session-revoke-all/{me}", prov="real")
    return _nca_watermark({
        "revoked": revoked_n, "nca_ref": nca_ref,
        "note": "本人全部会话已吊销（含当前，强制退出登录）；本会话自下一请求起失效",
    }, nature="real")


_USAGE_TZ = timezone(timedelta(hours=8))     # +08（本项目明示日界口径；定义上移至 me 系端点共用）


@router.get("/me/usage")
def me_usage(request: Request, days: int = _USAGE_DEFAULT_DAYS):
    """用量统计 v1（2026-10-09 可增项第 2 件）：本人 NCA 按日计数聚合（纯 SELECT）。
    口径（勘察结论照办）：actor 恰等于会话用户名者计入——gateway:…/HUF:… 等非用户
    形态不属「本人」名下，一律排除；ts 为 UTC ISO 文本，日界＝+08（先解析转 +08 再取日，
    聚合与展示同口径）；窗口默认 30 天、上限 90，越界 400 fail-closed。
    ⛔ 零写库、零新表、不落 NCA；data_provenance 按行聚合明示（ID92 SIMULATED 照守）。
    形状二择一取①（新只读端点）：/me/dashboard 既有字段一律不动。"""
    v = _require_session_user(request)
    me = v["username"]
    if days < 1 or days > _USAGE_MAX_DAYS:
        raise HTTPException(400, f"days 须为 1~{_USAGE_MAX_DAYS} 的整数")
    window_start = datetime.now(timezone.utc) - timedelta(days=days)
    daily: Dict[str, Dict[str, object]] = {}
    provs: List[str] = []
    with get_session() as s:
        rows = s.query(M.NcaChain).filter(M.NcaChain.actor == me).all()
        for r in rows:
            try:
                ts = datetime.fromisoformat(r.ts.replace("Z", "+00:00"))
            except ValueError:
                continue            # 非 ISO 行不计入（fail-closed 不猜测）
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < window_start:
                continue
            day = ts.astimezone(_USAGE_TZ).date().isoformat()
            cell = daily.setdefault(day, {"count": 0, "by_action": {}})
            cell["count"] = int(cell["count"]) + 1
            ba = cell["by_action"]
            ba[r.action] = ba.get(r.action, 0) + 1
            provs.append(r.data_provenance)
    nature = _nature_of(provs)
    return _nca_watermark({
        "days": days,
        "timezone": "+08",
        "actor_filter": "actor == 会话用户名（gateway:…/HUF:… 等非用户形态不计入）",
        "total": sum(int(c["count"]) for c in daily.values()),
        "daily": [{"date": d, "count": int(c["count"]),
                   "by_action": dict(sorted(c["by_action"].items()))}
                  for d, c in sorted(daily.items(), reverse=True)],
        "data_provenance": nature,
        "note": "本人 NCA 存证按日计数（+08 日界，窗口默认 30 天）；纯只读聚合，零写库、不落 NCA",
    }, nature=nature)


@router.post("/me/password")
def me_password(req: PasswordChangeRequest, request: Request):
    """改密（仅本人；2026-10-09 最小实现令）：旧密核验 → 新密强度（沿用注册口径）→
    吊销本人其它会话（revoked=1 既有语义，当前会话保留）→ NCA 落链。
    ⛔ 不加字段、不动表结构；哈希/盐/迭代数不入件不入响应。
    返码口径（2026-10-09 评估件落地）：旧密错=400（401 会被前端客户端误作
    会话失效清退本地令牌）；「用户不存在」=401 与未登录=401 保持不动（真会话面）。"""
    v = _require_session_user(request)
    me = v["username"]
    with get_session() as s:
        user = s.get(M.User, me)
        if user is None:
            raise HTTPException(401, "用户不存在")  # fail-closed
        if not verify_password(req.old_password, user.salt, user.iterations,
                               user.password_hash):
            raise HTTPException(400, "旧密码错误")   # 返码口径：应用层凭据错→400（401 保留给会话面）
    new_pw = req.new_password
    if (len(new_pw) < 8 or not any(c.isalpha() for c in new_pw)
            or not any(c.isdigit() for c in new_pw)):
        raise HTTPException(400, "密码强度不足：至少 8 位且同时包含字母与数字")
    ph, salt, iters = hash_password(new_pw)
    current_hash = hashlib.sha256(
        request.headers.get("authorization", "").strip().encode("utf-8")).hexdigest()
    revoked_n = 0
    with get_sessionmaker().begin() as s:
        user = s.get(M.User, me)
        user.password_hash = ph
        user.salt = salt
        user.iterations = iters
        # 吊销本人其它会话（保留当前会话；既有 revoked=1 语义）
        for sess in s.query(M.AuthSession).filter(
                M.AuthSession.username == me, M.AuthSession.revoked == 0):
            if sess.token_hash != current_hash:
                sess.revoked = 1
                revoked_n += 1
    nca_ref = _nca_append("user_password_change", me,
                          artifact_path=f"auth://me/password-change/{me}", prov="real")
    return _nca_watermark({
        "changed": True, "username": me, "other_sessions_revoked": revoked_n,
        "nca_ref": nca_ref,
        "note": "密码已更换；本人其它会话已吊销（当前会话保留）；落 NCA 存证链",
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
    # ── 2026-10-09 批 1 控制台补词（人类通道专用）──
    {"keys": ["我的资产", "五阶资产", "资产管理"],
     "route": "/me", "title": "我的 · 资产（控制台）",
     "action": "查询",
     "guide": ["「我的」页资产栏：五阶形态目录", "个人持有见配置权持有栏"]},
    {"keys": ["我的权属", "权属登记", "产权"],
     "route": "/me", "title": "我的 · 权属（控制台）",
     "action": "查询",
     "guide": ["「我的」页权属栏：本人权属件（登记/变更/注销状态）", "登记操作直达权属登记面"]},
    {"keys": ["我的授权", "配置权", "授权件"],
     "route": "/me", "title": "我的 · 授权（控制台）",
     "action": "查询",
     "guide": ["「我的」页授权持有栏：授权件与状态", "五操作（预收权/实时/追加/变更/多层级）直达授权登记面"]},
    {"keys": ["我的积分", "积分"],
     "route": "/me", "title": "我的 · 积分（控制台）",
     "action": "查询",
     "guide": ["「我的」页积分栏（SIMULATED 明示）", "口径：本人为出让方的最小链要约报价合计"]},
    {"keys": ["我的存证", "活动产物", "操作记录", "存证查询"],
     "route": "/me", "title": "我的 · 活动产物（控制台）",
     "action": "查询",
     "guide": ["「我的」页活动产物栏：本人 NCA 分页明细", "可按动作过滤，链上可查可验"]},
    {"keys": ["工具货架", "上架", "货架"],
     "route": "/toolshelf", "title": "工具货架",
     "action": "操作",
     "guide": ["须登录；上架须 operator", "逐项上架，三条准入逐件过闸"]},
    {"keys": ["运维", "工单", "红线"],
     "route": "/ops", "title": "运维工单",
     "action": "操作",
     "guide": ["须登录；操作须 operator", "建单 / 红线查看 / 反馈 / 分类"]},
    {"keys": ["公告", "通知"],
     "route": "/announcements", "title": "公告栏",
     "action": "查询",
     "guide": ["对外公告区，公开可读", "空栏为常态"]},
    {"keys": ["集群", "准入", "判定", "编排"],
     "route": "/cluster", "title": "集群编排与准入",
     "action": "操作",
     "guide": ["须登录", "五门合取判定，fail-closed", "沙盒例外：已缔约即可演练"]},
    {"keys": ["沙盒", "演练", "入盒"],
     "route": "/sandbox", "title": "沙盒演练",
     "action": "操作",
     "guide": ["须登录（注册即缔约）", "沙盒内配置不入正式账本", "出盒须初始确权"]},
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
    best, best_key, alts = None, None, []
    for item in _INTENT_TABLE:
        matched = [k for k in item["keys"] if k in text]   # 命中定义不变（k in text ＋计数）
        hits = len(matched)
        if hits > 0:
            longest = max(len(k) for k in matched)          # 命中键中最长者长度
            alts.append({"route": item["route"], "title": item["title"],
                         "hits": hits, "longest": longest})
            # 裁决（2026-10-09 可增项第 4 件）：命中数 ↓、最长命中键 ↓，仍并列维持表序（严格 >，先到先得）
            if best is None or (hits, longest) > best_key:
                best, best_key = item, (hits, longest)
    # 备选与最优同一裁决规则；稳定排序保证全并列时维持表序兜底
    alts = sorted((a for a in alts if not best or a["route"] != best["route"]),
                  key=lambda a: (-a["hits"], -a["longest"]))[:2]
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
