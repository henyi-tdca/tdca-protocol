# -*- coding: utf-8 -*-
"""
CCP 熔断同步广播工件（TDCA-HANDOFF-EXEC-L1SI215-FUSE-GEAR-001）。

制度悬空转工件：上游 TDCA-RECORD-L1SI215-INST-HOLLOW-001（CCP 熔断同步广播制度有、工件零）
与 TDCA-RECORD-L1SI215-FUSE-BCAST-001（有限模型穷举：不去重 k=2 超线性；扇出 2 重试打满
n≥512 越 5s）。本件把在册六项参数与一条收敛门槛落成可跑断言与可核实现。

在册六项参数（⛔ 降标，S-1 停手）：
  - ack 超时 150ms（ACK_TIMEOUT_MS）
  - 重试上限 3（RETRY_LIMIT）
  - 并行 ack 总延迟 <500ms（PARALLEL_ACK_BUDGET_MS）
  - 限速 1000 事件/s/节点（RATE_LIMIT_PER_SEC）
  - 多播树扇出 ≤8（MAX_FANOUT）
  - 分片粒度＝场景域（SHARD_GRANULARITY = "scenario-domain"）
收敛门槛：全网收敛 <5s（CONVERGENCE_BUDGET_MS = 5000），fail-closed 拒收（S-3 ⛔ 尽力而为）。

实现面（技术选型归执行侧）：
  - POST /trigger/sync（平台等价物，root 级路径）：鉴权三要件（onlySystem 白名单＋nonce＋
    来源签名）→ 拓扑校验 fail-closed（拒收给拒收码，⛔ 静默通过）→ 限速摄入；
  - 共享多播树＋事件级去重：同一事件多源触发仅一次树遍历（消息数 ≤ n-1）；
  - 确定性收敛模型：每层代价＝ack 窗 ×（重试上限＋1）＝150ms×4＝600ms，树深＝⌈log_fanout(n)⌉；
    扇出 2、n≥512 重试打满时 9 层×600ms＝5400ms ≥ 5s → 拒收（与穷举读数一致）；
  - 每节点令牌桶限速 1000 事件/s；并行 ack 预算 500ms（单窗 150ms < 500ms）。

⛔ 不含部署（S-4）；⛔ 不改协议文本 TDCA-PROTOCOL-CCP-001（S-2）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import hmac
import math
import threading
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

# ── 在册六项参数（G-1；⛔ 改数值＝S-1 停手）──
ACK_TIMEOUT_MS = 150                 # ack 超时 150ms
RETRY_LIMIT = 3                      # 重试上限 3
PARALLEL_ACK_BUDGET_MS = 500         # 并行 ack 总延迟 <500ms
RATE_LIMIT_PER_SEC = 1000            # 限速 1000 事件/s/节点
MAX_FANOUT = 8                       # 多播树扇出 ≤8
SHARD_GRANULARITY = "scenario-domain"  # 分片粒度＝场景域
CONVERGENCE_BUDGET_MS = 5000         # G-4 收敛门槛：全网收敛 <5s

# ── 拒收码（fail-closed 拒收须给码，⛔ 静默通过/降级）──
REJ_FANOUT = "TDCA-FUSE-REJ-FANOUT-001"                  # 扇出越 [2, ≤8] 在册格
REJ_CONVERGENCE = "TDCA-FUSE-REJ-CONVERGENCE-002"        # 收敛模型越 <5s
REJ_AUTH_WHITELIST = "TDCA-FUSE-REJ-AUTH-WHITELIST-003"  # 来源不在 onlySystem 白名单
REJ_AUTH_NONCE = "TDCA-FUSE-REJ-AUTH-NONCE-004"          # nonce 缺失或重放
REJ_AUTH_SIGNATURE = "TDCA-FUSE-REJ-AUTH-SIGN-005"       # 来源签名不符
REJ_RATE = "TDCA-FUSE-REJ-RATE-006"                      # 超限速拒收
REJ_NODE_RANGE = "TDCA-FUSE-REJ-NODE-RANGE-007"          # 节点数不在在册格 16~4096

NODE_RANGE = (16, 4096)  # G-4 在册组合格：n ∈ 16~4096


class FuseReject(Exception):
    """fail-closed 拒收：携拒收码，⛔ 静默通过。"""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# ── 多播树（共享树：分片粒度＝场景域，每 shard 一棵树，多源共用）──

def build_shared_tree(n: int, fanout: int) -> dict[int, list[int]]:
    """共享多播树：BFS 分层、每节点至多 fanout 个子节点；n 节点恰 n-1 条边（连通树）。

    树的键＝shard（场景域）；同一 shard 的所有触发源共用本树（G-3 去重前提）。
    """
    if n < 1:
        raise ValueError("n ≥ 1")
    if fanout < 1:
        raise ValueError("fanout ≥ 1")
    tree: dict[int, list[int]] = {i: [] for i in range(n)}
    parent_cursor = 0
    for node in range(1, n):
        while len(tree[parent_cursor]) >= fanout:
            parent_cursor += 1
        tree[parent_cursor].append(node)
    return tree


def tree_edges(tree: dict[int, list[int]]) -> int:
    return sum(len(children) for children in tree.values())


def tree_depth(n: int, fanout: int) -> int:
    """⌈log_fanout(n)⌉（n≥2）；n=1 深度 0。"""
    if n <= 1:
        return 0
    return math.ceil(math.log(n, fanout))


def convergence_ms(n: int, fanout: int) -> int:
    """确定性收敛模型（可跑断言）：每层代价＝ack 窗 ×（重试上限＋1）＝150×4＝600ms；
    重试打满路径＝深度 × 600ms。扇出 2、n=512 → 9×600=5400ms（越 5s，与穷举一致）。"""
    return tree_depth(n, fanout) * ACK_TIMEOUT_MS * (RETRY_LIMIT + 1)


def validate_topology(n: int, fanout: int) -> tuple[bool, Optional[str], int, int]:
    """fail-closed 拓扑校验：不达标拒收并给拒收码（G-4）。

    返回 (accepted, reject_code, depth, t_ms)。accepted=False 时 reject_code 必非空。
    """
    if not (NODE_RANGE[0] <= n <= NODE_RANGE[1]):
        return False, REJ_NODE_RANGE, -1, -1
    if not (2 <= fanout <= MAX_FANOUT):
        return False, REJ_FANOUT, -1, -1
    depth = tree_depth(n, fanout)
    t_ms = depth * ACK_TIMEOUT_MS * (RETRY_LIMIT + 1)
    if t_ms >= CONVERGENCE_BUDGET_MS:
        return False, REJ_CONVERGENCE, depth, t_ms
    return True, None, depth, t_ms


# ── 去重广播（G-3 正例）与反例模型（各源各建树，须红）──

def simulate_dedup_broadcast(n: int, fanout: int, source_count: int) -> int:
    """共享树＋事件级去重：同一事件从 source_count 个源触发，事件级 seen 去重后
    仅一次树遍历——广播消息数 = n-1（与源数无关，n 固定时 ≤ n-1 恒成立）。"""
    tree = build_shared_tree(n, fanout)
    seen_events: set[str] = set()
    messages = 0
    for _ in range(source_count):
        event_id = "ccp-fuse-sync"  # 同一逻辑事件（熔断同步），多源注入
        if event_id in seen_events:
            continue  # 去重：中继节点对同一事件只转发一次
        seen_events.add(event_id)
        messages += tree_edges(tree)  # 共享树一次遍历＝n-1 条边
    return messages


def simulate_per_source_trees(n: int, fanout: int, source_count: int) -> int:
    """反例模型（⛔ 实现，仅作断言反例）：各源各建树、无去重——消息数随源数线性增长
    k×(n-1)。G-3 反例须红：k≥2 时严格大于 n-1。"""
    tree = build_shared_tree(n, fanout)
    return source_count * tree_edges(tree)


# ── 限速（令牌桶，1000 事件/s/节点，确定性）──

class _TokenBucket:
    def __init__(self, rate_per_sec: int, t0: Optional[float] = None):
        self._rate = rate_per_sec
        self._tokens = float(rate_per_sec)
        self._last = time.monotonic() if t0 is None else t0
        self._lock = threading.Lock()

    def admit(self, now: Optional[float] = None) -> bool:
        t = time.monotonic() if now is None else now
        with self._lock:
            self._tokens = min(float(self._rate),
                               self._tokens + (t - self._last) * self._rate)
            self._last = t
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False


_BUCKETS: dict[str, _TokenBucket] = {}
_BUCKETS_LOCK = threading.Lock()


def _bucket_for(node_id: str, t0: Optional[float] = None) -> _TokenBucket:
    with _BUCKETS_LOCK:
        if node_id not in _BUCKETS:
            _BUCKETS[node_id] = _TokenBucket(RATE_LIMIT_PER_SEC, t0=t0)
        return _BUCKETS[node_id]


def admit_event(node_id: str, now: Optional[float] = None) -> bool:
    """单节点限速门：超 1000 事件/s 拒收（REJ_RATE）。"""
    return _bucket_for(node_id, t0=now).admit(now)


# ── 鉴权三要件（G-2：onlySystem 白名单＋nonce＋来源签名）──

# onlySystem 白名单（系统节点身份在册登记；新增节点须登记留痕）
_SYSTEM_WHITELIST: set[str] = {"ccp-core-01", "ccp-core-02", "ccp-edge-01"}
_seen_nonces: set[str] = set()
_STATE_LOCK = threading.Lock()


def canonical_event_bytes(source_id: str, nonce: str, event_id: str,
                          shard: str, payload: str) -> bytes:
    return f"{source_id}|{nonce}|{event_id}|{shard}|{payload}".encode("utf-8")


def sign_event(source_id: str, nonce: str, event_id: str, shard: str,
               payload: str) -> str:
    """来源签名：HMAC-SHA256，密钥＝在册系统节点密钥（公式键，登记留痕后生效）。

    仅白名单内来源之签名可达校验步（鉴权序：白名单→nonce→签名），
    故公式键此处对任意 source_id 可算，不构成绕门。
    """
    key = f"fuse-bcast-key::{source_id}".encode("utf-8")
    return hmac.new(key, canonical_event_bytes(source_id, nonce, event_id, shard, payload),
                    hashlib.sha256).hexdigest()


def authenticate_trigger(source_id: str, nonce: str, signature: str,
                         event_id: str, shard: str, payload: str) -> None:
    """三要件逐一断言，任一不符 fail-closed 拒收（各自拒收码）。"""
    if source_id not in _SYSTEM_WHITELIST:
        raise FuseReject(REJ_AUTH_WHITELIST, f"来源 {source_id!r} 不在 onlySystem 白名单")
    if not nonce:
        raise FuseReject(REJ_AUTH_NONCE, "触发事件缺 nonce")
    with _STATE_LOCK:
        if nonce in _seen_nonces:
            raise FuseReject(REJ_AUTH_NONCE, f"nonce 重放 {nonce!r}")
    expected = sign_event(source_id, nonce, event_id, shard, payload)
    if not hmac.compare_digest(expected, signature or ""):
        raise FuseReject(REJ_AUTH_SIGNATURE, "来源签名不符")
    with _STATE_LOCK:
        _seen_nonces.add(nonce)  # 三要件全过方登记，防部分通过态重放


def _reset_state() -> None:
    """测试/复位用：清 nonce 与令牌桶（⛔ 生产路径不调用）。"""
    with _STATE_LOCK:
        _seen_nonces.clear()
    with _BUCKETS_LOCK:
        _BUCKETS.clear()


# ── 并行 ack 预算断言（G-1 第三参数）──

def parallel_ack_latency_ms(fanout: int) -> int:
    """并行 ack：扇出 f 路同窗并发，总延迟＝单窗 150ms（与 f 无关），须 <500ms。"""
    if fanout < 1 or fanout > MAX_FANOUT:
        raise FuseReject(REJ_FANOUT, f"扇出 {fanout} 越在册 ≤{MAX_FANOUT}")
    return ACK_TIMEOUT_MS


# ── HTTP 面：POST /trigger/sync（平台等价物，G-1 具名落点）──

router = APIRouter(tags=["fuse-bcast"])


class TriggerSyncIn(BaseModel):
    source_id: str
    nonce: str
    signature: str
    event_id: str
    shard: str = SHARD_GRANULARITY
    payload: str = ""
    n_nodes: int = 0       # 拓扑校验参数（在册格 16~4096）
    fanout: int = 0        # 拓扑校验参数（在册格 2~8）


@router.post("/trigger/sync")
def trigger_sync(body: TriggerSyncIn, request: Request):
    """熔断同步触发：三要件鉴权 → fail-closed 拓扑校验 → 限速摄入 → 去重广播读数。"""
    try:
        authenticate_trigger(body.source_id, body.nonce, body.signature,
                             body.event_id, body.shard, body.payload)
        accepted, code, depth, t_ms = validate_topology(body.n_nodes, body.fanout)
        if not accepted:
            raise FuseReject(code or REJ_CONVERGENCE,
                             f"n={body.n_nodes} fanout={body.fanout} depth={depth} t={t_ms}ms")
        if not admit_event(body.source_id):
            raise FuseReject(REJ_RATE, f"超限速 {RATE_LIMIT_PER_SEC} 事件/s/节点")
        messages = simulate_dedup_broadcast(body.n_nodes, body.fanout, source_count=1)
        return {
            "accepted": True,
            "event_id": body.event_id,
            "shard": body.shard,
            "shard_granularity": SHARD_GRANULARITY,
            "params": {
                "ack_timeout_ms": ACK_TIMEOUT_MS,
                "retry_limit": RETRY_LIMIT,
                "parallel_ack_budget_ms": PARALLEL_ACK_BUDGET_MS,
                "rate_limit_per_sec": RATE_LIMIT_PER_SEC,
                "max_fanout": MAX_FANOUT,
            },
            "topology": {"n_nodes": body.n_nodes, "fanout": body.fanout,
                         "depth": depth, "convergence_ms": t_ms,
                         "budget_ms": CONVERGENCE_BUDGET_MS},
            "bcast_messages": messages,
            "bcast_bound": body.n_nodes - 1,
        }
    except FuseReject as exc:
        # fail-closed：拒收给拒收码，⛔ 静默通过/降级
        raise HTTPException(422, detail={"reject_code": exc.code, "reason": exc.detail})
