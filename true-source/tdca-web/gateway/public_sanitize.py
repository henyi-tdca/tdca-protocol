# -*- coding: utf-8 -*-
"""公开面出口脱敏 · 单一真源（L1SI191 TWO-001 B-1：一处定义、多处调用）。

两族同扫（B-2），两处公开面（library /paper/catalog 与 toolshelf /catalog）一律同扫：

① 凭据八形态（在册既有并集，出处：ops_logs_ops._CRED_PATTERNS 四形态
  ＋ library_ops/toolshelf_ops 原 _CATALOG_SENSITIVE 中 TDCA-CRT/TDCA-SES/邮箱/凭据类别词）：
  1 关键词赋值式（password/token/secret/api_key/... 后随 :或= 及值）
  2 sk-[A-Za-z0-9]{8,}
  3 bearer <token>
  4 PEM 私钥头（-----BEGIN ... PRIVATE KEY-----）
  5 TDCA-CRT- 静态令牌
  6 TDCA-SES- 会话令牌
  7 自然人邮箱
  8 凭据类别词（密码/口令/token/secret/凭据）

② 内部编号族（TWO-001 B-2 ②）：
  TDCA- 件号式样（含 200 字截断形）／GSEQ-／L1SI／NCA- 日期／T- 号／ID 号
  ＋在册原有两形态 FC·TL·CI- 与 NC-（保留，不缩面）

白名单（B-3）：只信在册。在册「索引不自造·原文照录」（GSEQ-6847）属前端构建面
（search-index.json），不经本层；本层白名单逐条带依据、⛔ 不通配。当前在册无条目，空表运行。
"""
import re

# ── ① 凭据八形态（组件正则各自带 (?i)；合并时统一 re.IGNORECASE，⛔ 不在 alternation 中途用内联旗标）──
_CRED_KEYWORD_ASSIGN = re.compile(
    r"(password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key|"
    r"authorization|private[_-]?key|client[_-]?secret)\s*[:=]\s*[^\s，。；]+")
_CRED_SK = re.compile(r"sk-[a-z0-9]{8,}", re.IGNORECASE)
_CRED_BEARER = re.compile(r"bearer\s+[a-z0-9._\-]{8,}", re.IGNORECASE)
_CRED_PEM = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE)
_CRED_CRT = re.compile(r"TDCA-CRT-[A-Za-z0-9-]+")
_CRED_SES = re.compile(r"TDCA-SES-[A-Za-z0-9-]+")
_CRED_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_CRED_CATEGORY_WORD = re.compile(r"密码|口令|token|secret|凭据", re.IGNORECASE)

# ── ② 内部编号族 ──
_INTERNAL_TDCA = re.compile(r"TDCA-[A-Z0-9]{2,}(?:-[A-Z0-9-]+)*")
_INTERNAL_LEGACY = re.compile(r"\b(FC|TL|CI)-[A-Z0-9]|\bNC-\d")
_INTERNAL_MISC = re.compile(r"GSEQ-\d+|L1SI\d+|NCA-|\bT-\d{2,}\b|\bID-\d{2,}\b")

# ── 合并出口正则（任一命中即敏感；调用方 fail-closed 语义不变）──
CATALOG_SENSITIVE = re.compile("|".join(
    p.pattern for p in (
        _CRED_KEYWORD_ASSIGN, _CRED_SK, _CRED_BEARER, _CRED_PEM,
        _CRED_CRT, _CRED_SES, _CRED_EMAIL, _CRED_CATEGORY_WORD,
        _INTERNAL_TDCA, _INTERNAL_LEGACY, _INTERNAL_MISC)),
    re.IGNORECASE)

# ── 白名单（B-3：逐条带依据，⛔ 不通配；空表运行）──
# 形态：[(豁免串, 依据), ...]；命中豁免串之字段不判敏感。
# 在册依据示例位（⛔ 未在册明定前不得填）：
#   ("TDCA-PAPER-REVIEW-001", "某某在册件明定本号可现于公开摘要（件号）")
CATALOG_EXEMPTIONS = []  # type: list[tuple[str, str]]


def _exempted(text: str) -> bool:
    for token, _basis in CATALOG_EXEMPTIONS:
        if token in text:
            return True
    return False


def is_catalog_sensitive(text: str) -> bool:
    """出口脱敏判定：命中任一族且不在白名单 → True（fail-closed 由调用方执行）。"""
    if not text:
        return False
    if _exempted(text):
        return False
    return bool(CATALOG_SENSITIVE.search(text))
