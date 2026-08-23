"""tdca_core_go · Python ↔ Go 核心引擎桥接（融入方案 I-2）

通过子进程调用 tdcad CLI（接口熵=0，JSON 同构）——Python 侧零改动接入 Go 核心。

对接点:
  - enforce_check: 准入门禁（替代/增强 tdca-toolchain `_check_auth` 强类型校验）
  - nca_append / nca_verify: NCA 存证链（通知机 NCA-Lite → Go 链）
  - nsfl_eval: 熔断判定（通知机 NSFL 触发 → Go 分级熔断）

制度锚定: DCD-CORE-GO-001 ｜ 融入方案 I-2 ｜ ID35（制度-技术同构）
数据纪律: 桥接输入/输出 JSON 与 Go 100% 兼容；SIMULATED 标注（ID92）
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class TdcadBridge:
    """tdcad CLI 桥接器。"""

    def __init__(self, tdcad_path: Optional[str] = None):
        """tdcad_path: tdcad 可执行文件路径；缺省自动探测（go run / 构建产物）。"""
        self._bin = tdcad_path or self._find_binary()

    @staticmethod
    def _find_binary() -> str:
        """探测 tdcad：1) 环境变量 2) 本地构建产物 3) PATH。"""
        env = os.environ.get("TDCAD_BIN")
        if env:
            return env
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "tdcad.exe")
        if os.path.exists(local):
            return local
        on_path = shutil.which("tdcad")
        if on_path:
            return on_path
        return "tdcad"  # 让子进程解析（go run 场景由调用方设置 TDCAD_BIN）

    # ---- 执行 ----

    def _run(self, args: List[str],
             stdin_data: Optional[bytes] = None) -> Dict[str, Any]:
        """执行 tdcad 并解析 JSON 输出。

        注: tdcad 对 REJECT/BLOCK/FUSED 返回非零退出码（判定语义），
            此处解析 stdout 结果返回——仅 JSON 解析失败/进程异常才抛错。
        """
        proc = subprocess.run(
            [self._bin] + args,
            input=stdin_data,
            capture_output=True, text=True, timeout=30,
        )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(
                f"tdcad {args[0]} failed: {proc.stderr.strip() or proc.stdout.strip()}")

    # ---- enforce ----

    def enforce_check(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """准入门禁校验（card → PASS/REJECT/BLOCK）。"""
        path = self._temp_json(card)
        try:
            return self._run(["enforce", "check", path])
        finally:
            self._cleanup(path)

    # ---- nca ----

    def nca_append(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """NCA 链追加（返回 head/count）。"""
        path = self._temp_json(record)
        try:
            return self._run(["nca", "append", path])
        finally:
            self._cleanup(path)

    def nca_verify(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """NCA 链验证（返回 verify/count）。"""
        path = self._temp_json(records)
        try:
            return self._run(["nca", "verify", path])
        finally:
            self._cleanup(path)

    # ---- nsfl ----

    def nsfl_eval(self, trigger_id: str, signal: str) -> Dict[str, Any]:
        """熔断判定（signal → ALLOW/WARN/BLOCK/FUSED）。

        注: BLOCK/FUSED 时 tdcad 返回非零退出码——桥接解析 stdout 结果并返回
            （判定结果非执行错误），仅 JSON 解析失败/进程异常才抛 RuntimeError。
        """
        proc = subprocess.run(
            [self._bin, "nsfl", "eval", trigger_id, signal],
            capture_output=True, text=True, timeout=30,
        )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(
                f"tdcad nsfl eval failed: {proc.stderr.strip() or proc.stdout.strip()}")

    # ---- 工具 ----

    @staticmethod
    def _temp_json(data: Any) -> str:
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    @staticmethod
    def _cleanup(path: str) -> None:
        try:
            os.remove(path)
        except OSError:
            pass
