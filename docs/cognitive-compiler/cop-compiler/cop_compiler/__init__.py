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

"""
TDCA-COP-COMPILER-001 · COP 编译器生产化打包库（M4 任务①）
================================================================
复用基座（只读引用，不改写）:
  - tdca-thinktank/research/topics/thinking-protocol/compiler/
    semantic_layer.py（语义层：U0 定值/负空间继承/U_CDE 联合/E 定标）
    batch_pipeline.py（批产管线：7 域一键编译/72 文件/强制门）
    schema_alignment.py（FORM-001 PART A-F 对齐）
    compiler_wiring.py（编译族接线：NCA/NSFL/强制门）
纪律:
  - M1-M3 FROZEN 基线不动；源模块只读引用（REUSE-001 §三.4）
  - 本包为生产化入口（import 转发 + 便捷 API），不复制源码
SPDX-License-Identifier: Apache-2.0
"""
import os
import sys

# 复用基座路径（只读引用）
_COMPILER_SRC = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "compiler_src",
))
if _COMPILER_SRC not in sys.path:
    sys.path.insert(0, _COMPILER_SRC)

# 版本与状态
__version__ = "V1.0.0"
__status__ = "DRAFT（M4 生产化部署）"
__basis__ = "DCD-COPCOMPILER-M1/M2/M3-FROZEN-001 + DCD-COPCOMPILER-M4-001"

# ============ 语义层（semantic_layer） ============
from semantic_layer import (
    U0_W, PRIMITIVE_CAP, NEGSPACE_BASELINE, E_CALIBRATION,
    NEGATIVE_U_THRESHOLD, DEGENERATE_SC_THRESHOLD,
    six_elements_completeness, negative_space_coverage,
    u0_semantic, compute_u0, attach_semantic,
    inherit_negative_space, apply_inheritance,
    s6_semantic, pipeline_compile, compile_with_semantics,
    cosine_sim, sc_scene, u_cde, u_cde_breakdown, attach_u_cde,
    degenerate_sc_check, get_calibration, update_calibration,
)

# ============ 批产管线（batch_pipeline） ============
from batch_pipeline import (
    DOMAINS, LIB, BATCH_OUT,
    list_domain_cops, list_domain_manifests, verify_manifests,
    admission_gate_precheck, compile_domain, compile_all,
    verify_72_files, acceptance, run_batch,
)

# ============ schema 对齐（schema_alignment） ============
from schema_alignment import (
    FORM_TO_COP_MAP, EXPLICIT_FIELDS,
    alignment_report, batch_alignment_report, full_alignment_report,
)

# ============ 编译族接线（compiler_wiring） ============
from compiler_wiring import (
    nca_emit_wiring, nsfl_breaker_wiring,
    enforce_entry_wiring, division_of_labor, run_wiring,
)

# ============ 便捷 API ============
def compile_cop(cop, scene_mode=None):
    """一键编译单个 COP：语义层增强（+ 可选 U_CDE）"""
    cop = s6_semantic(cop)
    if scene_mode:
        attach_u_cde(cop, scene_mode["scene_vector"], scene_mode["sc"])
    return cop


def batch_compile(domain="all", scene_mode=None):
    """一键批产：compile_domain（单域）或 compile_all（全域）"""
    if domain == "all":
        return compile_all()
    return compile_domain(domain, scene_mode=scene_mode)


__all__ = [
    # 版本
    "__version__", "__status__", "__basis__",
    # 语义层
    "U0_W", "PRIMITIVE_CAP", "NEGSPACE_BASELINE", "E_CALIBRATION",
    "NEGATIVE_U_THRESHOLD", "DEGENERATE_SC_THRESHOLD",
    "six_elements_completeness", "negative_space_coverage",
    "u0_semantic", "compute_u0", "attach_semantic",
    "inherit_negative_space", "apply_inheritance",
    "s6_semantic", "pipeline_compile", "compile_with_semantics",
    "cosine_sim", "sc_scene", "u_cde", "u_cde_breakdown", "attach_u_cde",
    "degenerate_sc_check", "get_calibration", "update_calibration",
    # 批产
    "DOMAINS", "LIB", "BATCH_OUT",
    "list_domain_cops", "list_domain_manifests", "verify_manifests",
    "admission_gate_precheck", "compile_domain", "compile_all",
    "verify_72_files", "acceptance", "run_batch",
    # schema 对齐
    "FORM_TO_COP_MAP", "EXPLICIT_FIELDS",
    "alignment_report", "batch_alignment_report", "full_alignment_report",
    # 接线
    "nca_emit_wiring", "nsfl_breaker_wiring",
    "enforce_entry_wiring", "division_of_labor", "run_wiring",
    # 便捷 API
    "compile_cop", "batch_compile",
]
