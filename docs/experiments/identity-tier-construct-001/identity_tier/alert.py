# -*- coding: utf-8 -*-
"""W-5 · 告警工件（第11、13条）

判据：锚数据之上链存证中唯一可信信息＝IP（其余缺失）⟹ 判告警。
处置：⛔ 不径行定档、⛔ 不静默降档；须附补充可信信息要求（⛔ 不得为空）；
状态机：待补 → 已补／已失效。
九字段（附表四）：alert_id／subject_ref／reason／observed／
required_supplement／raised_at／deadline／resolved_at／state。
⚠️ deadline 照追加件口径（N-30）：默认不设固定期限；调用方传 None 即该默认之如实表达（行为不变）。
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid


TZ = timezone(timedelta(hours=8))

ALERT_STATES = ('待补', '已补', '已失效')


@dataclass
class Alert:
    alert_id: str
    subject_ref: str          # ⛔ 不落内部编号与凭据值
    reason: str
    observed: List[str]
    required_supplement: List[str]   # Q-20：⛔ 非空
    raised_at: str
    deadline: Optional[str]          # N-30（追加件口径）：默认不设固定期限；None 即默认
    resolved_at: Optional[str]
    state: str = '待补'

    def to_dict(self):
        return asdict(self)


class AlertError(Exception):
    pass


class AlertWorkproduct:
    """仅 IP 判告警入口；⛔ 告警不与「未达门槛」混同（Q-21 处置字段互异）。"""

    def __init__(self, attest):
        """attest：存证接入件（W-6）——告警判定输入须为上链存证之可信信息。"""
        self.attest = attest
        self.alerts: List[Alert] = []
        self.disposition = {'待补': '要求补料＋补足后重判（不径行定档）',
                            '未达门槛': '不纳入定档＋不接纳入网'}

    def raise_for_ip_only(self, *, subject_ref: str,
                          required_supplement: List[str],
                          deadline: Optional[str] = None,
                          now: Optional[datetime] = None) -> Alert:
        # Q-20：补料要求 ⛔ 不得为空
        if not required_supplement:
            raise AlertError('required_supplement ⛔ 不得为空（Q-20）')
        # H-5：无存证不执行——判定输入须来自存证面
        if self.attest is None or not self.attest.verify():
            raise AlertError('无存证不执行：链验未过（H-5/Q-10）')
        now = now or datetime.now(TZ)
        a = Alert(alert_id=f'ALT-{uuid.uuid4().hex[:12].upper()}',
                  subject_ref=subject_ref,
                  reason='可信信息仅剩 IP（锚数据上链存证之唯一可信信息＝IP）',
                  observed=['IP'],
                  required_supplement=list(required_supplement),
                  raised_at=now.isoformat(),
                  deadline=deadline,       # N-30 追加件口径：默认不设固定期限，None 即默认
                  resolved_at=None,
                  state='待补')
        self.alerts.append(a)
        return a

    def supplement(self, alert_id: str, *, now: Optional[datetime] = None):
        a = self._get(alert_id)
        if a.state != '待补':
            raise AlertError(f'状态机越迁：{a.state} → 已补 不允许')
        a.state = '已补'
        a.resolved_at = (now or datetime.now(TZ)).isoformat()
        return a

    def expire(self, alert_id: str, *, now: Optional[datetime] = None):
        a = self._get(alert_id)
        if a.state != '待补':
            raise AlertError(f'状态机越迁：{a.state} → 已失效 不允许')
        a.state = '已失效'
        a.resolved_at = (now or datetime.now(TZ)).isoformat()
        return a

    def _get(self, alert_id: str) -> Alert:
        for a in self.alerts:
            if a.alert_id == alert_id:
                return a
        raise AlertError(f'告警不存在：{alert_id}')
