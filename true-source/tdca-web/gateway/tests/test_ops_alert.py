# -*- coding: utf-8 -*-
"""A-1b 运维异常报告（/api/v1/system/ops-alert）三态测试。

依 TDCA-HANDOFF-EXEC-L1SI214-SITE-HEALTH-001 ＋ AMEND-1：
  独立第四路（⛔ 不并入 overview/badge/cluster-status）；data_nature=real；
  无件→「当日运维无异常」；有件→原文 verbatim 不改一字；疑似凭据→fail-closed 500。
"""
from fastapi.testclient import TestClient

import api_v1
from app import app

client = TestClient(app)


def _set_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TDCA_OPS_ALERT_DIR", str(tmp_path))
    monkeypatch.setattr(api_v1, "_OPS_ALERT_DIR", str(tmp_path))


def test_ops_alert_none_state(tmp_path, monkeypatch):
    """无报告件：200 ＋ 当日运维无异常 ＋ real 水印。"""
    _set_dir(tmp_path, monkeypatch)
    r = client.get("/api/v1/system/ops-alert")
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["has_alert"] is False
    assert d["message"] == "当日运维无异常"
    assert d["raw_md"] is None
    assert d["generated_at"] is None
    assert r.json()["data_nature"] == "real"


def test_ops_alert_raw_verbatim(tmp_path, monkeypatch):
    """有报告件：原文逐字返回（⛔ 不改原文），生成时点非空。"""
    body = "# 运维异常报告 · 测试件\n\n| 级 | 面 | 读数 |\n| P1 | 样例 | 样例 |\n"
    (tmp_path / "_OPS-ALERT-20990101.md").write_text(body, encoding="utf-8")
    _set_dir(tmp_path, monkeypatch)
    r = client.get("/api/v1/system/ops-alert")
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["has_alert"] is True
    assert d["raw_md"] == body
    assert d["report_date"] == "20990101"
    assert d["generated_at"]
    assert r.json()["data_nature"] == "real"


def test_ops_alert_credential_failclosed(tmp_path, monkeypatch):
    """疑似凭据模式：fail-closed 500，内容不出件。"""
    (tmp_path / "_OPS-ALERT-20990102.md").write_text(
        "# 报告\n\npassword=hunter2\n", encoding="utf-8")
    _set_dir(tmp_path, monkeypatch)
    r = client.get("/api/v1/system/ops-alert")
    assert r.status_code == 500
    assert "hunter2" not in r.text


def test_ops_alert_old_file_still_served(tmp_path, monkeypatch):
    """无当日件但有历史件：仍服务最近一份（时序诚实由 generated_at 承担）。"""
    body = "# 旧报告\n"
    (tmp_path / "_OPS-ALERT-20981231.md").write_text(body, encoding="utf-8")
    _set_dir(tmp_path, monkeypatch)
    r = client.get("/api/v1/system/ops-alert")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["has_alert"] is True and d["raw_md"] == body
