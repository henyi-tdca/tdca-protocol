# -*- coding: utf-8 -*-
"""动态状态通道 · 新鲜度门 (GSEQ-0601 律三 v2 落地)
运行时 fail-closed: 快照缺失/断流/缺时间戳/超 SLA → 决策冻结, 降级为仅静态推理并标注 unverified。
用法:
    from data_feed_gate import freshness_gate
    verdict = freshness_gate(snapshot={"timestamp": 1756360800, "stream_ok": True},
                             sla={"max_staleness_s": 10})
    # {"gate": "pass"|"frozen", "unverified": bool, "staleness_s": float, "reason": str}
"""
import time


def freshness_gate(snapshot, sla, now=None):
    """snapshot: {"timestamp": epoch_s, "stream_ok": bool} | None
    sla: {"max_staleness_s": 正数}
    返回裁决: gate=pass(可求值 decision.if) / frozen(冻结, unverified=true)"""
    max_stale = None
    if isinstance(sla, dict):
        v = sla.get("max_staleness_s")
        if isinstance(v, (int, float)) and v > 0:
            max_stale = v
    if max_stale is None:
        return _frozen(None, "SLA 无效(缺 max_staleness_s 或非正数)")
    if now is None:
        now = time.time()
    if not isinstance(snapshot, dict):
        return _frozen(None, "状态快照缺失(断流/未初始化)")
    if snapshot.get("stream_ok") is not True:
        return _frozen(None, "数据流断流(stream_ok!=true)")
    ts = snapshot.get("timestamp")
    if not isinstance(ts, (int, float)):
        return _frozen(None, "快照缺时间戳(机读证据不完整)")
    staleness = float(now) - float(ts)
    if staleness < 0:
        staleness = 0.0
    if staleness > max_stale:
        return _frozen(staleness, "陈旧数据(staleness=%.1fs > SLA %.1fs)" % (staleness, max_stale))
    return {"gate": "pass", "unverified": False, "staleness_s": staleness, "reason": "新鲜度达标"}


def _frozen(staleness, reason):
    return {"gate": "frozen", "unverified": True,
            "staleness_s": staleness,
            "reason": "%s → 决策冻结, 降级为仅静态推理 (unverified)" % reason}
