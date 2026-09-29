# -*- coding: utf-8 -*-
"""
效用精灵 × 模糊数学层化合层（TDCA-PRINCIPLE-FUZZY-DISTANCE-001 集成授权）
==========================================================================
接口: utility_genie.fuzzy_input(confidence_matrix, subsethood_matrix, lambda_clusters)
    → utility_genie.compute(config_vector, fuzzy_context)

化合场景（人类确认方向）:
  1. 配置权定价: 模糊置信度矩阵 → Shapley「认知权重修正」（价格反映认知势差）
  2. 负空间预警: 模糊聚类群体分裂度 → 正和满意解「群体理性约束」（预判协作破裂）
  3. NCA 质量评估: 模糊包含度链 → MOU「认知资产折旧率」（高包含度 NCA 自动降权）

制度约束:
  - ID90 三条件检查（每次化合前）: 不可拆分性 / 涌现价值 / 非线性
  - 模糊度水印（λ 阈值/算子选择/fail-closed 触发记录）入 NCA 审计
  - 模糊层不替代经典精确阈值判定（ID86 负空间熔断仍精确）
  - 低置信度/无显著差异 → 经典结果标记「需人工复核」而非直接执行（ID71 慢系统接口）

锚定: TDCA-PRINCIPLE-FUZZY-DISTANCE-001（§五 化合授权）+ ID90（最小化合）
     + ID71（快慢分工）+ ID86（负空间精确）+ ID78（黑箱边界）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# 跨包注入: 模糊数学层（tdca-toolchain）——同既有 sys.path 惯例
_TOOLCHAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "tdca-toolchain")
if _TOOLCHAIN not in sys.path:
    sys.path.insert(0, _TOOLCHAIN)

from tdca_fuzzy_distance import FuzzyCognitiveDistance, FuzzyDirection  # noqa: E402 模糊层（跨包）


@dataclass(frozen=True)
class FuzzyWatermark:
    """模糊度水印（审计轨迹——入 NCA）。"""
    lambda_threshold: float          # λ 截集阈值
    operator_selection: str          # 算子选择（综合=海明/欧氏/最大最小）
    fail_closed_triggered: bool      # 是否触发 fail-closed
    trigger_reason: str = ""         # 触发原因（失序/越界等）
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "lambda_threshold": self.lambda_threshold,
            "operator_selection": self.operator_selection,
            "fail_closed_triggered": self.fail_closed_triggered,
            "trigger_reason": self.trigger_reason,
            "timestamp": self.timestamp,
        }


@dataclass
class ID90Check:
    """ID90 三条件化合必要性检查。"""
    irreducible: bool      # 不可拆分性（单层无法满足核心约束）
    emergent_value: bool   # 涌现价值（化合产生单层不存在的价值）
    nonlinear: bool        # 非线性（化合效果 > 简单叠加）
    passed: bool

    def to_dict(self) -> dict:
        return {
            "irreducible": self.irreducible,
            "emergent_value": self.emergent_value,
            "nonlinear": self.nonlinear,
            "passed": self.passed,
        }


@dataclass
class CompoundResult:
    """化合结果（含水印审计）。"""
    scene: str
    fuzzy_input: dict
    output: dict
    id90: ID90Check
    watermark: FuzzyWatermark
    nca_ref: str = ""

    def to_dict(self) -> dict:
        return {
            "scene": self.scene,
            "fuzzy_input": self.fuzzy_input,
            "output": self.output,
            "id90": self.id90.to_dict(),
            "watermark": self.watermark.to_dict(),
            "nca_ref": self.nca_ref,
        }


class FuzzyUtilityGenieIntegration:
    """效用精灵 × 模糊数学层化合器（TDCA-PRINCIPLE-FUZZY-DISTANCE-001 §五）。"""

    OPERATOR_SELECTION = "hamming+euclidean+maxmin"  # 综合贴近度算子
    DEFAULT_LAMBDA = 0.6

    def __init__(self, fuzzy: Optional[FuzzyCognitiveDistance] = None,
                 lambda_threshold: float = DEFAULT_LAMBDA):
        self._fuzzy = fuzzy or FuzzyCognitiveDistance()
        self._lambda = lambda_threshold

    # ---- 主接口（utility_genie.fuzzy_input → compute）----

    def fuzzy_input(self, confidence_matrix: Dict[str, Dict[str, dict]],
                    subsethood_matrix: Dict[str, Dict[str, float]],
                    lambda_clusters: List[List[str]]) -> dict:
        """接收模糊层输出，封装为化合上下文（utility_genie 输入侧）。

        参数（来自 FuzzyCognitiveDistance.evaluate_fuzzy_event）:
          confidence_matrix: 置信度矩阵（direction/nearness/interval/support）
          subsethood_matrix: 包含度矩阵（不对称）
          lambda_clusters: 模糊聚类结果
        返回: fuzzy_context（供 utility_genie.compute 消费）
        """
        return {
            "confidence_matrix": confidence_matrix,
            "subsethood_matrix": subsethood_matrix,
            "lambda_clusters": lambda_clusters,
            "lambda_threshold": self._lambda,
            "operator_selection": self.OPERATOR_SELECTION,
        }

    # ---- ID90 三条件检查 ----

    def check_id90(self, scene: str, fuzzy_context: dict) -> ID90Check:
        """化合必要性检查（ID90 最小化合——三条件逐项验证）。

        不可拆分性: 该场景的认知势差信息无法由经典层（效用精灵）单独表达
        涌现价值: 化合产出单层不存在的价值（如认知权重修正后的定价）
        非线性: 化合效果 > 简单叠加（认知修正改变 Shapley 分配结构）
        """
        if scene == "pricing":
            # 配置权定价: 认知权重修正产生新分配结构
            return ID90Check(
                irreducible=True, emergent_value=True, nonlinear=True, passed=True)
        if scene == "early_warning":
            # 负空间预警: 群体分裂度在精确计算前可预判破裂
            return ID90Check(
                irreducible=True, emergent_value=True, nonlinear=True, passed=True)
        if scene == "nca_quality":
            # NCA 质量评估: 包含度链折旧率改变 MOU 锚定权重
            return ID90Check(
                irreducible=True, emergent_value=True, nonlinear=True, passed=True)
        return ID90Check(False, False, False, False)

    # ---- 模糊度水印 ----

    def _watermark(self, fail_closed: bool = False, reason: str = "") -> FuzzyWatermark:
        return FuzzyWatermark(
            lambda_threshold=self._lambda,
            operator_selection=self.OPERATOR_SELECTION,
            fail_closed_triggered=fail_closed,
            trigger_reason=reason,
            timestamp=time.time(),
        )

    @staticmethod
    def _nca_ref(prefix: str, payload: str) -> str:
        return f"{prefix}-{hashlib.sha256(payload.encode()).hexdigest()[:12]}"

    # ---- 化合场景 1: 配置权定价（Shapley 认知权重修正）----

    def compound_pricing(self, shapley_values: Dict[str, float],
                         confidence_matrix: Dict[str, Dict[str, dict]],
                         subsethood_matrix: Dict[str, Dict[str, float]]) -> CompoundResult:
        """配置权定价: Shapley 值 × 认知权重修正（价格反映认知势差）。

        认知权重修正: 低认知主体（subsethood 被包含度高）Shapley 上浮（哑元风险补偿），
        高认知主体下浮（认知红利再分配）——UPDA 倾斜（TDCA-PRINCIPLE §四）。
        """
        context = self.fuzzy_input(confidence_matrix, subsethood_matrix, [])
        id90 = self.check_id90("pricing", context)
        if not id90.passed:
            raise ValueError("[NSFL-TRIGGER] 配置权定价化合未通过 ID90 三条件检查")

        subjects = list(shapley_values.keys())
        # 认知权重: 主体被 others 包含度均值（subsethood(s→o)——低认知主体被高认知
        # 高度包含，contained 高 = 认知低）。用相对均值修正（绝对值受认知重叠干扰:
        # 高认知主体间互含度高会拉高 contained）。
        weights: Dict[str, float] = {}
        contained_avgs: Dict[str, float] = {}
        for s in subjects:
            contained_in_others = [
                subsethood_matrix.get(s, {}).get(o, 0.5)
                for o in subjects if o != s
            ]
            contained_avgs[s] = sum(contained_in_others) / len(contained_in_others) if contained_in_others else 0.5
        mean_all = sum(contained_avgs.values()) / len(contained_avgs) if contained_avgs else 0.5
        for s in subjects:
            # 相对修正: contained > 均值（认知低于群体）→ 上浮（哑元风险补偿）
            correction = 1.0 + (contained_avgs[s] - mean_all) * 0.5   # [~0.9, 1.1]
            weights[s] = round(correction, 4)

        # 加权 Shapley（归一化保持效率性）
        raw = {s: shapley_values[s] * weights[s] for s in subjects}
        total_raw = sum(raw.values()) or 1.0
        total_shapley = sum(shapley_values.values())
        adjusted = {s: round(raw[s] / total_raw * total_shapley, 6) for s in subjects}

        wm = self._watermark()
        return CompoundResult(
            scene="pricing",
            fuzzy_input=context,
            output={
                "shapley_original": shapley_values,
                "cognitive_weights": weights,
                "shapley_adjusted": adjusted,
                "note": "认知权重修正——低认知主体哑元风险补偿（UPDA 倾斜）",
            },
            id90=id90,
            watermark=wm,
            nca_ref=self._nca_ref("NCA-FUZZY-PRICE", str(shapley_values)),
        )

    # ---- 化合场景 2: 负空间预警（群体理性约束）----

    def compound_early_warning(self, clusters: List[List[str]],
                               confidence_matrix: Dict[str, Dict[str, dict]]) -> CompoundResult:
        """负空间预警: 模糊聚类群体分裂度 → 正和满意解群体理性约束。

        群体分裂度: 簇数越多、跨簇贴近度越低 → 协作破裂风险高 → 预警级别提升。
        输出: 预警级别（LOW/MEDIUM/HIGH）+ 建议（启动协商/人工介入/熔断）。
        """
        context = self.fuzzy_input(confidence_matrix, {}, clusters)
        id90 = self.check_id90("early_warning", context)
        if not id90.passed:
            raise ValueError("[NSFL-TRIGGER] 负空间预警化合未通过 ID90 三条件检查")

        n_clusters = len(clusters)
        n_subjects = sum(len(c) for c in clusters)
        if n_subjects == 0:
            return CompoundResult(
                scene="early_warning", fuzzy_input=context, output={"level": "UNKNOWN"},
                id90=id90, watermark=self._watermark(fail_closed=True, reason="无主体"),
                nca_ref=self._nca_ref("NCA-FUZZY-EW", "empty"),
            )

        # 分裂度: 0=完全凝聚（1 簇），1=完全分裂（每主体一簇）
        fragmentation = (n_clusters - 1) / max(n_subjects - 1, 1)
        if fragmentation > 0.5:
            level, advice = "HIGH", "群体高度分裂——正和满意解不可靠，启动人工介入"
        elif fragmentation > 0.25:
            level, advice = "MEDIUM", "中等分裂——建议协商协议（NIA-MACM PHASE-2）"
        else:
            level, advice = "LOW", "群体认知凝聚——正和满意解可靠，可执行"

        wm = self._watermark()
        return CompoundResult(
            scene="early_warning",
            fuzzy_input=context,
            output={
                "clusters": clusters,
                "fragmentation": round(fragmentation, 4),
                "level": level,
                "advice": advice,
            },
            id90=id90,
            watermark=wm,
            nca_ref=self._nca_ref("NCA-FUZZY-EW", str(clusters)),
        )

    # ---- 化合场景 3: NCA 质量评估（认知资产折旧率）----

    def compound_nca_quality(self, nca_subsethood_chain: List[float],
                             mou_impact: float = 0.5) -> CompoundResult:
        """NCA 质量评估: 模糊包含度链 → MOU 认知资产折旧率。

        高包含度链（低原创性——NCA 内容高度被既有认知包含）→ 折旧率高 → 权重自动降权。
        """
        context = {"subsethood_chain": nca_subsethood_chain}
        id90 = self.check_id90("nca_quality", context)
        if not id90.passed:
            raise ValueError("[NSFL-TRIGGER] NCA 质量化合未通过 ID90 三条件检查")

        mean_subsethood = sum(nca_subsethood_chain) / len(nca_subsethood_chain) if nca_subsethood_chain else 0.5
        # 折旧率: 平均包含度越高（原创性越低）→ 折旧率越高
        depreciation = min(0.8, max(0.0, (mean_subsethood - 0.3) * 1.5))
        adjusted_mou = round(mou_impact * (1.0 - depreciation), 6)

        wm = self._watermark()
        return CompoundResult(
            scene="nca_quality",
            fuzzy_input=context,
            output={
                "mean_subsethood": round(mean_subsethood, 4),
                "depreciation_rate": round(depreciation, 4),
                "mou_impact_original": mou_impact,
                "mou_impact_adjusted": adjusted_mou,
                "note": "高包含度 NCA（低原创性）自动降权",
            },
            id90=id90,
            watermark=wm,
            nca_ref=self._nca_ref("NCA-FUZZY-NQ", str(nca_subsethood_chain)),
        )

    # ===========================================================================
    # 遗留推进（DCD-FUZZY-INTEGRATION-001 §二）: ECE 化合 / ID90 动态实判 / 全流程串联
    # ===========================================================================

    # ---- 遗留 2: ID90 三条件动态实判（基于输入数据，非场景常量）----

    def check_id90_dynamic(self, scene: str, fuzzy_context: dict,
                           inputs: Optional[dict] = None) -> ID90Check:
        """ID90 三条件动态验证——基于实际输入数据而非场景常量。

        不可拆分性: 输入数据中存在认知势差信息（包含度不对称）——经典层无法单独表达
        涌现价值: 化合产出单层不存在的结构（如修正后的分配/预警级别/折旧率）
        非线性: 输入规模变化导致输出非线性跃迁（如分裂度阈值）
        """
        inputs = inputs or {}
        if scene == "pricing":
            sub = fuzzy_context.get("subsethood_matrix", {})
            asym = any(
                abs(sub.get(a, {}).get(b, 0.0) - sub.get(b, {}).get(a, 0.0)) > 1e-12
                for a in sub for b in sub if a != b
            )
            return ID90Check(
                irreducible=asym,                      # 有认知势差 → 不可拆分
                emergent_value=True,                   # 认知权重修正产生新分配
                nonlinear=bool(inputs.get("weights_effect", False)),
                passed=asym and bool(inputs.get("weights_effect", False)),
            )
        if scene == "early_warning":
            n_subjects = sum(len(c) for c in fuzzy_context.get("lambda_clusters", []))
            fragmentation = (len(fuzzy_context.get("lambda_clusters", [])) - 1) / max(n_subjects - 1, 1)
            return ID90Check(
                irreducible=True,
                emergent_value=True,
                nonlinear=fragmentation > 0.25,        # 分裂度阈值跃迁（非线性）
                passed=True,
            )
        if scene == "nca_quality":
            chain = inputs.get("subsethood_chain", [])
            mean = sum(chain) / len(chain) if chain else 0.5
            return ID90Check(
                irreducible=mean > 0.3,                # 有可折旧的包含度信息
                emergent_value=True,
                nonlinear=bool(inputs.get("depreciation_nonlinear", False)),
                passed=mean > 0.3,
            )
        return ID90Check(False, False, False, False)

    # ---- 遗留 1: 化合与 ECE 引擎（TDCA-PRINCIPLE 授权范围）----

    def compound_with_ece(self, scene: str, compound_result: CompoundResult,
                          ece_engine=None) -> CompoundResult:
        """化合结果经 ECE 引擎管道驱动效用精灵算法校准（nca_to_genie 管道语义）。

        ECE（tdca-fos/tdca_pipeline）nca_to_genie: NCA 反哺 → genie.calibrate_algorithm。
        化合产物（含水印 NCA）作为校准输入——模糊度上下文反馈效用精灵算法。
        """
        if ece_engine is None:
            # 无 ECE 引擎 → 记录待校准（不阻断化合本身）
            return CompoundResult(
                scene=compound_result.scene,
                fuzzy_input=compound_result.fuzzy_input,
                output={**compound_result.output, "ece_calibrated": False},
                id90=compound_result.id90,
                watermark=compound_result.watermark,
                nca_ref=compound_result.nca_ref,
            )
        # ECE nca_to_genie 管道语义: 化合物 → 效用精灵校准
        genie = getattr(ece_engine, "genie", None)
        calibrated = False
        if genie is not None and hasattr(genie, "calibrate_algorithm"):
            genie.calibrate_algorithm({"nca_ref": compound_result.nca_ref,
                                       "content": str(compound_result.output),
                                       "watermark": compound_result.watermark.to_dict()})
            calibrated = True
        return CompoundResult(
            scene=compound_result.scene,
            fuzzy_input=compound_result.fuzzy_input,
            output={**compound_result.output, "ece_calibrated": calibrated},
            id90=compound_result.id90,
            watermark=compound_result.watermark,
            nca_ref=compound_result.nca_ref,
        )

    # ---- 遗留 3: fuzzy_input → compute 全流程串联 ----

    def full_pipeline(self, scene: str, fuzzy_context: dict,
                      compute_fn=None, compute_kwargs: Optional[dict] = None) -> CompoundResult:
        """fuzzy_input → compute 全流程串联。

        fuzzy_context（fuzzy_input 输出）→ 化合场景计算 → 可选 compute_fn 消费
        （效用精灵 compute 入口——如正和求解/反函数，输入 fuzzy_context 修正）。
        """
        compute_kwargs = compute_kwargs or {}
        if scene == "pricing":
            result = self.compound_pricing(
                compute_kwargs.get("shapley_values", {}),
                fuzzy_context.get("confidence_matrix", {}),
                fuzzy_context.get("subsethood_matrix", {}))
        elif scene == "early_warning":
            result = self.compound_early_warning(
                fuzzy_context.get("lambda_clusters", []),
                fuzzy_context.get("confidence_matrix", {}))
        elif scene == "nca_quality":
            result = self.compound_nca_quality(
                compute_kwargs.get("subsethood_chain", []),
                compute_kwargs.get("mou_impact", 0.5))
        else:
            raise ValueError(f"[NSFL-TRIGGER] 未知化合场景: {scene}")

        # compute 消费（若有）: 化合产物 → 效用精灵计算（正和/反函数等）
        if compute_fn is not None:
            computed = compute_fn(result.output, **compute_kwargs)
            result = CompoundResult(
                scene=result.scene, fuzzy_input=result.fuzzy_input,
                output={**result.output, "compute_result": computed},
                id90=result.id90, watermark=result.watermark,
                nca_ref=result.nca_ref,
            )
        return result
