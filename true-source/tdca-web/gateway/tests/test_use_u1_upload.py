# -*- coding: utf-8 -*-
"""「用」组 U-1 素材上传测试（/api/v1/use/upload——USE-U1-001）。

验收映射：① 未登录 401（fail-closed，⛔ 匿名不可传）
          ② 受理：传一件当场返回哈希、大小、归属、时间
          ③ 幂等：同哈希同归属重复传 → 返回同一条、⛔ 不多一条、磁盘不重复落盘
          ④ 拒收：五类各回一句人话理由（⛔ 只给错误码）
          ⑤ 回读 GET /use/upload/{id}：本人可读；他人 403；不存在 404
          ⑥ 留痕：upload_records 落一行（谁/何时/多大/哈希）＋NCA 回链非空
"""
import hashlib

import pytest
from fastapi.testclient import TestClient

import api_v1
import upload_ops
from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "UseU1-pass-2026"


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()
    # 落盘目录隔离到临时目录（本机无 /data 卷；生产为容器 /data/uploads）
    monkeypatch.setattr(upload_ops, "UPLOAD_DIR", tmp_path / "uploads")
    yield
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()


def _auth(uname="useu1tester01"):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _upload(body: bytes, filename: str, headers: dict):
    from urllib.parse import quote
    h = dict(headers)
    h["X-Upload-Filename"] = quote(filename)  # 前端同款 encodeURIComponent
    return client.post("/api/v1/use/upload", content=body, headers=h)


def test_no_session_401():
    r = _upload(b"hello", "note.md", {})
    assert r.status_code == 401


def test_accept_returns_hash_size_owner_time():
    body = "TDCA 用组 U1 测试素材正文".encode("utf-8")
    r = _upload(body, "素材说明.md", _auth())
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["sha256"] == hashlib.sha256(body).hexdigest()
    assert d["sha256_16"] == d["sha256"].upper()[:16]
    assert d["size_bytes"] == len(body)
    assert d["owner"] == "useu1tester01"
    assert d["accept_category"] == "文本文档"
    assert d["duplicate"] is False
    assert "uploaded_at" in d and d["nca_ref"]


def test_idempotent_same_hash_same_owner():
    h = _auth()
    body = b"same-same-content"
    r1 = _upload(body, "a.txt", h)
    r2 = _upload(body, "b.txt", h)  # 同名同哈希同人，再传
    assert r1.status_code == 200 and r2.status_code == 200
    d1, d2 = r1.json()["data"], r2.json()["data"]
    assert d2["duplicate"] is True
    assert d1["upload_id"] == d2["upload_id"]  # 同一条
    assert d1["sha256"] == d2["sha256"]
    with get_sessionmaker().begin() as s:
        n = s.query(M.UploadRecord).filter_by(sha256=d1["sha256"]).count()
    assert n == 1  # ⛔ 不多一条


def test_reject_human_reasons():
    h = _auth()
    cases = [
        (b"MZ-fake-exe", "run.exe", "可执行程序"),                                  # 拒收1 可执行
        (b"fake-docm", "m.docm", "宏"),                                             # 拒收2 带宏
        (b"", "empty.md", "空文件"),                                                # 空件
        (b"\x00" * (21 * 1024 * 1024), "big.md", "上限"),                           # 文本文档 21MB > 20MB
        (b"\x7fELF-fake", "mystery.bin", "暂不受理"),                               # 清单外
    ]
    for body, name, keyword in cases:
        r = _upload(body, name, h)
        assert r.status_code == 400, (name, r.status_code, r.text[:120])
        assert keyword in r.json()["detail"], (name, r.json()["detail"])


def test_canonical_accept_flips():
    """在册十类（USE-U2-001 §三）关键翻转：.sh 入代码／规范类受理；.pptx／.svg 已不在清单（拒）。"""
    h = _auth()
    r = _upload(b"echo hi\n", "deploy.sh", h)
    assert r.status_code == 200, r.text[:200]
    assert r.json()["data"]["accept_category"] == "代码／规范"
    for name in ("slides.pptx", "icon.svg"):
        r = _upload(b"x", name, h)
        assert r.status_code == 400 and "暂不受理" in r.json()["detail"], (name, r.text[:120])


def test_hard_name_constraints():
    """在册通用硬约束：⛔ 路径穿越／绝对路径；件名 ≤ 110 字符。"""
    h = _auth()
    for name in ("../etc/passwd.md", "a/b/c.md", "C:\\tmp\\x.md", "a..b.md"):
        r = _upload(b"x", name, h)
        assert r.status_code == 400, (name, r.status_code, r.text[:120])
    r = _upload(b"x", "长" * 111 + ".md", h)
    assert r.status_code == 400 and "110" in r.json()["detail"], r.text[:120]


def test_utf8_and_pii_and_encrypted():
    """在册通用硬约束 UTF-8；拒收 3 加密 zip；拒收 5 成批个人信息（≥3 处）。"""
    h = _auth()
    r = _upload("你好".encode("gbk"), "gbk.txt", h)
    assert r.status_code == 400 and "UTF-8" in r.json()["detail"], r.text[:120]
    # 加密 zip：PK\x03\x04 + 版本(2) + 标志(2, bit0=1)
    enc_zip = b"PK\x03\x04" + b"\x14\x00" + b"\x01\x00" + b"REST"
    r = _upload(enc_zip, "locked.zip", h)
    assert r.status_code == 400 and "加密" in r.json()["detail"], r.text[:120]
    pii = "姓名,身份证号\n" + "\n".join(f"张{i},11010119900101{i:04d}" for i in range(3))
    r = _upload(pii.encode("utf-8"), "pii.csv", h)
    assert r.status_code == 400 and "脱敏" in r.json()["detail"], r.text[:120]


def test_get_by_id_owner_and_guard():
    h = _auth("useu1owner01")
    r = _upload(b"my own material", "own.md", h)
    uid = r.json()["data"]["upload_id"]
    g = client.get(f"/api/v1/use/upload/{uid}", headers=h)
    assert g.status_code == 200
    d = g.json()["data"]
    assert d["upload_id"] == uid and d["owner"] == "useu1owner01"
    # 他人 403
    h2 = _auth("useu1other01")
    g2 = client.get(f"/api/v1/use/upload/{uid}", headers=h2)
    assert g2.status_code == 403
    # 不存在 404 人话
    g3 = client.get("/api/v1/use/upload/UPL-NOTEXIST0001", headers=h)
    assert g3.status_code == 404 and "没有这件" in g3.json()["detail"]


def test_record_and_disk_persisted():
    body = b"persist me"
    r = _upload(body, "p.txt", _auth("useu1persist01"))
    d = r.json()["data"]
    with get_sessionmaker().begin() as s:
        rec = s.get(M.UploadRecord, d["upload_id"])
        assert rec is not None
        assert rec.username == "useu1persist01"
        assert rec.sha256_16 == d["sha256_16"]
        assert rec.nca_ref
    import upload_ops as U
    assert (U.UPLOAD_DIR / f"{d['sha256_16']}.txt").read_bytes() == body  # 哈希前段文件名
