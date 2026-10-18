# -*- coding: utf-8 -*-
"""W-6 · 存证接入件（第11条 · 在册链规则）

复用原则（⛔ 不另造一条链）：本件是既有 NCA 哈希链之**接入件**（适配层），
以既有链规则为后端；沙盒位以同规则之本地隔离副本承载（跑完可弃，不触生产链）。
链规则：append-only；每条＝前序哈希 ‖ 本条载荷之 sha256；逐条可复验；断链即拒。
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
import uuid

TZ = timezone(timedelta(hours=8))
GENESIS_PREV = 'GENESIS'


@dataclass
class ChainEntry:
    seq: int
    prev_hash: str
    payload: dict
    entry_hash: str
    attestation_id: str
    at: str

    def recompute(self) -> str:
        body = json.dumps({'seq': self.seq, 'prev_hash': self.prev_hash,
                           'payload': self.payload, 'attestation_id': self.attestation_id,
                           'at': self.at}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(body.encode('utf-8')).hexdigest()


class AttestationChain:
    """在册 NCA 链规则之接入件（沙盒隔离副本）。"""

    def __init__(self):
        self.entries: list = []

    def append(self, payload: dict) -> ChainEntry:
        prev = self.entries[-1].entry_hash if self.entries else GENESIS_PREV
        at = datetime.now(TZ).isoformat()
        aid = f'NCA-{uuid.uuid4().hex[:12].upper()}'
        e = ChainEntry(seq=len(self.entries) + 1, prev_hash=prev,
                       payload=dict(payload), entry_hash='', attestation_id=aid, at=at)
        e.entry_hash = e.recompute()
        self.entries.append(e)
        return e

    def verify(self) -> bool:
        """Q-10：链无断链。逐条复验哈希与前序指针。"""
        prev = GENESIS_PREV
        for e in self.entries:
            if e.prev_hash != prev or e.entry_hash != e.recompute():
                return False
            prev = e.entry_hash
        return True

    def attest(self, *, kind: str, subject_ref: str, summary: str) -> ChainEntry:
        return self.append({'kind': kind, 'subject_ref': subject_ref,
                            'summary': summary})

    def to_dict(self):
        return {'entries': [asdict(e) for e in self.entries],
                'verify': self.verify()}
