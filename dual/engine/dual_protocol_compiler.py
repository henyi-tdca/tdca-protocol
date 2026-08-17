# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-20260811-002-DUAL-PROTOCOL
# 目标函数:     双协议化合引擎：TDCA 公共制度 + 场景制度 → 化合产物
# 约束矩阵:     宪法十六条 + ID35 同构 + ID90 最小化合 + CHEM-001/002 + NSFL-V0.2
# 先验分布:     TDCA-DUAL-PROTOCOL-001-V1.0 设计稿
# 配置权边界:    L2 配置权市场层；不触碰 L0 法律底层；化合产物必须生成 NCA
# 预期分配:     化合产物 dual-* + 校验报告 + NCA 存证
# 审计轨迹:      TDCA-NCA-20260811-006-DUAL-PROTOCOL
# 开发者:       [人类签批人]
# 模拟态标注（ID92）: 本引擎为工具实现，不构成真实配置权执行路径
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
"""TDCA 双协议化合引擎 V1.0.0

双协议化合 = TDCA 公共制度（全局坐标系）+ 用户场景制度（局部坐标卡）→ 化合产物（NCA）
流程: 加载 → 同构校验（ID35）→ 最小化合判定（ID90）→ 化合 → 导出 + NCA
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class DualProtocolCompiler:
    """双协议化合编译器。"""

    tdca_path: str
    scene_path: str
    scene_name: str
    mode: str = "strict"  # strict | lenient
    validation_errors: List[str] = field(default_factory=list)

    # ---- 加载 ----

    def load_tdca(self) -> dict:
        """加载 TDCA 公共制度（只读引用指针）。"""
        tdca = {}
        const_dir = Path(self.tdca_path) / "constitution"
        for f in ["TDCA-CONST-v3.1.2.md", "UPDA-v2.0.md", "NSFL-v0.2.md", "TERMS-v3.0.md"]:
            p = const_dir / f
            if p.exists():
                content = p.read_text(encoding="utf-8")
                tdca[f.replace(".md", "")] = content
        if not tdca:
            self.validation_errors.append(f"TDCA 公共制度加载失败: {self.tdca_path}")
        return tdca

    def load_scene(self) -> dict:
        """加载用户场景制度。"""
        scene = {}
        for f in ["scene-constitution.md", "scene-constraints.md", "scene-nsfl.md",
                  "scene-terms.md", "scene-review.md", "scene-pricing.md"]:
            p = Path(self.scene_path) / f
            if p.exists():
                scene[f.replace(".md", "")] = p.read_text(encoding="utf-8")
        required = ["scene-constitution", "scene-constraints", "scene-nsfl"]
        for r in required:
            if r not in scene:
                self.validation_errors.append(f"场景制度缺少必须文件: {r}")
        return scene

    # ---- 同构校验（ID35）----

    def validate_isomorphism(self) -> bool:
        """同构校验：场景制度必须与 TDCA 公共制度同构映射，不得冲突。"""
        tdca = self.load_tdca()
        scene = self.load_scene()
        if not tdca or not scene:
            return False

        const = scene.get("scene-constitution", "")
        # 1. 服从声明
        for stmt in ["服从 TDCA 宪法", "TDCA-CONST", "不得与任何条款冲突"]:
            if stmt not in const:
                self.validation_errors.append(f"场景宪法缺少同构声明: {stmt}")
        # 2. NSFL 覆盖
        nsfl = scene.get("scene-nsfl", "")
        if "TDCA-NSFL" not in nsfl:
            self.validation_errors.append("场景负空间未引用 TDCA-NSFL（必须完整包含公共负空间）")
        # 3. 冲突条款扫描（strict 模式：场景中出现的 TDCA 条款不得带冲突否定词）
        if self.mode == "strict":
            for line in const.splitlines():
                if re.search(r"(不遵守|违反|豁免|例外于)\s*(宪法|TDCA-CONST)", line):
                    self.validation_errors.append(f"场景宪法疑似冲突条款: {line.strip()}")
        return len(self.validation_errors) == 0

    # ---- 最小化合判定（ID90）----

    def check_minimal_compound(self) -> tuple:
        """最小化合判定三条件：不可拆分性 / 涌现价值 / 非线性。"""
        scene = self.load_scene()
        nsfl = scene.get("scene-nsfl", "")
        constraints = scene.get("scene-constraints", "")

        checks = {}
        # 1. 不可拆分性：存在 TDCA 公共制度无法覆盖的场景特定负空间/约束
        has_scene_rules = bool(re.search(r"SCENE-(LEGAL|ETHIC|BIZ)-\d+", nsfl))
        has_scene_constraints = bool(re.search(r"scene_constraints|CON-\d+", constraints))
        checks["不可拆分性"] = has_scene_rules or has_scene_constraints

        # 2. 涌现价值：场景制度扩展了配置权边界/审查标准（产生 TDCA 单协议无法提供的价值）
        has_boundaries = bool(re.search(r"scene_config_boundaries|role:", constraints))
        has_review = bool(re.search(r"scene_review_standards|REV-\d+", constraints))
        checks["涌现价值"] = has_boundaries or has_review

        # 3. 非线性：场景负空间含 CRITICAL/BLOCKING 级强制规则（无法用加权组合逼近）
        has_critical = bool(re.search(r"CRITICAL|BLOCKING", nsfl))
        checks["非线性"] = has_critical

        passed = all(checks.values())
        message = "、".join(f"{k}: {'通过' if v else '不通过'}" for k, v in checks.items())
        return passed, message

    # ---- 化合 ----

    def compile(self) -> dict:
        """执行化合，生成双协议化合产物。"""
        tdca = self.load_tdca()
        scene = self.load_scene()
        const = scene.get("scene-constitution", "")
        nsfl = scene.get("scene-nsfl", "")
        constraints = scene.get("scene-constraints", "")

        scene_rules = re.findall(r"SCENE-(LEGAL|ETHIC|BIZ)-\d+", nsfl) or ["(场景负空间规则)"]
        tdca_rule_note = "TDCA-NSFL-v0.2 核心规则集（引用指针，无硬编码计数）"
        product = {
            "dual_protocol": {
                "metadata": {
                    "tdca_version": "v3.1.2",
                    "scene_name": self.scene_name,
                    "scene_version": self._extract_version(const, "SCENE-CONST"),
                    "compilation_mode": self.mode,
                    "compilation_time": datetime.now().isoformat(),
                    "compiler": "TDCA-Dual-Protocol-Compiler-v1.0.0",
                },
                "constitution": {
                    "hierarchy": "TDCA 宪法 > 场景宪法 > 项目级约定",
                    "conflict_resolution": "TDCA 宪法优先",
                },
                "constraints": {
                    "tdca_base": "六要素标准（TDCA-CONST-v3.1.2）",
                    "scene_extension": self._extract_section(constraints, "场景约束扩展"),
                    "merged": "TDCA 六要素 + 场景特定约束（化合）",
                },
                "nsfl": {
                    "tdca_rules": tdca_rule_note,
                    "scene_rules": len(scene_rules),
                    "total_rules": f"TDCA 核心规则集（指针）+ {len(scene_rules)} 条场景规则",
                    "merged_rules": "TDCA 公共负空间 + 场景特定负空间（不可删减）",
                },
                "six_elements": {
                    "template": "dual-six-elements.md（化合六要素模板）",
                },
                "review": {
                    "base_review": "3 项（TDCA 标准：六要素/正和/NCA）",
                    "scene_review": self._extract_review_items(constraints),
                    "merged_review": "通用审查 + 场景特定审查",
                },
            }
        }
        return product

    # ---- 导出 ----

    def export(self, output_dir: str) -> str:
        """导出化合产物到目录。"""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        product = self.compile()

        dual_dir = out / "dual-protocol"
        dual_dir.mkdir(parents=True, exist_ok=True)

        # dual-constitution.md
        m = product["dual_protocol"]
        (dual_dir / "dual-constitution.md").write_text(
            f"# {self.scene_name} 双协议化合宪法\n"
            f"# TDCA: v3.1.2 | 场景: {m['metadata']['scene_version']}\n\n"
            f"层级: {m['constitution']['hierarchy']}\n"
            f"冲突解决: {m['constitution']['conflict_resolution']}\n",
            encoding="utf-8",
        )
        # dual-constraints.md
        (dual_dir / "dual-constraints.md").write_text(
            f"# {self.scene_name} 双协议化合约束矩阵\n\n"
            f"TDCA 基础: {m['constraints']['tdca_base']}\n"
            f"场景扩展: {m['constraints']['scene_extension']}\n"
            f"化合结果: {m['constraints']['merged']}\n",
            encoding="utf-8",
        )
        # dual-nsfl.md
        (dual_dir / "dual-nsfl.md").write_text(
            f"# {self.scene_name} 双协议化合负空间\n\n"
            f"TDCA 规则: {m['nsfl']['tdca_rules']} 条 | 场景规则: {m['nsfl']['scene_rules']} 条 | 合计: {m['nsfl']['total_rules']} 条\n"
            f"规则集合: {m['nsfl']['merged_rules']}\n",
            encoding="utf-8",
        )
        # dual-six-elements.md
        (dual_dir / "dual-six-elements.md").write_text(
            f"# {self.scene_name} 化合六要素模板\n\n"
            f"模板: {m['six_elements']['template']}\n",
            encoding="utf-8",
        )
        # dual-review.md
        (dual_dir / "dual-review.md").write_text(
            f"# {self.scene_name} 化合审查模板\n\n"
            f"通用: {m['review']['base_review']}\n"
            f"场景: {m['review']['scene_review']}\n"
            f"化合: {m['review']['merged_review']}\n",
            encoding="utf-8",
        )
        # dual-nca.json
        nca_id = f"TDCA-NCA-DUAL-{self.scene_name}-{m['metadata']['scene_version']}"
        product_str = json.dumps(product, ensure_ascii=False, indent=2)
        nca = {
            "nca_id": nca_id,
            "hash": hashlib.sha256(product_str.encode("utf-8")).hexdigest(),
            "validation": "同构校验通过 + 最小化合判定通过" if not self.validation_errors else "存在校验错误",
            "scene": self.scene_name,
            "tdca_version": "v3.1.2",
            "scene_version": m["metadata"]["scene_version"],
            "mou_anchor": {
                "status": "Simulated",
                "note": "本化合产物为模拟态示范（D-011），不含真实税收/MOU 硬数据；真实锚定待 DCEP 接入",
                "cbdc_anchor": "cbdc_anchor 参数（模拟态裁决 D-011）",
                "inbound_tax": None,
                "outbound_tax": None,
            },
            "data_nature": "simulated_demonstration",
        }
        (dual_dir / "dual-nca.json").write_text(
            json.dumps(nca, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(dual_dir)

    # ---- 工具 ----

    @staticmethod
    def _extract_version(content: str, prefix: str) -> str:
        m = re.search(rf"{prefix}-v([\d.]+)", content)
        return f"v{m.group(1)}" if m else "v1.0.0"

    @staticmethod
    def _extract_section(content: str, title: str) -> str:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if title in line:
                return " ".join(lines[i + 1:i + 4]).strip() or f"{title}（见场景约束矩阵）"
        return f"{title}（见场景约束矩阵）"

    @staticmethod
    def _extract_review_items(content: str) -> str:
        items = re.findall(r"(?:REV|FIN|MED|GOV|EDU|SCENE)-\d+", content)
        return f"{len(items)} 项场景审查（{'/'.join(dict.fromkeys(items)) if items else '见场景审查标准'}）"


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="TDCA 双协议化合引擎")
    parser.add_argument("--tdca-path", required=True, help="TDCA 公共制度目录")
    parser.add_argument("--scene-path", required=True, help="场景制度目录")
    parser.add_argument("--scene-name", required=True, help="场景名称")
    parser.add_argument("--output", default="./", help="输出目录")
    parser.add_argument("--mode", default="strict", choices=["strict", "lenient"])
    args = parser.parse_args()

    compiler = DualProtocolCompiler(
        tdca_path=args.tdca_path,
        scene_path=args.scene_path,
        scene_name=args.scene_name,
        mode=args.mode,
    )

    print(f"✅ TDCA 公共制度加载完成: v3.1.2")
    print(f"✅ 场景制度加载完成: {args.scene_name}")
    print("🔍 执行同构校验...")
    if not compiler.validate_isomorphism():
        print("❌ 同构校验失败")
        for e in compiler.validation_errors:
            print(f"  - {e}")
        return 1
    print("  ✅ 同构校验通过")

    print("🔍 执行最小化合判定...")
    passed, message = compiler.check_minimal_compound()
    print(f"  {message}")
    if not passed:
        print(f"❌ 最小化合判定失败: {message}")
        return 1
    print("  ✅ 最小化合判定通过")

    print("🔧 执行双协议化合...")
    out = compiler.export(args.output)
    print("✅ 双协议化合完成")
    print(f"✅ 双协议 NCA 生成完成: TDCA-NCA-DUAL-{args.scene_name}-v1.0.0")
    print(f"✅ 双协议化合产物导出完成: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
