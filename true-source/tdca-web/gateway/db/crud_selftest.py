# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M1 | 目标函数: CRUD 自测（任务书 M1 验收②：五项全绿才可交付）
# 约束矩阵: 设计包 §四——五表往返 / NCA 链式校验+断链检测 / MOU 唯一约束 / provenance 非法值 fail-closed / 金额整分零漂移
# 制度锚点: ID85（fail-closed：任何一项不过即非零退出）/ ID92 / C01 可观测
# 预期分配: 退出码 0 = 五项全过；任一失败打印 FAIL 并 exit 1
# 审计轨迹: NCA-KIMIWEB-003/004
# =============================================================================
"""CRUD 自测：在独立测试库上跑（不污染种子库）。用法：python -m db.crud_selftest"""
import datetime
import os
import sys
import tempfile

# 独立临时库：测试与种子库隔离（任务书纪律：测试存证不进协作审计链）
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name.replace("\\", "/")

from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from db import Base, get_engine, get_session, get_sessionmaker  # noqa: E402
from db import models  # noqa: E402,F401  （导入注册全部表）

engine = get_engine()  # 惰性工厂：此刻环境变量已生效，引擎指向临时库

_NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except Exception as e:  # noqa: BLE001
        FAILURES.append(name)
        print(f"FAIL  {name}: {type(e).__name__}: {e}")


def t1_five_table_roundtrip():
    """1. 五类核心表各插 1 条 → 读回一致"""
    with get_sessionmaker().begin() as s:
        s.add(models.Agent(agent_id="T-A1", name="自测智能体", five_role="M", created_at=_NOW))
        s.add(models.NcaChain(nca_id="T-NCA-1", prev_nca="GENESIS", action="TaskLodge",
                              actor="selftest", ts=_NOW))
        s.add(models.TaxEvent(event_id="T-EVT-1", type="dispatch_tax", agent_id="T-A1",
                              amount=100, ts=_NOW))
        s.add(models.MouRecord(agent_id="T-A1", period="2099-01", mou_inbound=60,
                               mou_outbound=40, ts=_NOW))
        s.add(models.SandboxState(requirement="SEA-T 自测要件", status="GREEN", checked_at=_NOW))
    with get_session() as s:
        assert s.get(models.Agent, "T-A1").name == "自测智能体"
        assert s.get(models.NcaChain, "T-NCA-1").prev_nca == "GENESIS"
        assert s.get(models.TaxEvent, "T-EVT-1").amount == 100
        mou = s.query(models.MouRecord).filter_by(agent_id="T-A1", period="2099-01").one()
        assert mou.mou_total == 100, f"mou_total 生成列错误: {mou.mou_total}"
        assert s.query(models.SandboxState).filter_by(requirement="SEA-T 自测要件").one().status == "GREEN"


def t2_nca_chain_and_break_detect():
    """2. NCA 链式校验：3 条链完整；断链检出"""
    with get_sessionmaker().begin() as s:
        s.add(models.NcaChain(nca_id="T-C1", prev_nca="GENESIS", action="TaskLodge", actor="t", ts=_NOW))
        s.add(models.NcaChain(nca_id="T-C2", prev_nca="T-C1", action="Delivery", actor="t", ts=_NOW))
        s.add(models.NcaChain(nca_id="T-C3", prev_nca="T-C2", action="HumanApproval", actor="t", ts=_NOW))
    with get_session() as s:
        ids = {r.nca_id: r.prev_nca for r in s.query(models.NcaChain).all()}
    # 链式校验
    cur = "T-C3"
    path = []
    while cur != "GENESIS":
        path.append(cur)
        cur = ids.get(cur)
        if cur is None:
            raise AssertionError(f"断链: {path[-1]} 的 prev 不存在")
    assert path == ["T-C3", "T-C2", "T-C1"]
    # 断链检测：删掉中间环节后必须检出
    with get_sessionmaker().begin() as s:
        s.delete(s.get(models.NcaChain, "T-C2"))
    with get_session() as s:
        ids = {r.nca_id: r.prev_nca for r in s.query(models.NcaChain).all()}
    cur, broken = "T-C3", False
    while cur != "GENESIS":
        prev = ids.get(cur)
        if prev is None:
            broken = True
            break
        cur = prev
    assert broken, "断链未检出（违反链式性纪律）"


def t3_mou_unique_constraint():
    """3. mou_records (agent_id, period) 唯一约束：重复插入被拒"""
    with get_sessionmaker().begin() as s:
        s.add(models.MouRecord(agent_id="T-A1", period="2099-02", mou_inbound=1, ts=_NOW))
    try:
        with get_sessionmaker().begin() as s:
            s.add(models.MouRecord(agent_id="T-A1", period="2099-02", mou_inbound=2, ts=_NOW))
        raise AssertionError("唯一约束未生效（重复插入被放行）")
    except IntegrityError:
        pass  # fail-closed 生效


def t4_provenance_check_fail_closed():
    """4. data_provenance 非法值被 CHECK 拒绝（ID92 fail-closed）"""
    try:
        with get_sessionmaker().begin() as s:
            s.add(models.Agent(agent_id="T-BAD", name="非法标注", created_at=_NOW,
                               data_provenance="fake"))
        raise AssertionError("CHECK 未生效（'fake' 被放行）")
    except IntegrityError:
        pass


def t5_money_integer_no_drift():
    """5. 金额整分往返：20500 分读回 20500，零浮点漂移"""
    with get_sessionmaker().begin() as s:
        s.add(models.TaxEvent(event_id="T-MONEY", type="settle", amount=20500, ts=_NOW))
    with get_session() as s:
        v = s.get(models.TaxEvent, "T-MONEY").amount
        assert isinstance(v, int) and v == 20500, f"金额漂移: {v!r}"
        # 205 元案例三笔合计校验（40+150+15 元 = 20500 分）
        assert 4000 + 15000 + 1500 == 20500


def main():
    Base.metadata.create_all(engine)
    print(f"CRUD 自测（独立临时库: {_tmp.name}）")
    check("T1 五表插入读回一致", t1_five_table_roundtrip)
    check("T2 NCA 链式校验 + 断链检出", t2_nca_chain_and_break_detect)
    check("T3 MOU 唯一约束拒重", t3_mou_unique_constraint)
    check("T4 provenance 非法值 fail-closed", t4_provenance_check_fail_closed)
    check("T5 金额整分零漂移", t5_money_integer_no_drift)
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass
    if FAILURES:
        print(f"\n结果: {len(FAILURES)} 项失败 → 交付不达标（fail-closed）")
        sys.exit(1)
    print("\n结果: 5/5 全过 ✅（M1 验收②达成）")


if __name__ == "__main__":
    main()
