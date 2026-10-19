# -*- coding: utf-8 -*-
"""A-24 存证公开自查入口 M1″ 测试（031 令步 3 · 五例必绿＋锚端点两例）。

令面五例：① 已知 nca_id ⟹ 200 十字段齐；② 不存在 ⟹ 404 同码；
③ 按公开口径重算 rec_hash 一致（抽 3 条三比三）；④ 篡改一字节 ⟹ 重算不符（能检出）；
⑤ 响应全文无 actor 原值、无内部编号、无凭据。
"""
import hashlib
import json

from fastapi.testclient import TestClient

import selfcheck_ops
from api_v1 import _nca_append, rec_hash_of
from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_SEED_ACTOR = "自然人测试员甲"   # 含自然人标识——验收其原值绝不出响应


def _seed_chain():
    """造三行连续链（走 _nca_append 写路径，即写时锚定口径）。"""
    ids = [_nca_append(f"M1PP_TEST_{i}", _SEED_ACTOR,
                       artifact_path=f"docs/test/artifact-{i}.md")
           for i in range(3)]
    selfcheck_ops._PUBLIC_IDS.update(ids)   # 登记进测试清单（conftest 每例起空集；AMEND-2 收窄后仍 200）
    return ids


def _recompute(row: M.NcaChain) -> str:
    """第三方视角：仅用响应可得字段 + 公开口径重算（actor 以库内值代，验证口径本身）。"""
    return rec_hash_of(row.nca_id, row.prev_nca, row.action, row.actor,
                       row.artifact_path, row.sha256_8, row.handshake_id,
                       row.data_provenance, row.ts)


# ---- ① 已知 nca_id ⟹ 200 十字段齐 ----
def test_m1pp_known_id_ten_fields():
    ids = _seed_chain()
    r = client.get(f"/api/v1/selfcheck/nca/{ids[0]}")
    assert r.status_code == 200
    body = r.json()["data"]
    assert "nca_watermark" in r.json()      # 全链路水印（前端 fail-closed 依赖）
    rec = body["record"]
    expect = {"nca_id", "action", "ts", "artifact_filename_sha256_16", "artifact_ext",
              "sha256_8", "rec_hash", "prev_hash", "detached", "detach_reason", "actor_hash"}
    assert set(rec.keys()) == expect, f"白名单漂移: {set(rec.keys()) ^ expect}"
    assert rec["nca_id"] == ids[0]
    # 035-A2 令脱敏：件名原值不出，回 sha256(件名 UTF-8) 前 16 位大写
    assert rec["artifact_filename_sha256_16"] == hashlib.sha256(
        "artifact-0.md".encode("utf-8")).hexdigest()[:16].upper()
    assert rec["artifact_ext"] == "md"
    assert rec["actor_hash"] == hashlib.sha256(
        _SEED_ACTOR.encode("utf-8")).hexdigest()[:8]       # 脱敏值口径
    assert body["page_disclaimer"].startswith("本查询可证：")


# ---- ② 不存在 ⟹ 404 同码同文 ----
def test_m1pp_missing_id_404_same_code():
    r1 = client.get("/api/v1/selfcheck/nca/NCA-NO-SUCH-1")
    r2 = client.get("/api/v1/selfcheck/nca/完全不存在之二")
    assert r1.status_code == 404 and r2.status_code == 404
    assert r1.json() == r2.json()          # 同码同文，防探测差异


# ---- ③ 抽 3 条：按口径重算 rec_hash 与返回一致（三比三） ----
def test_m1pp_recompute_three_of_three():
    ids = _seed_chain()
    with get_session() as s:
        rows = [s.get(M.NcaChain, i) for i in ids]
    for row in rows:
        r = client.get(f"/api/v1/selfcheck/nca/{row.nca_id}")
        assert r.status_code == 200
        returned = r.json()["data"]["record"]["rec_hash"]
        assert returned == _recompute(row) == row.rec_hash, "三向不一致"


# ---- ④ 篡改一字节 ⟹ 重算不符（能检出） ----
def test_m1pp_tamper_detected():
    ids = _seed_chain()
    target = ids[1]
    with get_sessionmaker().begin() as s:   # 直接改库一字节（模拟持库者改写）
        row = s.get(M.NcaChain, target)
        row.action = row.action + "X"
    with get_session() as s:
        row = s.get(M.NcaChain, target)
    r = client.get(f"/api/v1/selfcheck/nca/{target}")
    assert r.status_code == 200
    returned = r.json()["data"]["record"]["rec_hash"]
    assert returned != _recompute(row), "篡改后重算应不符——判据 2 失效即 S-4"


# ---- ⑤ 响应全文无 actor 原值、无内部编号、无凭据 ----
def test_m1pp_no_actor_no_secret_no_internal_id():
    ids = _seed_chain()
    r = client.get(f"/api/v1/selfcheck/nca/{ids[2]}")
    text = json.dumps(r.json(), ensure_ascii=False)
    assert _SEED_ACTOR not in text                    # ⛔ actor 原值（自然人标识）不出
    assert "artifact-2.md" not in text                # ⛔ 台账件名原值不出（035-A2 脱敏）
    assert "creator=" not in text                     # ⛔ 件名内嵌账号形态不出
    assert "TDCA-HANDOFF" not in text and "TDCA-EXEC" not in text   # ⛔ 内部编号
    assert "PRIVATE KEY" not in text and "TDCA-SES-" not in text \
        and "TDCA-CRT-" not in text and "password" not in text.lower()  # ⛔ 凭据形态
    assert '"handshake_id"' not in text               # ⛔ 全空无意义字段不出（JSON 键级；公式串点名属公开口径）


# ---- 锚端点：有种 ⟹ digest 一致；无种 ⟹ 503 fail-closed ----
def test_m1pp_anchor_available_and_consistent(tmp_path, monkeypatch):
    anchor = {"date": "2026-10-19", "row_count": 3,
              "anchor_digest": hashlib.sha256(b"2026-10-19|3|A,B,C").hexdigest().upper()[:16],
              "leaf_count": 3, "detached_count": 0,
              "schema_version": 2,
              "canonicalization": "sha256('date|row_count|sorted(leaf_hashes)')"}
    (tmp_path / "anchor-2026-10-19.json").write_text(
        json.dumps(anchor), encoding="utf-8")
    monkeypatch.setenv("TDCA_ANCHOR_DIR", str(tmp_path))
    r = client.get("/api/v1/selfcheck/anchor")
    assert r.status_code == 200
    a = r.json()["data"]["anchor"]
    assert a["row_count"] == 3 and a["anchor_digest"] == anchor["anchor_digest"]
    assert "page_disclaimer" in r.json()["data"]


def test_m1pp_anchor_missing_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("TDCA_ANCHOR_DIR", str(tmp_path))   # 空目录
    r = client.get("/api/v1/selfcheck/anchor")
    assert r.status_code == 503
    assert "ANCHOR_UNAVAILABLE" in r.text                # 不编造


# ---- spec 端点：口径公开（第三方可独立重算） ----
def test_m1pp_spec_public():
    r = client.get("/api/v1/selfcheck/spec")
    assert r.status_code == 200
    assert "rec_hash = sha256(" in r.json()["data"]["rec_hash_spec"]


# ---- AMEND-1①：artifact_ext 收紧（路径内嵌 ':sha1'／'rtbase=' 不外泄） ----
def test_amend1_ext_leaky_path_returns_empty():
    leaky = ("obs/NCA-WEB-225450bc3ed9.py:10fddbd3502918818d0a5e6eb0478febf096b109"
             ":rtbase=e64c9a6d,a8a79475,872e256e,5d584adc")
    ext = selfcheck_ops._artifact_ext(leaky)
    assert ext == ""
    assert ":" not in ext and "=" not in ext and "/" not in ext


def test_amend1_ext_normal_extensions_still_ok():
    assert selfcheck_ops._artifact_ext("docs/a.py") == "py"
    assert selfcheck_ops._artifact_ext("docs/b.md") == "md"
    assert selfcheck_ops._artifact_ext("docs/noext") == ""
    assert selfcheck_ops._artifact_ext("docs/x.PY") == "py"        # 大写归一仍正确
    assert selfcheck_ops._artifact_ext("a/f.python") == ""         # 超 5 长拒


# ---- AMEND-2：公开子集收窄（显式清单 · fail-closed · 不可区分） ----
def test_amend2_in_manifest_returns_200():
    ids = _seed_chain()
    r = client.get(f"/api/v1/selfcheck/nca/{ids[0]}")
    assert r.status_code == 200


def test_amend2_outside_manifest_returns_404():
    nca_id = _nca_append("M1PP_OUTSIDE", _SEED_ACTOR, artifact_path="docs/test/out.md")
    # 不走 _seed_chain（其自动登记），保持清单外
    r = client.get(f"/api/v1/selfcheck/nca/{nca_id}")
    assert r.status_code == 404


def test_amend2_empty_manifest_rejects_all():
    ids = _seed_chain()
    selfcheck_ops._PUBLIC_IDS.clear()      # 空清单 ⟹ 全部不可查（fail-closed）
    r = client.get(f"/api/v1/selfcheck/nca/{ids[0]}")
    assert r.status_code == 404


def test_amend2_outside_404_identical_to_missing_404():
    nca_id = _nca_append("M1PP_OUTSIDE2", _SEED_ACTOR, artifact_path="docs/test/out2.md")
    r_out = client.get(f"/api/v1/selfcheck/nca/{nca_id}")             # 清单外
    r_none = client.get("/api/v1/selfcheck/nca/NCA-NO-SUCH-AMEND2")  # 不存在
    assert r_out.status_code == 404 and r_none.status_code == 404
    assert r_out.text == r_none.text          # 状态码与响应体逐字相同
    for leak_word in ("未公开", "无权", "部分可见"):   # ⛔ 不得泄漏"存在但未公开"
        assert leak_word not in r_out.text


# ---- AMEND-2：清单加载器（缺失 ⟹ 空集 fail-closed） ----
def test_amend2_loader_missing_file_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("TDCA_SELFCHECK_MANIFEST", str(tmp_path / "no-such.yaml"))
    assert selfcheck_ops._load_public_ids() == set()


def test_amend2_loader_reads_ids_section(tmp_path, monkeypatch):
    m = tmp_path / "m.yaml"
    m.write_text("version: 1\ngenerated_from: 'x'\nids:\n  - AAA-1\n  - BBB-2\ncount: 2\n",
                 encoding="utf-8")
    monkeypatch.setenv("TDCA_SELFCHECK_MANIFEST", str(m))
    assert selfcheck_ops._load_public_ids() == {"AAA-1", "BBB-2"}
