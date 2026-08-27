"""TDCA × ACPs 制度层适配器（tdca-acps-adapter）。

独立 Apache-2.0 组件；协议层对接 ACPs 公开接口契约（AIC/ACS/ADP/AIP），
不复制上游代码、不修改上游源码（只赋能不改码）。
"""

from .adapter import TdcaAcpsAdapter, AllocationResult

__all__ = ["TdcaAcpsAdapter", "AllocationResult"]
__version__ = "0.1.0"
