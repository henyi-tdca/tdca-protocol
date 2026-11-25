# -*- coding: utf-8 -*-
"""K1FIX-001 验证：本地空库(ORM create_all，同既有套件路径)＋建 sim 两机器主体，
复跑 590 八例。注：迁移链 0001→0029 不 reproduces nca_chain M1″五列
（rec_hash/prev_hash/anchor_ok/detached/detach_reason 系生产带外补齐），
故功能复跑走与既有测试一致的 create_all 路径；迁移面由 test_migrations.py 另测。"""
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import tempfile

d = tempfile.mkdtemp()
db = os.path.join(d, "k1.db")
os.environ["DATABASE_URL"] = "sqlite:///" + db

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_engine
from db.models import Base
Base.metadata.create_all(get_engine())

# 造甲/乙两机器主体（external）
now = "2026-11-25T09:40:00+00:00"
con = sqlite3.connect(db)
for u in ("sim-sl1-0481", "sim-sl1-0482"):
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", f"Sim{u[-4:]}Xkpass1".encode(), salt, 120000)
    con.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?)",
                (u, h.hex(), salt.hex(), 120000, "viewer", "simulated", now))
    con.execute("INSERT INTO user_identities VALUES(?,?,?,?,?,?,?,?)",
                (u, "external", json.dumps({"name": u, "kind": "sim-agent", "batch": "K1FIX"}),
                 "TDCA-OWNER-CONTRACT-AUTH-SIM-K1FIX", None, "simulated", now, now))
con.commit()
con.close()

from fastapi.testclient import TestClient
from app import app
client = TestClient(app)

def login(u):
    r = client.post("/api/v1/auth/login",
                    json={"username": u, "password": f"Sim{u[-4:]}Xkpass1"})
    assert r.status_code == 200, r.text
    return r.json()["data"]["token"]

JIA, YI = "sim-sl1-0481", "sim-sl1-0482"
t_jia, t_yi = login(JIA), login(YI)
fails = []

def check(tag, cond, actual):
    print(("PASS" if cond else "FAIL"), tag, "->", actual)
    if not cond:
        fails.append(tag)

# G-2
r = client.post("/api/v1/cluster/grant/register",
    headers={"Authorization": t_jia},
    json={"subject_agent": "sim-sl1-0485", "scene_constraint": "K1FIX G-2a jia posing yi",
          "asset_order": 2, "full_composition": True, "legal_signer": YI,
          "signature": "SIMSIGK1G2A000000000001"})
check("G-2a 甲以乙legal_signer登记⟹403", r.status_code == 403, r.status_code)
r = client.post("/api/v1/cluster/grant/register",
    headers={"Authorization": t_yi},
    json={"subject_agent": "sim-sl1-0486", "scene_constraint": "K1FIX G-2b yi self",
          "asset_order": 2, "full_composition": True, "legal_signer": YI,
          "signature": "SIMSIGK1G2B000000000001"})
check("G-2b 乙本人登记⟹201", r.status_code == 201, r.status_code)
g2 = r.json()["data"]["grant_id"]

# G-3
r = client.post("/api/v1/cluster/grant/subgrant",
    headers={"Authorization": t_jia},
    json={"parent_grant_id": g2, "subject_agent": "sim-sl1-0487",
          "scene_constraint": "K1FIX G-3a jia on yi parent", "asset_order": 2,
          "full_composition": True, "legal_signer": JIA, "signature": "SIMSIGK1G3A000000000001"})
check("G-3a 甲对乙上级件转授⟹403", r.status_code == 403, r.status_code)
r = client.post("/api/v1/cluster/grant/subgrant",
    headers={"Authorization": t_yi},
    json={"parent_grant_id": g2, "subject_agent": "sim-sl1-0488",
          "scene_constraint": "K1FIX G-3b yi self subgrant", "asset_order": 2,
          "full_composition": True, "legal_signer": YI, "signature": "SIMSIGK1G3B000000000001"})
check("G-3b 乙本人转授⟹201", r.status_code == 201, r.status_code)
g3 = r.json()["data"]["grant_id"]

# G-4
r = client.post("/api/v1/cluster/grant/revoke",
    headers={"Authorization": t_jia}, json={"grant_id": g3})
check("G-4a 甲撤乙授权⟹403", r.status_code == 403, r.status_code)
r = client.post("/api/v1/cluster/grant/revoke",
    headers={"Authorization": t_yi}, json={"grant_id": g3})
check("G-4b 乙本人撤授权⟹200", r.status_code == 200, r.status_code)

# 绑定行核验
con = sqlite3.connect(db)
rows = con.execute("SELECT subject_username,role,object_ref,ref_value,binding_state FROM subject_bindings ORDER BY id").fetchall()
con.close()
print("\nbindings:")
for r in rows:
    print(" ", r)
print("\nSUMMARY:", "ALL PASS" if not fails else f"fails={fails}")
sys.exit(1 if fails else 0)
