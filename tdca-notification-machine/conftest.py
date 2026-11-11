# -*- coding: utf-8 -*-
"""通知机套件公共配置（L1SI211-EXTERNAL-FIX-001 A①）。

engine.notification_machine_engine 依赖 call_rules_engine（CALL-RULES V1.2），
该模块在公开树内（true-source/tdca-web/tdca-call-rules/engine，跟踪在册），
原测试未将其入 path 致公开面收集即败。此处按工作区相对位入 path，零新代码零外部依赖；
路径不存在（非本仓布局）时不动作，由用例自身报缺。
"""
import os
import sys

_WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作区根
_CALL_RULES_ENGINE = os.path.join(
    _WS, 'true-source', 'tdca-web', 'tdca-call-rules', 'engine')
if os.path.isdir(_CALL_RULES_ENGINE) and _CALL_RULES_ENGINE not in sys.path:
    sys.path.insert(0, _CALL_RULES_ENGINE)
