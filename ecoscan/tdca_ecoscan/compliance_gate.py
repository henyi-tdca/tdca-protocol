# SPDX-License-Identifier: Apache-2.0
"""tdca_ecoscan · 公开件机检门（W-7·复用既有合规监控位 NSFL-TRIGGER 闸规约）

对外件发布前机检（不公开四条，命中即阻断）：
  1. 内部编号（内部流转编号体系，如 TDCA-XXX-000 形态）；
  2. 凭据与密钥（AWS AKIA／GitHub ghp_gho／OpenAI sk-／Bearer／PEM 私钥头）；
  3. 自然人敏感信息（身份证号形态——留保守口径，不泛化误伤）；
  4. 负空间词面（调用方传入清单——⛔ 词面本身永不写入输出件，公开即失效）。

口径：
  · check_publication_safe(text, nsfl_terms=None) → 违规类别列表（空＝通过）；
  · assert_publication_safe(...) → 有违规即 raise ValueError（[NSFL-TRIGGER] fail-closed，
    与 commenter 既有闸同一规约——复用既有合规监控位，不新立阻断语义）；
  · 纯函数、零网络、零依赖。
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional

CAT_INTERNAL_ID = "internal_id"       # 内部编号
CAT_CREDENTIAL = "credential"         # 凭据与密钥
CAT_PII = "pii"                       # 自然人敏感信息
CAT_NSFL = "nsfl_term"                # 负空间词面

# 凭据形态（保守清单：高置信模式，宁漏勿误伤）
_CREDENTIAL_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                       # AWS Access Key
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),             # GitHub token
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                    # OpenAI 类 secret
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),          # Bearer token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),     # PEM 私钥头
]

# 内部编号形态：TDCA-大写段-数字段（如 TDCA-OPEN-COLLAB-001 / TDCA-E-123）
_INTERNAL_ID_PATTERN = re.compile(r"\bTDCA-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-\d{2,}\b")

# 自然人敏感信息（保守：18 位身份证号形态，含末位 X）
_PII_PATTERNS = [
    re.compile(r"\b\d{17}[\dXx]\b"),
]


def check_publication_safe(text: str,
                           nsfl_terms: Optional[Iterable[str]] = None) -> List[str]:
    """机检不公开四条；返回命中的违规类别列表（有序去重；空＝通过）。"""
    hits: List[str] = []
    if _INTERNAL_ID_PATTERN.search(text):
        hits.append(CAT_INTERNAL_ID)
    if any(p.search(text) for p in _CREDENTIAL_PATTERNS):
        hits.append(CAT_CREDENTIAL)
    if any(p.search(text) for p in _PII_PATTERNS):
        hits.append(CAT_PII)
    for term in (nsfl_terms or []):
        if term and term in text:
            hits.append(CAT_NSFL)
            break
    # 有序去重保稳定
    seen = set()
    out = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def assert_publication_safe(text: str,
                            nsfl_terms: Optional[Iterable[str]] = None,
                            context: str = "") -> None:
    """fail-closed 阻断：有违规即 raise（NSFL-TRIGGER 规约，与 commenter 闸同源）。"""
    hits = check_publication_safe(text, nsfl_terms)
    if hits:
        where = f"（{context}）" if context else ""
        raise ValueError(
            f"[NSFL-TRIGGER] 公开件机检阻断{where}: 命中 {', '.join(hits)}"
            "——不公开四条 fail-closed，⛔ 不得先发布再补")
