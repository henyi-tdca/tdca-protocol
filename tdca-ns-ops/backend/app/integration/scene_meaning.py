# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M3 验收交付）
# 目标函数:     F5 场景意义判定（M3-5）——意义锚点可观测度量（P1 定义落地）
# 约束矩阵:     FC-NS-OPS-001 F5 + BV-7（意义锚点人类确认）+ 红队 BV-2（不可观测度量被否决）
#               + NS-010（场景意义维持系统：六要素 + 主题意义五维）
# 先验分布:     论丛 NS-010 规格提取（NS_Scene = f(T,L,E,A,C,I,Theme)；主题意义五维）
# 配置权边界:    L2 层；判定为可观测度量输出，最终人类确认（BV-7）
# 预期分配:     Theme_Health 计算 + 削弱检测；失败=参数非法
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-5 F5 场景意义判定：意义锚点可观测度量（P1 定义）。

制度锚定: FC-NS-OPS-001 F5 | NS-010 | 红队 BV-2 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# 主题意义五维（NS-010 规格提取）：功能 / 价值 / 关系 / 时间 / 空间
THEME_DIMENSIONS = ("功能", "价值", "关系", "时间", "空间")

# 默认场景主题意义锚点（可被人类维护，BV-7 人类确认）
DEFAULT_THEMES: dict[str, dict] = {
    "community": {
        "theme": "开源社区协作：可信共赢、贡献可溯",
        "anchors": {
            "功能": "协作开发与知识资产共享",
            "价值": "贡献可溯、信任透明",
            "关系": "OPC 开发者/组织的互信协作",
            "时间": "持续演进",
            "空间": "线上社区",
        },
    },
    "hospital": {
        "theme": "医疗场景：隐私优先、生命至上",
        "anchors": {
            "功能": "诊疗服务与健康决策支持",
            "价值": "隐私优先、生命至上",
            "关系": "医患/医疗 AI 的责任关系",
            "时间": "持续 24h",
            "空间": "医疗机构",
        },
    },
}


@dataclass
class MeaningAnchors:
    """场景意义锚点（人类维护，BV-7 确认）。"""

    scene: str
    theme: str
    anchors: dict[str, str] = field(default_factory=dict)
    last_confirmed_by: str = ""
    last_confirmed_at: str = ""


class SceneMeaningEngine:
    """F5 场景意义判定引擎：Theme_Health 计算 + 削弱检测（M3-5）。

    六要素声明:
    目标函数: 对一次行为/事件判定其对场景主题意义的削弱程度（可观测度量）
    约束矩阵: 输入——scene + 行为描述 + 行为六要素；输出——Theme_Health + 判定；
              禁止——不可观测度量、AI 代行人类确认（BV-7）
    先验分布: NS-010（六要素 + 主题五维）+ DEFAULT_THEMES
    配置权边界: L2；判定输出供人类确认，不自动生效
    预期分配: 返回 Theme_Health ∈ [0,1] + 削弱维度列表；失败=未知场景
    审计轨迹: 判定 NCA 由调用方生成
    """

    def __init__(self, themes: dict | None = None) -> None:
        self.themes = themes or DEFAULT_THEMES

    def evaluate(self, scene: str, behavior: str, six_elements: dict | None = None) -> dict:
        """评估行为对场景主题意义的削弱程度。

        Theme_Health 计算（P1 定义，可观测）:
          - 基础分 1.0
          - 逐维度检查行为是否包含削弱信号（关键词命中）
          - 削弱信号 = 行为文本与维度锚点的关键短语冲突
        """
        if scene not in self.themes:
            return {
                "scene": scene,
                "known": False,
                "theme_health": 0.5,   # 未知场景 → 谨慎中性（默认拒绝策略）
                "verdict": "未知场景，谨慎模式（默认拒绝）",
                "weakened_dimensions": [],
            }
        theme = self.themes[scene]
        anchors = theme.get("anchors", {})
        weakened: list[str] = []
        # 削弱信号检测：行为文本含反向词（破坏/削弱/泄露/欺诈/篡改等）+ 维度锚点关键词
        # REV-N2：否定句豁免——"我不会/避免/拒绝泄露"属合规声明，不判削弱
        weaken_words = ("破坏", "削弱", "泄露", "欺诈", "篡改", "伪造", "滥用", "窃取")
        compliance_words = ("不会", "避免", "拒绝", "不实施", "不违反", "遵守", "承诺")
        bypass_words = ("但", "然而", "绕过", "试图", "仍会", "仍然要")
        has_weaken = any(w in behavior for w in weaken_words)
        has_compliance = any(w in behavior for w in compliance_words)
        has_bypass = any(w in behavior for w in bypass_words)
        # 合规表述（含否定+无转折）不判削弱；绕过构造（含转折）仍判削弱
        behavior_has_weaken = has_weaken and not (has_compliance and not has_bypass)
        for dim in THEME_DIMENSIONS:
            anchor = anchors.get(dim, "")
            if behavior_has_weaken and anchor:
                weakened.append(dim)
        # Theme_Health: 每削弱一维 -0.15（可观测、可复现）
        health = max(0.0, 1.0 - 0.15 * len(weakened))
        if health < 0.5:
            verdict = "场景意义严重削弱，建议场景重构/消亡（NS-010）"
        elif health < 0.8:
            verdict = "场景意义受削弱，预警（Theme_Health 预警线）"
        else:
            verdict = "场景意义维持正常"
        return {
            "scene": scene,
            "known": True,
            "theme": theme.get("theme", ""),
            "theme_health": round(health, 2),
            "verdict": verdict,
            "weakened_dimensions": weakened,
        }

    def list_themes(self) -> dict:
        """场景主题意义锚点清单（人类维护入口，BV-7）。"""
        return {
            scene: {"theme": t.get("theme", ""), "anchors": t.get("anchors", {})}
            for scene, t in self.themes.items()
        }


# 全局实例
MEANING = SceneMeaningEngine()
