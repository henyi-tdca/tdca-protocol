# -*- coding: utf-8 -*-
"""MCP 真实执行通道（M2 / #4）——S-Right 工具计划 → tdcad CLI

**动机（SRIGHT-001 §九-4）**：V1.1 的 MCP 桥接为 dry-run 计划态（`executed=false`）。
本模块给出**真实执行通道**：把计划中的四工具映射为 `tdcad` CLI 子命令（core-go 构建产物），
逐条执行并回传**真实** `rc/stdout`。

映射（接口熵=0，不新增协议）:
  enforce_check → `tdcad enforce check <card.json>`（AgentCard：protocol_version/scene_id/role/nsfl_boundary）
  nsfl_eval     → `tdcad nsfl eval <trigger> <signal>`（R1~R10；未知信号 fail-closed=BLOCK）
  nca_append    → `tdcad nca append <record.json>`（NcaRecord：prev_hash 须 = 链头 `sha256:genesis`）
  nca_verify    → `tdcad nca verify <records.json>`（数组→单记录链→Verify）

纪律:
  - **只执行无持久副作用子命令**：core-go CLI 每次新建内存态链/引擎（无落盘账本），
    故 `nca append` 不污染任何持久状态；本模块不执行 `mcp serve`（常驻服务，另议）
  - **未定位到构建产物即拒**（`CliTransportError`）——不虚报"已执行"
  - 判定语义仍以 S-Right / CLS 侧为准；本通道只负责"调得通、回得来"
  - `CliCallResult.simulated` 恒为 **False**（真实执行产物），与 dry-run 计划态区分

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

CORE_PROTOCOL_VERSION = "3.1.2"                       # core-go SupportedProtocol
CORE_SCENES = ("scene-phy-notification", "scene-collab")
CORE_ROLES = ("NM-Operator", "NM-Gov", "NM-Fin", "NM-Med")

CLI_TOOL_MAP = {
    "enforce_check": "enforce check <card.json>",
    "nsfl_eval": "nsfl eval <trigger> <signal>",
    "nca_append": "nca append <record.json>",
    "nca_verify": "nca verify <records.json>",
}


class CliTransportError(Exception):
    """CLI 通道纪律违例（未定位构建产物 / 计划非法）。"""


@dataclass
class CliCallResult:
    """单条 CLI 调用结果（真实 rc/stdout/stderr）。"""
    tool: str
    argv: List[str]
    rc: int
    stdout: Any
    stderr: str = ""
    ok: bool = False
    note: str = ""
    simulated: bool = False                           # 真实执行 ⇒ False

    def to_dict(self) -> Dict[str, Any]:
        return {"tool": self.tool, "argv": self.argv, "rc": self.rc, "ok": self.ok,
                "stdout": self.stdout, "stderr": self.stderr, "note": self.note,
                "simulated": False}


class CliTransport:
    """tdcad CLI 传输实现（`__call__(plan)` 与 `McpToolFaceAdapter.execute` 契约一致）。"""

    def __init__(self, executable: str = "tdcad", *, timeout: int = 15,
                 scene_map: Optional[Dict[str, str]] = None, role: str = "NM-Operator",
                 nsfl_boundary: Optional[List[str]] = None,
                 nsfl_signal_clean: str = "rate-limit"):
        self.executable = executable
        self.timeout = int(timeout)
        self.scene_map = dict(scene_map or {})
        self.role = role if role in CORE_ROLES else "NM-Operator"
        self.nsfl_boundary = list(nsfl_boundary or ["declared-boundary"])
        self.nsfl_signal_clean = nsfl_signal_clean   # R9：severity 1 → WARN（不熔断）

    # ---------- 定位与版本 ----------
    @staticmethod
    def locate(command: str = "tdcad") -> Optional[str]:
        """定位构建产物：以 PATH 解析为准（本包不假设本地目录布局）。未定位 → None。"""
        return shutil.which(command)

    def _exe(self) -> str:
        exe = self.locate(self.executable)
        if exe is None:
            raise CliTransportError(
                f"未定位到构建产物 {self.executable}（PATH 上未找到）——"
                "不得虚报已执行（须先经发布通道提供构建产物）")
        return exe

    def version(self) -> Dict[str, Any]:
        """`tdcad version`（只读；用于通道活体确认）。"""
        exe = self._exe()
        p = self._run(exe, ["version"])
        return {"executable": exe, "rc": p.returncode, "stdout": (p.stdout or "").strip(),
                "simulated": False}

    # ---------- 传输入口 ----------
    def __call__(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        results: List[CliCallResult] = []
        for call in plan.get("calls", []):
            tool = call.get("tool")
            params = call.get("params", {}) or {}
            if tool == "enforce_check":
                results.append(self._enforce_check(params))
            elif tool == "nsfl_eval":
                results.append(self._nsfl_eval(params))
            elif tool == "nca_append":
                results.append(self._nca_append(params))
            elif tool == "nca_verify":
                results.append(self._nca_verify(params))
            else:
                raise CliTransportError(f"未知工具（无 CLI 映射）：{tool!r}")
        return {"executed": True, "channel": "tdcad-cli", "transport": "stdio(subprocess)",
                "results": [r.to_dict() for r in results],
                "all_ok": all(r.ok for r in results),
                "executable": self._exe(), "simulated": False}

    # ---------- 四工具映射 ----------
    def _enforce_check(self, params: Dict[str, Any]) -> CliCallResult:
        card_in = dict(params.get("agent_card") or {})
        scene = params.get("scene") or ""
        card = {
            "agent_id": card_in.get("agent_id") or "",
            "protocol_version": CORE_PROTOCOL_VERSION,
            "scene_id": self.scene_map.get(scene, "scene-collab"),
            "role": self.role,
            "allowed_calls": ["tool-call"],
            "nsfl_boundary": self.nsfl_boundary,
        }
        path = self._write_json("agent_card", card)
        return self._invoke("enforce_check", ["enforce", "check", path],
                            ok_status="PASS", note=f"scene={scene}→{card['scene_id']}")

    def _nsfl_eval(self, params: Dict[str, Any]) -> CliCallResult:
        trigger = str(params.get("scene") or params.get("trigger") or "scene-default")
        signal = ("unauthorized-call" if params.get("declared_violation")
                  else self.nsfl_signal_clean)          # 未声明违规 → R9 WARN（不熔断）
        res = self._invoke("nsfl_eval", ["nsfl", "eval", trigger, signal])
        status = (res.stdout or {}).get("action", {}).get("status") if isinstance(res.stdout, dict) else None
        res.ok = (res.rc == 0 and not (res.stdout or {}).get("blocked", True))
        res.note = f"signal={signal} status={status}"
        return res

    def _nca_append(self, params: Dict[str, Any]) -> CliCallResult:
        content = params.get("content") or {}
        record = {
            "nca_id": str(content.get("nca_ref") or f"NCA-SRIGHT-{abs(hash(json.dumps(content, sort_keys=True))) % 10**8}"),
            "type": str(params.get("type") or "service"),
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "signer": "tdcad-cli-transport",
            "payload_ref": "FactHash_1",
            "prev_hash": "sha256:genesis",               # 单记录链（CLI 每次新建内存链）
            "nsfl": {"version": "V0.2", "triggered": False, "trigger_reason": None},
            "payload": content or {},
        }
        self._last_record = record
        path = self._write_json("nca_record", record)
        return self._invoke("nca_append", ["nca", "append", path], ok_status="appended")

    def _nca_verify(self, params: Dict[str, Any]) -> CliCallResult:
        records = params.get("records")
        if not records:
            records = [getattr(self, "_last_record", None) or {
                "nca_id": "NCA-SRIGHT-EMPTY", "type": "service",
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signer": "tdcad-cli-transport", "payload_ref": "FactHash_1",
                "prev_hash": "sha256:genesis",
                "nsfl": {"version": "V0.2", "triggered": False, "trigger_reason": None},
                "payload": {},
            }]
        path = self._write_json("nca_records", records)
        res = self._invoke("nca_verify", ["nca", "verify", path])
        res.ok = res.rc == 0 and bool((res.stdout or {}).get("verify", False))
        res.note = f"verify={(res.stdout or {}).get('verify')}"
        return res

    # ---------- 底层 ----------
    def _run(self, exe: str, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run([exe] + args, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=self.timeout)

    def _invoke(self, tool: str, args: List[str], ok_status: Optional[str] = None,
                note: str = "") -> CliCallResult:
        exe = self._exe()
        try:
            p = self._run(exe, args)
        except subprocess.TimeoutExpired:
            return CliCallResult(tool, [exe] + args, rc=-1, stdout={}, stderr="timeout",
                                 ok=False, note=note or f"超时（{self.timeout}s）")
        parsed: Any = (p.stdout or "").strip()
        if parsed.startswith("{") or parsed.startswith("["):
            try:
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                pass
        ok = p.returncode == 0
        if ok_status is not None and isinstance(parsed, dict):
            ok = ok and (parsed.get("status") == ok_status)
        return CliCallResult(tool, [exe] + args, rc=p.returncode, stdout=parsed,
                             stderr=(p.stderr or "").strip(), ok=ok, note=note)

    @staticmethod
    def _write_json(prefix: str, obj: Any) -> str:
        d = tempfile.mkdtemp(prefix="tdca_cli_")
        path = os.path.join(d, f"{prefix}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        return path
