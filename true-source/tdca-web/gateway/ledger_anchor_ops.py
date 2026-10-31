# -*- coding: utf-8 -*-
"""
AUDIT-ANCHOR-001：公开账本锚点（内部面）——规范化序列化 ＋ Merkle 批锚 ＋ 线性日锚。

规格依据：TDCA-SPEC-AUDIT-ANCHOR-001（V1.0-FROZEN-INTERNAL）§二 逐字实现：
  叶子 SHA-256(0x00 ‖ 规范化事件字节)；内部节点 SHA-256(0x01 ‖ 左 ‖ 右)；
  批锚＝Merkle 根（叶子按 event_id 的 UTF-8 字节序升序，奇数末位复制自身）；
  日锚 SHA-256(0x02 ‖ 规范化日头字节)。输出一律 sha256: ＋ 64 位小写十六进制。

边界：
  - 仅内部可见：anchors* 路由仅在环境变量 TDCA_AUDIT_ANCHOR_INTERNAL=1 时由 app.py 挂载；
  - ⛔ 不对外发布锚值（首锚公开另须明示）、⛔ 不上生产；
  - 排除项（§2.5）永不入规范化：内部编号／nca_watermark／data_nature／note／库内自增 id／任何密钥口令；
  - 一期批粒度＝一日一批（batch_id = "B<date>"）；结构变更须走新版规格件，⛔ 就地改本件。

SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

DAY_TZ = timezone(timedelta(hours=8))   # 规格 §2.4：date 取 +08 日界
FIVE_FIELDS = ("event_id", "type", "ts", "amount", "currency")

# ---------------------------------------------------------------------------
# §2.2 取值规范化
# ---------------------------------------------------------------------------

def normalize_ts(ts: str) -> str:
    """ts 一律转 UTC，YYYY-MM-DDTHH:MM:SS.ffffffZ（6 位小数补零）。无时区按 UTC 计。"""
    s = (ts or "").strip()
    if not s:
        return "0000-00-00T00:00:00.000000Z"
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        # 兼容裸日期等退化形态：原样不足位补零不臆造，交断言拦
        raise ValueError(f"ts 非 ISO-8601：{ts!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def normalize_amount(amount) -> str:
    """amount → 十进制字符串、2 位小数、不足补零；⛔ 浮点参与运算（全程整数/Decimal 语义）。

    入参为「元」的字符串/整数/Decimal（⛔ float）；含千分位或科学计数法输入一律拒绝
    （规范化规则约束的是输出形态，输入异常须显式失败，⛔ 静默猜解）。
    """
    from decimal import Decimal, InvalidOperation
    if isinstance(amount, float):
        raise ValueError("amount ⛔ 浮点入参")
    s = str(amount).strip().replace(" ", "")
    if not s:
        return "0.00"
    if "," in s or "e" in s.lower():
        raise ValueError(f"amount 形态非法（千分位/科学计数法）：{amount!r}")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"amount 非十进制：{amount!r}")
    if d != d.quantize(Decimal("0.01")):
        # 超过 2 位小数：不臆造，显式失败
        raise ValueError(f"amount 小数位超过 2：{amount!r}")
    neg = d < 0
    cents = int(abs(d) * 100)
    out = f"{cents // 100}.{cents % 100:02d}"
    return ("-" + out) if neg else out


def canonical_event(event: dict) -> dict:
    """五项字段定格（缺者空串）＋取值规范化；⛔ 多字段一律不入（§2.5 排除项在此被物理隔离）。"""
    return {
        "amount": normalize_amount(event.get("amount", "")),
        "currency": str(event.get("currency", "") or "").upper(),
        "event_id": str(event.get("event_id", "") or ""),
        "ts": normalize_ts(str(event.get("ts", "") or "")),
        "type": str(event.get("type", "") or ""),
    }


def canonical_json_bytes(obj: dict) -> bytes:
    """§2.3：键按 UTF-8 字节序升序（Python sort_keys 与 UTF-8 字节序等价）、`,`/`:` 无空格、
    无换行、字符串转义按 RFC 8785（ensure_ascii=False 原样输出非 ASCII）。"""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"),
                      sort_keys=True).encode("utf-8")


# ---------------------------------------------------------------------------
# §2.4 哈希与前缀区分
# ---------------------------------------------------------------------------

def _h(prefix: int, payload: bytes) -> bytes:
    return hashlib.sha256(bytes([prefix]) + payload).digest()


def to_hex(digest: bytes) -> str:
    return "sha256:" + digest.hex()


def leaf_digest(event: dict) -> bytes:
    """叶子＝SHA-256(0x00 ‖ 规范化事件字节)。"""
    return _h(0x00, canonical_json_bytes(canonical_event(event)))


def merkle_root(pairs) -> bytes:
    """pairs＝[(event_id, leaf_digest)]；叶子按 event_id 的 UTF-8 字节序升序；奇数末位复制自身。"""
    leaves = [d for _, d in sorted(pairs, key=lambda p: p[0].encode("utf-8"))]
    if not leaves:
        raise ValueError("空批 ⛔ 成锚")
    if len(leaves) % 2 == 1:
        leaves = leaves + [leaves[-1]]
    level = leaves
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            nxt.append(_h(0x01, level[i] + level[i + 1]))
        if len(nxt) % 2 == 1 and len(nxt) > 1:
            nxt = nxt + [nxt[-1]]
        level = nxt
    return level[0]


def day_header(date: str, prev_day_anchor: str, batches) -> dict:
    """日头五字段（§2.4）：date／prev_day_anchor（首日空串）／batch_count／event_count／batch_roots。"""
    return {
        "batch_count": len(batches),
        "batch_roots": [to_hex(root) for _, root, _ in batches],
        "date": date,
        "event_count": sum(n for _, _, n in batches),
        "prev_day_anchor": prev_day_anchor,
    }


def day_anchor_digest(date: str, prev_day_anchor: str, batches) -> bytes:
    """日锚＝SHA-256(0x02 ‖ 规范化日头字节)；batches＝[(batch_id, root_digest, event_count)]。"""
    return _h(0x02, canonical_json_bytes(day_header(date, prev_day_anchor, batches)))


def day_of(ts: str) -> str:
    """事件 ts → +08 日界 YYYY-MM-DD。"""
    s = (ts or "").strip()
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(DAY_TZ).date().isoformat()


# ---------------------------------------------------------------------------
# 批锚／日锚 发布与更正（状态机）
# ---------------------------------------------------------------------------

def _batch_id(date: str) -> str:
    return "B" + date


def compute_batch(events: list) -> dict:
    """一批事件 → 批锚四值（事件为公共五项口径，amount 为元之十进制字符串）。"""
    if not events:
        raise ValueError("空批 ⛔ 成锚")
    ids = sorted((str(e.get("event_id", "")) for e in events), key=lambda x: x.encode("utf-8"))
    pairs = [(str(e.get("event_id", "")), leaf_digest(e)) for e in events]
    root = merkle_root(pairs)
    return {"batch_id": _batch_id_of_events(events),
            "batch_root": root, "event_count": len(events),
            "first_event_id": ids[0], "last_event_id": ids[-1]}


def _batch_id_of_events(events: list) -> str:
    # 一期：一日一批，批＝当日全部事件；批锚 id 由日界决定（确定性，无随机分量）
    days = {day_of(str(e.get("ts", ""))) for e in events}
    if len(days) != 1:
        raise ValueError(f"跨日事件 ⛔ 同批：{sorted(days)}")
    return _batch_id(days.pop())


def publish_day(sess, date: str, now: str) -> dict:
    """发布某日（幂等：已有行则跳过返回既有）。返回日锚行字典。"""
    from db import models as M

    existing = sess.get(M.AuditDayAnchor, (date, 1))
    if existing is not None:
        return _row_dict(existing)
    rows = sess.query(M.TaxEvent).all()
    events = [{"event_id": r.event_id, "type": r.type, "ts": r.ts,
               "amount": _cents_to_str(r.amount), "currency": ""}
              for r in rows if day_of(r.ts) == date]
    prev = _last_anchored_anchor(sess, date)
    prev_str = prev if prev else ""
    if not events:
        row = M.AuditDayAnchor(date=date, version=1, status="none", day_anchor=None,
                               prev_day_anchor=None, batch_count=0, event_count=0,
                               published_at=now)
        sess.add(row)
        return _row_dict(row)
    b = compute_batch(events)
    batches = [(b["batch_id"], b["batch_root"], b["event_count"])]
    anchor = day_anchor_digest(date, prev_str, batches)
    sess.add(M.AuditBatchAnchor(batch_id=b["batch_id"], version=1, date=date,
                                batch_root=to_hex(b["batch_root"]),
                                event_count=b["event_count"],
                                first_event_id=b["first_event_id"],
                                last_event_id=b["last_event_id"], created_at=now))
    sess.add(M.AuditDayAnchor(date=date, version=1, status="anchored",
                              day_anchor=to_hex(anchor), prev_day_anchor=prev_str,
                              batch_count=1, event_count=b["event_count"], published_at=now))
    return {"date": date, "version": 1, "status": "anchored", "day_anchor": to_hex(anchor),
            "prev_day_anchor": prev_str, "batch_count": 1,
            "event_count": b["event_count"], "published_at": now}


def correct_day(sess, date: str, now: str) -> list:
    """更正（§四.3）：该日起已发布各日逐日重锚为新版本（旧行原样保留，⛔ 删改旧锚）。

    返回新版行清单（首行为被更正日）。更正当日的 prev 沿用其首版 prev（链语义不变），
    其后各日 prev 取上一 anchored 日之【最新版】日锚。
    """
    from db import models as M

    first = sess.get(M.AuditDayAnchor, (date, 1))
    if first is None:
        raise ValueError(f"{date} 未发布，⛔ 更正（缺日请走正常发布）")
    # 级联范围：自更正日起之「已锚定」日（none 日不参与串联，⛔ 无谓新版）
    latest = _latest_rows(sess)
    published = sorted(d for d in latest if d >= date and latest[d]["status"] == "anchored")
    out = []
    prev = _version_prev(sess, date, 1) or ""
    for d in sorted(published):
        ver = _next_version(sess, d)
        rows = sess.query(M.TaxEvent).all()
        events = [{"event_id": r.event_id, "type": r.type, "ts": r.ts,
                   "amount": _cents_to_str(r.amount), "currency": ""}
                  for r in rows if day_of(r.ts) == d]
        if not events:
            row = M.AuditDayAnchor(date=d, version=ver, status="none", day_anchor=None,
                                   prev_day_anchor=None, batch_count=0, event_count=0,
                                   published_at=now)
            sess.add(row)
            out.append(_row_dict(row))
            continue
        b = compute_batch(events)
        batches = [(b["batch_id"], b["batch_root"], b["event_count"])]
        anchor = day_anchor_digest(d, prev, batches)
        prev_str = prev or ""          # 首日空串（入日头亦入库；API 侧 none 日才返 null）
        sess.add(M.AuditBatchAnchor(batch_id=b["batch_id"], version=ver, date=d,
                                    batch_root=to_hex(b["batch_root"]),
                                    event_count=b["event_count"],
                                    first_event_id=b["first_event_id"],
                                    last_event_id=b["last_event_id"], created_at=now))
        sess.add(M.AuditDayAnchor(date=d, version=ver, status="anchored",
                                  day_anchor=to_hex(anchor), prev_day_anchor=prev_str,
                                  batch_count=1, event_count=b["event_count"],
                                  published_at=now))
        prev = to_hex(anchor)
        out.append({"date": d, "version": ver, "status": "anchored",
                    "day_anchor": to_hex(anchor), "prev_day_anchor": prev_str,
                    "batch_count": 1, "event_count": b["event_count"], "published_at": now})
    return out


def verify_chain(sess) -> list:
    """断链判定（§四.2）：逐日取【最新版】，anchored 日之 prev 须等于上一 anchored 日最新版日锚。

    返回违例清单（空＝链完整）。none 日不参与串联。
    """
    from db import models as M

    latest = _latest_rows(sess)
    violations = []
    prev_anchor = None
    for d in sorted(latest):
        row = latest[d]
        if row["status"] != "anchored":
            continue
        expect = prev_anchor if prev_anchor else (row["prev_day_anchor"] or "")
        if (row["prev_day_anchor"] or "") != expect:
            violations.append({"date": d, "expect": expect or "(首日空串)",
                               "got": row["prev_day_anchor"]})
        prev_anchor = row["day_anchor"]
    return violations


def _latest_rows(sess) -> dict:
    from db import models as M

    rows = sess.query(M.AuditDayAnchor).all()
    latest = {}
    for r in rows:
        if r.date not in latest or r.version > latest[r.date].version:
            latest[r.date] = r
    return {d: _row_dict(r) for d, r in latest.items()}


def _last_anchored_anchor(sess, before_date: str):
    from db import models as M

    rows = [r for r in sess.query(M.AuditDayAnchor).all()
            if r.date < before_date and r.status == "anchored"]
    if not rows:
        return None
    latest = {}
    for r in rows:
        if r.date not in latest or r.version > latest[r.date].version:
            latest[r.date] = r
    return sorted(latest.values(), key=lambda r: r.date)[-1].day_anchor


def _version_prev(sess, date: str, version: int):
    from db import models as M

    row = sess.get(M.AuditDayAnchor, (date, version))
    return row.prev_day_anchor if row else None


def _next_version(sess, date: str) -> int:
    from db import models as M

    vs = [r.version for r in sess.query(M.AuditDayAnchor.version)
          .filter_by(date=date).all()]
    return (max(vs) if vs else 0) + 1


def _cents_to_str(cents: int) -> str:
    """金额整分（库内形态）→ 元之十进制字符串（整数运算，⛔ 浮点）。"""
    neg = cents < 0
    c = abs(int(cents))
    out = f"{c // 100}.{c % 100:02d}"
    return ("-" + out) if neg else out


def _row_dict(r) -> dict:
    return {"date": r.date, "version": r.version, "status": r.status,
            "day_anchor": r.day_anchor, "prev_day_anchor": r.prev_day_anchor,
            "batch_count": r.batch_count, "event_count": r.event_count,
            "published_at": r.published_at}


def export_day_input(sess, date: str) -> dict:
    """导出某日复算输入（喂离线复算脚本 tools/audit_anchor_recalc.py）。"""
    from db import models as M

    row = None
    vs = [r for r in sess.query(M.AuditDayAnchor).all() if r.date == date]
    if vs:
        row = max(vs, key=lambda r: r.version)
    rows = sess.query(M.TaxEvent).all()
    events = [{"event_id": r.event_id, "type": r.type, "ts": r.ts,
               "amount": _cents_to_str(r.amount), "currency": ""}
              for r in rows if day_of(r.ts) == date]
    return {"date": date, "status": row.status if row else "unpublished",
            "prev_day_anchor": (row.prev_day_anchor if row else None) or "",
            "batches": [{"batch_id": _batch_id(date), "events": events}]}


# ---------------------------------------------------------------------------
# 内部面路由（app.py 仅在 TDCA_AUDIT_ANCHOR_INTERNAL=1 时挂载，⛔ 对外暴露）
# ---------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException  # noqa: E402

from api_v1 import _nca_watermark, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/audit", tags=["audit-anchor"])


@router.get("/anchors")
def anchors_list():
    """锚点日列表（已发布区间逐日一行；none 日显式出行且双 null，⛔ 缺行、⛔ 占位哈希）。"""
    from db import get_session
    import db.models as M

    with get_session() as s:
        rows = s.query(M.AuditDayAnchor).all()
    latest = {}
    for r in rows:
        if r.date not in latest or r.version > latest[r.date].version:
            latest[r.date] = r
    days = [{"date": r.date, "day_anchor": r.day_anchor, "prev_day_anchor": r.prev_day_anchor,
             "batch_count": r.batch_count, "event_count": r.event_count, "status": r.status}
            for _, r in sorted(latest.items())]
    return _nca_watermark({"days": days, "total": len(days), "note": "锚点日列表（内部面；none 日双 null 不入链）"})


@router.get("/anchors/{date}")
def anchors_day(date: str):
    """某日锚点详情：日锚＋批锚清单（batch_id／batch_root／event_count／first／last event_id）。"""
    import re

    from db import get_session
    import db.models as M

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise HTTPException(400, "date 须为 YYYY-MM-DD")
    with get_session() as s:
        rows = [r for r in s.query(M.AuditDayAnchor).all() if r.date == date]
        if not rows:
            raise HTTPException(404, "该日不在已发布锚区间（缺日不出行于详情面，⛔ 臆造）")
        row = max(rows, key=lambda r: r.version)
        batches = []
        if row.status == "anchored":
            bs = [b for b in s.query(M.AuditBatchAnchor).all()
                  if b.date == date and b.version == row.version]
            batches = [{"batch_id": b.batch_id, "batch_root": b.batch_root,
                        "event_count": b.event_count, "first_event_id": b.first_event_id,
                        "last_event_id": b.last_event_id} for b in sorted(bs, key=lambda b: b.batch_id)]
    return _nca_watermark({"date": row.date, "day_anchor": row.day_anchor,
                           "prev_day_anchor": row.prev_day_anchor, "status": row.status,
                           "version": row.version, "batches": batches,
                           "note": "日锚详情（内部面；更正留多版本，此处为最新版）"})


# ---------------------------------------------------------------------------
# CLI：python -m ledger_anchor_ops publish|correct|export|verify-chain
# ---------------------------------------------------------------------------

def _cli():
    import argparse
    import json as _json
    import sys

    from db import get_session, get_sessionmaker
    import db.models as M

    ap = argparse.ArgumentParser(description="AUDIT-ANCHOR-001 发布／更正／导出／验链")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_pub = sub.add_parser("publish", help="发布至指定日（含缺日 none 行；幂等）")
    p_pub.add_argument("--to", required=True, help="截止日 YYYY-MM-DD（含）")
    p_cor = sub.add_parser("correct", help="更正：该日起逐日重锚为新版本（旧版不删）")
    p_cor.add_argument("--date", required=True)
    p_cor.add_argument("--reason", default="")
    p_exp = sub.add_parser("export", help="导出某日复算输入 JSON")
    p_exp.add_argument("--date", required=True)
    sub.add_parser("verify-chain", help="断链判定（取各日最新版）")
    a = ap.parse_args()

    get_sessionmaker()  # 惰性引擎先按 DATABASE_URL 就绪
    from sqlalchemy import inspect as _inspect
    eng = get_sessionmaker().kw["bind"]
    have = set(_inspect(eng).get_table_names())
    need = {M.AuditDayAnchor.__tablename__, M.AuditBatchAnchor.__tablename__}
    missing = need - have
    if missing:
        print(f"缺表 {sorted(missing)}——请先跑迁移 0021", file=sys.stderr)
        sys.exit(2)

    now = _utc()
    with get_session() as s:
        if a.cmd == "publish":
            start_candidates = [r.date for r in s.query(M.AuditDayAnchor.date).distinct()]
            if not start_candidates:
                ev_days = sorted({day_of(r.ts) for r in s.query(M.TaxEvent).all()})
                if not ev_days:
                    print("无事件可锚", file=sys.stderr)
                    sys.exit(1)
                start_candidates = [ev_days[0]]
            start = min(start_candidates)
            from datetime import date as _date
            d0 = _date.fromisoformat(start)
            d1 = _date.fromisoformat(a.to)
            if d1 < d0:
                print(f"--to {a.to} 早于链首 {start}", file=sys.stderr)
                sys.exit(1)
            out = []
            cur = d0
            with get_sessionmaker().begin() as sb:
                while cur <= d1:
                    out.append(publish_day(sb, cur.isoformat(), now))
                    cur = _date.fromordinal(cur.toordinal() + 1)
            print(_json.dumps({"published": out}, ensure_ascii=False, indent=1))
        elif a.cmd == "correct":
            try:
                with get_sessionmaker().begin() as sb:
                    out = correct_day(sb, a.date, now)
            except ValueError as e:
                print(str(e), file=sys.stderr)
                sys.exit(1)
            print(_json.dumps({"corrected_from": a.date, "reason": a.reason,
                               "new_versions": out}, ensure_ascii=False, indent=1))
        elif a.cmd == "export":
            print(_json.dumps(export_day_input(s, a.date), ensure_ascii=False, indent=1))
        elif a.cmd == "verify-chain":
            v = verify_chain(s)
            print(_json.dumps({"chain_ok": not v, "violations": v}, ensure_ascii=False, indent=1))
            sys.exit(0 if not v else 1)


if __name__ == "__main__":
    _cli()
