# -*- coding: utf-8 -*-
"""035-A2 令 A-5 自检：三例响应全文正则扫（creator= / founder / 件名原值 .py/.md）。
造件名内嵌 creator=founder 且为 .py 的极端行，验证呈现层脱敏后四类命中全 0。"""
import json
import re

from fastapi.testclient import TestClient

import selfcheck_ops
from api_v1 import _nca_append
from app import app

client = TestClient(app)


def test_a2_desensitize_scan():
    ids = [_nca_append(f"A2_SCAN_{i}", "founder",
                       artifact_path=f"docs/x/agent:AGENT-NM-0{i}:creator=founder:"
                                     f"loaded=engine{i}.py")
           for i in range(3)]
    selfcheck_ops._PUBLIC_IDS.update(ids)   # 登记进测试清单（conftest 每例起空集）
    pats = {"creator=": r"creator=", "founder": r"founder",
            ".py 件名模式": r"\w+\.py", ".md 件名模式": r"\w+\.md"}
    totals = {k: 0 for k in pats}
    for i in ids:
        r = client.get(f"/api/v1/selfcheck/nca/{i}")
        assert r.status_code == 200
        rec = r.json()["data"]["record"]
        text = json.dumps(r.json(), ensure_ascii=False)
        print(i, rec["artifact_filename_sha256_16"], rec["artifact_ext"])
        for k, p in pats.items():
            totals[k] += len(re.findall(p, text))
    assert totals == {k: 0 for k in pats}, f"脱敏不净: {totals}"
