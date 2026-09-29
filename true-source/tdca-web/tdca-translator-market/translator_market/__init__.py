# -*- coding: utf-8 -*-
"""W4 翻译器市场包（T-P4-002/003）。"""
from .market import SceneTranslatorMarket, TranslatorEntry
from .mou_split import MOUSplitContract, default_mou_value_fn

__all__ = ["MOUSplitContract", "SceneTranslatorMarket", "TranslatorEntry",
           "default_mou_value_fn"]
__version__ = "T-P4-002/003-DEV"
