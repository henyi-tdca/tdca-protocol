# -*- coding: utf-8 -*-
"""NCA 链写入原子性测试（NCA-ATOMIC-001 主改）。

验收映射：
  并发 32 写零分叉      → test_concurrent_appends_no_fork
                        （同 prev 批内不重复；恰一条锚到批外旧尾；沿 prev 走 n 步内必出批且无环）
  取尾按插入序          → test_tail_by_insertion_order
                        （同秒双写后后者 prev=前者 id，而非同 ts 歧义行）
  同 prev 重复即告警    → test_fork_alert_on_duplicate_prev（NCA_FORK_ALERT，不阻断写入）
"""
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import column, desc

import api_v1
from db import get_sessionmaker
from db import models as M

_ACTION = "TEST_NCA_ATOMIC"
_LOG = "tdca.nca"


def _atomic_rows():
    with get_sessionmaker().begin() as s:
        rows = s.query(M.NcaChain).filter(M.NcaChain.action == _ACTION).all()
        return [(r.nca_id, r.prev_nca) for r in rows]   # 会话内取成纯元组防 detach


def test_concurrent_appends_no_fork():
    n = 32
    with ThreadPoolExecutor(max_workers=16) as ex:
        ids = list(ex.map(lambda i: api_v1._nca_append(_ACTION, f"tester-{i:02d}"), range(n)))
    assert len(set(ids)) == n                       # 主键全异
    rows = _atomic_rows()
    assert len(rows) == n
    id_set = {rid for rid, _ in rows}
    prevs = [p for _, p in rows]
    assert len(set(prevs)) == n                     # 原子性：本批同 prev 零重复
    outside = [p for p in prevs if p not in id_set]
    assert len(outside) == 1                        # 恰一条锚到写前旧尾
    prev_map = dict(rows)
    for nid in id_set:                              # 链 Walk：n 步内出批且无环
        cur, seen = nid, {nid}
        for _ in range(n):
            cur = prev_map[cur]
            if cur not in id_set:
                break
            assert cur not in seen, "NCA 链出现环（断链）"
            seen.add(cur)
        else:
            pytest.fail("沿 prev 走 n 步未出批：链结构异常")


def test_tail_by_insertion_order():
    a = api_v1._nca_append(_ACTION, "order-a")
    b = api_v1._nca_append(_ACTION, "order-b")   # 与 a 同秒概率高，正考取尾口径
    with get_sessionmaker().begin() as s:
        pa = s.get(M.NcaChain, a).nca_id
        pb = s.get(M.NcaChain, b).prev_nca
    assert pb == pa                                # 后者必链前者（插入序取尾）


def test_fork_alert_on_duplicate_prev(caplog):
    tag = uuid.uuid4().hex[:8]
    with get_sessionmaker().begin() as s:
        tail = (s.query(M.NcaChain).order_by(desc(column("rowid"))).first())
        base = tail.nca_id if tail else "GENESIS"
        for t in ("a", "b"):                     # 直接种一对同 prev 分叉（模拟旧并发缺陷产物）
            s.add(M.NcaChain(nca_id=f"TEST-FORK-{tag}-{t}", prev_nca=base,
                             action="TEST_FORK_SEED", actor="test", ts="2026-10-09T00:00:00+00:00",
                             data_provenance="simulated"))
    with caplog.at_level(logging.WARNING, logger=_LOG):
        nid = api_v1._nca_append("TEST_AFTER_FORK", "test")   # 告警不阻断：写仍成功
    assert nid
    assert any("NCA_FORK_ALERT" in r.getMessage() for r in caplog.records)
