# -*- coding: utf-8 -*-
"""
C1 · NSFL 词法分析器（Lexer）
=============================
将 NSFL 源码文本切分为 Token 流。

文法（BNF，V0.1）:
  declaration := "NSFL" ":" operator ns_type "." action [params] ["|" parameter] ["@" layer] [note]
  operator    := "⊗" | "⊘" | "⊙"
  ns_type     := IDENT          # schema 注册的 NS_Type（LEGAL / DATA_CROSS_BORDER / ...）
  action      := IDENT          # 行为/操作标识（可含分段，如 data.leak）
  params      := "(" arg ("," arg)* ")"
  arg         := NUMBER | STRING | IDENT
  parameter   := arg            # ⊘/⊙ 的操作数（数值/档位/域标签）
  layer       := IDENT          # 可选 IIE 层显式标注（L0/L1/L2）
  note        := "—" TEXT | "#" TEXT | "//" TEXT   # 自然语言语义注释（C1 语义分析输入）

锚定: D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL §三（NS_Type 枚举）
     + DCD-NSFL-COMPILER-001（C1 词法/语法/语义分析）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class NSFLTokenType(Enum):
    NSFL = "NSFL"            # 关键字 NSFL
    COLON = "COLON"          # :
    OPERATOR = "OPERATOR"    # ⊗ ⊘ ⊙
    IDENT = "IDENT"          # 标识符
    DOT = "DOT"              # .
    NUMBER = "NUMBER"        # 数值（整数/小数/指数）
    STRING = "STRING"        # 引号字符串
    LPAREN = "LPAREN"        # (
    RPAREN = "RPAREN"        # )
    COMMA = "COMMA"          # ,
    PIPE = "PIPE"            # |
    AT = "AT"                # @
    NOTE = "NOTE"            # 自然语言语义注释（— / # / // 起）
    EOF = "EOF"              # 流结束


@dataclass(frozen=True)
class NSFLToken:
    type: NSFLTokenType
    value: str
    line: int
    col: int

    def __repr__(self) -> str:  # pragma: no cover - 调试辅助
        return f"NSFLToken({self.type.value}, {self.value!r}, L{self.line}:C{self.col})"


# 运算符字面量 → 语义名（C2 执行语义见 operators.py）
OPERATOR_LITERALS = {"⊗": "FORBID", "⊘": "LIMIT", "⊙": "SCENE"}

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NUMBER_RE = re.compile(r"\d+(\.\d+)?([eE][+-]?\d+)?")
_STRING_QUOTES = {"'", '"'}


class NSFLSyntaxError(ValueError):
    """词法/语法错误（携带位置）。"""

    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"NSFL 语法错误 @L{line}:C{col}: {message}")
        self.message = message
        self.line = line
        self.col = col


class NSFLLexer:
    """NSFL 源码 → Token 流（一次扫描，位置完整）。"""

    def __init__(self, source: str):
        if not isinstance(source, str):
            raise TypeError("NSFL 源码必须为 str")
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    # ---- 字符工具 ----

    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else ""

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_ws(self) -> None:
        while self.pos < len(self.source) and self._peek() in " \t\r\n":
            self._advance()

    def _error(self, msg: str) -> NSFLSyntaxError:
        return NSFLSyntaxError(msg, self.line, self.col)

    # ---- 主入口 ----

    def tokenize(self) -> List[NSFLToken]:
        tokens: List[NSFLToken] = []
        while self.pos < len(self.source):
            self._skip_ws()
            if self.pos >= len(self.source):
                break
            ch = self._peek()
            line, col = self.line, self.col

            # 注释/语义注释（— 或 # 或 //）→ NOTE token（吸收至行尾）
            if ch in ("—", "–") or ch == "#":
                tokens.append(self._read_note())
                continue
            if ch == "/" and self._peek(1) == "/":
                tokens.append(self._read_note())
                continue

            # 运算符
            if ch in OPERATOR_LITERALS:
                self._advance()
                tokens.append(NSFLToken(NSFLTokenType.OPERATOR, ch, line, col))
                continue

            # 单字符符号
            single = {
                ":": NSFLTokenType.COLON,
                ".": NSFLTokenType.DOT,
                "(": NSFLTokenType.LPAREN,
                ")": NSFLTokenType.RPAREN,
                ",": NSFLTokenType.COMMA,
                "|": NSFLTokenType.PIPE,
                "@": NSFLTokenType.AT,
            }
            if ch in single:
                self._advance()
                tokens.append(NSFLToken(single[ch], ch, line, col))
                continue

            # 字符串
            if ch in _STRING_QUOTES:
                tokens.append(self._read_string())
                continue

            # 数字（含负数：-5 / -0.5）
            if ch.isdigit() or (ch == "-" and self._peek(1).isdigit()):
                start = self.pos
                if ch == "-":
                    self._advance()
                m = _NUMBER_RE.match(self.source, self.pos)
                if m is None:
                    raise self._error(f"非法数字字面量: {self.source[start:self.pos+8]!r}")
                text = self.source[start:self.pos + len(m.group(0))]
                for _ in range(len(text) - (self.pos - start)):
                    self._advance()
                tokens.append(NSFLToken(NSFLTokenType.NUMBER, text, line, col))
                continue

            # 标识符
            if ch.isalpha() or ch == "_":
                m = _IDENT_RE.match(self.source, self.pos)
                text = m.group(0)
                for _ in text:
                    self._advance()
                if text == "NSFL":
                    tokens.append(NSFLToken(NSFLTokenType.NSFL, text, line, col))
                else:
                    tokens.append(NSFLToken(NSFLTokenType.IDENT, text, line, col))
                continue

            raise self._error(f"未预期字符 {ch!r}")

        tokens.append(NSFLToken(NSFLTokenType.EOF, "", self.line, self.col))
        return tokens

    # ---- 读取器 ----

    def _read_note(self) -> NSFLToken:
        """吸收注释/语义注释至行尾（保留文本供 C1 语义分析）。"""
        line, col = self.line, self.col
        if self._peek() in ("—", "–", "#") or (self._peek() == "/" and self._peek(1) == "/"):
            self._advance()
            if self._peek() == "/":
                self._advance()
        start = self.pos
        while self.pos < len(self.source) and self._peek() != "\n":
            self._advance()
        text = self.source[start:self.pos].strip()
        return NSFLToken(NSFLTokenType.NOTE, text, line, col)

    def _read_string(self) -> NSFLToken:
        line, col = self.line, self.col
        quote = self._advance()
        buf: List[str] = []
        while self.pos < len(self.source):
            ch = self._advance()
            if ch == "\\":
                if self.pos >= len(self.source):
                    break
                buf.append(self._advance())
                continue
            if ch == quote:
                return NSFLToken(NSFLTokenType.STRING, "".join(buf), line, col)
            buf.append(ch)
        raise self._error("未闭合字符串")
