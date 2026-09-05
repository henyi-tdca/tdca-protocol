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

"""cop_compiler 生产化打包库测试（M4 任务①）
覆盖: 导入 / 导出符号 / 便捷 API（compile_cop/batch_compile）/ 定标读取
溯源: DCD-COPCOMPILER-M4-001 任务①（打包可导入 + 回归全绿）
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
sys.path.insert(0, os.path.join(_THIS, '..'))
import cop_compiler as CC


class TestPackage:
    def test_导入(self):
        assert CC.__version__ == "V1.0.0"
        assert "DRAFT" in CC.__status__

    def test_导出符号(self):
        assert "compute_u0" in CC.__all__
        assert "compile_domain" in CC.__all__
        assert "alignment_report" in CC.__all__
        assert "run_wiring" in CC.__all__
        assert len(CC.__all__) >= 50

    def test_复用基座只读(self):
        # 打包库不复制源码（引用发布树内 compiler_src/ 路径）
        assert "compiler_src" in CC._COMPILER_SRC

    def test_compile_cop_便捷API(self):
        cop = yaml.safe_load(open(os.path.join(CC.LIB, "stratagems", "第36计-走为上.yaml"), encoding="utf-8"))
        r = CC.compile_cop(cop)
        assert "semantic" in r and r["semantic"]["u0"] > 0

    def test_compile_cop_U_CDE(self):
        cop = yaml.safe_load(open(os.path.join(CC.LIB, "stratagems", "第36计-走为上.yaml"), encoding="utf-8"))
        scene = {"scene_vector": [0.7, 0.3, 0.8, 0.6, 0.4], "sc": CC.sc_scene(0.8, 0.8, 0.8, 0.1)}
        r = CC.compile_cop(cop, scene_mode=scene)
        assert 0 <= r["semantic"]["u_cde"]["u_cde"] <= 1

    def test_batch_compile_单域(self):
        rep = CC.batch_compile("mechanism_design")
        assert rep["ok"] == 1

    def test_E定标读取(self):
        cal = CC.get_calibration()
        assert cal["version"] == "V1.0-TENTATIVE"
        assert CC.NEGATIVE_U_THRESHOLD == 0.15

    def test_schema_对齐API(self):
        rep = CC.batch_alignment_report("stratagems")
        assert rep["avg_completeness"] >= 90
