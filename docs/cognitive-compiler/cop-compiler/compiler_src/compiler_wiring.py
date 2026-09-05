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

"""COP 编译器 · 编译族接线模块（TDCA-TP-S3-001 §3.2/3.3 落地）
================================================================
依据:
  - TDCA-TP-S3-001 §3.2 平行编译族（FC-005/NSFL 编译器/COP 编译器分工）+ §3.3 分工关系
  - 承接指令 P2: ⑦ NCA 发射 ⑧ NSFL 熔断 ⑨ FC-005/NSFL 编译器衔接 ⑩ 强制门概念原型
  - ID56 操作即确权（NCA 发射）；ID86 NSFL 熔断；生态准入强制门（TDCA-CORE-20260815-01）
  - enforce_entry.py（cop-library/tdca_core/，复用基座只读引用）
状态: DRAFT（M1 开发交付物，走 DCD-COP-COMPILER-001 M1 范围）
溯源链: TDCA-TP-S3-001 FROZEN → 本模块（编译族接线）→ M1 验收
"""
import hashlib
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import semantic_layer as SL
import batch_pipeline as BP

COMPILER_DIR = _THIS
TDCA_CORE_DIR = os.path.join(BP.LIB, "tdca_core")
NSFL_VERSION = "V0.1"


# ============ ⑦ NCA 发射接线（操作即确权 ID56） ============
def nca_emit_wiring(domain="stratagems", index=1):
    """NCA 发射接线验证：批产 → 独立 NCA 存证链（NCA-COPCOMPILER-*）
    主链 nca_generator（操作即确权）+ 独立链（REUSE-001 §三.4 不并入主库）双通道
    返回: 接线验证结果 dict
    """
    result = {"wiring": "NCA 发射", "id56": "操作即确权", "emitted": False}
    # 未知域防御（不抛 KeyError）
    if domain not in BP.DOMAINS:
        return {**result, "error": f"未知域: {domain}"}
    # 复用 batch_pipeline 的独立存证链发射（已验证）
    cops = BP.list_domain_cops(domain)
    if not cops:
        return {**result, "error": "域为空"}
    with open(cops[index - 1], "r", encoding="utf-8") as f:
        cop = yaml.safe_load(f)
    SL.attach_semantic(cop)
    # 暂存增强 COP 到 batch-output（供 NCA 哈希）
    out_dir = os.path.join(BP.BATCH_OUT, domain)
    os.makedirs(out_dir, exist_ok=True)
    rel = os.path.basename(cops[index - 1])
    out_path = os.path.join(out_dir, rel)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cop, f, allow_unicode=True, sort_keys=False)
    nca_path = BP.emit_nca(domain, index, cop, out_path)
    result["emitted"] = True
    result["nca_path"] = nca_path
    result["cop_id"] = cop.get("COP-ID")
    result["u0"] = cop.get("semantic", {}).get("u0")
    # 主链 nca_generator 接线检查（可导入即可用，不实际写主库避免污染）
    try:
        sys.path.insert(0, COMPILER_DIR)
        import nca_generator as NCA
        result["main_chain_importable"] = True
        result["main_chain_note"] = "nca_generator.generate_nca 主链可用；批产走独立链（REUSE-001 §三.4）"
    except ImportError as e:
        result["main_chain_importable"] = False
        result["main_chain_error"] = str(e)
    return result


# ============ ⑧ NSFL 熔断接线（ID86 + TDCA-CORE 负空间继承） ============
def nsfl_breaker_wiring():
    """NSFL 熔断接线验证：
    1) 组合 COP 负空间继承（语义层）→ 继承约束触 NSFL 熔断候选（⊗ 语义）
    2) nsfl_runtime 熔断器可用性（ID86 负空间不可越）
    返回: 验证结果 dict
    """
    result = {"wiring": "NSFL 熔断", "id86": "负空间不可越", "checks": {}}
    # 1) 语义层负空间继承（走为上 ⟂ 围魏救赵）
    import test_semantic_layer as TSL  # noqa: F401（复用其加载函数）
    zou = None
    for fn in os.listdir(os.path.join(BP.LIB, "stratagems")):
        if "走为上" in fn:
            with open(os.path.join(BP.LIB, "stratagems", fn), "r", encoding="utf-8") as f:
                zou = yaml.safe_load(f)
            break
    wj = None
    for fn in os.listdir(os.path.join(BP.LIB, "stratagems")):
        if "围魏救赵" in fn:
            with open(os.path.join(BP.LIB, "stratagems", fn), "r", encoding="utf-8") as f:
                wj = yaml.safe_load(f)
            break
    if zou and wj:
        comb, inherited, union = SL.inherit_negative_space(zou, [wj])
        result["checks"]["inheritance"] = {
            "parent": zou["COP-ID"], "interpretant": wj["COP-ID"],
            "combined": len(comb), "inherited": len(inherited), "union": union,
        }
        # 2) 熔断候选判定：继承约束中凡含「失效/禁止/不可」类 ⊗ 即构成熔断条件
        fuse_candidates = [x for x in inherited if any(k in x for k in ("失效", "禁止", "不可", "不得"))]
        result["checks"]["fuse_candidates"] = fuse_candidates
        result["checks"]["fuse_triggered"] = len(fuse_candidates) > 0
    # 3) nsfl_runtime 熔断器可用性
    try:
        sys.path.insert(0, COMPILER_DIR)
        import nsfl_runtime as NSFL
        result["checks"]["runtime_importable"] = True
        result["checks"]["circuit_break_class"] = hasattr(NSFL, "NSFLCircuitBreak")
        result["checks"]["trigger_fn"] = hasattr(NSFL, "trigger_circuit_break")
    except ImportError as e:
        result["checks"]["runtime_importable"] = False
        result["checks"]["runtime_error"] = str(e)
    return result


# ============ ⑩ 强制门概念接线（生态准入） ============
def enforce_entry_wiring():
    """强制门概念原型：生态准入（enforce_entry.py 复用基座，只读引用）
    语义: 凡加入 TDCA 生态的主体必须已加载核心协议（TDCA-CORE-20260815-01），否则拒绝准入
    返回: 接线验证结果 dict
    """
    result = {"wiring": "强制门（生态准入）", "core_id": "TDCA-CORE-20260815-01"}
    try:
        sys.path.insert(0, TDCA_CORE_DIR)
        import enforce_entry as EE
        # 1) 核心协议在位
        base = EE.load_core_base()
        result["core_loaded"] = True
        result["core_cop_id"] = base.get("COP-ID")
        # 2) 准入门：已加载核心 → 准入通过
        admitted = EE.ecosystem_admit("cop-compiler-batch", loaded_ids=[EE.MANDATORY_CORE_ID], note="M1 批产准入验证")
        result["admit_with_core"] = True
        # 3) 未加载核心 → 拒绝（AdmissionDenied）
        try:
            EE.ecosystem_admit("rogue-entity", loaded_ids=[], note="未加载核心")
            result["reject_without_core"] = False
        except EE.AdmissionDenied:
            result["reject_without_core"] = True
    except (ImportError, FileNotFoundError) as e:
        result["error"] = str(e)
    return result


# ============ ⑨ FC-005 / NSFL 编译器分工衔接 ============
def division_of_labor():
    """编译族分工衔接（TDCA-TP-S3-001 §3.2/3.3）：返回衔接声明（供文档/验证）
    五成员: L1 函数语料 / L2 COP（本编译器）/ L3 制度注入 + FC-005 + NSFL 编译器
    """
    return {
        "family": "编译族（五成员）",
        "division": [
            {"member": "L1 函数语料编译器", "produce": "自然语言指令 → 六要素函数语料", "status": "已实现（function_corpus_compiler.py）"},
            {"member": "L2 COP 编译器（本立项）", "produce": "专家知识/范式 → COP（六要素+NSFL+NCA）", "status": "M1 语义层+批产+接线（本交付）"},
            {"member": "L3 制度注入器", "produce": "制度原理 → Executor 认知层+熔断+NCA", "status": "已实现（MEMO-006 四步注入）"},
            {"member": "FC-005 知识图谱编译器", "produce": "tdca-official-kb → Cytoscape 拓扑图", "status": "DCD-006-FC005（tdca-knowledge-graph-compiler/）"},
            {"member": "NSFL 编译器", "produce": "负空间规则 → NSFL 运行时", "status": "DCD-NSFL-COMPILER-001（tdca-nsfl-compiler/）"},
        ],
        "complement": "COP 编译器产「怎么想」，FC-005 产「是什么」图视图，NSFL 编译器产「不可越」运行时，制度注入器产「全局基座」——四者互补",
        "wiring_points": [
            "COP 编译器批产 → NCA 发射（⑦）→ 存证链",
            "COP 负空间继承（语义层）→ NSFL 熔断候选（⑧）→ NSFL 编译器运行时联动",
            "COP 生态准入（⑩ 强制门）→ 核心协议 TDCA-CORE-20260815-01 前置加载",
            "FC-005 读取 tdca-official-kb → 拓扑可视化（只读引用，不反向依赖）",
        ],
    }


def run_wiring():
    """编译族接线全量验证主流程"""
    result = {
        "nca": nca_emit_wiring(),
        "nsfl": nsfl_breaker_wiring(),
        "enforce_entry": enforce_entry_wiring(),
        "division": division_of_labor(),
    }
    return result


if __name__ == "__main__":  # pragma: no cover - 接线验证主入口
    import json
    r = run_wiring()
    print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
