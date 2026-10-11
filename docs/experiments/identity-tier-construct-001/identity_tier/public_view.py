# -*- coding: utf-8 -*-
"""W-7 · 公开面字段件（第14条：只引不回写）

公开面四字段（在册登记公开口径）：权属信息／授权信息／授权状态／获取方式。
四条不公开（Q-8 零命中）：内部编号词面／凭据值／人名／本机真实路径串。
出域事件（Q-9）：主键仍为我方码，外部码仅随附。
"""
import re
from dataclasses import dataclass

PUBLIC_FIELDS = ('权属信息', '授权信息', '授权状态', '获取方式')

_FORBIDDEN_PATTERNS = {
    '内部编号词面': re.compile(r'GSEQ-\d+|L1-SI-\d+|NCA-[0-9A-F]{12}'),
    '凭据值': re.compile(r'(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+', re.I),
    '人名': re.compile(r'[\u4e00-\u9fff]{2,4}(?=:)|创始人|管理员(?:姓|$)'),
    '本机真实路径串': re.compile(r'[A-Za-z]:\\Users\\[^\s\\/]+'),
}


@dataclass(frozen=True)
class PublicRecord:
    权属信息: str
    授权信息: str
    授权状态: str
    获取方式: str
    primary_key: str          # 我方码
    external_code: str = None  # 外部码仅随附（出域）


class PublicViewError(Exception):
    pass


def render_public_view(rec: PublicRecord) -> dict:
    """四字段齐校验＋不公开零命中扫描（Q-8）；主键＝我方码（Q-9）。"""
    view = {k: getattr(rec, k) for k in PUBLIC_FIELDS}
    missing = [k for k, v in view.items() if v is None or str(v).strip() == '']
    if missing:
        raise PublicViewError(f'公开面缺字段：{missing}（Q-8）')
    for k, v in view.items():
        for label, pat in _FORBIDDEN_PATTERNS.items():
            if pat.search(str(v)):
                raise PublicViewError(f'不公开内容命中[{label}]于字段[{k}]（Q-8）')
    if not rec.primary_key:
        raise PublicViewError('出域事件主键必须为我方码（Q-9）')
    out = dict(view)
    out['primary_key'] = rec.primary_key            # 主键＝我方码
    if rec.external_code:
        out['external_code_attached'] = rec.external_code  # 外部码仅随附
    return out
