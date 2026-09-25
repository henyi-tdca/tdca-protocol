# -*- coding: utf-8 -*-
"""大学纲目 ⟂ TDCA核心 化合实证 (儒家系统思维纲领库 · 跨范式化合空间验证)
验证: 大学第03目 止于至善(知止有定) 作为 interpretant 注入 TDCA 核心-02 可审计自主决策,
证明"纲目级 COP"已进入 compose_general 跨范式化合空间, 为"中国文化 ⊕ 辩证实践方法论"化合提供中方基协议素材。
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
# 解释项 = 大学第03目 止于至善 (三纲总摄·知止有定)
INTERP = os.path.join(_THIS, "第03目-止于至善.yaml")
OUT_COMP = os.path.join(_THIS, "COMPOSED-第03目_知止决策.yaml")
OUT_REPORT = os.path.join(_THIS, "COMPOSITION-REPORT-第03目_可审计决策.md")

# 绑定步: 父计"决策门"在'判进/退/待'处的语义被解释项 reframe
BIND_STEP = "判进/退/待"
REFRA = ("可审计自主决策门在'判进/退/待'处, 注入大学第03目'止于至善·知止有定'的知止: "
         "决策不只求全程可审计留痕, 更须先'知止'——明确不可为的边界(恰合 NSFL 负空间)与至善目标, "
         "再沿'止→定→静→安→虑→得'阶梯可审计推进。自主决策因而既全程可审计, 又以边界框范不为妄动, "
         "emergent='知止有界的可审计自主决策'。")
PAIR_LABEL = "大学第03目(止于至善·知止有定) ⟂ TDCA核心-02(可审计自主决策)"

if __name__ == "__main__":
    print("===== 大学纲目跨范式化合实证 =====")
    compose(PARENT, INTERP, BIND_STEP, REFRA, OUT_COMP, OUT_REPORT,
            fc_id="TDCA-FC-DXUE-COMP03", pair_label=PAIR_LABEL)
    print("[DONE] 组合产物: %s" % OUT_COMP)
    print("[DONE] 实证报告: %s" % OUT_REPORT)
