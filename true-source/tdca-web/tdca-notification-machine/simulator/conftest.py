# -*- coding: utf-8 -*-
"""通知机模拟器套件公共配置（L1SI211-EXTERNAL-FIX-001 A① 补）。

散落件单跑时 rootdir=simulator，上级 conftest 不载——此处再放一份钉载，
与 tdca-notification-machine/conftest.py 同逻辑（sys.modules 幂等守卫，
双载不重复）。engine 包钉载免疫 tools/*/engine.py 常规模块遮蔽；
call_rules_engine 按工作区相对位入 path（树内在册）。
"""
import importlib.util
import os
import sys
from importlib.machinery import ModuleSpec as _ModuleSpec

_NM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tdca-notification-machine/
_WS = os.path.dirname(_NM)                                         # 工作区根

_ENGINE_DIR = os.path.join(_NM, 'engine')
if os.path.isdir(_ENGINE_DIR) and 'engine' not in sys.modules:
    _spec = _ModuleSpec('engine', loader=None, is_package=True)
    _spec.submodule_search_locations = [_ENGINE_DIR]
    sys.modules['engine'] = importlib.util.module_from_spec(_spec)

_CALL_RULES_ENGINE = os.path.join(
    _WS, 'true-source', 'tdca-web', 'tdca-call-rules', 'engine')
if os.path.isdir(_CALL_RULES_ENGINE) and _CALL_RULES_ENGINE not in sys.path:
    sys.path.insert(0, _CALL_RULES_ENGINE)
