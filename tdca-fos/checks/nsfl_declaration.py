# -*- coding: utf-8 -*-
"""
TDCA 负空间声明文件 — REPO-003 绝对负空间（NSFL）
制度锚定: TDCA-KG-001 §2.2 NSFLRule | ID38 破例识别 | ID85/ID86 熔断
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

声明: 以下领域属于本系统绝对负空间，任何代码/查询/推理不得触碰。
NSFL-Declaration:
  - 本声明文件自身不可被修改（OTA 不可升级锚点同等级）
SPDX-License-Identifier: TDCA-Internal
"""

LEGAL_NSFL = {
    "id": "NSFL-LEGAL-001",
    "scope": "法律负空间",
    "rule": "LEGAL-BOUNDARY-002",
    "prohibitions": [
        "不得将知识图谱用于任何违反中国现行法律法规的查询或推理",
        "不得通过技术手段绕过数据主权、隐私保护、网络安全相关法规",
    ],
    "action": "BLOCKED + ALT-PATH-001",
    "human_override": False,
}

INSTITUTIONAL_NSFL = {
    "id": "NSFL-INST-001",
    "scope": "制度负空间",
    "rule": "LEGAL-BOUNDARY-002 / ID38",
    "immutable_anchors": [
        "REPO-003-type-tag",   # 七库类型标签（TypeSystem §9.3）
        "NCA-BIDIRECTIONAL",   # NCA 双向地位
        "IP-QUANTUM",          # IP 库 quantum 属性
        "NCA-IMMUTABLE",       # NCA 不可删除
    ],
    "prohibitions": [
        "不得修改 TypeSystem-Confirmation-001 §9.3 不可升级核心锚点",
        "任何试图'破例'修改锚点的代码必须被 NSFL 熔断器自动阻断",
    ],
    "action": "BLOCKED + 宪法修正案慢系统流程",
    "human_override": False,
}

COGNITIVE_NSFL = {
    "id": "NSFL-COG-001",
    "scope": "认知负空间",
    "prohibitions": [
        "不得将知识库用于生成虚假制度原理",
        "不得伪造宪法条目",
        "不得虚构 NCA 存证",
        "所有知识单元必须溯源至真实白皮书文本",
    ],
    "action": "BLOCKED + 溯源校验",
    "human_override": False,
}

ECONOMIC_NSFL = {
    "id": "NSFL-ECO-001",
    "scope": "经济负空间",
    "prohibitions": [
        "不得在没有真实税收数据支撑的情况下模拟或伪造 MOU 锚定值",
        "MOU 必须是真实进项/出项税收的映射（ID79 / ID92）",
    ],
    "action": "BLOCKED + 税收数据核验",
    "human_override": False,
}

ALL_NSFL = [LEGAL_NSFL, INSTITUTIONAL_NSFL, COGNITIVE_NSFL, ECONOMIC_NSFL]


def get_nsfl_declarations() -> list:
    """返回全部负空间声明"""
    return list(ALL_NSFL)
