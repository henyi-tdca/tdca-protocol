# -*- coding: utf-8 -*-
"""论语篇目 ⟂ TDCA核心 化合实证 (儒家系统思维基库 · 跨范式化合空间验证)
验证: 论语第12篇 颜渊(克己复礼为仁) 作为 interpretant 注入 TDCA 核心-02 可审计自主决策,
证明"篇目级 COP"已进入 compose_general 跨范式化合空间, 为"中国文化 ⊕ 马克思主义"化合提供中方基协议素材。
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
# 解释项 = 论语第12篇 颜渊 (仁本忠恕·克己复礼)
INTERP = os.path.join(_THIS, "第12篇-颜渊.yaml")
OUT_COMP = os.path.join(_THIS, "COMPOSED-第12篇_克己守礼决策.yaml")
OUT_REPORT = os.path.join(_THIS, "COMPOSITION-REPORT-第12篇_可审计决策.md")

# 绑定步: 父计"决策门"在'判进/退/待'处的语义被解释项 reframe
BIND_STEP = "判进/退/待"
REFRA = ("可审计自主决策门在'判进/退/待'处, 注入论语第12篇'克己复礼为仁'的克己守礼: "
         "决策不只求全程可审计留痕, 更须以'克己'(节制私欲)与'复礼'(归正规范)为前置约束——"
         "自主决策因而既全程可审计, 又受仁礼框范、不为私利逾矩,  emergent='克己守礼的可审计自主决策'。")
PAIR_LABEL = "论语第12篇(颜渊·克己复礼为仁) ⟂ TDCA核心-02(可审计自主决策)"

if __name__ == "__main__":
    print("===== 论语篇目跨范式化合实证 =====")
    compose(PARENT, INTERP, BIND_STEP, REFRA, OUT_COMP, OUT_REPORT,
            fc_id="TDCA-FC-LYU-COMP12", pair_label=PAIR_LABEL)
    print("[DONE] 组合产物: %s" % OUT_COMP)
    print("[DONE] 实证报告: %s" % OUT_REPORT)
