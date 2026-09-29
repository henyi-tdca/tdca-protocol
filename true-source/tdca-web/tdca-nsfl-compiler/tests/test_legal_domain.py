# -*- coding: utf-8 -*-
"""法律域典型场景回归测试（EXP-LEGAL-COMPILE-001 实验用例固化）。

4 条著作权侵权认定编译用例纳入编译器 CI 测试集（人类裁决 2026-08-11）——
验证「法律负空间可编程化」链路: 法务智能体检索条款 → NSFL 声明 → 编译器编译。

锚定: EXP-LEGAL-COMPILE-001（实验归档）+ ID86（法律禁止=绝对负空间）
     + ID85（三不可/三可）+ ID73（判例解释项）+ ID35（制度-技术同构）
"""
import pytest

from nsfl_compiler import NSFLCompiler, CompileStatus

# 著作权侵权认定用例（来源: 法务智能体 KG-LEGAL L-CN-CR-001/002 + 判例 J-003）
COPYRIGHT_DECLARATIONS = [
    # (声明, 期望 fuse_type, 期望 fuse_level, 期望 alt_path 语义)
    ("NSFL: ⊗ LEGAL.copyright.unlicensed_reproduce(work) — 未经著作权人许可复制作品（著作权法第 10 条）",
     "LEGAL", "PERMANENT_BAN", "absolute"),
    ("NSFL: ⊗ LEGAL.copyright.unlicensed_distribute(work) — 未经许可发行/信息网络传播作品（著作权法第 10 条）",
     "LEGAL", "PERMANENT_BAN", "absolute"),
    ("NSFL: ⊙ SENSITIVE_CONTENT.copyright.fair_use(work) | personal_study:observe — 合理使用（个人学习/评论/教学科研，著作权法第 24 条）",
     "ETHICAL", "OBSERVE", "scenario"),
    ("NSFL: ⊙ SENSITIVE_CONTENT.copyright.ai_training(work) | public_article:suspend — AI 训练使用公开文章（合理使用边界，判例 J-003）",
     "ETHICAL", "SUSPEND", "scenario"),
]


class TestCopyrightLegalDomain:
    """法律域典型场景（著作权侵权认定）回归——实验用例固化。"""

    def test_compile_for_scene_legal(self):
        """场景驱动入口: 场景+素材 → 编译（方案 B 沙盒流程）。"""
        res = NSFLCompiler().compile_for_scene(
            scene={
                "action": "unlicensed_reproduce",
                "ns_type": "LEGAL",
                "operator": "⊗",
                "note": "未经著作权人许可复制作品（著作权法第 10 条）",
                "domain": "copyright",
            },
            legal_refs=["L-CN-CR-001"],
        )
        assert res.ok
        ir = res.ir
        assert ir.rule["fuse_type"] == "LEGAL"
        assert ir.rule["alt_path"] is None
        assert ir.directive["fuse_level"] == "PERMANENT_BAN"
        assert "L-CN-CR-001" in ir.rule["source_ref"]  # 素材引用入审计

    def test_compile_for_scene_fair_use(self):
        """场景化豁免: 合理使用 ⊙（第 24 条）。"""
        res = NSFLCompiler().compile_for_scene(
            scene={
                "action": "fair_use",
                "ns_type": "SENSITIVE_CONTENT",
                "operator": "⊙",
                "parameter": "personal_study:observe",
                "note": "合理使用（个人学习，著作权法第 24 条）",
                "domain": "copyright",
            },
            legal_refs=["L-CN-CR-002"],
        )
        assert res.ok
        assert res.ir.rule["fuse_type"] == "ETHICAL"
        assert res.ir.directive["fuse_level"] == "OBSERVE"
        assert "L-CN-CR-002" in res.ir.rule["source_ref"]

    def test_compile_for_scene_no_legal_ref(self):
        """无素材引用也可编译（素材=输入原料，非必需）。"""
        res = NSFLCompiler().compile_for_scene(
            scene={"action": "aggregate_data", "ns_type": "TECH_CONSTRAINT",
                   "operator": "⊘", "parameter": "max:100",
                   "note": "数据聚合限频", "domain": "data"})
        assert res.ok
        assert "no-legal-ref" in res.ir.rule["source_ref"]

    @pytest.mark.parametrize("src,fuse_type,fuse_level,kind", COPYRIGHT_DECLARATIONS,
                             ids=["cr10-reproduce", "cr10-distribute",
                                  "cr24-fair_use", "j003-ai_training"])
    def test_copyright_compilation(self, src, fuse_type, fuse_level, kind):
        """4 条著作权用例全部编译成功且语义正确（EXP 实验基线）。"""
        res = NSFLCompiler().compile(src, source_ref="著作权法侵权认定")
        assert res.ok, res.errors
        assert res.status == CompileStatus.OK
        ir = res.ir
        assert ir.rule["fuse_type"] == fuse_type
        assert ir.directive["fuse_level"] == fuse_level
        # ID86: 绝对负空间无替代路径；场景化负空间可配置
        if kind == "absolute":
            assert ir.rule["alt_path"] is None
            assert ir.rule["severity"] == "HIGH"
            assert ir.directive["tier"] == "ATOMIC"
        else:
            assert ir.directive["tier"] == "HARD"  # 场景化 ⊙ 默认 HARD 档

    def test_legal_absolute_no_escape(self):
        """ID86 自动施加: 侵权规则无逃生路径（法律禁止=绝对负空间）。"""
        res = NSFLCompiler().compile(
            "NSFL: ⊗ LEGAL.copyright.unlicensed_reproduce(work) — 复制作品（第 10 条）")
        assert res.ok
        rule = res.ir.rule
        assert rule["alt_path"] is None
        assert rule["severity"] == "HIGH"
        assert rule["enabled"] is True
        d = res.ir.directive
        assert d["fuse_level"] == "PERMANENT_BAN"
        assert d["tier"] == "ATOMIC"

    def test_fair_use_not_auto_exempted(self):
        """ID85 三可原则: 合理使用非自动豁免，须显式场景化声明。"""
        # 无场景化声明的复制行为 → LEGAL 绝对禁止（不因"合理使用"概念自动豁免）
        res = NSFLCompiler().compile(
            "NSFL: ⊗ LEGAL.copyright.unlicensed_reproduce(work) — 复制（无场景）")
        assert res.ok
        assert res.ir.rule["fuse_type"] == "LEGAL"
        # 场景化豁免须显式 ⊙ 声明（如 fair_use 用例）——schema 无自动降级路径
        assert res.ir.rule["severity"] == "HIGH"

    def test_four_cases_full_chain(self):
        """4 条用例全链路（词法→语法→语义→schema→IR）无回归。"""
        compiler = NSFLCompiler()
        for src, *_ in COPYRIGHT_DECLARATIONS:
            r = compiler.compile(src)
            assert r.ok and r.ir is not None
            assert r.ir.bytecode, "字节码为空"
            assert r.ir.rule["rule_id"].startswith("NSFL-")
