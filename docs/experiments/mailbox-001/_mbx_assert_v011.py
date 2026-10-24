# -*- coding: utf-8 -*-
"""V0.11 断言校验器（只读 · 合成样本自检）

件：TDCA-SPEC-MAILBOX-001 V0.11-DRAFT 之新增断言之可机验实现
断言：A2-RH / A1-DL / A1-BC ＋ V0.11 新增格式规（投递态、预算四值、状态项两分、
      容器重启⟷重建、授权信封）

跑法：
  python sim-mailbox-001/_mbx_assert_v011.py            # 合规集 ＋ 对抗集
退出码：0 全过（合规集零违规 ∧ 对抗集逐条捕获）；1 有未捕获/误伤
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ALLOWED_STATUS_CLASS = {"registered", "probe"}
ALLOWED_VERDICT = {"within", "over"}
ALLOWED_DELIVERED = {"pending", "received", "expired", "na"}
FORBIDDEN_PROBE_WORDING = ("预期外探测",)
CRED_PAT = re.compile(r"(授权码|password|secret|token)\s*[:=]\s*\S+", re.I)


# ---------- 卡面 ----------
def check_card(card):
    """返回违规码列表（空＝通过）。"""
    v = []
    d = card.get("delivered")
    if d not in ALLOWED_DELIVERED:
        v.append("DEL-1: delivered 缺失或越枚举")
    if d == "received" and not card.get("received_sha256_16"):
        v.append("A2-RH/DEL-2: received 未报哈希（视同 pending）")
    if d == "received" and card.get("received_sha256_16") and \
            card.get("_expected_sha16") and card["received_sha256_16"] != card["_expected_sha16"]:
        v.append("A2-RH/DEL-3: received 哈希与旁注不符（计违规并降回 pending）")
    if d == "expired" and not card.get("disposal"):
        v.append("A1-DL: expired 无处置记录")
    # ⭐ 凭据形态检查对整卡始终适用（自纠：原实现误置于 auth_envelope 分支内，致无信封之卡漏检）
    if CRED_PAT.search(json.dumps(card, ensure_ascii=False)):
        v.append("AE-3: 件内含授权码/签名值形态")
    env = card.get("auth_envelope")
    if env is not None:
        need = ["template_ref", "auth_id", "version", "requirement_digest",
                "signature_event_nca", "parent_auth_id"]
        miss = [k for k in need if k not in env]
        if miss:
            v.append("AE-1: 授权信封缺字段 " + ",".join(miss))
        dig = env.get("requirement_digest") or {}
        miss4 = [k for k in ("R1", "R2", "R3", "R4") if not dig.get(k)]
        if miss4:
            v.append("AE-1b: 四要件摘要缺 " + ",".join(miss4))
        if env.get("template_ref") != "TDCA-TEMPLATE-AUTH-001":
            v.append("AE-1c: template_ref 非在册模板")
        if env.get("body_text"):
            v.append("AE-2: 信封复制条款正文（应只引 auth_id）")
        if CRED_PAT.search(json.dumps(card, ensure_ascii=False)):
            v.append("AE-3: 件内含授权码/签名值形态")
    return v


# ---------- 回报侧 ----------
def check_return(ret, card):
    v = []
    bc = ret.get("budget_compliance")
    if bc is None:
        return ["A1-BC: 回报缺 budget_compliance"]
    for k in ("budget_seconds", "used_seconds", "verdict", "over_reason"):
        if k not in bc or bc.get(k) in (None, ""):
            v.append("A1-BC/" + k + ": 四值缺项")
    if bc.get("verdict") not in ALLOWED_VERDICT:
        v.append("BC-2: verdict 非 within/over（第三写法）")
    if bc.get("verdict") == "over" and bc.get("over_reason") in (None, "", "n/a"):
        v.append("BC-3: over 无超因（视为未报）")
    if card and bc.get("budget_seconds") != card.get("budget_seconds"):
        v.append("BC-4: budget_seconds 与卡面不符（不得改写）")

    for it in ret.get("status_items", []) or []:
        sc = it.get("status_class")
        if sc not in ALLOWED_STATUS_CLASS:
            v.append("SS-1: status_class 越枚举（" + str(it.get("item")) + "）")
        if sc == "probe" and any(w in json.dumps(it, ensure_ascii=False)
                                 for w in FORBIDDEN_PROBE_WORDING):
            v.append("SS-2: probe 项写作「预期外探测」")

    for c in ret.get("container_report", []) or []:
        if "started_at" not in c:
            v.append("CR-1: 容器缺 started_at（不可分辨重建）")
            continue
        inside = c.get("started_at_in_window") is True
        if c.get("restart_count") == 0 and inside and \
                c.get("state") != "recreated":
            v.append("CR-2: restart_count=0 而 started_at 在窗内却未标 recreated")

    for cl in ret.get("read_claims", []) or []:
        target = cl.get("target")
        sha = cl.get("sha256_16")
        exp = (ret.get("_expected_sha16") or {}).get(target)
        if not sha:
            v.append("A2-RH: 声称已读未报哈希（" + str(target) + "）")
        elif exp and sha != exp:
            v.append("A2-RH: 声称已读哈希不符（" + str(target) + "）")
    return v


# ---------- 样本 ----------
CARD_BASE = {"id": "C1", "command": "日巡", "constraint": "只读", "budget_seconds": 600,
             "expected_output": "一件", "subject": "日巡", "actor": "exec",
             "delivery_form": "online", "delivered": "pending"}

GOOD_CARDS = [
    dict(CARD_BASE, id="G1", delivered="pending"),
    dict(CARD_BASE, id="G2", delivered="na"),
    dict(CARD_BASE, id="G3", delivered="received",
         received_sha256_16="AAAA1111BBBB2222", _expected_sha16="AAAA1111BBBB2222"),
    dict(CARD_BASE, id="G4", delivered="expired", disposal="改期至次日"),
    dict(CARD_BASE, id="G5", delivered="pending",
         auth_envelope={"template_ref": "TDCA-TEMPLATE-AUTH-001", "auth_id": "TDCA-AUTH-001",
                        "version": "V1.0-FROZEN",
                        "requirement_digest": {"R1": "F3", "R2": "五阶一至五", "R3": "全构成",
                                               "R4": "本人签署"},
                        "signature_event_nca": "GSEQ-5000", "parent_auth_id": "n/a"}),
]

BAD_CARDS = [
    (dict(CARD_BASE, id="B1", delivered="received"), "A2-RH/DEL-2"),
    (dict(CARD_BASE, id="B2", delivered="received",
          received_sha256_16="DEAD0000DEAD0000", _expected_sha16="AAAA1111BBBB2222"), "A2-RH/DEL-3"),
    (dict(CARD_BASE, id="B3", delivered="expired"), "A1-DL"),
    (dict(CARD_BASE, id="B4", delivered="AUTO"), "DEL-1"),
    (dict(CARD_BASE, id="B5", delivered="pending",
          auth_envelope={"template_ref": "TDCA-TEMPLATE-AUTH-001", "auth_id": "A",
                         "version": "V1", "requirement_digest": {"R1": "x"},
                         "signature_event_nca": "n", "parent_auth_id": "n/a"}), "AE-1b"),
    (dict(CARD_BASE, id="B6", delivered="pending",
          auth_envelope={"template_ref": "OTHER", "auth_id": "A", "version": "V1",
                         "requirement_digest": {"R1": 1, "R2": 2, "R3": 3, "R4": 4},
                         "signature_event_nca": "n", "parent_auth_id": "n/a"}), "AE-1c"),
    (dict(CARD_BASE, id="B7", delivered="pending", note="授权码: ABC123"), "AE-3"),
]

RET_GOOD = {
    "budget_compliance": {"budget_seconds": 600, "used_seconds": 210,
                          "verdict": "within", "over_reason": "n/a"},
    "status_items": [{"item": "1", "status_class": "registered"},
                     {"item": "4-2", "status_class": "probe"}],
    "container_report": [{"name": "gateway", "restart_count": 0,
                          "started_at": "2026-10-15T00:00:00+08:00",
                          "started_at_in_window": False, "state": "running"},
                         {"name": "chain", "restart_count": 0,
                          "started_at": "2026-10-21T00:00:00+08:00",
                          "started_at_in_window": True, "state": "recreated"}],
    "read_claims": [{"target": "CARD-1", "sha256_16": "AAAA1111BBBB2222"}],
    "_expected_sha16": {"CARD-1": "AAAA1111BBBB2222"},
}

BAD_RETS = [
    ({}, None, "A1-BC"),
    ({"budget_compliance": {"budget_seconds": 600, "used_seconds": 210,
                            "verdict": "within"}}, None, "A1-BC/over_reason"),
    ({"budget_compliance": {"budget_seconds": 600, "used_seconds": 700,
                            "verdict": "OVER", "over_reason": "x"}}, None, "BC-2"),
    ({"budget_compliance": {"budget_seconds": 600, "used_seconds": 700,
                            "verdict": "over", "over_reason": "n/a"}}, None, "BC-3"),
    ({"budget_compliance": {"budget_seconds": 999, "used_seconds": 1,
                            "verdict": "within", "over_reason": "n/a"}},
     dict(CARD_BASE, budget_seconds=600), "BC-4"),
    ({"budget_compliance": RET_GOOD["budget_compliance"],
      "status_items": [{"item": "4-2", "status_class": "guess"}]}, None, "SS-1"),
    ({"budget_compliance": RET_GOOD["budget_compliance"],
      "status_items": [{"item": "4-2", "status_class": "probe",
                        "note": "预期外探测"}]}, None, "SS-2"),
    ({"budget_compliance": RET_GOOD["budget_compliance"],
      "container_report": [{"name": "chain", "restart_count": 0}]}, None, "CR-1"),
    ({"budget_compliance": RET_GOOD["budget_compliance"],
      "container_report": [{"name": "chain", "restart_count": 0,
                            "started_at": "2026-10-21T00:00:00+08:00",
                            "started_at_in_window": True, "state": "running"}]}, None, "CR-2"),
    ({"budget_compliance": RET_GOOD["budget_compliance"],
      "read_claims": [{"target": "CARD-1"}]}, None, "A2-RH"),
    ({"budget_compliance": RET_GOOD["budget_compliance"],
      "read_claims": [{"target": "CARD-1", "sha256_16": "WRONG0000000000"}],
      "_expected_sha16": {"CARD-1": "AAAA1111BBBB2222"}}, None, "A2-RH"),
]


def main():
    print("=== V0.11 断言校验器 · 合成样本自检 ===")
    fp = 0
    for c in GOOD_CARDS:
        v = check_card(c)
        if v:
            fp += 1
            print("  [误伤] 合规卡", c["id"], v)
    vr = check_return(RET_GOOD, dict(CARD_BASE, budget_seconds=600))
    if vr:
        fp += 1
        print("  [误伤] 合规回报", vr)
    print("合规集：卡 %d ＋ 回报 1 ⟹ 误伤 %d" % (len(GOOD_CARDS), fp))

    miss = 0
    for c, code in BAD_CARDS:
        v = check_card(c)
        ok = any(code in x for x in v)
        if not ok:
            miss += 1
            print("  [未捕获] 对抗卡", c["id"], "期望", code, "实得", v)
    for ret, card, code in BAD_RETS:
        v = check_return(ret, card)
        ok = any(code in x for x in v)
        if not ok:
            miss += 1
            print("  [未捕获] 对抗回报 期望", code, "实得", v)
    total = len(BAD_CARDS) + len(BAD_RETS)
    print("对抗集：%d 条 ⟹ 捕获 %d／未捕获 %d" % (total, total - miss, miss))
    print("口径：A2-RH（声称已读须报哈希）／A1-DL（expired 须有处置）／A1-BC（预算四值必报）")
    print("      DEL／BC／SS／CR／AE 为 V0.11 新增格式规")
    verdict = "PASS" if (fp == 0 and miss == 0) else "FAIL"
    print("VERDICT=%s" % verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
