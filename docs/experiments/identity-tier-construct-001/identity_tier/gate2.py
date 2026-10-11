# -*- coding: utf-8 -*-
"""W-4 · 门二接入件（第15、7条）

入网（另须加载协议、接受制度约束）。⛔ 未过门一不得入网（Q-6）；两道门不可互替。
接入处置按档：固锚/移锚/记名 ⟹ 可接入（按在册准入与登记复用）；
未达门槛 ⟹ ⛔ 不接入；待补 ⟹ ⏳ 补足后重判（接入挂起）。
"""
from dataclasses import dataclass


class Gate2Denied(Exception):
    code = 'GATE2-DENIED'


@dataclass(frozen=True)
class Admission:
    admitted: bool
    loads_protocol: bool
    accepts_constraints: bool
    disposition: str          # 接入／挂起待补／拒入（未达门槛）
    primary_key: str          # 主键＝我方码（Q-9 出域仍为我方码）


class Gate2:
    def admit(self, *, subject_internal_code: str, gate1_passed: bool,
              verdict, accepted_protocol: bool, accepted_constraints: bool) -> Admission:
        # Q-6：未过门一 ⛔ 不得入网；两门不可互替（本门不重复核验属性）
        if not gate1_passed:
            raise Gate2Denied('未过门一 ⛔ 不得入网（第15条/Q-6）')
        if not (accepted_protocol and accepted_constraints):
            raise Gate2Denied('入网须另加载协议并接受制度约束（第15条）')
        if verdict.outcome == '未达门槛':
            # 第9条：匿名/未达门槛 ⛔ 不接纳入网（仅指配置网络接入）
            return Admission(False, True, True, '拒入（未达门槛）',
                             subject_internal_code)
        if verdict.outcome == '待补' or verdict.is_state_pending:
            return Admission(False, False, False, '挂起待补（补足后重判）',
                             subject_internal_code)
        return Admission(True, True, True, '接入',
                         subject_internal_code)

    def can_configure(self, *, admitted: Admission, authorization_defined: bool) -> bool:
        # Q-7：无授权定义之组合 ⛔ 不可配置（无定则默认无授权项）
        return admitted.admitted and authorization_defined
