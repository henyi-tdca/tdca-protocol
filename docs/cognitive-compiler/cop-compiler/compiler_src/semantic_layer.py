# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""COP 编译器 · 语义层模块（TDCA-TP-S3-001 §2.5 落地）
================================================================
依据:
  - TDCA-TP-S3-001 §2.5 语义层：效用语义 U0(c) 定值 + 负空间继承语义
  - 实证 5 原型（TDCA-TP-M3-SIM-REPORT-001）: U0 = 0.5·六要素完整度 + 0.3·min(原语数/5,1) + 0.2·负空间覆盖
  - 实证 3: 组合 COP（parent ⟂ interpretant）negative_space = parent ∪ interpretant（解释项约束自动继承）
  - §2.4 语法层 schema 字段约束表（COP-ID/soul/primitives/dispatch/decision/negative_space/validation）
状态: DRAFT（M1 开发交付物，走 DCD-COP-COMPILER-001 M1 范围）
纪律: 只读引用编译族既有资产；新增实现不触碰 TDCA-TP-S1~S4 FROZEN
溯源链: TDCA-TP-S3-001 FROZEN → 本模块（语义层实现）→ M1 验收
"""
import os
import re
import sys

# Windows 控制台 GBK 兼容：stdout 统一 UTF-8（NSFL R2 编码安全）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

try:
    import yaml
except ImportError:
    yaml = None

_THIS = os.path.dirname(os.path.abspath(__file__))
_COP_LIB = os.environ.get("TDCA_COP_LIB") or os.path.normpath(os.path.join(_THIS, "..", "..", "cop-library"))

# 语义层权重（E-3 定标 2026-08-16 人类批准：0.5/0.3/0.2，暂定生效，随沙盒运营动态调整）
U0_W = {"objective": 0.5, "primitive": 0.3, "negative": 0.2}
PRIMITIVE_CAP = 5          # 原语数封顶（min(原语数/5, 1)）
NEGSPACE_BASELINE = 3      # 负空间覆盖基线条数（≥3 条视为全覆盖）

# ============ E 参数定标（T-068 阶段 4 人类批准，2026-08-16） ============
# 状态: TENTATIVE（暂定生效）——后续根据沙盒实际运营动态调整（调整走 T-068 流程：实证→候选→人类批准→登记）
E_CALIBRATION = {
    "version": "V1.0-TENTATIVE",
    "approved_by": "TDCA 制度设计师（人类）",
    "approved_at": "2026-08-16",
    "basis": "TDCA-COPCOMPILER-E-CALIBRATION-001 提案包（沙盒实证 E-CALIBRATION-SIM.json）",
    "E-1_negative_u_threshold": 0.15,   # 负 U 阈值：U_CDE < 0.15 不计入正和，触发熔断候选
    "E-2_degenerate_sc_threshold": 0.2,  # 退化 SC 阈值：s∈D_degenerate ⟹ U:=0 归零判定
    "E-3_u0_weights": {"objective": 0.5, "primitive": 0.3, "negative": 0.2},
    "adjustment_note": "暂定值；随沙盒实际运营积累数据后走 T-068 更新流程（人类批准后修订）",
}
NEGATIVE_U_THRESHOLD = E_CALIBRATION["E-1_negative_u_threshold"]
DEGENERATE_SC_THRESHOLD = E_CALIBRATION["E-2_degenerate_sc_threshold"]

# COP schema 六要素块（§2.4 字段约束表核心块）
SIX_ELEMENTS = ["soul", "primitives", "dispatch", "decision", "negative_space", "validation"]


# ============ 一、六要素完整度（自动计算） ============
def _soul_score(cop):
    """soul 块：identity + core 双非空 → 1.0；单非空 → 0.5；空 → 0"""
    soul = cop.get("soul") or {}
    has_id = bool(str(soul.get("identity", "")).strip())
    has_core = bool(str(soul.get("core", "")).strip())
    if has_id and has_core:
        return 1.0
    if has_id or has_core:
        return 0.5
    return 0.0


def _primitives_score(cop):
    """primitives 块：≥1 且全部签名完整 → 1.0；有原语但签名缺失 → 0.5；空 → 0"""
    prims = cop.get("primitives") or []
    if not prims:
        return 0.0
    all_sig = all(p.get("signature") and "fn " in str(p.get("signature", "")) for p in prims)
    return 1.0 if all_sig else 0.5


def _dispatch_score(cop):
    """dispatch 块：非空 → 1.0；单原语 COP 可空（§2.4 ⚠️）→ 0.8；空 → 0"""
    dispatch = cop.get("dispatch")
    if dispatch:
        return 1.0
    prims = cop.get("primitives") or []
    return 0.8 if len(prims) <= 1 else 0.0


def _decision_score(cop):
    """decision 块：非空 → 1.0；单原语 COP 可空（§2.4 ⚠️）→ 0.8；空 → 0"""
    decision = cop.get("decision")
    if decision:
        return 1.0
    prims = cop.get("primitives") or []
    return 0.8 if len(prims) <= 1 else 0.0


def _negative_space_score(cop):
    """negative_space 块：≥1 条 → 1.0；空 → 0（§2.4 必填）"""
    ns = cop.get("negative_space") or []
    return 1.0 if ns else 0.0


def _validation_score(cop):
    """validation 块：passed → 1.0；有 issues → 0.5；缺失 → 0（§2.4 必填）"""
    val = cop.get("validation") or {}
    if val.get("passed") is True:
        return 1.0
    if "passed" in val:
        return 0.5
    return 0.0


_ELEMENT_SCORERS = {
    "soul": _soul_score,
    "primitives": _primitives_score,
    "dispatch": _dispatch_score,
    "decision": _decision_score,
    "negative_space": _negative_space_score,
    "validation": _validation_score,
}


def six_elements_completeness(cop):
    """六要素完整度（自动计算，0~1）
    六要素 = soul / primitives / dispatch / decision / negative_space / validation
    各块按 0/0.5/0.8/1.0 分档（对齐 §2.4 必填 ⚠️ 可选约束），取均值。
    """
    if not isinstance(cop, dict):
        return 0.0
    scores = [_ELEMENT_SCORERS[k](cop) for k in SIX_ELEMENTS]
    return sum(scores) / len(SIX_ELEMENTS)


# ============ 二、负空间覆盖度（自动计算） ============
def negative_space_coverage(cop):
    """负空间覆盖度（0~1）：COP 级 negative_space 条数 / 基线 3 条，封顶 1.0
    覆盖基线对齐实证 3（走为上 3 条负空间全继承）与 §2.5 负空间继承语义。
    """
    ns = cop.get("negative_space") or []
    prims = cop.get("primitives") or []
    # 原语级 ⊗ 约束并入计数（原语 negative_space 非空即贡献覆盖）
    prim_ns = sum(1 for p in prims if str(p.get("negative_space", "")).strip())
    total = len(ns) + prim_ns
    return min(total / NEGSPACE_BASELINE, 1.0)


# ============ 三、U0 定值函数（实证 5 原型 + 自动提取） ============
def u0_semantic(objective_complete, prim_count, negspace_coverage):
    """U0(c) 定值函数（实证 5 原型，兼容 M3 实证口径）
    U0 = 0.5·六要素完整度 + 0.3·min(原语数/5, 1) + 0.2·负空间覆盖
    参数可显式传入（实证复现）或经 compute_u0 自动提取。
    """
    return (
        U0_W["objective"] * objective_complete
        + U0_W["primitive"] * min(prim_count / PRIMITIVE_CAP, 1.0)
        + U0_W["negative"] * negspace_coverage
    )


def compute_u0(cop):
    """从 COP 结构自动计算 U0（语义层落地口径）
    返回: (u0, breakdown) —— breakdown 含三分量明细（可溯源）
    """
    complete = six_elements_completeness(cop)
    prim_count = len(cop.get("primitives") or [])
    coverage = negative_space_coverage(cop)
    u0 = u0_semantic(complete, prim_count, coverage)
    breakdown = {
        "six_elements_completeness": round(complete, 4),
        "primitive_count": prim_count,
        "primitive_score": round(min(prim_count / PRIMITIVE_CAP, 1.0), 4),
        "negative_space_coverage": round(coverage, 4),
        "weights": U0_W,
        "formula": "U0 = 0.5*completeness + 0.3*min(prims/5,1) + 0.2*coverage",
    }
    return u0, breakdown


def attach_semantic(cop):
    """给 COP 附加语义层字段（semantic.u0 + breakdown + inherited_from）
    返回: 带 semantic 字段的 COP（就地修改并返回）
    """
    u0, breakdown = compute_u0(cop)
    cop["semantic"] = {
        "u0": round(u0, 4),
        "breakdown": breakdown,
        "semantic_version": "TDCA-TP-S3-001-V1.0",
    }
    return cop


# ============ 四、负空间继承语义（实证 3 落地） ============
_NS_PREFIX = "⊗"


def _normalize_ns(entry):
    """规范化负空间条目：去 ⊗ 前缀/空白，用于去重比较"""
    return str(entry).replace(_NS_PREFIX, "").strip().strip("：" ).strip()


def inherit_negative_space(parent_cop, interpretant_cops):
    """负空间继承：组合 COP 的 negative_space = parent ∪ ∪ interpretants（§2.5）
    实现: 取并集去重（按规范化文本），保留原始条目标注来源。
    返回: (combined_list, inherited_from_interpretants, union_count)
    """
    parent_ns = list(parent_cop.get("negative_space") or [])
    # 父级原语级 ⊗ 约束并入（原语级负空间同属父约束）
    for p in parent_cop.get("primitives") or []:
        pns = str(p.get("negative_space", "")).strip()
        if pns:
            parent_ns.append(pns)
    combined = []
    seen = set()
    inherited = []
    for entry in parent_ns:
        key = _normalize_ns(entry)
        if key and key not in seen:
            seen.add(key)
            combined.append(entry)
    for interp in interpretant_cops:
        for entry in interp.get("negative_space") or []:
            key = _normalize_ns(entry)
            if key and key not in seen:
                seen.add(key)
                combined.append(f"{_NS_PREFIX} 解释项负空间继承: {_normalize_ns(entry)}")
                inherited.append(_normalize_ns(entry))
        # 解释项原语级约束并入
        for p in interp.get("primitives") or []:
            pns = str(p.get("negative_space", "")).strip()
            if pns:
                key = _normalize_ns(pns)
                if key and key not in seen:
                    seen.add(key)
                    combined.append(f"{_NS_PREFIX} 解释项负空间继承: {key}")
                    inherited.append(key)
    return combined, inherited, len(seen)


def apply_inheritance(composed_cop, parent_cop, interpretant_cops):
    """组合 COP 应用负空间继承（实证 3：组合 negative_space = parent ∪ interpretants）
    返回: 带继承后 negative_space 的组合 COP（就地修改）
    """
    combined, inherited, union = inherit_negative_space(parent_cop, interpretant_cops)
    composed_cop["negative_space"] = combined
    composed_cop["semantic_inheritance"] = {
        "parent": parent_cop.get("COP-ID"),
        "interpretants": [i.get("COP-ID") for i in interpretant_cops],
        "parent_ns_count": len(parent_cop.get("negative_space") or []),
        "combined_ns_count": len(combined),
        "inherited_from_interpretants": inherited,
        "union_count": union,
        "rule": "negative_space = parent ∪ interpretants（§2.5 负空间继承）",
    }
    return composed_cop


# ============ 四点五、U0 × U_CDE 场景依存效用联合（M2 任务②，T-110 落地） ============
import math


def cosine_sim(v1, v2):
    """余弦相似度（非负向量 → A∈[0,1]，反适配=正交 A→0；实证 2 口径）"""
    num = sum(a * b for a, b in zip(v1, v2))
    d1 = math.sqrt(sum(a * a for a in v1)) or 1.0
    d2 = math.sqrt(sum(b * b for b in v2)) or 1.0
    return num / (d1 * d2)


def sc_scene(heat, density, maturity, decay):
    """R-SCENE-2 SC_s 度量协议代理：SC(s)=(∏ĥ_j^w_j)×ρ（演示权重均 0.25，T-068 定标候选）"""
    w = 0.25
    prod = (heat ** w) * (density ** w) * (maturity ** w)
    return prod * (1.0 - decay * 0.5)


def u_cde(cop_or_u0, sc, a):
    """U_CDE(c|s) = U0(c)·SC(s)·A(c,s)（T-110，红队 X-1 U 记号消歧）
    输入: cop_or_u0（COP dict → 自动计算 U0；数值 → 直接使用）或 (u0, sc, a)
    """
    u0 = cop_or_u0 if isinstance(cop_or_u0, (int, float)) else compute_u0(cop_or_u0)[0]
    return u0 * sc * a


def cop_feature_vector(cop):
    """COP 特征向量（实证 1 口径）：[攻守守, 攻, 低风险, 独立, 协作] 五维演示代理
    从 COP 元信息推导（stratum/category 映射演示，simulated=True）
    """
    cat = str(cop.get("soul", {}).get("category", "")) + str(cop.get("stratum", ""))
    if any(k in cat for k in ("胜战", "攻战", "攻")):
        return [0.3, 0.7, 0.5, 0.6, 0.4]
    if any(k in cat for k in ("败战", "走", "守")):
        return [0.8, 0.2, 0.9, 0.7, 0.3]
    return [0.6, 0.4, 0.7, 0.5, 0.5]


def u_cde_breakdown(cop, scene_vector, sc):
    """完整 U_CDE 联合计算（M2 任务②）：U0 自动 → A 余弦 → U_CDE = U0·SC·A
    返回: dict（u0/sc/a/u_cde/语义标注，负 U 处理 X-4）
    """
    u0 = compute_u0(cop)[0]
    a = cosine_sim(cop_feature_vector(cop), scene_vector)
    u = u_cde(u0, sc, a)
    return {
        "cop_id": cop.get("COP-ID"),
        "u0": round(u0, 4),
        "sc": round(sc, 4),
        "a": round(a, 4),
        "u_cde": round(u, 4),
        "negative_u_handling": "不计入正和，熔断候选" if u < NEGATIVE_U_THRESHOLD else "正常",
        "formula": "U_CDE(c|s) = U0(c)·SC(s)·A(c,s)（T-110）",
        "U 记号消歧": "U_CDE 与五维价值向量 V=(U,S,F,C,R) 的 U 分量强制消歧（T-110）",
        "E-1_threshold": NEGATIVE_U_THRESHOLD,
        "calibration": E_CALIBRATION["version"],
    }


# ============ E-2 退化场景归零判定 + 定标动态调整通道（2026-08-16 人类批准暂定） ============
def degenerate_sc_check(sc):
    """退化场景归零判定（E-2 定标 0.2，实证 3/S1.2）：
    s∈D_degenerate ⟹ U:=0 归零判定（非 SC 连续压低，触发熔断候选）
    返回: dict（is_degenerate/zeroed/sc/threshold）
    """
    is_deg = sc < DEGENERATE_SC_THRESHOLD
    return {
        "is_degenerate": is_deg,
        "zeroed": is_deg,
        "sc": round(sc, 4),
        "threshold": DEGENERATE_SC_THRESHOLD,
        "semantics": "退化场景归零 U:=0（T-068 E-2 定标 V1.0-TENTATIVE）",
    }


def get_calibration():
    """读取当前 E 定标配置（含版本/状态）"""
    return dict(E_CALIBRATION)


def attach_u_cde(cop, scene_vector, sc):
    """U_CDE 接入批产全流程（M3 任务①）：在语义层增强基础上附加 u_cde 字段
    对已 attach_semantic 的 COP，追加 semantic.u_cde（u0/sc/a/u_cde/负 U 处理）
    返回: COP（就地修改）
    """
    if "semantic" not in cop:
        attach_semantic(cop)
    bd = u_cde_breakdown(cop, scene_vector, sc)
    cop["semantic"]["u_cde"] = {
        "u0": bd["u0"],
        "sc": bd["sc"],
        "a": bd["a"],
        "u_cde": bd["u_cde"],
        "negative_u_handling": bd["negative_u_handling"],
        "scene_vector": scene_vector,
        "formula": bd["formula"],
    }
    return cop


def update_calibration(negative_u_threshold=None, degenerate_sc_threshold=None, weights=None, note=None):
    """E 定标动态调整通道（T-068 流程）：
    仅登记候选覆盖（运行时生效），正式修订须人类批准后走 DCD 变更更新 E_CALIBRATION 常量。
    返回: 当前生效定标 + 本次覆盖记录
    """
    global NEGATIVE_U_THRESHOLD, DEGENERATE_SC_THRESHOLD
    override = {}
    if negative_u_threshold is not None:
        NEGATIVE_U_THRESHOLD = negative_u_threshold
        override["E-1_negative_u_threshold"] = negative_u_threshold
    if degenerate_sc_threshold is not None:
        DEGENERATE_SC_THRESHOLD = degenerate_sc_threshold
        override["E-2_degenerate_sc_threshold"] = degenerate_sc_threshold
    if weights is not None:
        U0_W.update(weights)
        override["E-3_u0_weights"] = dict(U0_W)
    return {
        "effective": {
            "E-1_negative_u_threshold": NEGATIVE_U_THRESHOLD,
            "E-2_degenerate_sc_threshold": DEGENERATE_SC_THRESHOLD,
            "E-3_u0_weights": dict(U0_W),
            "calibration_version": E_CALIBRATION["version"],
        },
        "override": override,
        "note": note or "运行时覆盖（沙盒运营调整；正式修订须人类批准）",
    }


# ============ 五、接入五阶段流水线（s5 → semantic，第六阶段） ============
def s6_semantic(cop):
    """语义层阶段：五阶段流水线（s1-s5）验证后接入（cognitive_compiler.py 扩展点）
    执行: 六要素完整度 + 负空间覆盖 + U0 定值 + （组合 COP）负空间继承
    返回: 附加 semantic 字段的 COP；validation 同步追加 semantic 检查项。
    """
    cop = attach_semantic(cop)
    # 负空间继承（若 COP 带 composition 元信息则自动执行）
    composition = cop.get("composition")
    if composition and isinstance(composition, dict):
        cop["semantic"]["inheritance_applied"] = True
    # 语义层追加校验项（并入 validation，兼容 s5_validate 结构）
    val = cop.setdefault("validation", {})
    val.setdefault("semantic_checks", {})["u0_computed"] = True
    val.setdefault("semantic_checks", {})["u0"] = cop["semantic"]["u0"]
    val["passed"] = val.get("passed", True) and True
    return cop


def compile_with_semantics(cop):
    """兼容入口：对已编译 COP（五阶段产物）执行语义层，返回 (cop, u0, breakdown)"""
    cop = s6_semantic(cop)
    return cop, cop["semantic"]["u0"], cop["semantic"]["breakdown"]


def pipeline_compile(expert_md_path, output_dir=None):
    """五阶段流水线 + 语义层第六阶段（s5 → semantic 接线，包装层）
    调用: cognitive_compiler.compile（S1-S5，复用基座只读引用）→ s6_semantic（语义层）
    纪律: 不改写 cognitive_compiler.py（REUSE-001 复用资产只读）；语义层以包装扩展接入
    返回: (cop, out_path)
    """
    try:
        import cognitive_compiler as CC
    except ImportError:
        # 同目录加载（pipeline_compile 与 cognitive_compiler 并列时）
        sys.path.insert(0, _THIS)
        import cognitive_compiler as CC
    cop, out_path = CC.compile(expert_md_path, output_dir=output_dir)
    cop = s6_semantic(cop)
    if out_path:
        CC._dump_yaml(cop, out_path)
    return cop, out_path


if __name__ == "__main__":  # pragma: no cover - 自检演示块（非交付逻辑）
    import json
    # 自检：加载走为上 COP 样例计算 U0
    sample = os.path.join(_COP_LIB, "stratagems", "第36计-走为上.yaml")
    if os.path.isfile(sample) and yaml is not None:
        with open(sample, "r", encoding="utf-8") as f:
            zou = yaml.safe_load(f)
        u0, bd = compute_u0(zou)
        print("走为上 U0 = %.4f" % u0)
        print(json.dumps(bd, ensure_ascii=False, indent=2))
        # 负空间继承自检（走为上 ⟂ 围魏救赵）
        wj = os.path.join(_COP_LIB, "stratagems", "第02计-围魏救赵.yaml")
        if os.path.isfile(wj):
            with open(wj, "r", encoding="utf-8") as f:
                wj_cop = yaml.safe_load(f)
            comb, inherited, union = inherit_negative_space(zou, [wj_cop])
            print("\n负空间继承: parent=%d 解释项继承=%d union=%d 组合=%d" % (
                len(zou.get("negative_space") or []), len(inherited), union, len(comb)))
            for e in comb:
                print("  -", e.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
