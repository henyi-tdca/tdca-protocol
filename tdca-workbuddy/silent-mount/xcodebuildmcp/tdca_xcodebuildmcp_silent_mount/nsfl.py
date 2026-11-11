# -*- coding: utf-8 -*-
"""挂载引用（EXTERNAL-FIX-002-B）：nsfl 单一实现收敛。
正本：tdca-workbuddy/silent-mount/klavis/tdca_klavis_silent_mount/nsfl.py
归属：xcodebuildmcp/tdca_xcodebuildmcp_silent_mount
本文件不含实现，仅加载正本并再导出全部公开名（挂载语义不变）。
"""
import importlib.util as _ilu
import pathlib as _pl

MOUNT_OWNER = 'xcodebuildmcp/tdca_xcodebuildmcp_silent_mount'
_canon = (_pl.Path(__file__).resolve().parents[2]
          / "klavis" / "tdca_klavis_silent_mount" / "nsfl.py")
_spec = _ilu.spec_from_file_location("tdca_workbuddy_canonical_nsfl", str(_canon))
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
__all__ = [k for k in vars(_mod) if not k.startswith("_")]
