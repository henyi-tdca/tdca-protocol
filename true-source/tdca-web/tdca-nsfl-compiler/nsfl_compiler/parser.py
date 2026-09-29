# -*- coding: utf-8 -*-
"""
C1 · NSFL 语法分析器（Parser）
=============================
Token 流 → AST（NSFLDeclaration）。

文法（V0.1，对齐 lexer.py BNF）:
  declaration := "NSFL" ":" operator ns_type "." action [params] ["|" parameter] ["@" layer] [note]
  operator    := "⊗" | "⊘" | "⊙"
  ns_type     := IDENT
  action      := IDENT（可含 . 分段，如 data.leak）
  params      := "(" arg ("," arg)* ")"
  parameter   := arg
  layer       := IDENT
  note        := NOTE

锚定: DCD-NSFL-COMPILER-001（C1）+ D2-NSFL-UNION-SCHEMA-001（NS_Type/NS_Rule 结构）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .lexer import NSFLSyntaxError, NSFLToken, NSFLTokenType, NSFLLexer


@dataclass(frozen=True)
class NSFLDeclaration:
    """NSFL 声明 AST 节点。"""

    operator: str                 # ⊗ / ⊘ / ⊙
    ns_type: str                  # LEGAL / DATA_CROSS_BORDER / ...
    action: str                   # 行为标识（分段连接，如 data.leak）
    args: List[str] = field(default_factory=list)      # 调用参数
    parameter: Optional[str] = None   # ⊘/⊙ 操作数（数值/档位/域标签）
    layer: Optional[str] = None       # 显式 IIE 层标注（L0/L1/L2）
    note: str = ""                # 自然语言语义注释（C1 语义分析输入）
    line: int = 0
    col: int = 0

    @property
    def operator_name(self) -> str:
        """运算符语义名（⊗→FORBID / ⊘→LIMIT / ⊙→SCENE）。"""
        from .lexer import OPERATOR_LITERALS
        return OPERATOR_LITERALS[self.operator]

    def to_dict(self) -> dict:
        return {
            "operator": self.operator,
            "operator_name": self.operator_name,
            "ns_type": self.ns_type,
            "action": self.action,
            "args": list(self.args),
            "parameter": self.parameter,
            "layer": self.layer,
            "note": self.note,
            "line": self.line,
            "col": self.col,
        }


class NSFLParser:
    """递归下降解析器（单声明）。"""

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[NSFLToken] = []
        self.index = 0

    # ---- 工具 ----

    def _peek(self) -> NSFLToken:
        return self.tokens[self.index]

    def _next(self) -> NSFLToken:
        tok = self.tokens[self.index]
        if tok.type != NSFLTokenType.EOF:
            self.index += 1
        return tok

    def _expect(self, ttype: NSFLTokenType, msg: str) -> NSFLToken:
        tok = self._peek()
        if tok.type != ttype:
            raise NSFLSyntaxError(f"{msg}（期望 {ttype.value}，实际 {tok.type.value} {tok.value!r}）", tok.line, tok.col)
        return self._next()

    def _accept(self, ttype: NSFLTokenType) -> Optional[NSFLToken]:
        if self._peek().type == ttype:
            return self._next()
        return None

    # ---- 入口 ----

    def parse(self) -> NSFLDeclaration:
        self.tokens = NSFLLexer(self.source).tokenize()
        self.index = 0
        return self._parse_declaration()

    def parse_many(self) -> List[NSFLDeclaration]:
        """解析多声明（以换行/分号分隔不在此文法内——V0.1 单声明；多声明由编译器层切分）。"""
        return [self.parse()]

    # ---- 文法 ----

    def _parse_declaration(self) -> NSFLDeclaration:
        head = self._expect(NSFLTokenType.NSFL, "声明必须以 NSFL 关键字开头")
        self._expect(NSFLTokenType.COLON, "NSFL 后须跟冒号")
        op_tok = self._expect(NSFLTokenType.OPERATOR, "须声明运算符 ⊗/⊘/⊙")
        ns_type_tok = self._expect(NSFLTokenType.IDENT, "运算符后须跟 NS_Type（如 LEGAL）")
        self._expect(NSFLTokenType.DOT, "NS_Type 后须跟 '.'")
        action_tok = self._expect(NSFLTokenType.IDENT, "'.' 后须跟行为标识（action）")

        # 行为标识允许分段（data.leak → data.leak）
        action = action_tok.value
        while self._peek().type == NSFLTokenType.DOT:
            self._next()
            part = self._expect(NSFLTokenType.IDENT, "分段标识符缺失")
            action = f"{action}.{part.value}"

        # 可选调用参数 (args)
        args: List[str] = []
        if self._accept(NSFLTokenType.LPAREN):
            if self._peek().type != NSFLTokenType.RPAREN:
                args.append(self._parse_arg())
                while self._accept(NSFLTokenType.COMMA):
                    args.append(self._parse_arg())
            self._expect(NSFLTokenType.RPAREN, "参数列表未闭合")

        # 可选操作数 | parameter
        parameter: Optional[str] = None
        if self._accept(NSFLTokenType.PIPE):
            parameter = self._parse_arg()

        # 可选 IIE 层 @ layer
        layer: Optional[str] = None
        if self._accept(NSFLTokenType.AT):
            layer_tok = self._expect(NSFLTokenType.IDENT, "@ 后须跟层标识（L0/L1/L2）")
            layer = layer_tok.value

        # 可选语义注释
        note = ""
        if self._peek().type == NSFLTokenType.NOTE:
            note = self._next().value

        # 尾部不应有其余 token（除 EOF）
        trailing = self._peek()
        if trailing.type != NSFLTokenType.EOF:
            raise NSFLSyntaxError(f"声明后存在多余 token: {trailing.value!r}", trailing.line, trailing.col)

        return NSFLDeclaration(
            operator=op_tok.value,
            ns_type=ns_type_tok.value,
            action=action,
            args=args,
            parameter=parameter,
            layer=layer,
            note=note,
            line=head.line,
            col=head.col,
        )

    def _parse_arg(self) -> str:
        tok = self._peek()
        if tok.type in (NSFLTokenType.NUMBER, NSFLTokenType.STRING, NSFLTokenType.IDENT):
            first = self._next().value
            # 参数支持 "max:100" / "domain:tag" 组合（IDENT COLON arg）
            if self._peek().type == NSFLTokenType.COLON:
                self._next()
                rest = self._parse_arg()
                return f"{first}:{rest}"
            return first
        raise NSFLSyntaxError(f"非法参数 token: {tok.type.value} {tok.value!r}", tok.line, tok.col)
