# -*- coding: utf-8 -*-
"""国标报送包（批量导出）——GB/Z 185.4 智能体描述 + 185.7 工具属性描述（M2 / #8）

用途:
  - 将**多个工具描述与多个智能体描述**一次性导出为「报送包」：逐件 JSON + `manifest.json` 清单
  - 逐件过 `validate_gbz` 校验（**fail-closed：任一件不合法则整包不产出**）
  - `verify_bundle` 回验（重算逐件 sha256 + 计数 + 清单自洽）
  - 报文形态：`to_tool_sync_list`（185.7 §6.2 工具同步列表 `toolSyncList`）/ `to_tool_request`（`toolRequestList`）

纪律:
  - 文件名净化（防路径注入）；**只写调用方指定的 `out_dir`**，不触碰其它路径
  - manifest 自带 `x-tdca-simulated`（ 模拟态标注）与国标格式声明
  - 内部制度属性沿用 `x-tdca-*` 前缀（前缀隔离，不破坏国标格式规范性）
  - 时间基线 +08

用法:
    res = make_bundle([("tool", tool_obj), ("agent", agent_obj)], bundle_id="B-001",
                      out_dir=..., write=True)
    assert res["valid"];  assert verify_bundle(out_dir)["valid"]

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:                                        # 包内导入（import national_format.gbz_bundle）
    from .gbz_format import (X_PREFIX, GbzFormatError, validate_gbz)
except ImportError:                         # 顶层导入（sys.path 指向模块目录，测试风格）
    from gbz_format import (X_PREFIX, GbzFormatError, validate_gbz)

GBZ_BUNDLE_FORMAT = "GB/Z 185.4+185.7"
KINDS = ("tool", "agent")
_CST = timezone(timedelta(hours=8))


class GbzBundleError(Exception):
    """报送包构造/回验纪律违例。"""


def _now_iso() -> str:
    return datetime.now(_CST).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _sha256_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _canonical(obj: Any) -> bytes:
    """规范序列化（排序键、UTF-8、无 ASCII 转义）——保证哈希可复算。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sanitize_name(name: str, maxlen: int = 64) -> str:
    """文件名净化：仅保留 [A-Za-z0-9._-]，防路径注入（`..`/分隔符/驱动符一律剔除）。"""
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(name))[:maxlen].strip("._")
    return safe or "item"


def _entry_id(kind: str, obj: Dict[str, Any]) -> str:
    if kind == "tool":
        return str(obj.get("toolId") or "")
    if kind == "agent":
        return str(obj.get("agentId") or "")
    raise GbzBundleError(f"未知 kind: {kind}")


def make_bundle(items: Iterable[Tuple[str, Dict[str, Any]]], *, bundle_id: str,
                generated_at: Optional[str] = None, out_dir: Optional[str] = None,
                write: bool = False, profile: str = "national") -> Dict[str, Any]:
    """构造国标报送包（逐件校验 + 清单 + 可选落盘，fail-closed）。

    目标函数: 多工具/多智能体 → 可校验、可回验的报送包（含清单与逐件摘要）
    约束矩阵: ① bundle_id 必填 ② items 非空 ③ kind ∈ {tool,agent} ④ 同 kind 内 id 唯一且非空
              ⑤ 逐件过 validate_gbz(profile) ⑥ write=True 时 out_dir 必填且仅在其下创建 tools/agents
    先验分布: TDCA 国标格式规范 V1.1；原文 185.7 §6.2（同步列表报文形态）
    配置权边界: L2 报送格式层（不访问外部系统）
    预期分配: 返回 {"valid","errors","manifest","files"}；任一件不合法 → valid=False 且**不落盘**
    审计轨迹: manifest.generatedAt + 逐件 sha256（调用方登记 NCA）
    """
    errors: List[str] = []
    if not bundle_id or not isinstance(bundle_id, str):
        raise GbzBundleError("bundleId 必填")
    items = list(items or [])
    if not items:
        raise GbzBundleError("报送包不得为空（至少一件）")

    seen: set = set()
    entries: List[Dict[str, Any]] = []
    payloads: Dict[str, bytes] = {}
    counts = {k: 0 for k in KINDS}
    for kind, obj in items:
        if kind not in KINDS:
            errors.append(f"未知 kind: {kind}")
            continue
        if not isinstance(obj, dict):
            errors.append(f"[{kind}] 条目非 dict")
            continue
        eid = _entry_id(kind, obj)
        if not eid:
            errors.append(f"[{kind}] 缺少标识（toolId/agentId）")
            continue
        key = f"{kind}:{eid}"
        if key in seen:
            errors.append(f"重复条目: {key}")
            continue
        seen.add(key)
        try:
            v = validate_gbz(obj, kind=kind, profile=profile)
        except GbzFormatError as exc:
            errors.append(f"[{key}] 校验异常: {exc}")
            continue
        if not v["valid"]:
            bad = [k for k, ok in v["checks"].items() if not ok]
            errors.append(f"[{key}] 校验未过: {bad}")
        data = _canonical(obj)
        fname = f"{sanitize_name(eid)}.json"
        rel = f"{'tools' if kind == 'tool' else 'agents'}/{fname}"
        payloads[rel] = data
        counts[kind] += 1
        entries.append({"kind": kind, "id": eid, "file": rel,
                        "sha256": _sha256_bytes(data), "valid": v["valid"],
                        "checks": v["checks"]})

    manifest: Dict[str, Any] = {
        "bundleId": bundle_id,
        "generatedAt": generated_at or _now_iso(),
        "format": GBZ_BUNDLE_FORMAT,
        "profile": profile,
        "counts": counts,
        "entries": entries,
        f"{X_PREFIX}simulated": True,               # 模拟态标注
        f"{X_PREFIX}bundleOrigin": "tdca-national-format",
    }
    valid = (not errors) and all(e["valid"] for e in entries) and len(entries) == len(items)
    manifest["bundleSha256"] = _sha256_bytes(_canonical(entries))
    manifest["valid"] = valid

    written: Dict[str, str] = {}
    if write:
        if not out_dir:
            raise GbzBundleError("write=True 时必须提供 out_dir")
        if not valid:
            # fail-closed：任一件不合法则不落盘（保证产出的包必为全合法包）
            return {"valid": False, "errors": errors + ["fail-closed: 含不合法件，未落盘"],
                    "manifest": manifest, "files": {}}
        base = os.path.abspath(out_dir)
        os.makedirs(os.path.join(base, "tools"), exist_ok=True)
        os.makedirs(os.path.join(base, "agents"), exist_ok=True)
        for rel, data in payloads.items():
            p = os.path.join(base, *rel.split("/"))
            with open(p, "wb") as f:
                f.write(data)
            written[rel] = p
        mp = os.path.join(base, "manifest.json")
        with open(mp, "wb") as f:
            f.write(_canonical(manifest))
        written["manifest.json"] = mp

    return {"valid": valid, "errors": errors, "manifest": manifest, "files": written}


def verify_bundle(out_dir: str) -> Dict[str, Any]:
    """回验报送包：清单自洽 + 逐件 sha256 复算 + 计数一致。

    目标函数: 独立复核已落盘报送包（防篡改 / 防缺件 / 防清单漂移）
    约束矩阵: 只读；缺件、哈希不符、计数不符、清单缺失均记 errors
    先验分布: make_bundle 产出的 manifest.json
    配置权边界: L2 报送格式层（只读）
    预期分配: {"valid","errors","manifest"}
    审计轨迹: 调用方登记 NCA（复核即存证）
    """
    errors: List[str] = []
    mp = os.path.join(out_dir, "manifest.json")
    if not os.path.isfile(mp):
        return {"valid": False, "errors": ["缺少 manifest.json"], "manifest": {}}
    with open(mp, "rb") as f:
        manifest = json.loads(f.read().decode("utf-8"))
    entries = manifest.get("entries", [])
    counts = {"tool": 0, "agent": 0}
    for e in entries:
        p = os.path.join(out_dir, *str(e.get("file", "")).split("/"))
        if not os.path.isfile(p):
            errors.append(f"缺件: {e.get('file')}")
            continue
        with open(p, "rb") as f:
            got = _sha256_bytes(f.read())
        if got != e.get("sha256"):
            errors.append(f"哈希不符: {e.get('file')}")
        counts[e.get("kind")] = counts.get(e.get("kind"), 0) + 1
    if counts != manifest.get("counts"):
        errors.append(f"计数不符: 实测 {counts} ≠ 清单 {manifest.get('counts')}")
    if manifest.get("bundleSha256") != _sha256_bytes(_canonical(entries)):
        errors.append("清单 bundleSha256 不自洽（entries 已被改动）")
    return {"valid": not errors, "errors": errors, "manifest": manifest}


# ---------------------------------------------------------------- 185.7 §6.2 报文形态（出向）
def to_tool_sync_list(tools: Iterable[Dict[str, Any]], *, sync_type: int = 1,
                      timestamp: Optional[int] = None) -> Dict[str, Any]:
    """GB/Z 185.7 §6.2 工具同步报文：`syncType` + `timestamp` + `toolSyncList`。

    目标函数: 多工具 → 国标工具同步列表（1=完整列表，2=更新列表）
    约束矩阵: sync_type ∈ {1,2}；每件需携带 toolId（原文 6.2/附录 A.3.2）
    先验分布: 原文 §6.2 + 附录 A.3.2 示例
    配置权边界: L2 报送格式层
    预期分配: 报文 dict（toolSyncList 仅带国标字段，制度属性留于件内 x-tdca-*）
    审计轨迹: 调用方登记 NCA
    """
    if sync_type not in (1, 2):
        raise GbzBundleError("syncType 仅允许 1（完整列表）或 2（更新列表）")
    lst = []
    for t in tools or []:
        if not t.get("toolId"):
            raise GbzBundleError("toolSyncList 每件需含 toolId")
        item = {"toolId": t["toolId"]}
        for k in ("toolName", "toolVersion"):
            if k in t:
                item[k] = t[k]
        lst.append(item)
    return {"syncType": sync_type,
            "timestamp": int(timestamp if timestamp is not None else datetime.now(_CST).timestamp()),
            "toolSyncList": lst}


def to_tool_request(request_type: int = 1, *, timestamp: Optional[int] = None) -> Dict[str, Any]:
    """GB/Z 185.7 §6.2 工具请求报文：`requestType`（1=申请工具列表，2=更新工具列表）+ `timestamp`。"""
    if request_type not in (1, 2):
        raise GbzBundleError("requestType 仅允许 1（申请列表）或 2（更新列表）")
    return {"requestType": request_type,
            "timestamp": int(timestamp if timestamp is not None else datetime.now(_CST).timestamp())}
