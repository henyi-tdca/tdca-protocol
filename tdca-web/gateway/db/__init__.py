# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M1 | 目标函数: M1 数据库层——连接工厂（惰性单例：import 不建引擎，环境变量后置于首次调用生效）
# 约束矩阵: 任务书 §二 M1；禁止改 FROZEN 前端；测试库与种子库隔离（python -m 父包先 import 的陷阱由惰性化根除）
# 制度锚点: ID92 / ID85（fail-closed）/ ID79
# 先验分布: KIMI-WEB-DB-M1-DESIGN-001
# 配置权边界: L2 数据层
# 预期分配: Base + get_database_url() + get_engine() + get_session()
# 审计轨迹: NCA-KIMIWEB-003/004
# =============================================================================
"""db 包：声明基类 + 惰性连接工厂（import 时不建引擎）。"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tdca.db")


def get_database_url() -> str:
    """连接串：环境变量 DATABASE_URL 优先；默认 SQLite 文件库（切 PostgreSQL 零改码）。"""
    return os.environ.get("DATABASE_URL", "sqlite:///" + _DEFAULT_PATH)


class Base(DeclarativeBase):
    """全部 10 表的声明基类。"""


_engine = None
_Session = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url(), future=True)
    return _engine


def get_sessionmaker():
    """sessionmaker 单例（支持 .begin() 上下文：提交/回滚 + 自动关闭）。"""
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), autoflush=False, future=True)
    return _Session


def get_session():
    """新会话（每次调用新建 session 实例）。"""
    return get_sessionmaker()()
