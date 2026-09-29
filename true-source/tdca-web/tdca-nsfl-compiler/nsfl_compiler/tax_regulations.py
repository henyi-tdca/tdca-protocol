# -*- coding: utf-8 -*-
"""TAX 域法规素材表（TDCA-TASK-TAXLAW-001 L-2）——税务官决策依据的法规内容源。

法规源（裁决①，DCD-TAXLAW-001）:
  - KG-LEGAL 种子: L-CN-TX-001/002（税收征管法 63/66 条要点，SEED 模拟态）
  - TDCA 制度条款: 宪法第12条（MOU 锚定）/第18条（税收义务）/定义5.19（税收函数累进）

用途:
  - 供 NSFL 编译器 compile_for_scene 的 legal_refs 内容化（L-3）
  - 供税务官智能体 check_regulatory_compliance 决策依据（L-4）

纪律: 模拟态 SEED（ID92，D-011）；真实法条全文留待 D-010 法学家（ID33 OTA）；
      不引入外部增值税档位（DCD-MICROTAX-003 裁决①）。
"""
from __future__ import annotations

from typing import Dict, List, Optional

# (law_id, title, article, point, severity, fuse_type, domain)
_RAW: tuple = (
    ("L-CN-TX-001", "税收征收管理法", "第63条",
     "禁止偷税（伪造/隐匿账簿、拒不申报）", "HIGH", "LEGAL", "tax"),
    ("L-CN-TX-002", "税收征收管理法", "第66条",
     "禁止骗取出口退税", "HIGH", "LEGAL", "tax"),
    ("TDCA-ART-12", "宪法第十二条", "MOU 锚定规则",
     "MOU=进项税+出项税总和；T(y_t)>0 否则效用权重归零、价格强制归零；禁止场外交易规避税收锚定",
     "HIGH", "LEGAL", "tax"),
    ("TDCA-ART-18", "宪法第十八条", "税收义务",
     "依法履行纳税义务；配置权交易通过智能合约自动计税扣缴；不得规避/逃避/拖延；税务信息真实准确",
     "HIGH", "LEGAL", "tax"),
    ("TDCA-DEF-519", "函数白皮书定义5.19", "税收函数",
     "税收函数是累进的——低效用低税率，高效用高税率，确保税收再分配功能",
     "HIGH", "LEGAL", "tax"),
)

TAX_REGULATIONS: Dict[str, dict] = {
    r[0]: {
        "law_id": r[0], "title": r[1], "article": r[2],
        "point": r[3], "severity": r[4], "fuse_type": r[5],
        "domain": r[6], "simulated": True,   # ID92 模拟态标注（D-011）
    }
    for r in _RAW
}

# 违规模式 → 法规引用（供税务官决策映射）
TAX_VIOLATION_TO_LAW: Dict[str, str] = {
    "tax_evasion": "L-CN-TX-001",          # 偷税
    "tax_fraud_refund": "L-CN-TX-002",     # 骗取出口退税
    "tax_bypass_mou": "TDCA-ART-12",       # 场外规避税收锚定
    "tax_false_report": "TDCA-ART-18",     # 申报失实
    "tax_regressivity": "TDCA-DEF-519",    # 违反累进原则
}


def load_tax_regulations(refs: Optional[List[str]] = None) -> List[dict]:
    """加载 TAX 域法规素材（refs 过滤；缺省返回全部）。

    输出结构: {law_id, title, article, point, severity, fuse_type, domain, simulated}
    """
    if refs is None:
        return list(TAX_REGULATIONS.values())
    out = []
    for ref in refs:
        reg = TAX_REGULATIONS.get(ref)
        if reg:
            out.append(reg)
    return out


def resolve_violation_law(violation: str) -> Optional[dict]:
    """违规模式 → 法规引用（税务官决策轨迹 law_id 解析）。"""
    law_id = TAX_VIOLATION_TO_LAW.get(violation)
    if law_id is None:
        return None
    return TAX_REGULATIONS.get(law_id)
