"""TDCA × openpencil 静默挂载适配器（tdca-openpencil-silent-mount）。

独立组件；协议层对接 ZSeven-W/openpencil 公开接口语义（开放创作工具（公开接口语义）），
不复制上游代码、不修改上游源码、不真实连接上游 API（静默挂载 = 对方零感知）。
仅模拟态试点 · 未实连上游。
"""

from .adapter import TdcaOpenpenSilentMount

__all__ = ["TdcaOpenpenSilentMount"]
__version__ = "0.1.0"
__simulated__ = True
