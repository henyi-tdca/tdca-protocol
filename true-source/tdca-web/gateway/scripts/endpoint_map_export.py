# -*- coding: utf-8 -*-
"""ENDPOINT-MAP-001 端点对照表自动生成器。

口径（TDCA-HANDOFF-EXEC-L1SI214-ENDPOINT-MAP-001）：
  - 唯一真源＝路由声明（app 路由反射）；⛔ 人工手抄、⛔ 双源维护；
  - 覆盖全部 /api/v1/* 端点（框架自动加的 HEAD/OPTIONS 不入表）；
  - 每条 {path, methods, 鉴权要求, 一句话用途}；
  - 鉴权要求机推（⛔ 猜填）：端内会话门（_require_session_user/_subject_gate/
    _require_ops_admin/_require_founder/validate_session）→「会话 TDCA-SES」；
    否则中间件凭据闸（/api/v1/governance 前缀或写方法）→「证书 TDCA-CRT」（会话亦通）；
    其余 →「匿名」。登录/登记豁免面（_AUTH_EXEMPT）→「匿名」；
  - 一句话用途取端点 docstring 首行并机洗内部编号（GSEQ/L1SI/TDCA-E/批 N），
    洗空则「待补」（照 S-2'，⛔ 猜填）；
  - 零时间戳字段：连跑两次逐字节一致（E-4）。

用法（网关机venv）：
  python3 scripts/endpoint_map_export.py            # 生成并对账，写落对照表.json
  python3 scripts/endpoint_map_export.py --check    # 只对账（CI 门禁：不一致即退出 1）
"""
from __future__ import annotations

import argparse
import inspect
import json
import re
import sys
from pathlib import Path

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = GATEWAY_ROOT.parents[1] / "tdca-site"
MAP_PATH = SITE_ROOT / "docs" / "site" / "endpoint-map" / "端点对照表.json"

AUTH_VOCAB = ("匿名", "会话 TDCA-SES", "证书 TDCA-CRT")

# 端内会话门：命中任一即「会话 TDCA-SES」（均以 _require_session_user 为根，机读源码判定）
_SESSION_TOKENS = ("_require_session_user", "_subject_gate",
                   "_require_ops_admin", "_require_founder", "validate_session")
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_FRAMEWORK_METHODS = {"HEAD", "OPTIONS"}

# 公开面机洗：内部编号与批次标记（E-5——⛔ 内部编号入公开表）
_INTERNAL_PAT = re.compile(
    r"(GSEQ-\d+|L1SI\d+(?:-[A-Z0-9]+)*|TDCA-E-[A-Z0-9-]+|批\s*\d+|"
    r"(?<![A-Za-z])B-\d{1,2}(?![-\d]))")


def _auth_modules():
    sys.path.insert(0, str(GATEWAY_ROOT))
    import auth  # noqa: E402
    return auth


def sanitize_purpose(line: str) -> str:
    """机洗内部编号；洗空则「待补」（照 S-2'，⛔ 猜填）。"""
    s = _INTERNAL_PAT.sub("", line or "")
    s = re.sub(r"\s+", " ", s).strip(" —-·｜|，,。；;：:")
    return s if s else "待补"


def derive_auth(path: str, methods: list, src: str, auth) -> str:
    """鉴权要求机推（⛔ 猜填）：会话门 → 中间件凭据闸 → 匿名。"""
    if path in tuple(auth._AUTH_EXEMPT):
        return "匿名"
    if any(t in src for t in _SESSION_TOKENS):
        return "会话 TDCA-SES"
    sensitive = path.startswith(tuple(auth._SENSITIVE_PREFIXES))
    if sensitive or any(m not in _SAFE_METHODS for m in methods):
        return "证书 TDCA-CRT"
    return "匿名"


def _iter_api_routes(container):
    """递归展平 APIRoute：在役网关经 _IncludedRouter（original_router）懒挂路由，
    须 unwrap 后取真实路由声明（S-1' 反射可达，不停手）。"""
    for route in getattr(container, "routes", []):
        from fastapi.routing import APIRoute
        if isinstance(route, APIRoute):
            yield route
        elif hasattr(route, "original_router"):
            yield from _iter_api_routes(route.original_router)
        elif hasattr(route, "routes"):
            yield from _iter_api_routes(route)


def collect_routes(app) -> list:
    """路由反射：全部 /api/v1/* 端点 → 对照条目（按 path+methods 排序，字节稳定）。"""
    auth = _auth_modules()
    seen = set()
    out = []
    for route in _iter_api_routes(app):
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not methods or not path.startswith("/api/v1"):
            continue
        # 内部置旗面（AUDIT-ANCHOR-001）：仅 TDCA_AUDIT_ANCHOR_INTERNAL=1 挂载，生产
        # 实例路由不存在（404 非 401，不泄露存在性）——不入公开对照表（E-5 口径）
        if path.startswith("/api/v1/audit/"):
            continue
        methods = sorted(m for m in methods if m not in _FRAMEWORK_METHODS)
        if not methods:
            continue
        key = (path, tuple(methods))
        if key in seen:
            continue
        seen.add(key)
        fn = route.endpoint
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            src = ""
        doc_lines = (inspect.getdoc(fn) or "").splitlines()
        purpose = sanitize_purpose(doc_lines[0].strip()) if doc_lines else "待补"
        out.append({
            "path": path,
            "methods": methods,
            "鉴权要求": derive_auth(path, methods, src, auth),
            "一句话用途": purpose,
        })
    out.sort(key=lambda e: (e["path"], ",".join(e["methods"])))
    return out


def render(endpoints: list) -> str:
    doc = {
        "meta": {
            "task": "endpoint-map-001",
            "generated_by": "tdca-web/gateway/scripts/endpoint_map_export.py"
                            "（路由反射·自动对账·⛔人工手抄）",
            "coverage": "/api/v1/*（框架自动 HEAD/OPTIONS 不入表；内部置旗面 "
                        "/api/v1/audit/* 仅 TDCA_AUDIT_ANCHOR_INTERNAL=1 挂载、生产路由"
                        "不存在，不入公开表——列入即泄露存在性）",
            "auth_derivation": "端内会话门(_require_session_user/_subject_gate/"
                               "_require_ops_admin/_require_founder/validate_session)"
                               "→会话 TDCA-SES；否则中间件凭据闸"
                               "(/api/v1/governance 前缀或写方法，TDCA-SES 会话"
                               "或 TDCA-CRT 静态令牌均可)→证书 TDCA-CRT；"
                               "其余(含 _AUTH_EXEMPT 登录/登记豁免面)→匿名",
            "purpose_source": "端点 docstring 首行机洗（内部编号 GSEQ/L1SI/TDCA-E/"
                              "批 N 机洗剔除；洗空标 待补，⛔ 猜填）",
            "note": "零时间戳：连跑两次逐字节一致（E-4）；CI 门禁断言"
                    "「路由声明端点集 == 本表端点集」（tests/test_endpoint_map_gate.py）",
        },
        "endpoints": endpoints,
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def load_map() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def endpoint_set(entries) -> set:
    return {(e["path"], tuple(e["methods"])) for e in entries}


def diff_against_map(app) -> tuple:
    """(only_in_routes, only_in_map)——两侧差集；皆空即一致。"""
    routes = endpoint_set(collect_routes(app))
    m = endpoint_set(load_map()["endpoints"])
    return sorted(routes - m), sorted(m - routes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="只对账不写入：不一致即退出 1（CI 门禁）")
    args = ap.parse_args()

    if str(GATEWAY_ROOT) not in sys.path:
        sys.path.insert(0, str(GATEWAY_ROOT))
    from app import app  # 惰性导入：--help 不拉应用
    endpoints = collect_routes(app)
    doc = render(endpoints)

    if args.check:
        m = load_map()
        routes_set = endpoint_set(endpoints)
        map_set = endpoint_set(m["endpoints"])
        if routes_set == map_set:
            print(f"ENDPOINT-MAP GATE PASS: {len(routes_set)} 端点一致")
            return 0
        print("ENDPOINT-MAP GATE FAIL: 路由声明与对照表不一致")
        for p, ms in sorted(routes_set - map_set):
            print(f"  只在路由声明: {','.join(ms)} {p}")
        for p, ms in sorted(map_set - routes_set):
            print(f"  只在对照表:   {','.join(ms)} {p}")
        return 1

    MAP_PATH.write_text(doc, encoding="utf-8")
    print(f"written: {MAP_PATH} ({len(endpoints)} endpoints)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
