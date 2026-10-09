"""paperclip_nca · Paperclip 化合内化包（DCD-PAPERCLIP-COMPOUND-001 M1）

M1a: 编排协议 → TDCA 协作语义编译适配器（ID21 协作即调用）
M1b: 协作调用 → NCA 存证转换
制度锚定: ID21 / BIDIR-001 / ID92
SPDX-License-Identifier: TDCA-Internal
"""
from .adapter import (
    PaperclipAdapter,
    CollabCall,
    CollabNca,
)

__all__ = ["PaperclipAdapter", "CollabCall", "CollabNca"]
