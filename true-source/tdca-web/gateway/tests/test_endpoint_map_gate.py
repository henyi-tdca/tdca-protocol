# -*- coding: utf-8 -*-
"""ENDPOINT-MAP-001 CI 门禁：路由声明端点集 == 对照表端点集（不一致即红）。

判据（令面 §三）：
  E-1 覆盖全：逐条 diff 为空；含本框新增 /me/tokens /me/permissions
    /me/privilege-admin/appoint|revoke /ownership/history；
  E-2 字段齐：每条含 path/methods/鉴权要求/一句话用途（鉴权取值限闭集）；
  E-5 公开面口径：对照表文本不含内部编号/凭据值/内网路径。
门禁有效性（E-3）由脚本 diff_against_map 在役实测（加临时端点→红→撤→绿），
回报附实录；本件为常驻断言，路由漂移即 CI 红。
"""
import json
import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import endpoint_map_export as em  # noqa: E402

from app import app  # noqa: E402

MAP_PATH = em.MAP_PATH

REQUIRED_NEW = (
    "/api/v1/me/tokens",
    "/api/v1/me/permissions",
    "/api/v1/me/privilege-admin/appoint",
    "/api/v1/me/privilege-admin/revoke",
    "/api/v1/ownership/history/{record_id}",  # 令面写作 /ownership/history，路由声明带参
)

_FORBIDDEN_PAT = re.compile(
    r"(GSEQ-\d+|L1SI\d+(?:-[A-Z0-9]+)*|TDCA-E-[A-Z0-9-]+|"
    r"TDCA-SES-[A-Za-z0-9]|TDCA-CRT-[A-Za-z0-9]|Bearer\s|"
    r"10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|/home/|/root/)")


def test_e1_route_set_matches_map():
    """E-1：路由声明端点集 == 对照表端点集（逐条 diff 为空）。"""
    only_routes, only_map = em.diff_against_map(app)
    assert not only_routes, f"只在路由声明: {only_routes}"
    assert not only_map, f"只在对照表: {only_map}"


def test_e1_required_new_endpoints_present():
    """E-1（本框新增端点在册）。"""
    m = em.load_map()
    paths = {e["path"] for e in m["endpoints"]}
    missing = [p for p in REQUIRED_NEW if p not in paths]
    assert not missing, f"对照表缺本框新增端点: {missing}"


def test_e2_fields_present():
    """E-2：每条四字段齐、非空；鉴权要求限闭集（⛔ 猜填）。"""
    m = em.load_map()
    assert m["endpoints"], "对照表为空"
    for e in m["endpoints"]:
        for k in ("path", "methods", "鉴权要求", "一句话用途"):
            assert e.get(k), f"{e.get('path')} 缺字段 {k}"
        assert e["鉴权要求"] in em.AUTH_VOCAB, \
            f"{e['path']} 鉴权取值越闭集: {e['鉴权要求']}"


def test_e5_public_surface_clean():
    """E-5：公开面口径——无内部编号、无凭据值、无内网路径。"""
    text = MAP_PATH.read_text(encoding="utf-8")
    hits = _FORBIDDEN_PAT.findall(text)
    assert not hits, f"公开面污染: {sorted(set(hits))[:5]}"


def test_e4_map_is_single_source():
    """仓内端点对照表唯一一份（⛔ 追加成双份）。"""
    siblings = list(MAP_PATH.parent.glob("端点对照表*.json"))
    assert siblings == [MAP_PATH], f"对照表多余副本: {siblings}"


def test_internal_flagged_surface_not_leaked():
    """内部置旗面（/api/v1/audit/*）不入公开对照表（AUDIT-ANCHOR-001：不泄露存在性）。"""
    m = em.load_map()
    leaked = [e["path"] for e in m["endpoints"]
              if e["path"].startswith("/api/v1/audit/")]
    assert not leaked, f"内部置旗面泄露: {leaked}"
