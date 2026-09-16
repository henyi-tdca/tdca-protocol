#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1.1-REV 过渡期分轨加载 · SIL 正反例（模拟态，硬件未投产部署）。

对应 tdca-firmware-spec-V1.1-REV.md §二：
  正例（新版轨 se-required）：签名缺失/非法 → 拒载 + [SIGNATURE-FAIL]；签名合法 → 加载成功
  反例（旧版轨 hmac-only）   ：无 SE 签名 → 不拒载；HMAC 校验失败 → 标记降级（不拒载）
  未知版本                    → fail-closed 拒载
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "simulator"))

from l1_active_loader import L1ActiveRejected, load_l1_active  # noqa: E402


def _write_l1(tmp: Path, l1: dict) -> Path:
    d = tmp / "session-index"
    d.mkdir(parents=True)
    (d / "L1-active.json").write_text(json.dumps(l1, ensure_ascii=False), encoding="utf-8")
    return tmp


_L1_BASE = {"scene_id": "scene-phy-notification", "role": "NM-Operator",
            "config_right_hash": "sha256:sim", "binding_ref": "config/scene-binding.json",
            "expires": None}
_L1_SIGNED = dict(_L1_BASE, sign={"alg": "SM2", "value": "mock", "signed_at": "sim"})


# ── 正例（新版轨）────────────────────────────────────────────
def test_new_track_valid_signature_loads(tmp_path):
    r = load_l1_active(_write_l1(tmp_path, _L1_SIGNED), "1.1.0-sim")
    assert r["loaded"] and r["track"] == "se-required" and not r["degraded"]


def test_new_track_missing_signature_rejected(tmp_path):
    try:
        load_l1_active(_write_l1(tmp_path, _L1_BASE), "1.1.0-sim")
        raise AssertionError("应当拒载")
    except L1ActiveRejected as e:
        assert "[SIGNATURE-FAIL]" in str(e)


def test_new_track_malformed_signature_rejected(tmp_path):
    bad = dict(_L1_BASE, sign={"alg": "SM2", "value": ""})
    try:
        load_l1_active(_write_l1(tmp_path, bad), "1.1.0-sim")
        raise AssertionError("应当拒载")
    except L1ActiveRejected as e:
        assert "[SIGNATURE-FAIL]" in str(e)


# ── 反例（旧版轨）────────────────────────────────────────────
def test_old_track_unsigned_loads_not_rejected(tmp_path):
    r = load_l1_active(_write_l1(tmp_path, _L1_BASE), "1.0.0-sim")
    assert r["loaded"] and r["track"] == "hmac-only" and not r["degraded"]


def test_old_track_hmac_failure_degrades_not_rejects(tmp_path):
    bad = dict(_L1_BASE, hmac="corrupted")
    r = load_l1_active(_write_l1(tmp_path, bad), "1.0.0-sim")
    assert r["loaded"] and r["degraded"] and r["marker"] == "HMAC-DEGRADED"


# ── 未知版本 fail-closed ─────────────────────────────────────
def test_unknown_version_fail_closed(tmp_path):
    try:
        load_l1_active(_write_l1(tmp_path, _L1_SIGNED), "9.9.9-unknown")
        raise AssertionError("应当拒载")
    except L1ActiveRejected as e:
        assert "[UNKNOWN-FIRMWARE]" in str(e)
