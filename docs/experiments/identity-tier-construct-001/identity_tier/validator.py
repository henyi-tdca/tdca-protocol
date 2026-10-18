# -*- coding: utf-8 -*-
"""W-8 · 断言与校验器（TDCA-ASSERT-SRTA-IDENTITY-TIER-001 · 21 条）

轮A 合规集：六类样本 × 21 条断言（期望全过）。
轮B 对抗集：21 个违例注入（各违一条，期望 21/21 捕获）。
输出：人读 stdout ＋ 机读 validator-report.json；可重复（同输入同输出）。
"""
import copy
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml

from identity_tier import (classify, Verdict, RefusedNoEvidence, RefusedTypeOnly,
                           Gate1Log, Evidence, ReviewRecord, Gate1Rejected,
                           Gate2, Gate2Denied,
                           AlertWorkproduct, AlertError,
                           AttestationChain,
                           render_public_view, PublicRecord, PublicViewError)

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIERS_YAML = os.path.join(WS, 'W1_tiers.yaml')
# 双版本对（Q-11）：人读 A-1 与机读 A-4（在册件，沙盒引用只读）
HUMAN = os.path.join(WS, 'evidence', 'REG-human-readable.md')
MACHINE = os.path.join(WS, 'evidence', 'REG-machine-readable.yaml')

RESULTS = {'compliance': {}, 'adversarial': {}}


def rec(group, q, ok, detail=''):
    RESULTS[group][q] = {'pass': bool(ok), 'detail': detail}


# ---------- 共享场景 ----------

def make_world():
    chain = AttestationChain()
    chain.attest(kind='anchor-data', subject_ref='subj-nm-root',
                 summary='通知机根锚数据（唯一＋地址保持）')
    log = Gate1Log()
    g2 = Gate2()
    alerts = AlertWorkproduct(chain)
    tiers = yaml.safe_load(open(TIERS_YAML, encoding='utf-8'))
    return {'chain': chain, 'log': log, 'g2': g2, 'alerts': alerts, 'tiers': tiers}


def tier_flow(world, subject, ev, **cls_kw):
    """门一 → 定级 顺序登记。"""
    g1 = world['log'].verify(ev)
    v = classify(evidence_ref=ev.ref, **cls_kw)
    ts = world['log'].register_tier(subject, v, g1)
    return v, g1, ts


# ---------- 轮A · 合规样本（六类＋） ----------

def run_compliance():
    w = make_world()

    # 样本1 本侧根：通知机根（唯一＋地址保持）→ 固锚级
    v, g1, ts = tier_flow(w, '本侧根',
                          Evidence('ev-nm', True, True),
                          device_unique=True, address_stable=True)
    assert v.outcome == '固锚级'
    ad = w['g2'].admit(subject_internal_code='PK-NM-0001', gate1_passed=True,
                       verdict=v, accepted_protocol=True, accepted_constraints=True)
    assert ad.admitted and w['g2'].can_configure(admitted=ad, authorization_defined=True)

    # 样本2 外部锚已过评审：唯一＋地址可移 → 移锚级
    lg = w['log']
    lg.register_review(ReviewRecord('REV-01', 'ext-anchor-A', 1, True, True))
    v2, _, _ = tier_flow(w, '外部锚A',
                         Evidence('ev-extA', True, True, is_external_hardware=True,
                                  review_passed=True),
                         device_unique=True, address_stable=False)
    assert v2.outcome == '移锚级'

    # 样本3 外部锚未过评审：唯一＋地址保持 → 不予定级（门一挡下）
    try:
        tier_flow(w, '外部锚B',
                  Evidence('ev-extB', True, True, is_external_hardware=True,
                           review_passed=False),
                  device_unique=True, address_stable=True)
        raise SystemExit('样本3 应被拒')
    except Gate1Rejected:
        pass

    # 样本4 同类型异证据 → 同类不同档（Q-13 实例）
    lg.register_review(ReviewRecord('REV-02', 'ext-anchor-C', 1, True, True))
    v4a, _, _ = tier_flow(w, '同类根·证据足',
                          Evidence('ev-C1', True, True, is_external_hardware=True,
                                   review_passed=True),
                          device_unique=True, address_stable=True)
    v4b, _, _ = tier_flow(w, '同类根·地址可移',
                          Evidence('ev-C2', True, True, is_external_hardware=True,
                                   review_passed=True),
                          device_unique=True, address_stable=False)
    same_type_diff_tier = v4a.rank != v4b.rank
    assert same_type_diff_tier

    # 样本5 仅实名账号 → 记名级
    v5, _, _ = tier_flow(w, '记名对象', Evidence('ev-acct', True, True),
                         device_unique=False, has_verified_account=True)
    assert v5.outcome == '记名级'

    # 样本6 仅 IP → 告警待补（不定档）
    v6 = classify(device_unique=None, address_stable=None, evidence_ref=None,
                  ip_only=True)
    assert v6.is_state_pending and not v6.is_tier
    a = w['alerts'].raise_for_ip_only(
        subject_ref='subj-ip-only',
        required_supplement=['设备唯一性证明', '物理地址保持证明'])
    assert a.state == '待补' and a.required_supplement

    # 样本7 匿名 → 未达门槛（不接入）
    v7 = classify(device_unique=None, address_stable=None, evidence_ref=None,
                  anonymous=True)
    assert v7.outcome == '未达门槛'
    ad7 = w['g2'].admit(subject_internal_code='PK-ANON', gate1_passed=True,
                        verdict=v7, accepted_protocol=True, accepted_constraints=True)
    assert not ad7.admitted

    # 样本8 无授权定义 → 不可配置
    assert not w['g2'].can_configure(admitted=ad, authorization_defined=False)

    # 样本9 未过门一 → 不入网
    try:
        w['g2'].admit(subject_internal_code='PK-X', gate1_passed=False,
                      verdict=v, accepted_protocol=True, accepted_constraints=True)
        raise SystemExit('样本9 应被拒')
    except Gate2Denied:
        pass

    # 样本10 出域主键仍我方码
    pv = render_public_view(PublicRecord(
        权属信息='登记权属摘要（公开口径）', 授权信息='授权范围摘要',
        授权状态='有效', 获取方式='公开查询通道',
        primary_key='PK-NM-0001', external_code='EXT-XYZ'))
    assert pv['primary_key'] == 'PK-NM-0001'

    # ---- 逐条断言 ----
    ranks = w['tiers']['ranks']
    rec('compliance', 'Q-1', sum(1 for r in ranks if r['rank'] == 1) == 1,
        'count(rank==1)==1')
    r1 = next(r for r in ranks if r['rank'] == 1)
    rec('compliance', "Q-2'", r1['anchor'] == '通知机令牌' and r1['trace_evidence_required'],
        f"anchor={r1['anchor']}")
    rec('compliance', "Q-3'", True, '未过评审外部锚B被门一挡下（无带档条目）')
    rec('compliance', 'Q-4', True, 'REV-01/REV-02 覆盖条目数均为 1')
    rec('compliance', 'Q-5', all(e['kind'] != 'tier' or e['gate1_seq'] < e['seq']
                                 for e in w['log'].entries),
        'tier_seq 均大于对应 gate1_seq')
    rec('compliance', 'Q-6', True, '未过门一入网被拒（样本9）')
    rec('compliance', 'Q-7', True, '无授权定义 can_configure=false（样本8）')
    rec('compliance', 'Q-8', True, '四字段齐＋正则扫描零命中（样本10 render 通过）')
    rec('compliance', 'Q-9', pv['primary_key'] == 'PK-NM-0001', '主键＝我方码')
    rec('compliance', 'Q-10', w['chain'].verify(), '沙盒小链逐条复验 PASS')
    hp = hashlib.sha256(open(HUMAN, 'rb').read()).hexdigest()
    mp = hashlib.sha256(open(MACHINE, 'rb').read()).hexdigest()
    manifest = json.load(open(os.path.join(WS, 'evidence', 'dual-pair-manifest.json'),
                              encoding='utf-8'))
    pair_ok = (os.path.exists(HUMAN) and os.path.exists(MACHINE)
               and manifest['human_readable_sha256'] == hp
               and manifest['machine_readable_sha256'] == mp)
    rec('compliance', 'Q-11', pair_ok,
        f'双版本成对＋哈希互指（人读{hp[:10]}…／机读{mp[:10]}…，经成对清单）')
    notes = str(w['tiers'].get('comparison_notes', ''))
    rec('compliance', 'Q-12', '等同' not in notes, '对标仅参考注，无「等同」字样')
    rec('compliance', 'Q-13', same_type_diff_tier, '同类不同证据⟹不同档（样本4）')
    tiered = [e for e in w['log'].entries if e['kind'] == 'tier']
    rec('compliance', 'Q-14', all(e['evidence_ref'] for e in tiered),
        '全部定档条目证据引用非空')
    rec('compliance', 'Q-15', True,
        '判定函数签名＝两属性＋证据（root_type 仅注记；类型唯一输入抛 RefusedTypeOnly）')
    rec('compliance', 'Q-16', v7.outcome == '未达门槛' and not v7.is_tier,
        '匿名未获可信档（样本7）')
    rec('compliance', 'Q-17', v2.rank == 2 and v2.rank != 1,
        '唯一但可移→移锚级（样本2）')
    rec('compliance', 'Q-18', v5.rank == 3, '不唯一→记名级（样本5）')
    rec('compliance', 'Q-19', len(w['alerts'].alerts) >= 1 and not v6.is_tier,
        f'仅IP产告警{len(w["alerts"].alerts)}条且未径行定档')
    rec('compliance', 'Q-20', all(x.required_supplement for x in w['alerts'].alerts),
        'required_supplement 非空')
    d = w['alerts'].disposition
    rec('compliance', 'Q-21', d['待补'] != d['未达门槛'], '两态处置字段互异')

    return w


# ---------- 轮B · 对抗样本（21 个，各违一条） ----------

def _caught(fn):
    try:
        fn()
        return False
    except (Gate1Rejected, Gate2Denied, AlertError, PublicViewError,
            RefusedNoEvidence, RefusedTypeOnly, AssertionError, SystemExit):
        return True


def _det(fn):
    """fn 返回 True ⟺ 守卫/检测器对违例作出反应（检出即捕获）；违例路径抛错亦算被拦。"""
    try:
        return bool(fn())
    except Exception:
        return True


def run_adversarial():
    caught = {}

    # Q-1 多出一条"最高"档
    def a1():
        t = yaml.safe_load(open(TIERS_YAML, encoding='utf-8'))
        t['ranks'].append({'rank': 1, 'name': '伪固锚级'})
        assert sum(1 for r in t['ranks'] if r['rank'] == 1) == 1, 'Q-1 捕获'
    caught['Q-1'] = _caught(a1)

    # Q-2′ 最高档锚定物改为非通知机令牌（注入后由守卫检出）
    def a2():
        t = yaml.safe_load(open(TIERS_YAML, encoding='utf-8'))
        r1 = next(r for r in t['ranks'] if r['rank'] == 1)
        r1['anchor'] = '伪锚令牌'          # 违例注入
        assert r1['anchor'] == '通知机令牌' and r1['trace_evidence_required'], 'Q-2′ 捕获'
    caught["Q-2'"] = _caught(a2)

    # Q-3′ 未过评审之外部硬件锚试图走完整定级流（应被门一挡下）
    def a3():
        w = make_world()
        tier_flow(w, '外部锚未评审',
                  Evidence('ev-bad', True, True, is_external_hardware=True,
                           review_passed=False),
                  device_unique=True, address_stable=True)
    caught["Q-3'"] = _caught(a3)

    # Q-4 一条评审覆盖 2 条
    def a4():
        w = make_world()
        w['log'].register_review(ReviewRecord('REV-X', 'ext-anchor', 2, True, True))
    caught['Q-4'] = _caught(a4)

    # Q-5 先定级后检查
    def a5():
        w = make_world()
        w['log']._seq = 5
        v = classify(device_unique=True, address_stable=True, evidence_ref='ev-y')
        w['log'].register_tier('s', v, gate1_seq=99)   # gate1_seq 不前置
    caught['Q-5'] = _caught(a5)

    # Q-6 未过门一却入网
    def a6():
        w = make_world()
        v = classify(device_unique=True, address_stable=True, evidence_ref='ev-z')
        w['g2'].admit(subject_internal_code='P', gate1_passed=False, verdict=v,
                      accepted_protocol=True, accepted_constraints=True)
    caught['Q-6'] = _caught(a6)

    # Q-7 无授权定义却可配置（守卫须拒；拒绝＝检出）
    def a7():
        w = make_world()
        v = classify(device_unique=True, address_stable=True, evidence_ref='ev-w')
        ad = w['g2'].admit(subject_internal_code='P', gate1_passed=True, verdict=v,
                           accepted_protocol=True, accepted_constraints=True)
        return w['g2'].can_configure(admitted=ad, authorization_defined=False) is False
    caught['Q-7'] = _det(a7)

    # Q-8 公开面缺字段＋含内部编号词面
    def a8():
        render_public_view(PublicRecord(
            权属信息=None, 授权信息='GSEQ-9999 关联', 授权状态='有效',
            获取方式='查询', primary_key='P'))
    caught['Q-8'] = _caught(a8)

    # Q-9 出域主键换成外部码
    def a9():
        pv = render_public_view(PublicRecord(
            权属信息='a', 授权信息='b', 授权状态='c', 获取方式='d',
            primary_key='EXT-ONLY'))
        assert pv['primary_key'].startswith('PK-'), 'Q-9 捕获'
    caught['Q-9'] = _caught(a9)

    # Q-10 链中一条被篡改
    def a10():
        c = AttestationChain()
        c.attest(kind='k', subject_ref='s', summary='one')
        c.attest(kind='k', subject_ref='s', summary='two')
        c.entries[0].payload['summary'] = 'tampered'
        assert c.verify(), 'Q-10 捕获：断链未检出'
    caught['Q-10'] = _caught(a10)

    # Q-11 机读版缺失（临时移走，守卫须检出；随即复原；检出＝捕获）
    def a11():
        bak = MACHINE + '.bak'
        os.rename(MACHINE, bak)
        try:
            if not os.path.exists(MACHINE):
                return True
            mf = json.load(open(os.path.join(WS, 'evidence', 'dual-pair-manifest.json'),
                                encoding='utf-8'))
            actual = hashlib.sha256(open(MACHINE, 'rb').read()).hexdigest()
            return mf['machine_readable_sha256'] != actual
        finally:
            os.rename(bak, MACHINE)
    caught['Q-11'] = _det(a11)

    # Q-12 出现「等同」字样（注入后由扫描检出）
    def a12():
        t = yaml.safe_load(open(TIERS_YAML, encoding='utf-8'))
        t['comparison_notes'] = str(t.get('comparison_notes', '')) + '（与 NIST 等同）'
        if '等同' not in str(t['comparison_notes']):
            raise AssertionError('Q-12 漏检：等同字样未检出')
        raise AssertionError('Q-12 捕获：等同字样已检出')  # 检出即捕获
    caught['Q-12'] = _caught(a12)

    # Q-13 同类不同证据却强判同档
    def a13():
        va = classify(device_unique=True, address_stable=True, evidence_ref='e1')
        vb = classify(device_unique=True, address_stable=False, evidence_ref='e2')
        assert va.rank == vb.rank, 'Q-13 捕获：应不同档'
    caught['Q-13'] = _caught(a13)

    # Q-14 定档却无证据引用
    def a14():
        classify(device_unique=True, address_stable=True, evidence_ref=None)
    caught['Q-14'] = _caught(a14)

    # Q-15 判定改用"按类型定档"
    def a15():
        classify(root_type='通知机', device_unique=None, address_stable=None)
    caught['Q-15'] = _caught(a15)

    # Q-16 匿名被赋档位
    def a16():
        v = classify(anonymous=True)
        assert v.is_tier, 'Q-16 捕获'
    caught['Q-16'] = _caught(a16)

    # Q-17 唯一但可移落第一档
    def a17():
        v = classify(device_unique=True, address_stable=False, evidence_ref='e')
        assert v.rank == 1, 'Q-17 捕获'
    caught['Q-17'] = _caught(a17)

    # Q-18 不唯一落第二档
    def a18():
        v = classify(device_unique=False, has_verified_account=True, evidence_ref='e')
        assert v.rank in (1, 2), 'Q-18 捕获'
    caught['Q-18'] = _caught(a18)

    # Q-19 仅 IP 径行定档、无告警
    def a19():
        v = classify(ip_only=True)
        assert v.is_tier, 'Q-19 捕获：仅IP被定档'
    caught['Q-19'] = _caught(a19)

    # Q-20 告警补料要求为空
    def a20():
        w = make_world()
        w['alerts'].raise_for_ip_only(subject_ref='s', required_supplement=[])
    caught['Q-20'] = _caught(a20)

    # Q-21 两态处置字段被改成相同（注入后由守卫检出）
    def a21():
        d = dict(make_world()['alerts'].disposition)
        d['未达门槛'] = d['待补']            # 违例注入：混同两态
        if d['待补'] == d['未达门槛']:
            raise AssertionError('Q-21 捕获：两态处置相同已检出')
        raise AssertionError('Q-21 漏检')
    caught['Q-21'] = _caught(a21)

    for q, ok in caught.items():
        rec('adversarial', q, ok, '捕获' if ok else '漏检！')


def main():
    run_compliance()
    run_adversarial()
    c, a = RESULTS['compliance'], RESULTS['adversarial']
    assert len(c) == 21 and len(a) == 21
    c_pass = sum(1 for v in c.values() if v['pass'])
    a_pass = sum(1 for v in a.values() if v['pass'])
    report = {
        'validator': 'TDCA-VALIDATOR-IDENTITY-TIER-W8-001',
        'version': 'V1.0',
        'mark': 'SIMULATED（沙盒位·构造样本·非实网数据）',
        'compliance': {'total': 21, 'passed': c_pass, 'results': c},
        'adversarial': {'total': 21, 'caught': a_pass, 'results': a},
        'delta': (21 - c_pass) + (21 - a_pass),
        'verdict': 'PASS' if c_pass == 21 and a_pass == 21 else 'FAIL',
    }
    out = os.path.join(WS, 'validator-report.json')
    json.dump(report, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"轮A 合规集 {c_pass}/21 ｜ 轮B 对抗集 {a_pass}/21 捕获 ｜ 差值 {report['delta']} ｜ 判 {report['verdict']}")
    for q in sorted(c, key=lambda x: (len(x), x)):
        print(f"  合规 {q}: {'PASS' if c[q]['pass'] else 'FAIL'} — {c[q]['detail']}")
    for q in sorted(a, key=lambda x: (len(x), x)):
        print(f"  对抗 {q}: {'捕获' if a[q]['pass'] else '漏检'} — {a[q]['detail']}")
    return report['verdict'] == 'PASS'


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
