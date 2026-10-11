# -*- coding: utf-8 -*-
"""W-3 · 门一核验件（第7、17条）

- 核验两项属性之证据：可验证（verifiable）＋ 不可篡改（tamper_evident）是否成立；
- 核验 ⭐前置于定级（Q-5：gate1_seq < tier_seq）；核验不通过 ⟹ ⛔不予定级、⛔不得入网；
- 外部硬件锚：须评审定级·一事一议（Q-4：任一评审覆盖条目数==1）；
  未过评审者 ⛔不带档（Q-3′）；评审核心＝能否提供「锚定根物理变迁」之法律可采信证据（第8条）。

照追加件口径（AMEND-1 第17条，冲突以追加件为准）：
- 「可采信」判准 ＝ 可验证 ＋ 不可篡改，判者 ＝ 我方单方（N-22 已定；本体附表一该行已删除）；
- 可信信息自证（第18条）：数据自带其信息数据，⛔ 不设外部补料门槛；仅 IP 不能自证 ⟹ 判告警；
- 评审与承认（第19条）：外部先做、我方复核评审后承认、评审主体＝我方、两道门不变；
- 核验之技术字段形态归我方自办（N-23），本件只承载判据，不代定形态取值。
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Evidence:
    ref: str                       # 证据引用（⛔ 不落凭据值）
    verifiable: bool               # 可验证：第三方可查证
    tamper_evident: bool           # 不可篡改：防事后改
    is_external_hardware: bool = False
    review_passed: Optional[bool] = None   # 外部硬件锚之评审结论（一事一议）


class Gate1Rejected(Exception):
    code = 'GATE1-REJECT'


@dataclass
class ReviewRecord:
    review_id: str
    anchor_ref: str
    covers_count: int            # Q-4：必须为 1（一事一议）
    core_checked: bool           # 评审核心＝法律可采信之物理变迁证据
    passed: bool


@dataclass
class Gate1Log:
    """核验流水：seq 单调递增；定级只可在核验之后登记。"""
    entries: list = field(default_factory=list)
    _seq: int = 0

    def _next(self, kind: str):
        self._seq += 1
        return self._seq

    def verify(self, ev: Evidence) -> int:
        """核验（门一主体）。返回核验序号。不通过即拒。"""
        seq = self._next('gate1')
        if not (ev.verifiable and ev.tamper_evident):
            self.entries.append({'seq': seq, 'kind': 'gate1', 'ref': ev.ref,
                                 'result': 'REJECT'})
            raise Gate1Rejected(f'核验不通过：可验证={ev.verifiable} '
                                f'不可篡改={ev.tamper_evident}（第7条）')
        if ev.is_external_hardware:
            # Q-3′：未过评审之外部硬件锚 ⛔不带档、⛔不予定级
            if ev.review_passed is not True:
                self.entries.append({'seq': seq, 'kind': 'gate1',
                                     'ref': ev.ref, 'result': 'REJECT-NO-REVIEW'})
                raise Gate1Rejected('外部硬件锚未过评审 ⛔不予定级（第8条/Q-3′）')
        self.entries.append({'seq': seq, 'kind': 'gate1', 'ref': ev.ref,
                             'result': 'PASS'})
        return seq

    def register_review(self, rec: ReviewRecord):
        """评审登记：Q-4 一事一议——覆盖数必须为 1。"""
        seq = self._next('review')
        if rec.covers_count != 1:
            self.entries.append({'seq': seq, 'kind': 'review',
                                 'review_id': rec.review_id, 'result': 'REJECT-BATCH'})
            raise Gate1Rejected('评审 ⛔ 不得批量覆盖（Q-4：覆盖条目数必须为 1）')
        if not rec.core_checked:
            raise Gate1Rejected('评审未核「锚定根物理变迁之法律可采信证据」（第8条）')
        self.entries.append({'seq': seq, 'kind': 'review',
                             'review_id': rec.review_id,
                             'anchor_ref': rec.anchor_ref,
                             'passed': rec.passed, 'result': 'RECORDED'})
        return seq

    def register_tier(self, subject_ref: str, verdict, gate1_seq: int) -> int:
        """定级登记（Q-5：tier_seq > gate1_seq，核验前置）。"""
        if gate1_seq >= self._seq + 1:
            pass
        seq = self._seq + 1
        if not gate1_seq < seq:
            raise Gate1Rejected('定级未前置核验（Q-5）')
        if verdict.is_tier and not verdict.evidence_ref:
            raise Gate1Rejected('定档无证据引用（Q-14）')
        self._seq = seq
        self.entries.append({'seq': seq, 'kind': 'tier', 'subject': subject_ref,
                             'outcome': verdict.outcome, 'evidence_ref': verdict.evidence_ref,
                             'gate1_seq': gate1_seq, 'result': 'TIERED'})
        return seq
