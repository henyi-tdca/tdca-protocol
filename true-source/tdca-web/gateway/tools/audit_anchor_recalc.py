# -*- coding: utf-8 -*-
"""AUDIT-ANCHOR-001 离线复算脚本（第三方独立验证用）。

依据 TDCA-SPEC-AUDIT-ANCHOR-001（V1.0-FROZEN-INTERNAL）§二逐字独立实现——
⛔ 不 import 网关任何模块（零凭据、零网络、仅标准库）；喂入 `export` 导出的
某日复算输入 JSON，逐字节重算批锚与日锚，输出 sha256: 锚值与接口所发布值比对。

用法：
  python tools/audit_anchor_recalc.py < export-2026-08-20.json
  python tools/audit_anchor_recalc.py export-2026-08-20.json

退出码：0＝复算完成（锚值见输出，自行与接口值比对）；2＝输入形态非法。
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal, InvalidOperation


def normalize_ts(ts: str) -> str:
    from datetime import datetime, timezone
    s = (ts or "").strip()
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def normalize_amount(amount) -> str:
    if isinstance(amount, float):
        raise ValueError("amount ⛔ 浮点入参")
    s = str(amount).strip().replace(" ", "")
    if not s:
        return "0.00"
    if "," in s or "e" in s.lower():
        raise ValueError(f"amount 形态非法：{amount!r}")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"amount 非十进制：{amount!r}")
    if d != d.quantize(Decimal("0.01")):
        raise ValueError(f"amount 小数位超过 2：{amount!r}")
    neg = d < 0
    cents = int(abs(d) * 100)
    out = f"{cents // 100}.{cents % 100:02d}"
    return ("-" + out) if neg else out


def canonical_event(event: dict) -> dict:
    return {
        "amount": normalize_amount(event.get("amount", "")),
        "currency": str(event.get("currency", "") or "").upper(),
        "event_id": str(event.get("event_id", "") or ""),
        "ts": normalize_ts(str(event.get("ts", "") or "")),
        "type": str(event.get("type", "") or ""),
    }


def canonical_json_bytes(obj: dict) -> bytes:
    # RFC 8785：键按 UTF-8 字节序升序（sort_keys 等价）、无空格、无换行、非 ASCII 原样输出
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"),
                      sort_keys=True).encode("utf-8")


def _h(prefix: int, payload: bytes) -> bytes:
    return hashlib.sha256(bytes([prefix]) + payload).digest()


def leaf_digest(event: dict) -> bytes:
    return _h(0x00, canonical_json_bytes(canonical_event(event)))


def merkle_root(pairs) -> bytes:
    leaves = [d for _, d in sorted(pairs, key=lambda p: p[0].encode("utf-8"))]
    if not leaves:
        raise ValueError("空批 ⛔ 成锚")
    if len(leaves) % 2 == 1:
        leaves = leaves + [leaves[-1]]
    level = leaves
    while len(level) > 1:
        nxt = [_h(0x01, level[i] + level[i + 1]) for i in range(0, len(level), 2)]
        if len(nxt) % 2 == 1 and len(nxt) > 1:
            nxt = nxt + [nxt[-1]]
        level = nxt
    return level[0]


def main() -> int:
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = json.load(sys.stdin)

    date = doc["date"]
    prev = doc.get("prev_day_anchor", "")
    if doc.get("status") == "none":
        print(json.dumps({"date": date, "status": "none",
                          "note": "缺日无锚（day_anchor 恒为 null，⛔ 占位哈希）"},
                         ensure_ascii=False))
        return 0
    batches = doc["batches"]
    batch_roots = []
    event_count = 0
    detail = []
    for b in batches:
        events = b["events"]
        pairs = [(str(e.get("event_id", "")), leaf_digest(e)) for e in events]
        root = merkle_root(pairs)
        batch_roots.append("sha256:" + root.hex())
        event_count += len(events)
        detail.append({"batch_id": b["batch_id"], "event_count": len(events),
                       "batch_root": "sha256:" + root.hex()})
    header = {"batch_count": len(batches), "batch_roots": batch_roots,
              "date": date, "event_count": event_count, "prev_day_anchor": prev}
    anchor = _h(0x02, canonical_json_bytes(header))
    print(json.dumps({"date": date, "status": "anchored", "batches": detail,
                      "day_anchor": "sha256:" + anchor.hex()},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError) as e:
        print(f"输入非法：{e}", file=sys.stderr)
        sys.exit(2)
