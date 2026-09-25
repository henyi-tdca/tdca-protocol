# -*- coding: utf-8 -*-
"""道德经 ⟂ TDCA核心-02 化合实证 (验证中文化合基库 operand 进 compose_general 跨范式空间)
绑定步: 道德经主原语 dao_fa_zi_ran 的 step "顺因循理" 被 TDCA核心-02 解释项机制重构。
"""
import os
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "compositions"))

from compose_general import compose

PARENT = os.path.join(_THIS, "第01百家-道德经 (道家根本经典).yaml")
INTERP = os.path.join(_THIS, "..", "tdca_core", "第02核心-可审计自主决策协议.yaml")

if __name__ == "__main__":
    composed, nid, npath = compose(
        PARENT, INTERP,
        bind_step="顺因循理",
        reframe_text=("自主决策须以'道法自然'为元准则: 决策门不只判进/退/待, 更须顺因循理、不强为——"
                      "在必败/不可逆情境主动'不退而待'转为顺势蓄势; 原语状态机调度下游 skill 时遵循无为而治:"
                      "定方向放权、不代庖, 让 skill 自组织执行; NSFL 护栏即'道'之红线(逆道妄为即熔断)。"
                      "可审计顺势自主决策: 人类审计的是'是否顺道 + 是否留痕 + 是否守底线', 而非逐条指令。"),
        out_comp=os.path.join(_THIS, "COMPOSED-道德经_可审计决策.yaml"),
        out_report=os.path.join(_THIS, "COMPOSITION-REPORT-道德经_可审计决策.md"),
        fc_id="TDCA-FC-HS-COMPOSE-0102",
        pair_label="道德经(中国文化) ⟂ TDCA核心-02(可审计自主决策)",
    )
    print("[COMPOSED] %s" % composed["COP-ID"])
    print("[REPORT] %s" % os.path.join(_THIS, "COMPOSITION-REPORT-道德经_可审计决策.md"))
    print("[NCA] %s" % nid)
    print("[DONE] 工作区 NCA 总数=%d" % len(__import__("nca_generator").list_ncas()))
