"""maka_nca · Maka Runtime Event Log → TDCA-NCA 格式转换器（DCD-MAKA-COMPOUND-001 M1a）

Maka 是 Apache 孵化器项目（apache/maka）——Runtime Event Log（append-only）:
  model / tool_call / tool_result / termination 事件记录。

制度契合: append-only log = 天然 NCA 载体（哈希链同构，ID91 自反化合点）——
TDCA 只需标准化格式而非发明。

M1a 功能:
  - parse_event_log: 解析 Maka 事件日志（jsonl/list）
  - to_nca_record: 单事件 → TDCA-NCA 六要素记录（对齐 nca-template.yaml 11 字段）
  - build_audit_chain: 事件序列 → NCA 审计轨迹哈希链（append-only 特性保持）
  - hash_chain: 链式哈希（prev_hash → cur_hash）

制度锚定: ID91（自反化合）/ MEMO-006 附录 C（NCA 模板）/ ID92（数据性质标注）
NSFL-Declaration:
  - 转换不修改 Maka 核心（仓库优先 + 双向赋能纪律，BIDIR-001）
  - 合成/演示数据标注 SIMULATED（ID92），不冒充真实运行数据
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Maka Event Log 事件类型
EVENT_MODEL = "model"
EVENT_TOOL_CALL = "tool_call"
EVENT_TOOL_RESULT = "tool_result"
EVENT_TERMINATION = "termination"
EVENT_TYPES = {EVENT_MODEL, EVENT_TOOL_CALL, EVENT_TOOL_RESULT, EVENT_TERMINATION}

# NCA Operation-Type 映射（Maka 事件 → TDCA 操作类型）
EVENT_TO_OP_TYPE = {
    EVENT_MODEL: "Agent-Inference",
    EVENT_TOOL_CALL: "Tool-Invoke",
    EVENT_TOOL_RESULT: "Tool-Result",
    EVENT_TERMINATION: "Agent-Termination",
}


@dataclass(frozen=True)
class NcaRecord:
    """TDCA-NCA 记录（六要素对齐 + 审计链）。"""
    nca_id: str
    function_call_id: str
    operation_type: str
    operator: str
    timestamp: str
    scope: str
    source_event: dict               # 原始 Maka 事件（ID92 标注）
    provenance: str
    prev_hash: Optional[str] = None
    record_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "NCA-ID": self.nca_id,
            "Function-Call-ID": self.function_call_id,
            "Operation-Type": self.operation_type,
            "Operator": self.operator,
            "Timestamp": self.timestamp,
            "Scope": self.scope,
            "Source-Event": self.source_event,
            "Provenance": self.provenance,
            "Prev-Hash": self.prev_hash,
            "Record-Hash": self.record_hash,
        }


class MakaNcaConverter:
    """Maka Event Log → TDCA-NCA 转换器（M1a）。"""

    def __init__(self, operator: str = "maka-agent", provenance: str = "SIMULATED"):
        self._operator = operator
        self._provenance = provenance

    # ---- 解析 ----

    def parse_event_log(self, raw: str) -> List[dict]:
        """解析 Maka 事件日志（JSONL 字符串或 JSON 数组字符串）。"""
        raw = raw.strip()
        if not raw:
            raise ValueError("[NSFL-TRIGGER] 空事件日志")
        events = []
        if raw.startswith("["):
            events = json.loads(raw)
        else:
            for line in raw.splitlines():
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        if not events:
            raise ValueError("[NSFL-TRIGGER] 事件日志无内容")
        for e in events:
            self._validate_event(e)
        return events

    def parse_event_list(self, events: List[dict]) -> List[dict]:
        """解析事件列表（已结构化）。"""
        if not events:
            raise ValueError("[NSFL-TRIGGER] 空事件列表")
        for e in events:
            self._validate_event(e)
        return events

    # ---- 单事件转换（M1a 核心）----

    def to_nca_record(self, event: dict, seq: int = 1,
                      prev_hash: Optional[str] = None,
                      date_str: Optional[str] = None) -> NcaRecord:
        """单事件 → TDCA-NCA 记录（对齐 nca-template 11 字段语义）。"""
        self._validate_event(event)
        ts = datetime.now(timezone.utc)
        date_str = date_str or ts.strftime("%Y%m%d")
        op_type = EVENT_TO_OP_TYPE.get(event["type"], "Agent-Event")

        # NCA-ID: Maka 事件溯源（NCA-MAKA-{date}-{seq}）
        nca_id = f"NCA-MAKA-{date_str}-{seq:03d}"
        # Function-Call-ID: 事件关联调用
        fc_id = event.get("call_id") or event.get("session_id") or f"maka-fc-{seq:03d}"

        record = NcaRecord(
            nca_id=nca_id,
            function_call_id=fc_id,
            operation_type=op_type,
            operator=event.get("agent", self._operator),
            timestamp=event.get("ts") or ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            scope=f"Maka {event['type']} 事件存证（append-only 审计链）",
            source_event=event,
            provenance=event.get("provenance", self._provenance),
            prev_hash=prev_hash,
        )
        # 计算本记录哈希（含 prev_hash —— 链式）
        digest_src = json.dumps({
            "nca_id": record.nca_id,
            "operation_type": record.operation_type,
            "timestamp": record.timestamp,
            "event": record.source_event,
            "prev_hash": record.prev_hash,
        }, ensure_ascii=False, sort_keys=True)
        record_hash = hashlib.sha256(digest_src.encode("utf-8")).hexdigest()
        return NcaRecord(
            nca_id=record.nca_id, function_call_id=record.function_call_id,
            operation_type=record.operation_type, operator=record.operator,
            timestamp=record.timestamp, scope=record.scope,
            source_event=record.source_event, provenance=record.provenance,
            prev_hash=record.prev_hash, record_hash=record_hash,
        )

    # ---- 审计轨迹哈希链（M1a append-only 保持）----

    def build_audit_chain(self, events: List[dict]) -> List[NcaRecord]:
        """事件序列 → NCA 审计轨迹哈希链（每记录 prev_hash 指向前一记录哈希）。"""
        events = self.parse_event_list(events)
        chain: List[NcaRecord] = []
        prev = None
        for i, ev in enumerate(events, start=1):
            rec = self.to_nca_record(ev, seq=i, prev_hash=prev)
            chain.append(rec)
            prev = rec.record_hash
        return chain

    def verify_chain(self, records: List[NcaRecord]) -> bool:
        """验证审计链完整性（哈希连续，append-only 特性）。"""
        prev = None
        for rec in records:
            if rec.prev_hash != prev:
                return False
            prev = rec.record_hash
        return True

    # ---- 校验 ----

    def _validate_event(self, event: dict) -> None:
        if not isinstance(event, dict):
            raise ValueError("[NSFL-TRIGGER] 事件必须为 dict")
        etype = event.get("type")
        if etype not in EVENT_TYPES:
            raise ValueError(f"[NSFL-TRIGGER] 非法事件类型: {etype}")
        if "provenance" in event and event["provenance"] not in ("SIMULATED",) and not event["provenance"].startswith("REAL"):
            raise ValueError(f"[NSFL-TRIGGER] 非法 provenance: {event['provenance']}")
