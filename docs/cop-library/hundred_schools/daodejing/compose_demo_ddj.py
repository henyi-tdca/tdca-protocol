# -*- coding: utf-8 -*-
"""道德经章句 ⟂ TDCA核心 化合实证 (道家系统思维基库 · 跨范式化合空间验证)
验证: 道德经章句(如第36章 将欲歙之/微明/柔弱胜刚强) 作为 interpretant 注入 TDCA 核心-02 可审计自主决策,
证明"章句级 COP"已进入 compose_general 跨范式化合空间, 为"中国文化 ⊕ 马克思主义"化合提供中方基协议素材。
"""
import os
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "config"))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "nca-generator"))
sys.path.insert(0, os.path.join(_THIS, "..", ".."))  # cognitive_compiler 根
sys.path.insert(0, _THIS)

from compositions.compose_general import compose

# 父计 = TDCA 核心-02 可审计自主决策 (显式可信底座协议)
PARENT = os.path.join(_THIS, "..", "..", "tdca_core", "第02核心-可审计自主决策协议.yaml")
# 解释项 = 道德经第36章 (辩证转化·微明·柔弱胜刚强)
INTERP = os.path.join(_THIS, "第36章-将欲歙之.yaml")
OUT_COMP = os.path.join(_THIS, "COMPOSED-第36章_可审计顺势决策.yaml")
OUT_REPORT = os.path.join(_THIS, "COMPOSITION-REPORT-第36章_可审计决策.md")

# 绑定步: 父计"决策门"在'判进/退/待'处的语义被解释项 reframe
BIND_STEP = "判进/退/待"
REFRA = ("可审计自主决策门在'判进/退/待'处, 注入道德经第36章'将欲歙之必固张之'的微明顺势: "
         "决策不只判当下强弱, 更察对手'将歙'之几于未萌, 以柔弱守势待其自反——"
         "自主决策因而既全程可审计留痕, 又合'道之顺势',  emergent='可审计微明顺势决策'。")
PAIR_LABEL = "道德经第36章(将欲歙之/微明/柔弱胜刚强) ⟂ TDCA核心-02(可审计自主决策)"

if __name__ == "__main__":
    print("===== 道德经章句跨范式化合实证 =====")
    compose(PARENT, INTERP, BIND_STEP, REFRA, OUT_COMP, OUT_REPORT,
            fc_id="TDCA-FC-DDJ-COMP36", pair_label=PAIR_LABEL)
    print("[DONE] 组合产物: %s" % OUT_COMP)
    print("[DONE] 实证报告: %s" % OUT_REPORT)
