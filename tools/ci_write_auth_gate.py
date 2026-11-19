# -*- coding: utf-8 -*-
"""
ci_write_auth_gate —— AUTHFOUR-001（UNIFYAUTH-001 步三）写端点统一鉴权硬闸。

闸规（fail-closed）：
  true-source/tdca-web/gateway/*_ops.py 内全部 @router.post/put/patch/delete 端点，
  函数体必须引用 require_write_privilege（四档统一写鉴权依赖），
  否则其「方法＋全路径」必须逐条命中 gateway/write_auth_whitelist.py
  （⛔禁整族通配；白名单外之写端点＝打红阻断）。
  白名单条目若已不对应任何在册端点（死条目）＝打红（防登记漂移）。
  S-UA4：首跑大面积打红（>10）即停手核基线——本闸落地时基线＝零红
  （48 端点已挂依赖＋21 条白名单在册）。
用法：python3 tools/ci_write_auth_gate.py（仓库根为 cwd；exit 0 绿／exit 1 红）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import ast
import io
import os
import sys

GATEWAY_DIR = os.path.join("true-source", "tdca-web", "gateway")
WRITE_METHODS = ("post", "put", "patch", "delete")


def _router_prefix(tree: ast.Module) -> str:
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id == "router":
                call = node.value
                if isinstance(call, ast.Call):
                    for kw in call.keywords:
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                            return str(kw.value.value or "")
    return ""


def _route_paths(tree: ast.Module) -> list[tuple[str, str, str]]:
    """[(method, full_path, func_name)] —— 写路由全集。"""
    prefix = _router_prefix(tree)
    out = []
    for node in ast.walk(tree):
        fn = node if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else None
        if fn is None:
            continue
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "router"):
                continue
            meth = dec.func.attr.lower()
            if meth not in WRITE_METHODS:
                continue
            if not dec.args or not isinstance(dec.args[0], ast.Constant):
                continue
            path = str(dec.args[0].value)
            out.append((meth.upper(), prefix + path, fn.name))
    return out


def _has_write_privilege(tree: ast.Module, func_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and sub.id == "require_write_privilege":
                    return True
            return False
    return False


def main() -> int:
    sys.path.insert(0, os.path.abspath(GATEWAY_DIR))
    try:
        import write_auth_whitelist as WL  # noqa: N813
    except ImportError as exc:  # 白名单件缺失＝fail-closed
        print(f"[write-auth-gate] RED: 白名单件不可导入：{exc}")
        return 1
    white = {(m, p) for (m, p, _u, _r) in WL.WHITELIST}

    reds: list[str] = []
    seen: set[tuple[str, str]] = set()
    total = conv = 0
    files = sorted(f for f in os.listdir(GATEWAY_DIR) if f.endswith("_ops.py"))
    for fn in files:
        p = os.path.join(GATEWAY_DIR, fn)
        try:
            tree = ast.parse(io.open(p, encoding="utf-8").read())
        except SyntaxError as exc:
            reds.append(f"{fn}: 语法错误 {exc}")
            continue
        for meth, full, func in _route_paths(tree):
            total += 1
            seen.add((meth, full))
            if _has_write_privilege(tree, func):
                conv += 1
                continue
            if (meth, full) not in white:
                reds.append(f"{fn} {meth} {full} -> {func}：未挂依赖且不在白名单")
    stale = sorted(white - seen)
    for (m, pth) in stale:
        reds.append(f"白名单死条目：{m} {pth}（不对应任何在册写端点）")

    print(f"[write-auth-gate] 写端点合计 {total}：挂依赖 {conv}，白名单 {len(white)}")
    if reds:
        print(f"[write-auth-gate] RED {len(reds)} 条：")
        for r in reds:
            print("  -", r)
        return 1
    print("[write-auth-gate] GREEN：零红")
    return 0


if __name__ == "__main__":
    sys.exit(main())
