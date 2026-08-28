# -*- coding: utf-8 -*-
"""立场分离校验测试套件 (GSEQ-0601 · ≥10 用例)
运行: python test_stance_separation.py  → 全绿退出 0
"""
import os
import sys
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "config"))
sys.path.insert(0, os.path.join(ROOT, "nca-generator"))

import stance_separation_check as SSC
from stance_separation_check import check_cop, StanceViolation
import stance_neutrality as SN
import cognitive_compiler as CC

PASS = []
FAIL = []


def case(name, fn):
    try:
        fn()
        PASS.append(name)
        print("[PASS] %s" % name)
    except Exception as e:
        FAIL.append((name, str(e)))
        print("[FAIL] %s :: %s" % (name, e))


def base_cop(**kw):
    cop = {
        "COP-ID": "TEST-001",
        "soul": {"identity": "t", "core": "中性机制核表述"},
        "primitives": [{"name": "f", "signature": "fn f(x) -> y", "nca_emit": True}],
        "dispatch": {"main_pipeline": "f"},
        "decision": [{"if": "中性触发条件", "call": "f"}],
        "negative_space": ["⊗ 中性边界"],
        "nsfl_version": "V0.1",
    }
    cop.update(kw)
    return cop


# T1 R1: 原语携带 stance 字段 → 拒绝
def t1():
    cop = base_cop(primitives=[{"name": "f", "signature": "fn f(x) -> y", "stance": "主动试探"}])
    try:
        check_cop(cop, strict=True)
        raise AssertionError("应拒绝")
    except StanceViolation:
        pass


# T2 R1: 根节点携带 stance 字段 → 拒绝
def t2():
    cop = base_cop(stance="暴露警示")
    try:
        check_cop(cop, strict=True)
        raise AssertionError("应拒绝")
    except StanceViolation:
        pass


# T3 R2: scene_binding 缺 bindings → 拒绝
def t3():
    cop = base_cop(scene_binding={"schema": "x"})
    try:
        check_cop(cop, strict=True)
        raise AssertionError("应拒绝")
    except StanceViolation:
        pass


# T4 R2: 绑定缺 scene/stance → 拒绝
def t4():
    cop = base_cop(scene_binding={"bindings": [{"binding_id": "B1"}]})
    try:
        check_cop(cop, strict=True)
        raise AssertionError("应拒绝")
    except StanceViolation:
        pass


# T5 R2: 合法绑定(缺 mounts) → R3 拒绝
def t5():
    cop = base_cop(scene_binding={"bindings": [{"scene": "侦查", "stance": "试探"}]})
    try:
        check_cop(cop, strict=True)
        raise AssertionError("应拒绝")
    except StanceViolation:
        pass


# T6 R3: mounts 残缺 → 拒绝
def t6():
    cop = base_cop(scene_binding={"bindings": [{"scene": "s", "stance": "t"}]},
                   mounts={"scene": "a", "skill": "b"})
    try:
        check_cop(cop, strict=True)
        raise AssertionError("应拒绝")
    except StanceViolation:
        pass


# T7 R3: 四类挂载齐备 → 通过
def t7():
    cop = base_cop(scene_binding={"bindings": [{"scene": "s", "stance": "t"}]},
                   mounts={"scene": "a", "knowledge_graph": "b", "skill": "c", "contract": "d"})
    assert check_cop(cop, strict=True) == []


# T8 R4: fail-closed 异常类型正确
def t8():
    try:
        check_cop(base_cop(stance="x"), strict=True)
        raise AssertionError("应抛 StanceViolation")
    except SSC.StanceViolation:
        pass


# T9 兼容: 旧 COP(无 scene_binding/stance) → 通过
def t9():
    assert check_cop(base_cop(), strict=True) == []


# T10 实物: 打草惊蛇机制核 yaml → s5_validate + 校验器双通过
def t10():
    cop = yaml.safe_load(open(os.path.join(ROOT, "stratagems", "第13计-打草惊蛇-机制核.yaml"), encoding="utf-8"))
    CC.s5_validate(cop)
    assert cop["validation"]["passed"] is True
    check_cop(cop, strict=True)


# T11 实物: 三十六计旧计 COP(立场词已在 primitives, 律一范围外) → 校验器通过(兼容)
def t11():
    cop = yaml.safe_load(open(os.path.join(ROOT, "stratagems", "第02计-围魏救赵.yaml"), encoding="utf-8"))
    check_cop(cop, strict=True)


# T12 扫描器: 机制核 soul.core/decision 0 立场命中
def t12():
    cop = yaml.safe_load(open(os.path.join(ROOT, "stratagems", "第13计-打草惊蛇-机制核.yaml"), encoding="utf-8"))
    hits = [h for _, v in SN.yaml_field_paths(cop) for h in SN.find_hits(v)]
    assert hits == [], hits


# T13 词表: 中性替换往返一致 (映射确定性)
def t13():
    assert SN.neutralize("敌方习以为常, 己方可守") == "对方习以为常, 行动方可守"
    assert SN.neutralize("攻敌必救") == "攻其必救"


# T14 编译集成: s5_validate 对违规 COP 直接熔断(抛 StanceViolation)
def t14():
    cop = base_cop(stance="x")
    try:
        CC.s5_validate(cop)
        raise AssertionError("应熔断")
    except SSC.StanceViolation:
        pass


case("T1 R1 原语立场字段拒绝", t1)
case("T2 R1 根节点立场字段拒绝", t2)
case("T3 R2 scene_binding 缺 bindings 拒绝", t3)
case("T4 R2 绑定缺 scene/stance 拒绝", t4)
case("T5 R2/R3 绑定无 mounts 拒绝", t5)
case("T6 R3 mounts 残缺拒绝", t6)
case("T7 R3 四类挂载齐备通过", t7)
case("T8 R4 fail-closed 异常类型", t8)
case("T9 旧 COP 兼容通过", t9)
case("T10 打草惊蛇机制核实物双校验", t10)
case("T11 三十六计旧计兼容通过", t11)
case("T12 机制核扫描 0 立场命中", t12)
case("T13 词表中性替换确定性", t13)
case("T14 s5_validate 集成熔断", t14)


# ---- 律三v2 动态状态通道 (R5 + 新鲜度门) ----
import data_feed_gate as DFG


def valid_feed(**kw):
    df = {"source": "SCADA/MQTT", "variables": [{"name": "对方反应信号"}],
          "freshness_sla": {"max_staleness_s": 10, "on_breach": "freeze"}}
    df.update(kw)
    return df


# T15 R5a: state_dependent=true 无 data_feed → 拒绝
def t15():
    cop = base_cop(state_dependent=True)
    try:
        check_cop(cop, strict=True)
        raise AssertionError("应拒绝")
    except StanceViolation:
        pass


# T16 R5b: data_feed 结构残缺 → 拒绝 (source/variables/sla 三缺口)
def t16():
    for bad in [{"source": "", "variables": [], "freshness_sla": {}},
                valid_feed(variables=[]),
                valid_feed(freshness_sla={"max_staleness_s": 0})]:
        cop = base_cop(state_dependent=True, mounts={"data_feed": bad})
        try:
            check_cop(cop, strict=True)
            raise AssertionError("应拒绝: %s" % bad)
        except StanceViolation:
            pass


# T17 R5: 合法 data_feed → 通过
def t17():
    cop = base_cop(state_dependent=True, mounts={"data_feed": valid_feed()})
    assert check_cop(cop, strict=True) == []


# T18 新鲜度门: 新鲜快照 → pass
def t18():
    now = 1756360000.0
    v = DFG.freshness_gate({"timestamp": now - 3, "stream_ok": True},
                           {"max_staleness_s": 10}, now=now)
    assert v["gate"] == "pass" and v["unverified"] is False, v


# T19 新鲜度门: 陈旧快照 → frozen + unverified
def t19():
    now = 1756360000.0
    v = DFG.freshness_gate({"timestamp": now - 30, "stream_ok": True},
                           {"max_staleness_s": 10}, now=now)
    assert v["gate"] == "frozen" and v["unverified"] is True, v


# T20 新鲜度门: 缺时间戳 / 断流 / 快照缺失 / SLA 无效 → 全部 frozen (fail-closed)
def t20():
    now = 1756360000.0
    for snap, sla in [({"stream_ok": True}, {"max_staleness_s": 10}),
                      ({"timestamp": now, "stream_ok": False}, {"max_staleness_s": 10}),
                      (None, {"max_staleness_s": 10}),
                      ({"timestamp": now, "stream_ok": True}, {})]:
        v = DFG.freshness_gate(snap, sla, now=now)
        assert v["gate"] == "frozen" and v["unverified"] is True, (snap, sla, v)


# T21 试点实物: 机制核 + 两绑定 均携合法 data_feed 且过全部校验
def t21():
    core = yaml.safe_load(open(os.path.join(ROOT, "stratagems", "第13计-打草惊蛇-机制核.yaml"), encoding="utf-8"))
    assert core.get("state_dependent") is True
    check_cop(core, strict=True)
    for b in ("打草惊蛇-场景A-侦查试探.yaml", "打草惊蛇-场景B-暴露警示.yaml"):
        bind = yaml.safe_load(open(os.path.join(ROOT, "stratagems", "bindings", b), encoding="utf-8"))
        assert SSC.check_data_feed(bind["mounts"]["data_feed"]) == [], b


case("T15 R5a 状态依赖缺 data_feed 拒绝", t15)
case("T16 R5b data_feed 结构残缺拒绝", t16)
case("T17 R5 合法 data_feed 通过", t17)
case("T18 新鲜度门 新鲜快照 pass", t18)
case("T19 新鲜度门 陈旧快照 frozen", t19)
case("T20 新鲜度门 四类异常全 frozen", t20)
case("T21 试点实物 机制核+绑定 data_feed", t21)

print("════ %d/%d 通过 ════" % (len(PASS), len(PASS) + len(FAIL)))
sys.exit(0 if not FAIL else 1)
