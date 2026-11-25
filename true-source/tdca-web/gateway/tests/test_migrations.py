# -*- coding: utf-8 -*-
"""MIGRATE-GATE-001 迁移链闸三判据（2026-11-25 起为迁移 PR 之 CI 必需作业）。

判据：
  ① 空库 `alembic upgrade head` 成功（全新部署路径）；
  ② `alembic heads` 恰单头（重号/成环即在此判据爆雷——!618 撞号事故同型防线）；
  ③ 既有库兼验：自 0026 头（f0a2→f0a1b2c3d4e5）之库升级至新头成功
     （L1 异审点：!618 撞号恰只在既有库路径暴露差异）。

硬约束（本测试自身亦须遵守）：
  - ⛔ downgrade 于含数据之库运行——本文件不做 downgrade 用例；
  - 每用例独立一次性临时库（tmp_path），跑完即弃。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

alembic = pytest.importorskip("alembic", reason="迁移闸需 alembic（requirements 已列）")
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]            # gateway/
_SCRIPT = _ROOT / "db" / "migrations"
_EXPECTED_HEAD = "1a2b3c4d5e6f"   # 0027 idempotency_key（WIDEMPOT-REVID-001 改号后）
_PREV_HEAD = "f0a1b2c3d4e5"      # 0026 acceptance_verdicts


def _cfg(db_path: Path) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_SCRIPT))
    cfg.set_main_option("sqlalchemy.url", "sqlite:///" + db_path.as_posix())
    return cfg


def _version(db_path: Path) -> str | None:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT version_num FROM alembic_version").fetchone()
        return row[0] if row else None
    finally:
        con.close()


@pytest.fixture()
def mig_db(tmp_path, monkeypatch):
    """一次性临时库；monkeypatch 使 env.py 之 get_database_url() 现读本库。"""
    db = tmp_path / "mig.db"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + db.as_posix())
    return db


# 判据①：空库 upgrade head 成功
def test_fresh_db_upgrade_head(mig_db):
    command.upgrade(_cfg(mig_db), "head")
    assert _version(mig_db) == _EXPECTED_HEAD
    con = sqlite3.connect(mig_db)
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(idempotency_key)")]
    finally:
        con.close()
    assert len(cols) == 9, f"idempotency_key 应恰 9 列，实得 {len(cols)}"


# 判据②：heads 恰单头（重号/成环在 ScriptDirectory 装载即抛错，亦在本判据捕获）
def test_heads_exactly_single(mig_db):
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(_cfg(mig_db))
    heads = [str(h) for h in script.get_heads()]
    assert heads == [_EXPECTED_HEAD], f"应恰单头 {_EXPECTED_HEAD}，实得 {heads}"


# 判据③：既有库兼验——自 0026 头升级至新头成功（撞号只在既有库路径暴露之防线）
def test_existing_db_from_0026_upgrades(mig_db):
    command.upgrade(_cfg(mig_db), _PREV_HEAD)
    assert _version(mig_db) == _PREV_HEAD
    command.upgrade(_cfg(mig_db), "head")
    assert _version(mig_db) == _EXPECTED_HEAD
