# -*- coding: utf-8 -*-
"""W-2 · 判定引擎（TDCA-REG-IDENTITY-TIER-001 第6条）

判定式（次序）：
1. 取两属性（设备唯一性、物理地址可移动性）＋ 证据引用；
2. 唯一且保持 ⟹ 固锚级；3. 唯一而可移 ⟹ 移锚级；
4. 非唯一（有注册实名认证账号）⟹ 记名级；
5. 仅 IP ⟹ 待补（告警）；匿名 ⟹ 未达门槛。

红线（Q-13/Q-14/Q-15/Q-16/Q-17/Q-18）：
- ⛔ 不以根之类型为唯一输入（判定函数签名＝两属性＋证据）；
- ⛔ 定档不得无证据引用；两项属性缺一即降档；
- 同类型之根不必然同档（视证据）。
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Verdict:
    outcome: str            # 固锚级 / 移锚级 / 记名级 / 未达门槛 / 待补
    rank: Optional[int]     # 1..4；待补/未达门槛为 None
    evidence_ref: Optional[str]
    is_tier: bool           # 是否已定档（待补/未达门槛=False）
    is_state_pending: bool = False   # 待补（告警态）


class RefusedNoEvidence(Exception):
    """Q-14：定档不得无证据引用。"""
    code = 'Q-14'


class RefusedTypeOnly(Exception):
    """Q-15：⛔ 不得单凭根之类型定档。"""
    code = 'Q-15'


def classify(*, device_unique: Optional[bool] = None,
             address_stable: Optional[bool] = None,
             evidence_ref: Optional[str] = None,
             has_verified_account: bool = False,
             ip_only: bool = False,
             anonymous: bool = False,
             root_type: Optional[str] = None) -> Verdict:
    """第6条判定式。两属性＋证据为输入；root_type 仅作注记，⛔ 不作定档依据。

    - 仅 IP（无设备属性、无实名账号）⟹ 待补（is_tier=False，转告警）；
    - 匿名 ⟹ 未达门槛（⛔ 不入网，由门二执行）；
    - 两项属性缺一即降档：缺唯一性但有实名账号 ⟹ 记名级。
    """
    # Q-15：若调用方只给 root_type、两属性全缺 ⟹ 拒绝（不以类型为唯一输入）
    if root_type is not None and device_unique is None and address_stable is None \
            and not has_verified_account and not ip_only and not anonymous:
        raise RefusedTypeOnly('⛔ 单凭根之类型不得定档（第6条）')

    # Q-16：匿名 ⟹ 未达门槛，⛔ 不得获可信档
    if anonymous:
        return Verdict('未达门槛', None, None, is_tier=False)

    # 第10/11条：仅 IP ⟹ 待补（告警态），⛔ 不径行定档
    if ip_only or (device_unique is None and not has_verified_account
                   and not anonymous):
        return Verdict('待补', None, None, is_tier=False, is_state_pending=True)

    # Q-14：以下分支皆属"定档"，必须带证据引用
    if device_unique is True or has_verified_account or \
            (device_unique is False):
        if not evidence_ref:
            raise RefusedNoEvidence('⛔ 定档不得无证据引用（第6条/GSEQ-4347）')

    if device_unique is True:
        # 唯一且保持 ⟹ 一档；唯一而可移 ⟹ 二档（Q-17：可移⛔不落一档）
        if address_stable is True:
            return Verdict('固锚级', 1, evidence_ref, is_tier=True)
        if address_stable is False:
            return Verdict('移锚级', 2, evidence_ref, is_tier=True)
        # 两属性缺一即降档：唯一性在、地址保持未知 ⟹ 不得落一档
        return Verdict('移锚级', 2, evidence_ref, is_tier=True)

    if device_unique is False:
        # Q-18：不唯一 ⟹ ⛔ 不得落第一、二档
        if has_verified_account:
            return Verdict('记名级', 3, evidence_ref, is_tier=True)
        # 不唯一且无实名账号 ⟹ 证据不足，落待补
        return Verdict('待补', None, None, is_tier=False, is_state_pending=True)

    raise ValueError('输入不满足第6条判定式之任何分支')
