# -*- coding: utf-8 -*-
"""统一网关测试路径配置。"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]           # tdca-gateway/
_WS = Path(__file__).resolve().parents[1].parents[0]  # workspace 根
for _sub in ("tdca-d2-union", "tdca-cscp", "tdca-workbuddy",
             "tdca-translator-market", "tdca-cross-scene"):
    _p = _WS / _sub
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------
# M2 测试库隔离：app 导入前把 DATABASE_URL 指向独立临时库并种 simulated-only
# 数据。db 包为惰性工厂（引擎在首个请求时绑定），此处设环境变量必生效。
# 约束：_get()/_post() 断言 data_nature == "simulated" → 所有种子行必须
# 显式 data_provenance="simulated"（TermsRegistry 默认 real，需覆盖）。
# ---------------------------------------------------------------------
import os
import tempfile

_TMP = Path(tempfile.mkdtemp(prefix="tdca-test-"))
os.environ["DATABASE_URL"] = "sqlite:///" + (_TMP / "test.db").as_posix()

# 对外补齐 C（L1SI166-CHANNEL-GAP-001 项 C）：沙盒准入保金阈值——测试态给正阈值使
# 闸可开（缺省语义＝闸关闭由 gap_c 专项用例直测；⛔ 硬编码进业务代码，仅测试配置）。
os.environ.setdefault("TDCA_UTILITY_DEPOSIT_MIN_MOU", "1")

# GO-LIVE-001 收口附页 §二步6b：注册开关——测试态默认开（既有套件验开放逻辑），
# 开关专项用例以 monkeypatch 拨 0 直测收口语义（生产缺省 0=关，部署配置另落）。
os.environ.setdefault("TDCA_AGENT_REG_OPEN", "1")

_EIOS = _WS / "tdca-eios"
if str(_EIOS) not in sys.path:
    sys.path.insert(0, str(_EIOS))

from db import get_engine, get_session  # noqa: E402
from db.models import (  # noqa: E402
    Agent, AssetOrder, AttestationRequest, Base, MouRecord, NcaChain,
    SandboxState, SystemMetric, TaxEvent, TermsRegistry,
)

Base.metadata.create_all(get_engine())

_NOW = "2026-08-20T00:00:00+00:00"


def _seed():
    from genie_api import GenieAPI
    caps = GenieAPI().CAPABILITIES
    with get_session() as s:
        s.add(SystemMetric(total_deliveries=128, total_tax_settled=20500,
                           avg_latency_ms=5.2, total_fused=3, total_fail_closed=7,
                           theta=0.65, phi=0.5, ts=_NOW,
                           data_provenance="simulated"))
        for no, (name, desc) in enumerate([
                ("效用权", "场景效用函数调用权"),
                ("配置权", "L2 配置权市场层（ID76）"),
                ("NCA 嵌套认知资产", "调用即存证（ID91）"),
                ("MOU 税收锚定凭证", "进项+出项（ID79）"),
                ("跨场景配置画像", "多场景偏态档案（L-6 演进）")], start=1):
            s.add(AssetOrder(order_no=no, name=name, description=desc,
                             asset_count=0, data_provenance="simulated"))
        for i, (req, st) in enumerate([
                ("任务书六要素", "GREEN"), ("前置核验（613 测试绿）", "GREEN"),
                ("沙盒编译-核验闭环", "GREEN"), ("激活系数>1.2 门槛", "AMBER"),
                ("人类 HUF 终裁", "GREEN")], start=1):
            s.add(SandboxState(requirement=req, status=st, note="测试态",
                               checked_at=_NOW, data_provenance="simulated"))
        for tid, term, dfn in [
                ("T-NCA", "NCA", "嵌套认知资产（Nested Cognitive Asset）"),
                ("T-NSFL", "NSFL", "负空间函数语言（Negative Space Function Language）"),
                ("T-MOU", "MOU", "最低可见效用 = 进项税收 + 出项税收（税收锚定硬下限）"),
                ("T-SI", "SI", "会话索引文件（Session Index）"),
                ("T-FC", "FC", "函数调用任务（Function Call）"),
                ("T-MRCR", "MRCR", "多角色兼容性规则（Multi-Role Compatibility Rule）"),
                ("T-PUCR", "PUCR", "配置权预售（Pre-sale of Configuration Rights）"),
                ("T-TDCA", "TDCA", "可信数字协作架构 ⟨ℑ, 𝒯, ℰ, 𝒫, 𝒦⟩")]:
            s.add(TermsRegistry(term_id=tid, term=term, definition=dfn,
                                data_provenance="simulated"))
        for i, role in enumerate(["NM-Operator", "NM-Gov", "NM-Fin", "NM-Med"], start=1):
            s.add(Agent(agent_id=f"AGENT-NM-{i:02d}", name=role,
                        tdid=f"TDID-{role}", status="active",
                        scene="notification", audit_count=0,
                        created_at=_NOW, data_provenance="simulated"))
        for i, (ep, meta) in enumerate(caps.items(), start=1):
            s.add(Agent(agent_id=f"EIOS-{i:02d}", name=meta["capability"],
                        endpoint=ep, capability=meta["capability"],
                        status="active", created_at=_NOW,
                        data_provenance="simulated"))
        s.add(TaxEvent(event_id="EVT-T1", type="dispatch_tax", agent_id="AGENT-A",
                       call_id="CALL-1", amount=4000, tax_rate_bp=200,
                       ts=_NOW, data_provenance="simulated"))
        s.add(TaxEvent(event_id="EVT-T2", type="royalty", agent_id="AGENT-B",
                       call_id="CALL-1", amount=15000, tax_rate_bp=750,
                       ts=_NOW, data_provenance="simulated"))
        s.commit()


_seed()


# ---------------------------------------------------------------------
# AMEND-2 公开子集收窄：每测试以空公开清单起（fail-closed 语义不被
# 默认放行污染）；需要 200 的用例自行登记：
#   selfcheck_ops._PUBLIC_IDS.update(ids)
# ---------------------------------------------------------------------
import pytest


@pytest.fixture(autouse=True)
def _public_ids_fresh():
    import selfcheck_ops
    fresh: set[str] = set()
    orig = selfcheck_ops._PUBLIC_IDS
    selfcheck_ops._PUBLIC_IDS = fresh
    yield fresh
    selfcheck_ops._PUBLIC_IDS = orig


@pytest.fixture(autouse=True)
def _chreg_rate_fresh():
    """块 E 登记频控内存窗逐测清零（同进程多测试文件共用 TestClient IP，
    不清零会假性触限 429——频控阈值面向真实单客户端，⛔ 让测试间互相污染）。"""
    import agent_channel_ops
    agent_channel_ops._chreg_hits.clear()
    yield
    agent_channel_ops._chreg_hits.clear()
