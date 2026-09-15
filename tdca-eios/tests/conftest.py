# -*- coding: utf-8 -*-
"""EIOS 冒烟测试公共配置（TDCA-PHASE-E-INT-1-SMOKE-TEST）

解决多归档模块同名 `src` 包冲突：
  - TIMA（tdca-tima/src）→ 保持 `src`（EIOS cks_deployment 依赖 `from src.cks_protocol`）
  - FC-012（tdca-flow-orchestrator/src）→ 注册为别名包 `fc012`
其余模块（FC-001/004/005）→ 目录入 sys.path 直接导入
"""
import importlib.util
import os
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 工作区根

# ---- TIMA: 保持 src 包名（EIOS 模块兼容） ----
TIMA_SRC = os.path.join(WS, 'tdca-tima')
sys.path.insert(0, TIMA_SRC)
import src.models          # noqa: E402
import src.cks_protocol    # noqa: E402
import src.l0_legal_memory  # noqa: E402
import src.l1_ownership_memory  # noqa: E402
import src.l2_config_memory  # noqa: E402
import src.l3_utility_memory  # noqa: E402
import src.basis_transformer  # noqa: E402
import src.mindmos_bridge  # noqa: E402

# ---- FC-012: 注册为别名包 fc012（避免 src 冲突） ----
FO_SRC = os.path.join(WS, 'tdca-flow-orchestrator', 'src')


def _register_package(alias: str, src_dir: str):
    pkg_spec = importlib.util.spec_from_file_location(
        alias, os.path.join(src_dir, '__init__.py'),
        submodule_search_locations=[src_dir])
    pkg = importlib.util.module_from_spec(pkg_spec)
    sys.modules[alias] = pkg
    pkg_spec.loader.exec_module(pkg)
    return pkg


_register_package('fc012', FO_SRC)
import fc012.models  # noqa: E402
import fc012.flow_engine  # noqa: E402
import fc012.phase_machine  # noqa: E402
import fc012.mou_closer  # noqa: E402
import fc012.nca_reporter  # noqa: E402
import fc012.fuse_adapter  # noqa: E402

# ---- FC-001 / FC-004 / FC-005 / EIOS src: 目录入 path ----
for p in [
    WS,                                     # tdca_nca_generator.py (FC-001)
    os.path.join(WS, 'tdca-utility-genie'),  # FC-004
    os.path.join(WS, 'tdca-knowledge-graph-compiler'),  # FC-005
    os.path.join(WS, 'tdca-eios', 'src'),   # EIOS M2/M3/M4
]:
    if p not in sys.path:
        sys.path.insert(0, p)
