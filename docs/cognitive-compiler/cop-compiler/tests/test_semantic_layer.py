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

"""semantic_layer.py 测试（P0 语义层 M1 交付物）
覆盖: U0 定值公式 / 六要素完整度 / 负空间覆盖 / 负空间继承（实证 3 口径）/ 流水线接入
溯源: TDCA-TP-S3-001 §2.5 + TDCA-TP-M3-SIM-REPORT-001（实证 3/5）
"""
import os
import sys

import pytest

try:
    import yaml
except ImportError:
    yaml = None

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
sys.path.insert(0, os.path.join(_THIS, '..', 'compiler_src'))
import semantic_layer as SL

LIB = os.environ.get("TDCA_COP_LIB") or os.path.join(_THIS, "..", "cop-library")
STRATAGEMS = os.path.join(LIB, "stratagems")
COMPOSITIONS = os.path.join(LIB, "compositions")


def _load(rel):
    if rel.startswith("cop-library/"):
        path = os.path.join(LIB, rel[len("cop-library/"):])
    elif rel.startswith("compiler/"):
        path = os.path.join(_THIS, "..", "compiler_src", rel[len("compiler/"):])
    else:
        path = os.path.join(_THIS, "..", rel)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_stratagem(name):
    for fn in os.listdir(STRATAGEMS):
        if name in fn:
            with open(os.path.join(STRATAGEMS, fn), "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError(name)


# ============ U0 定值函数（实证 5 复现） ============
class TestU0Formula:
    def test_实证5_麦肯锡(self):
        # 实证 5: U0(麦肯锡)=0.910（complete=0.9, prim=7, neg=0.8）
        u0 = SL.u0_semantic(0.9, 7, 0.8)
        assert abs(u0 - 0.910) < 1e-9

    def test_实证5_走为上(self):
        # 实证 5: U0(走为上)=0.640（complete=0.8, prim=1, neg=0.9）
        u0 = SL.u0_semantic(0.8, 1, 0.9)
        assert abs(u0 - 0.640) < 1e-9

    def test_权重结构(self):
        # 权重: 0.5/0.3/0.2（E-3 定标候选，随沙盒实证推进）
        assert SL.U0_W == {"objective": 0.5, "primitive": 0.3, "negative": 0.2}

    def test_原语数封顶(self):
        # min(原语数/5, 1)：5 → 0.3 满格；10 → 仍 0.3
        u0_5 = SL.u0_semantic(1.0, 5, 1.0)
        u0_10 = SL.u0_semantic(1.0, 10, 1.0)
        assert u0_5 == pytest.approx(1.0)
        assert u0_10 == pytest.approx(1.0)

    def test_区间边界(self):
        # U0 ∈ [0,1]
        assert SL.u0_semantic(0, 0, 0) == pytest.approx(0.0)
        assert SL.u0_semantic(1, 5, 1) == pytest.approx(1.0)

    def test_负空间覆盖基线条数(self):
        # 3 条基线：≥3 条 → 覆盖 1.0
        assert SL.negative_space_coverage({"negative_space": ["a", "b", "c"], "primitives": []}) == pytest.approx(1.0)
        assert SL.negative_space_coverage({"negative_space": ["a"], "primitives": []}) == pytest.approx(1 / 3)


# ============ 六要素完整度（自动计算） ============
class TestSixElementsCompleteness:
    def _complete_cop(self):
        return {
            "soul": {"identity": "x", "core": "y"},
            "primitives": [{"name": "a", "signature": "fn a(x) -> y"}],
            "dispatch": {"main_pipeline": "a"},
            "decision": [{"if": "p", "call": "a"}],
            "negative_space": ["⊗ ns1"],
            "validation": {"passed": True},
        }

    def test_全要素完整(self):
        assert SL.six_elements_completeness(self._complete_cop()) == pytest.approx(1.0)

    def test_soul_缺core(self):
        cop = self._complete_cop()
        cop["soul"] = {"identity": "x"}
        assert SL.six_elements_completeness(cop) == pytest.approx((0.5 + 1 + 1 + 1 + 1 + 1) / 6)

    def test_primitives_签名缺失(self):
        cop = self._complete_cop()
        cop["primitives"] = [{"name": "a", "signature": "a(x)"}]
        assert SL.six_elements_completeness(cop) == pytest.approx((1 + 0.5 + 1 + 1 + 1 + 1) / 6)

    def test_primitives_空(self):
        cop = self._complete_cop()
        cop["primitives"] = []
        assert SL.six_elements_completeness(cop) == pytest.approx((1 + 0 + 1 + 1 + 1 + 1) / 6)

    def test_非dict输入(self):
        assert SL.six_elements_completeness(None) == 0.0
        assert SL.six_elements_completeness("cop") == 0.0

    def test_单原语可空dispatch_decision(self):
        # 单原语 COP：dispatch/decision 可空 → 0.8 分档（§2.4 ⚠️）
        cop = self._complete_cop()
        del cop["dispatch"]
        del cop["decision"]
        assert SL.six_elements_completeness(cop) == pytest.approx((1 + 1 + 0.8 + 0.8 + 1 + 1) / 6)

    def test_缺negative_space(self):
        cop = self._complete_cop()
        cop["negative_space"] = []
        assert SL.six_elements_completeness(cop) == pytest.approx((1 + 1 + 1 + 1 + 0 + 1) / 6)

    def test_validation_未通过(self):
        cop = self._complete_cop()
        cop["validation"] = {"passed": False, "issues": ["x"]}
        assert SL.six_elements_completeness(cop) == pytest.approx((1 + 1 + 1 + 1 + 1 + 0.5) / 6)

    def test_多原语_缺dispatch_decision_降0(self):
        # 多原语 COP 缺 dispatch/decision → 0 分档（§2.4 多原语必填）
        cop = self._complete_cop()
        cop["primitives"] = [
            {"name": "a", "signature": "fn a(x) -> y"},
            {"name": "b", "signature": "fn b(x) -> y"},
        ]
        del cop["dispatch"]
        del cop["decision"]
        assert SL.six_elements_completeness(cop) == pytest.approx((1 + 1 + 0 + 0 + 1 + 1) / 6)

    def test_soul_全空(self):
        cop = self._complete_cop()
        cop["soul"] = {}
        assert SL.six_elements_completeness(cop) == pytest.approx((0 + 1 + 1 + 1 + 1 + 1) / 6)


# ============ compute_u0 自动提取（真实 COP） ============
class TestComputeU0:
    def test_走为上_自动提取(self):
        zou = _load_stratagem("走为上")
        u0, bd = SL.compute_u0(zou)
        # 手动核算: complete=1.0(全要素) prim=1→0.2 coverage=1.0(3条基线)
        expect = 0.5 * 1.0 + 0.3 * 0.2 + 0.2 * 1.0
        assert u0 == pytest.approx(expect)
        assert bd["primitive_count"] == 1
        assert bd["six_elements_completeness"] == pytest.approx(1.0)
        assert 0 <= u0 <= 1

    def test_麦肯锡_自动提取(self):
        mck = _load("compiler/麦肯锡思维协议.yaml")
        u0, bd = SL.compute_u0(mck)
        # 麦肯锡: 7 原语 → prim=1.0（封顶）; 负空间 3 条 + 原语级 ⊗ 计数 → coverage
        assert bd["primitive_count"] == 7
        assert bd["primitive_score"] == pytest.approx(1.0)
        assert 0 <= u0 <= 1

    def test_全部三十六计U0(self):
        # 批产口径：36 计全部可计算 U0 ∈ [0,1] 且无异常
        cnt = 0
        for fn in sorted(os.listdir(STRATAGEMS)):
            if fn.endswith(".yaml"):
                with open(os.path.join(STRATAGEMS, fn), "r", encoding="utf-8") as f:
                    cop = yaml.safe_load(f)
                u0, _ = SL.compute_u0(cop)
                assert 0 <= u0 <= 1
                cnt += 1
        assert cnt == 36

    def test_attach_semantic(self):
        zou = _load_stratagem("走为上")
        SL.attach_semantic(zou)
        assert "semantic" in zou
        assert "u0" in zou["semantic"]
        assert "breakdown" in zou["semantic"]


# ============ 负空间继承（实证 3 口径） ============
class TestNegativeSpaceInheritance:
    def test_走为上_围魏救赵_继承(self):
        zou = _load_stratagem("走为上")
        wj = _load_stratagem("围魏救赵")
        comb, inherited, union = SL.inherit_negative_space(zou, [wj])
        # 实证 3: 走为上 3 条全继承；围魏救赵解释项约束并入
        assert union >= 3
        assert "敌无必救之处或无回援动机则失效" in "".join(inherited)
        assert len(comb) == union

    def test_组合COP_实证3_全继承(self):
        # 组合资产 COMPOSED-走为上_围魏救赵 已含继承结果（实证 3 验证物）
        composed = _load("cop-library/compositions/COMPOSED-走为上_围魏救赵.yaml")
        zou = _load_stratagem("走为上")
        ns_combined = set(SL._normalize_ns(x) for x in composed.get("negative_space", []))
        zou_ns = set(SL._normalize_ns(x) for x in zou.get("negative_space", []))
        # 走为上 3 条负空间全部出现在组合 COP 中（全继承）
        assert zou_ns <= ns_combined
        # 组合负空间条数 ≥ 父条数（解释项并入）
        assert len(ns_combined) >= len(zou_ns)

    def test_apply_inheritance(self):
        zou = _load_stratagem("走为上")
        wj = _load_stratagem("围魏救赵")
        composed = {"COP-ID": "COMPOSED-TEST", "primitives": zou["primitives"]}
        SL.apply_inheritance(composed, zou, [wj])
        assert "semantic_inheritance" in composed
        assert composed["semantic_inheritance"]["parent"] == zou["COP-ID"]
        assert len(composed["negative_space"]) >= 3

    def test_去重(self):
        # 相同约束不重复并入
        comb, inherited, union = SL.inherit_negative_space(
            {"COP-ID": "P", "negative_space": ["⊗ 相同约束"], "primitives": []},
            [{"COP-ID": "I", "negative_space": ["⊗ 相同约束"], "primitives": []}],
        )
        assert union == 1
        assert len(comb) == 1

    def test_解释项原语级_约束并入(self):
        # 解释项原语级 ⊗ 约束（negative_space 字段）并入组合负空间
        parent = {"COP-ID": "P", "negative_space": ["⊗ 父约束"], "primitives": []}
        interp = {
            "COP-ID": "I",
            "negative_space": [],
            "primitives": [{"name": "x", "negative_space": "⊗ 原语级约束: 禁越界"}],
        }
        comb, inherited, union = SL.inherit_negative_space(parent, [interp])
        assert "原语级约束" in "".join(inherited)
        assert union == 2

    def test_空输入(self):
        comb, inherited, union = SL.inherit_negative_space(
            {"COP-ID": "P", "negative_space": [], "primitives": []}, []
        )
        assert union == 0
        assert comb == []

    def test_实证3_三组合批量继承(self):
        # 验收「负空间继承 3/3 组合验证」：走为上⟂围魏救赵 / 走为上⟂囚徒困境 / 围魏救赵⟂囚徒困境
        combos = [
            ("COMPOSED-走为上_围魏救赵.yaml", "走为上", "围魏救赵"),
            ("COMPOSED-走为上_囚徒困境.yaml", "走为上", "囚徒困境"),
            ("COMPOSED-围魏救赵_囚徒困境.yaml", "围魏救赵", "囚徒困境"),
        ]
        for comp_fn, p_name, i_name in combos:
            composed = _load("cop-library/compositions/" + comp_fn)
            parent = _load_stratagem(p_name)
            # 组合 COP 的负空间必须包含父 COP 全部约束（继承规则成立）
            ns_comp = set(SL._normalize_ns(x) for x in composed.get("negative_space", []))
            ns_parent = set(SL._normalize_ns(x) for x in parent.get("negative_space", []))
            assert ns_parent <= ns_comp, f"{comp_fn}: 父约束未全部继承"
            # 组合负空间条数 ≥ 父条数（解释项并入）
            assert len(ns_comp) >= len(ns_parent), f"{comp_fn}: 继承后少于父级"
            print(f"  ✓ {comp_fn}: parent={len(ns_parent)} combined={len(ns_comp)} 继承成立")


# ============ 流水线接入（s5 → semantic） ============
class TestPipelineIntegration:
    def test_s6_semantic(self):
        zou = _load_stratagem("走为上")
        SL.s6_semantic(zou)
        assert zou["semantic"]["u0"] > 0
        assert zou["validation"]["semantic_checks"]["u0_computed"] is True
        assert zou["validation"]["passed"] is True

    def test_compile_with_semantics(self):
        mck = _load("compiler/麦肯锡思维协议.yaml")
        cop, u0, bd = SL.compile_with_semantics(mck)
        assert cop["semantic"]["u0"] == u0
        assert bd["primitive_count"] == 7

    def test_组合COP_接入语义层(self):
        composed = _load("cop-library/compositions/COMPOSED-走为上_围魏救赵.yaml")
        SL.s6_semantic(composed)
        assert "semantic" in composed
        assert composed["semantic"]["u0"] > 0

    def test_负空间覆盖_原语级计数(self):
        # 原语级 ⊗ 约束计入负空间覆盖（麦肯锡 COP：7 原语中 4 条带 ⊗ + COP 级 3 条）
        mck = _load("compiler/麦肯锡思维协议.yaml")
        cov = SL.negative_space_coverage(mck)
        assert cov == pytest.approx(1.0)  # 3(COP级) + 4(原语级) ≥ 基线 3 → 封顶


# ============ M2 任务②: U0 × U_CDE 场景依存效用联合（T-110） ============
class TestUCDE:
    def test_公式(self):
        # U_CDE(c|s) = U0·SC·A
        assert SL.u_cde(0.8, 0.5, 0.4) == pytest.approx(0.16)
        assert SL.u_cde(1.0, 1.0, 1.0) == pytest.approx(1.0)

    def test_cosine_sim_非负标度(self):
        # A∈[0,1]；相同向量 → 1.0；正交 → 0
        assert SL.cosine_sim([1, 0], [1, 0]) == pytest.approx(1.0)
        assert SL.cosine_sim([1, 0], [0, 1]) == pytest.approx(0.0)
        assert 0 <= SL.cosine_sim([0.8, 0.2], [0.7, 0.3]) <= 1

    def test_实证1_复现(self):
        # 实证 1: 走为上在商业转型场景 U_CDE=0.796（U0=1.0 原型口径）
        zou = _load_stratagem("走为上")
        sc = SL.sc_scene(0.8, 0.8, 0.8, 0.1)
        a = SL.cosine_sim([0.8, 0.2, 0.9, 0.7, 0.3], [0.7, 0.3, 0.8, 0.6, 0.4])
        # 联合: 用真实 COP 自动 U0 × SC × A
        u = SL.u_cde(zou, sc, a)
        assert 0 <= u <= 1
        assert u == pytest.approx(SL.compute_u0(zou)[0] * sc * a)

    def test_联合计算_完整明细(self):
        zou = _load_stratagem("走为上")
        bd = SL.u_cde_breakdown(zou, [0.7, 0.3, 0.8, 0.6, 0.4], SL.sc_scene(0.8, 0.8, 0.8, 0.1))
        assert bd["cop_id"] == zou["COP-ID"]
        assert bd["u0"] > 0 and 0 <= bd["a"] <= 1 and 0 <= bd["u_cde"] <= 1
        assert "熔断候选" in bd["negative_u_handling"] or "正常" in bd["negative_u_handling"]

    def test_负U处理_X4(self):
        # 低 U（<0.15）不计入正和，触发熔断候选（红队 X-4）
        bd = SL.u_cde_breakdown(_load_stratagem("走为上"), [1.0, 0.0, 0.0, 0.0, 0.0], 0.1)
        if bd["u_cde"] < 0.15:
            assert "熔断候选" in bd["negative_u_handling"]
        else:
            assert "正常" in bd["negative_u_handling"]

    def test_U记号消歧声明(self):
        bd = SL.u_cde_breakdown(_load_stratagem("走为上"), [0.7, 0.3, 0.8, 0.6, 0.4], 0.5)
        assert "U_CDE 与五维价值向量" in bd["U 记号消歧"]


# ============ 五阶段流水线接入（s5 → semantic） ============
class TestPipelineWiring:
    def test_s2s4_组装_经s5s6(self):
        """复用 compile_thirty_six_stratagems.assemble_one（S2-S4）→ s5_validate → s6_semantic"""
        sys.path.insert(0, _THIS)
        import compile_thirty_six_stratagems as C36

        cop, fn = C36.assemble_one("胜战计", 1, "瞒天过海", "man_tian_guo_hai",
                                   "示假隐真", "己方关键行动需隐蔽",
                                   ["制造假象"], "敌方识破则失效")
        # S5（cognitive_compiler 内嵌于 assemble_one）
        assert cop["validation"]["passed"] is True
        # S6 语义层接入
        SL.s6_semantic(cop)
        assert "semantic" in cop
        assert cop["semantic"]["u0"] > 0
        assert cop["validation"]["semantic_checks"]["u0_computed"] is True

    def test_pipeline_compile_包装层(self, tmp_path):
        """pipeline_compile：五阶段 + 语义层（不改写 cognitive_compiler.py）"""
        # 构造最小专家 md（frontmatter + fn 签名块）
        md = tmp_path / "expert.md"
        md.write_text(
            "---\nname: test-expert\ndisplayName: 测试专家\nprofession: 测试\n---\n\n"
            "## 方法论\n1. **测试方法**\n`fn solve(x) -> y`\n前置：p\n后置：q\n⊗ 约束：禁越界\n",
            encoding="utf-8",
        )
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        cop, out_path = SL.pipeline_compile(str(md), output_dir=str(out_dir))
        assert cop["semantic"]["u0"] > 0
        assert os.path.isfile(out_path)
        # 落盘产物含语义层字段（回读校验）
        with open(out_path, "r", encoding="utf-8") as f:
            persisted = yaml.safe_load(f)
        assert persisted["semantic"]["u0"] == cop["semantic"]["u0"]
