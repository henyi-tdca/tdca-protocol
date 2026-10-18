# -*- coding: utf-8 -*-
"""相遇线 ↔ 身份线 **接口断言**校验器 V1.0（本侧自跑 · 有限模型穷举）

⭐ 依据：⭐ `TDCA-RULING-ENCOUNTER-IDENTITY-INTERFACE-001`（⭐ 接口巩固件 · 六处落定）
        ⭐ `TDCA-RULING-ENCOUNTER-IDENTITY-INTERFACE-001` §四-`3`（⭐ 接口断言 · 本批办）
⭐ 断言：⭐ `I-A1`~`I-A6`（⭐ 六条 · ⭐ 见下）
⭐ 跑法：⭐ 合规集（⭐ `6` 类）× 断言全过；⭐ 对抗集（⭐ `7` 条 · ⭐ 各违一条）× ⭐ 须逐条捕获（⭐ 暴露力）
⭐ 方法：⭐ 换实现 ＋ 换序（⭐ 输入顺序打乱后逐条不变）＋ 可重复（⭐ 重跑逐位一致）
⭐ 纪律：⭐ 不出网 · ⭐ 零对外 · ⭐ 沙盒位隔离且跑完复原；⛔ 不含凭据值与人名与本机真实路径串
"""
import ast
import copy
import hashlib
import json
import os
import random
import shutil
import sys
from dataclasses import dataclass, field, replace

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ast.parse(open(__file__, encoding="utf-8").read())
print("ast.parse 自检: OK（相遇×身份 接口断言校验器 V1.0）")

SANDBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp-enc-identity-interface")  # 改造令·甲：脚本旁相对沙盒位（跑完自删）

# ── 一、口径常量（照接口巩固件） ──────────────────────────────────────────────
TIER_NAMES = ("固锚级", "移锚级", "记名级", "未达门槛")     # 四档
TIER_STATES = ("待补", "未定档")                          # 态 · ⛔ 非档
TIER_ALLOWED = TIER_NAMES + TIER_STATES
STATES = ("发现", "相遇", "握手", "交互", "结算", "拒绝")
HANDSHAKE = "握手"
ENCOUNTER = "相遇"


@dataclass(frozen=True)
class Rec:
    rid: str
    subject: str
    state_to: str
    tier_ref: str
    identity_checked: bool = False
    written_back: bool = False          # ⛔ 须恒为 false（只引不回写）
    excluded_due_to_anonymous: bool = False  # ⛔ 须恒为 false（匿名不得被剔出相遇）
    gate1_seq: int = 1                   # 准入（门一）序
    encounter_seq: int = 2               # 相遇序
    note: str = ""


def detect(recs, subjects=None):
    """检测器（换实现：规则表 + 首命中 + 集合式判定）。返回 {qid: (passed, detail)}"""
    out = {}
    # I-A1 握手须身份确认
    bad = [r.rid for r in recs if r.state_to == HANDSHAKE and not r.identity_checked]
    out["I-A1"] = (not bad, f"握手态未确认身份 = {bad}")
    # I-A2 相遇不要求身份确认（匿名者不被剔出相遇）
    has_anon_enc = any(r.state_to == ENCOUNTER and not r.identity_checked
                       and r.tier_ref in ("未达门槛", "待补", "未定档") for r in recs)
    bad2 = [r.rid for r in recs if r.excluded_due_to_anonymous]
    out["I-A2"] = (has_anon_enc and not bad2,
                   f"匿名/待补之相遇记录存在={has_anon_enc}；因匿名被剔出={bad2}")
    # I-A3 待补态不得握手
    bad3 = [r.rid for r in recs if r.tier_ref == "待补" and r.state_to == HANDSHAKE]
    out["I-A3"] = (not bad3, f"待补态握手 = {bad3}")
    # I-A4a 档位取值合法
    bad4 = [r.rid for r in recs if r.tier_ref not in TIER_ALLOWED]
    out["I-A4a"] = (not bad4, f"非法档位取值 = {bad4}")
    # I-A4b 只引不回写
    bad5 = [r.rid for r in recs if r.written_back]
    out["I-A4b"] = (not bad5, f"回写身份库 = {bad5}")
    # I-A5 顺序：准入（门一）先于相遇
    bad6 = [r.rid for r in recs if r.state_to == ENCOUNTER and not (r.gate1_seq < r.encounter_seq)]
    out["I-A5"] = (not bad6, f"相遇早于准入 = {bad6}")
    # I-A6 未定档须如实记（⛔ 不留空 · ⛔ 不他填）
    bad7 = [r.rid for r in recs if r.tier_ref.strip() == ""]
    out["I-A6"] = (not bad7, f"档位留空 = {bad7}")
    return out


# ── 二、合规集（六类） ───────────────────────────────────────────────────────
def compliant():
    return [
        Rec("R01", "S-固锚", ENCOUNTER, "固锚级", identity_checked=False, gate1_seq=1, encounter_seq=2),
        Rec("R01b", "S-固锚", HANDSHAKE, "固锚级", identity_checked=True, gate1_seq=1, encounter_seq=2),
        Rec("R02", "S-匿名", ENCOUNTER, "未达门槛", identity_checked=False, gate1_seq=1, encounter_seq=2),
        Rec("R03", "S-待补", ENCOUNTER, "待补", identity_checked=False, gate1_seq=1, encounter_seq=2),
        Rec("R04", "S-未定", ENCOUNTER, "未定档", identity_checked=False, gate1_seq=1, encounter_seq=2),
        Rec("R05", "S-记名", HANDSHAKE, "记名级", identity_checked=True, gate1_seq=1, encounter_seq=2),
        Rec("R06", "S-补足", HANDSHAKE, "记名级", identity_checked=True, gate1_seq=1, encounter_seq=2,
            note="待补补足后重判再握手"),
        Rec("R07", "S-移锚", ENCOUNTER, "移锚级", identity_checked=False, gate1_seq=1, encounter_seq=2),
    ]


# ── 三、对抗集（七条 · 各违一条） ──────────────────────────────────────────────
def adversarial():
    base = compliant()
    cases = []

    def run(mod):
        return detect(mod)

    def ok(recs):
        r = run(recs)
        return all(v[0] for v in r.values())

    # V1 握手未确认身份
    c = [replace(r, identity_checked=False) if r.rid == "R05" else r for r in base]
    cases.append(("I-A1", not run(c)["I-A1"][0] and ok(recs=[r for r in c if r.rid != "R05"])))
    # V2 匿名相遇被剔出
    c = [replace(r, excluded_due_to_anonymous=True) if r.rid == "R02" else r for r in base]
    cases.append(("I-A2", not run(c)["I-A2"][0]))
    # V3 待补态握手
    c = base + [Rec("X3", "S-待补", HANDSHAKE, "待补", identity_checked=True)]
    cases.append(("I-A3", not run(c)["I-A3"][0]))
    # V4 非法档位取值
    c = [replace(r, tier_ref="INVALID") if r.rid == "R07" else r for r in base]
    cases.append(("I-A4a", not run(c)["I-A4a"][0]))
    # V5 回写身份库
    c = [replace(r, written_back=True) if r.rid == "R01b" else r for r in base]
    cases.append(("I-A4b", not run(c)["I-A4b"][0]))
    # V6 相遇早于准入
    c = [replace(r, gate1_seq=5, encounter_seq=2) if r.rid == "R01" else r for r in base]
    cases.append(("I-A5", not run(c)["I-A5"][0]))
    # V7 档位留空
    c = [replace(r, tier_ref="") if r.rid == "R04" else r for r in base]
    cases.append(("I-A6", not run(c)["I-A6"][0]))
    return cases


# ── 四、主流程 ───────────────────────────────────────────────────────────────
def main():
    os.makedirs(SANDBOX, exist_ok=True)
    recs = compliant()
    res = detect(recs)
    n_ok = sum(1 for v in res.values() if v[0])

    # 换序：打乱输入
    shuffled = copy.deepcopy(recs)
    random.Random(20261011).shuffle(shuffled)
    res_sh = detect(shuffled)
    order_inv = all(res[k][0] == res_sh[k][0] for k in res)

    # 可重复：重跑
    rep = detect(compliant())
    repeatable = all(rep[k] == res[k] for k in res)

    adv = adversarial()
    caught = sum(1 for _, c in adv if c)

    with open(os.path.join(SANDBOX, "interface_assert_result.json"), "w", encoding="utf-8") as f:
        json.dump({"asserts": {k: v[0] for k, v in res.items()},
                   "order_invariant": order_inv, "repeatable": repeatable,
                   "adversarial_caught": f"{caught}/{len(adv)}"}, f, ensure_ascii=False, indent=1)

    print("── 轮 A：合规集（六类） ──")
    for k in sorted(res):
        print(f"  [{'PASS' if res[k][0] else 'FAIL'}] {k:6s} {res[k][1]}")
    print(f"  断言通过：{n_ok}/{len(res)}")
    print("── 换序 ──  原序与打乱序一致：", order_inv)
    print("── 可重复 ──  重跑逐位一致：", repeatable)
    print("── 轮 B：对抗集（七条） ──")
    for q, c in adv:
        print(f"  [{'捕获' if c else '漏检'}] {q}")
    print(f"  暴露力：{caught}/{len(adv)}")
    verdict = "PASS" if (n_ok == len(res) and order_inv and repeatable and caught == len(adv)) else "FAIL"
    print(f"── 汇总 ──  断言 {len(res)} ｜ 全过 {n_ok} ｜ 换序不变 {order_inv} ｜ 可重复 {repeatable} "
          f"｜ 对抗捕获 {caught}/{len(adv)} ｜ VERDICT = {verdict}")

    shutil.rmtree(SANDBOX, ignore_errors=True)
    print("  沙盒态已复原（⛔ 未涉主干/站点/主仓）")
    print("=== 相遇×身份 接口断言校验器 V1.0 · 跑通 ===")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
