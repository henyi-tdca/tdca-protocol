"""paperclip_nca · Paperclip 编排协议 → TDCA 协作语义编译适配器（DCD-PAPERCLIP-COMPOUND-001 M1a）

Paperclip（paperclipai/paperclip，MIT）是多智能体编排平台——组织隐喻：
agents 分工/协作/调度如组织成员。与 TDCA 制度骨架同构（协作即调用 ID21）。

M1a 功能:
  - parse_orchestration: 解析 Paperclip 编排协议（tasks/agents/dependencies）
  - compile_to_collab: 编排 → TDCA 协作语义（协作即调用 ID21）
  - build_collab_nca: 每次编排调用落 NCA 存证
  - orchestration_summary: 编排结构摘要（agents/tasks/依赖数）

制度锚定: ID21（协作即调用）/ BIDIR-001（协议编译层贡献）/ ID92
NSFL-Declaration:
  - 不修改 Paperclip 核心（仓库优先 + 双向赋能纪律）
  - 合成/演示数据标注 SIMULATED（ID92）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CollabCall:
    """TDCA 协作语义调用（ID21 协作即调用）。"""
    task_id: str
    agent: str
    depends_on: List[str]       # 依赖的 task_id（编排边）
    action: str                 # 协作动作
    status: str
    call_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent": self.agent,
            "depends_on": self.depends_on,
            "action": self.action,
            "status": self.status,
            "call_hash": self.call_hash,
        }


@dataclass(frozen=True)
class CollabNca:
    """编排调用 NCA 存证记录。"""
    nca_id: str
    task_id: str
    agent: str
    operation_type: str          # Collab-Invoke
    timestamp: str
    scope: str
    collab: dict
    provenance: str

    def to_dict(self) -> dict:
        return {
            "NCA-ID": self.nca_id,
            "Task-ID": self.task_id,
            "Agent": self.agent,
            "Operation-Type": self.operation_type,
            "Timestamp": self.timestamp,
            "Scope": self.scope,
            "Collab-Call": self.collab,
            "Provenance": self.provenance,
        }


class PaperclipAdapter:
    """Paperclip 编排 → TDCA 协作语义编译适配器（M1a）。"""

    def __init__(self, provenance: str = "SIMULATED"):
        self._provenance = provenance

    # ---- 解析 ----

    def parse_orchestration(self, raw: str) -> dict:
        """解析 Paperclip 编排协议 JSON。"""
        if not raw or not raw.strip():
            raise ValueError("[NSFL-TRIGGER] 空编排协议")
        data = json.loads(raw)
        if "tasks" not in data or not isinstance(data["tasks"], list):
            raise ValueError("[NSFL-TRIGGER] 编排协议缺 tasks 数组")
        for t in data["tasks"]:
            if "task_id" not in t or "agent" not in t:
                raise ValueError("[NSFL-TRIGGER] 任务缺 task_id/agent")
        return data

    # ---- 编译（M1a 核心：编排 → 协作语义 ID21）----

    def compile_to_collab(self, orchestration: dict) -> List[CollabCall]:
        """编排协议 → TDCA 协作语义调用列表（ID21 协作即调用）。"""
        tasks = orchestration["tasks"]
        calls = []
        for t in tasks:
            depends = t.get("depends_on", [])
            action = t.get("action", "execute")
            status = t.get("status", "scheduled")
            digest = json.dumps({
                "task_id": t["task_id"], "agent": t["agent"],
                "depends_on": depends, "action": action, "status": status,
            }, ensure_ascii=False, sort_keys=True)
            call_hash = hashlib.sha256(digest.encode("utf-8")).hexdigest()
            calls.append(CollabCall(
                task_id=t["task_id"], agent=t["agent"],
                depends_on=list(depends), action=action, status=status,
                call_hash=call_hash,
            ))
        return calls

    # ---- NCA 存证（M1b 存证转换）----

    def build_collab_ncas(self, calls: List[CollabCall],
                          orchestration_id: str = "orch-1") -> List[CollabNca]:
        """协作调用 → NCA 存证链（每次编排调用落链）。"""
        ts = datetime.now(timezone.utc)
        date_str = ts.strftime("%Y%m%d")
        ncas = []
        for i, c in enumerate(calls, start=1):
            ncas.append(CollabNca(
                nca_id=f"NCA-PAPERCLIP-{date_str}-{i:03d}",
                task_id=c.task_id, agent=c.agent,
                operation_type="Collab-Invoke",
                timestamp=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                scope=f"Paperclip 编排协作调用存证（ID21 协作即调用，{orchestration_id}）",
                collab=c.to_dict(),
                provenance=self._provenance,
            ))
        return ncas

    # ---- 摘要 ----

    def orchestration_summary(self, orchestration: dict) -> dict:
        """编排结构摘要（agents/tasks/依赖数）。"""
        tasks = orchestration["tasks"]
        agents = sorted({t["agent"] for t in tasks})
        dep_count = sum(len(t.get("depends_on", [])) for t in tasks)
        return {
            "orchestration_id": orchestration.get("orchestration_id", "unnamed"),
            "agents": agents,
            "task_count": len(tasks),
            "dependency_count": dep_count,
            "acyclic": self._is_acyclic(tasks),
        }

    @staticmethod
    def _is_acyclic(tasks: List[dict]) -> bool:
        """编排依赖无环（DAG 校验——协作流合法性）。"""
        by_id = {t["task_id"]: t for t in tasks}
        visited = {}

        def dfs(tid: str) -> bool:
            if visited.get(tid) == 1:
                return False          # 环
            if visited.get(tid) == 2:
                return True
            visited[tid] = 1
            for dep in by_id.get(tid, {}).get("depends_on", []):
                if dep in by_id and not dfs(dep):
                    return False
            visited[tid] = 2
            return True

        return all(t["task_id"] not in by_id or dfs(t["task_id"]) for t in tasks)
