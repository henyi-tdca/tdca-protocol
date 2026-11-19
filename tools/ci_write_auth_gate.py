# -*- coding: utf-8 -*-
"""
ci_write_auth_gate —— AUTHFOUR-001（UNIFYAUTH-001 步三）写端点统一鉴权硬闸
＋ GATEEXPAND-001/002 覆盖扩面（api_v1.py 纳入·比对键三列化·拒绕桩单列）。

闸规（fail-closed）：true-source/tdca-web/gateway/ 内 *_ops.py 与 api_v1.py
全部常规写端点（@router.post/put/patch/delete）须挂 require_write_privilege
（四档统一写鉴权依赖），否则其「文件前缀＋方法＋全路径」必须逐条命中
gateway/write_auth_whitelist.py（⛔禁整族通配；死条目亦红）。

GATEEXPAND-002 增列（依 TDCA-RULING-L1SI222-GATECOUNT-001）：
- 比对键三列化：(文件前缀, method, 全路径) —— 五文件重名实证：
  agent_channel_ops/authorization_ops/ownership_ops/toolshelf_ops 各持
  "/register"，api_v1 持 "/auth/register"，无文件前缀无法区分。
- 拒绕桩单列：@router.api_route(..., methods=...) 形态之写方法拒绝桩
  （现册＝library_ops.py 两枚 ANON-READ-001 写守卫，fail-closed 已覆盖）
  ⛔计入常规写端点、⛔须挂依赖、⛔入白名单；闸须识别该形态并单独计数上报。
  护栏：拒绕桩函数体必须含 raise（确属拒绝桩）；若以 api_route 新登记真实
  写端点（无 raise）⟹ 打红，须走常规挂依赖/白名单路径。
- 三数分列：常规写端点 / 拒绕桩 / 合计面（⛔混计）。

基数（GATECOUNT-001 裁定）：常规 85（*_ops.py 69 ＋ api_v1.py 16）；
拒绕桩 2；合计面 87。挂依赖 48 ＋ 白名单 37（21＋新增 10）＋ 本次挂依赖 6 ＝ 85。
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
# GATEEXPAND-001/002：覆盖范围扩至 api_v1.py（非 ops 写端点纳入）
SCAN_FILES = ("api_v1.py",)


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


def _module_const(tree: ast.Module, name: str):
    """取模块级常量（如 library_ops._WRITE_METHODS）之字面量值；取不到 None。"""
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id == name and isinstance(
                node.value, (ast.Constant, ast.Tuple, ast.List)
            ):
                try:
                    return ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    return None
    return None


def _api_route_methods(tree: ast.Module, dec: ast.Call):
    """解析 @router.api_route(..., methods=...) 之方法集（常量/模块级元组）。"""
    for kw in dec.keywords:
        if kw.arg != "methods":
            continue
        v = kw.value
        if isinstance(v, ast.Constant):
            return {str(v.value)}
        if isinstance(v, (ast.Tuple, ast.List)):
            try:
                return {str(x) for x in ast.literal_eval(v)}
            except (ValueError, TypeError):
                return set()
        if isinstance(v, ast.Name):
            got = _module_const(tree, v.id)
            if isinstance(got, str):
                return {got}
            if isinstance(got, (tuple, list)):
                return {str(x) for x in got}
        return set()
    return set()


def _func_has_raise(tree: ast.Module, fn) -> bool:
    """拒绕桩护栏：函数体含 raise，或其调用的本文件模块级函数（一层）含 raise
    ——library_ops.py 两枚桩经 _write_guard 抛 403/405，护栏须能解析此形态。"""
    if any(isinstance(sub, ast.Raise) for sub in ast.walk(fn)):
        return True
    local = {
        n.name: n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
            callee = local.get(sub.func.id)
            if callee is not None and any(
                isinstance(s2, ast.Raise) for s2 in ast.walk(callee)
            ):
                return True
    return False


def _route_paths(tree: ast.Module) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str, tuple[str, ...]]]]:
    """返回 (常规写路由, 拒绕桩)。

    常规：[(method, full_path, func_name)] —— @router.post/put/patch/delete。
    拒绕桩：[(full_path, func_name, methods)] —— @router.api_route 写方法形态，
    按「枚」计数（GATECOUNT-001：library_ops.py 两枚），methods 为覆盖写方法集。
    """
    prefix = _router_prefix(tree)
    regular: list[tuple[str, str, str]] = []
    stubs: dict[tuple[str, str], tuple[str, str, set[str]]] = {}
    for node in ast.walk(tree):
        fn = node if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else None
        if fn is None:
            continue
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "router"):
                continue
            if not dec.args or not isinstance(dec.args[0], ast.Constant):
                continue
            path = str(dec.args[0].value)
            attr = dec.func.attr.lower()
            if attr in WRITE_METHODS:
                regular.append((attr.upper(), prefix + path, fn.name))
            elif attr == "api_route":
                methods = {m.lower() for m in _api_route_methods(tree, dec)}
                hit = methods & set(WRITE_METHODS)
                if not hit:
                    continue
                key = (prefix + path, fn.name)
                if key not in stubs:
                    stubs[key] = (prefix + path, fn.name, set())
                stubs[key][2].update(hit)
                if not _func_has_raise(tree, fn):
                    stubs[key] = (prefix + path, fn.name, stubs[key][2] | {"__NO_RAISE__"})
    out = [(p, f, tuple(sorted(m))) for (p, f, m) in stubs.values()]
    return regular, out


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
    # 比对键三列化（GATEEXPAND-002）：(文件前缀, method, 全路径)
    white = {(f, m, p) for (f, m, p, _u, _r) in WL.WHITELIST}

    reds: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    stubs_seen: list[tuple[str, str, str]] = []
    total = conv = wl_hit = 0
    files = sorted(
        f for f in os.listdir(GATEWAY_DIR)
        if f.endswith("_ops.py") or f in SCAN_FILES
    )
    for fn in files:
        stem = fn[:-3]  # 文件前缀
        p = os.path.join(GATEWAY_DIR, fn)
        try:
            tree = ast.parse(io.open(p, encoding="utf-8").read())
        except SyntaxError as exc:
            reds.append(f"{fn}: 语法错误 {exc}")
            continue
        regular, stubs = _route_paths(tree)
        for meth, full, func in regular:
            total += 1
            seen.add((stem, meth, full))
            if _has_write_privilege(tree, func):
                conv += 1
                continue
            if (stem, meth, full) in white:
                wl_hit += 1
                continue
            reds.append(f"{fn} {meth} {full} -> {func}：未挂依赖且不在白名单")
        for full, func, methods in stubs:
            stubs_seen.append((stem, full, func, methods))
            # 护栏：api_route 写形态必须确为拒绝桩（函数体/一层内联 helper 含 raise）
            if "__NO_RAISE__" in methods:
                reds.append(
                    f"{fn} {full} -> {func}：api_route 写方法无 raise，"
                    "非拒绝桩，须走常规挂依赖/白名单路径"
                )
    stale = sorted(white - seen)
    for (f, m, pth) in stale:
        reds.append(f"白名单死条目：{f} {m} {pth}（不对应任何在册常规写端点）")

    print(f"[write-auth-gate] 常规写端点 {total}：挂依赖 {conv}，白名单 {wl_hit}")
    print(f"[write-auth-gate] 拒绕桩·已覆盖（fail-closed）{len(stubs_seen)} 枚：")
    for (f, pth, func, methods) in stubs_seen:
        print(f"  - {f} {pth} -> {func}（{','.join(m.upper() for m in methods if m != '__NO_RAISE__')}）")
    print(f"[write-auth-gate] 合计面 {total + len(stubs_seen)}（常规 {total}＋拒绕桩 {len(stubs_seen)}）")
    if reds:
        print(f"[write-auth-gate] RED {len(reds)} 条：")
        for r in reds:
            print("  -", r)
        return 1
    print("[write-auth-gate] GREEN：零红")
    return 0


if __name__ == "__main__":
    sys.exit(main())
