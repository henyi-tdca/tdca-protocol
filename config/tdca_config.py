"""TDCA 协议网络共享配置 - 路径与常量
来源: TDCA-MEMO-006
所有运行时模块通过本模块解析路径与协议常量。
"""
import os

# .tdca-protocol/ 根
PROTOCOL_ROOT = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# TDCA归档文件夹/ 根
ARCHIVE_ROOT = os.path.normpath(os.path.dirname(PROTOCOL_ROOT))

# 关键路径
NCA_DIR = os.path.join(ARCHIVE_ROOT, ".tdca-nca")
BACKUP_DIR = os.path.join(ARCHIVE_ROOT, ".tdca-backup")
AUDIT_LOG = os.path.join(PROTOCOL_ROOT, "audit", "audit-trail.log")
COGNITIVE_DIR = os.path.join(PROTOCOL_ROOT, "cognitive")
COMPILER_DIR = os.path.join(PROTOCOL_ROOT, "compiler")
NSFL_DIR = os.path.join(PROTOCOL_ROOT, "nsfl-runtime")
CHECKLIST_DIR = os.path.join(PROTOCOL_ROOT, "checklist")

# 协议常量
PROTOCOL_VERSION = "TDCA-PROTOCOL-REASONIX-ALIGNMENT-001 V1.0"
NSFL_VERSION = "V0.1"
OPERATOR = "Reasonix-Executor"

# 认知状态向量初始值（本地操作型 AI 固化）
DEFAULT_COGNITIVE_STATE = {
    "A": ("L2", "受控自主，关键操作需人类签名"),
    "D": ("D2", "基于制度规则推理，不自主创设规则"),
    "L": ("L0", "无在线学习"),
    "C": ("C1", "单智能体执行"),
    "SC": ("SC1", "基础日志记录，通过 NCA 自证"),
}

DEFAULT_MAX_RETRY = 0


def ensure_dirs():
    """确保关键目录存在（幂等）"""
    for d in [NCA_DIR, BACKUP_DIR, os.path.join(PROTOCOL_ROOT, "audit")]:
        os.makedirs(d, exist_ok=True)


def archive_relative(path):
    """返回相对归档根的路径（用于日志可读性）"""
    try:
        return os.path.relpath(path, ARCHIVE_ROOT)
    except ValueError:
        return path
