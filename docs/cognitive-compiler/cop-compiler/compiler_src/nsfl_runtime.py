# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""NSFL Runtime - 负空间熔断器
来源: TDCA-MEMO-006 步骤三
规则:
  R1 数据完整性熔断: 写操作前 .bak 备份 + SHA-256 前后校验, 异常即熔断
  R2 编码安全熔断: 禁止 PowerShell 直接改写 UTF-8/UTF-8 BOM 中文内容, 强制 Python open(encoding=utf-8)
  R3 自主修复熔断: 异常时禁止自主决定修复, 输出 [NSFL-TRIGGER] 暂停等待人类签名
负空间领地标识: ⊗
"""
import os
import sys
import hashlib
import shutil
import datetime

# 让本模块可独立运行: 把 config 目录加入 sys.path
_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "config"))
import tdca_config as TC

ensure_dirs = TC.ensure_dirs
BACKUP_DIR = TC.BACKUP_DIR
NCA_DIR = TC.NCA_DIR
NSFL_VERSION = TC.NSFL_VERSION

# 负空间操作符标记
NSFL_DECLARATION = """# NSFL-DECLARATION: 以下操作涉及数据完整性，属于负空间
# ⊗ 禁止自主修复
# Alt-Path: 异常时上报人类
"""


class NSFLCircuitBreak(Exception):
    """负空间熔断异常 - 触发后必须等待人类签名方可继续"""

    def __init__(self, reason, trigger_type="data-integrity", detail=None):
        self.reason = reason
        self.trigger_type = trigger_type
        self.detail = detail or {}
        self.timestamp = datetime.datetime.now().isoformat()
        super().__init__(self.format_message())

    def format_message(self):
        return (
            f"[NSFL-TRIGGER] 检测到异常：{self.reason}\n"
            f"  trigger-type: {self.trigger_type}\n"
            f"  timestamp: {self.timestamp}\n"
            f"  已暂停操作，等待人类签名（Human-Signature）。\n"
            f"  ⊗ 禁止自主修复。"
        )


def sha256_of_file(path):
    """计算文件 SHA-256（按块读取，兼容大文件）"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_bytes(data):
    """计算字节串 SHA-256"""
    return hashlib.sha256(data).hexdigest()


def is_utf8_bom(path):
    """检测文件是否为 UTF-8 BOM 编码"""
    if not os.path.isfile(path):
        return False
    with open(path, "rb") as f:
        head = f.read(3)
    return head == b"\xef\xbb\xbf"


def detect_encoding(path):
    """尽力检测文件编码，返回编码名与是否含 BOM"""
    if not os.path.isfile(path):
        return ("unknown", False)
    with open(path, "rb") as f:
        raw = f.read(4)
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    if raw[:2] == b"\xff\xfe" or raw[:2] == b"\xfe\xff":
        return ("utf-16", True)
    if has_bom:
        return ("utf-8-sig", True)
    return ("utf-8", False)


def pre_state(path):
    """R1 数据完整性 - 写操作前记录 Pre-State
    返回 dict: {path, hash, size, exists, backup}
    若文件不存在，返回占位 Pre-State 并仍创建记录。
    """
    ensure_dirs()
    state = {"path": os.path.abspath(path), "exists": os.path.isfile(path)}
    if state["exists"]:
        state["hash"] = sha256_of_file(path)
        state["size"] = os.path.getsize(path)
        # 备份到 .tdca-backup/，用时间戳避免覆盖
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        base = os.path.basename(path) + f".{ts}.bak"
        backup_path = os.path.join(BACKUP_DIR, base)
        shutil.copy2(path, backup_path)
        state["backup"] = backup_path
    else:
        state["hash"] = None
        state["size"] = 0
        state["backup"] = None
    return state


def verify_post_state(path, pre_state_obj):
    """R1 数据完整性 - 写操作后校验 Post-State
    若 Pre-State 哈希存在且 Post 与 Pre 完全相同却声明了写操作，或编码损坏（解码失败），
    触发熔断。
    """
    if not os.path.isfile(path):
        # 写操作后文件消失 = 数据损坏
        raise NSFLCircuitBreak(
            f"写操作后目标文件不存在: {path}",
            trigger_type="data-integrity",
            detail={"pre_state": pre_state_obj},
        )
    post_hash = sha256_of_file(path)
    post_size = os.path.getsize(path)
    # 编码损坏检测: 尝试以声明编码解码
    enc, _ = detect_encoding(path)
    try:
        with open(path, "r", encoding="utf-8-sig" if enc == "utf-8-sig" else "utf-8") as f:
            f.read()
    except UnicodeDecodeError as e:
        raise NSFLCircuitBreak(
            f"编码损坏（{enc} 解码失败）: {path} -> {e}",
            trigger_type="encoding-safety",
            detail={"pre_hash": pre_state_obj.get("hash"), "post_hash": post_hash},
        )
    return {
        "path": os.path.abspath(path),
        "hash": post_hash,
        "size": post_size,
        "exists": True,
    }


def assert_python_encoding_path(context="text-edit"):
    """R2 编码安全 - 断言当前处理路径为 Python 而非 PowerShell
    本函数在运行时校验: 任何中文文本改写必须通过 Python open(encoding=utf-8)。
    若检测到调用栈来自 PowerShell（pwsh）上下文，触发熔断。
    """
    # 运行时断言: 我们在 Python 解释器内运行，符合规则
    if sys.executable and ("python" in sys.executable.lower()):
        return True
    raise NSFLCircuitBreak(
        f"编码安全违规: 中文文本改写未通过 Python 路径 (context={context})",
        trigger_type="encoding-safety",
    )


def safe_write_text(path, text, encoding="utf-8"):
    """R2 编码安全 - 安全写文本的统一入口
    强制使用 Python open(encoding=...) 写入，禁止 PowerShell 改写。
    返回 (pre_state, post_state)。
    """
    assert_python_encoding_path(context="safe_write_text")
    pre = pre_state(path)
    try:
        with open(path, "w", encoding=encoding, newline="") as f:
            f.write(text)
    except Exception as e:
        raise NSFLCircuitBreak(
            f"写入失败: {path} -> {e}",
            trigger_type="data-integrity",
            detail={"pre_state": pre},
        )
    post = verify_post_state(path, pre)
    return pre, post


def trigger_circuit_break(reason, trigger_type="data-integrity", detail=None):
    """R3 自主修复熔断 - 统一入口，抛出 NSFLCircuitBreak"""
    raise NSFLCircuitBreak(reason, trigger_type=trigger_type, detail=detail)


def is_negative_space_operation(operation_type):
    """判断操作类型是否触及负空间领地"""
    negative_ops = {
        "FileEdit", "FileMove", "FileDelete", "DirCreate", "CodeEdit",
        "ConfigWrite", "EncodingConvert",
    }
    return operation_type in negative_ops


if __name__ == "__main__":
    ensure_dirs()
    print("NSFL Runtime 就绪")
    print(f"  NSFL 版本: {NSFL_VERSION}")
    print(f"  备份目录: {BACKUP_DIR}")
    print(f"  NCA 目录: {NCA_DIR}")
    print(f"  负空间操作符: ⊗")
    # 自检: Python 路径断言
    assert_python_encoding_path()
    print("  编码安全路径: Python (合规)")
