# -*- coding: utf-8 -*-
"""TDCA 智能体遗产继承机制模块（G3）——创建主体消亡的权益承接。"""
from .estate import (DISPOSITIONS, Beneficiary, EstateRecord,  # noqa: F401
                     InheritanceError, InheritanceRegistry, Testament)

__all__ = ["InheritanceRegistry", "Testament", "Beneficiary", "EstateRecord",
           "InheritanceError", "DISPOSITIONS"]
