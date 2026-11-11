# -*- coding: utf-8 -*-
"""通知机套件公共配置（L1SI211-EXTERNAL-FIX-001 A①）。

两件确定性的事：
1. engine 包钉载——全量 PYTHONPATH 含 tools/cog_align 等之 engine.py 常规模块
   （常规模块于任何位次胜命名空间包），`import engine` 会被遮蔽成非包。
   此处按文件位直接钉载 tdca-notification-machine/engine 入 sys.modules，
   免疫 path 序（与 app.py 五目录重置顶同理，只加不改导入语义）。
2. call_rules_engine（CALL-RULES V1.2）在公开树内
   （true-source/tdca-web/tdca-call-rules/engine，跟踪在册），原测试未将其入
   path 致公开面收集即败——此处按工作区相对位入 path，零新代码零外部依赖；
   路径不存在（非本仓布局）时不动作，由用例自身报缺。
"""
import importlib.util
import os
import sys

_NM = os.path.dirname(os.path.abspath(__file__))            # tdca-notification-machine/
_WS = os.path.dirname(_NM)                                   # 工作区根

# ---- 1) engine 包钉载（⛔ 被 tools/*/engine.py 常规模块遮蔽之确定性解法） ----
# engine/ 无 __init__.py（命名空间包），手工构造 ModuleSpec 钉入 sys.modules。
from importlib.machinery import ModuleSpec as _ModuleSpec

_ENGINE_DIR = os.path.join(_NM, 'engine')
if os.path.isdir(_ENGINE_DIR) and 'engine' not in sys.modules:
    _spec = _ModuleSpec('engine', loader=None, is_package=True)
    _spec.submodule_search_locations = [_ENGINE_DIR]
    sys.modules['engine'] = importlib.util.module_from_spec(_spec)

# ---- 2) call_rules_engine 入 path（树内在册，补原测试之缺） ----
_CALL_RULES_ENGINE = os.path.join(
    _WS, 'true-source', 'tdca-web', 'tdca-call-rules', 'engine')
if os.path.isdir(_CALL_RULES_ENGINE) and _CALL_RULES_ENGINE not in sys.path:
    sys.path.insert(0, _CALL_RULES_ENGINE)
