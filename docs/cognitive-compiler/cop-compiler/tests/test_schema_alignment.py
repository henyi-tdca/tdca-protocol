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

"""schema_alignment.py 测试（M3 任务③：白皮书 schema 对齐）
覆盖: FORM-001 PART A-F 映射表 / 单 COP 对齐报告 / 域全量报告 / 7 域汇总
溯源: TDCA-TP-FORM-001 + 白皮书 schema + DCD-COPCOMPILER-M3-001 任务③（≥90%）
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
LIB = os.environ.get("TDCA_COP_LIB") or os.path.join(_THIS, "..", "cop-library")
import schema_alignment as SA


def _load(rel):
    if rel.startswith("cop-library/"):
        path = os.path.join(LIB, rel[len("cop-library/"):])
    else:
        path = os.path.join(_THIS, "..", rel)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestMappingTable:
    def test_六部分映射(self):
        parts = {m[0] for m in SA.FORM_TO_COP_MAP}
        assert "PART A 元数据" in parts and "PART B NSFL" in parts
        assert "PART C 六要素" in parts and "PART D NCA" in parts
        assert "PART E 市场化" in parts and "PART F 校验" in parts

    def test_显式字段13项(self):
        assert len(SA.EXPLICIT_FIELDS) == 13


class TestAlignmentReport:
    def test_单COP_完整映射(self):
        cop = _load("cop-library/stratagems/第01计-瞒天过海.yaml")
        r = SA.alignment_report(cop, "stratagems")
        assert r["cop_id"] == cop["COP-ID"]
        assert r["completeness"] == 100.0
        assert r["missing_count"] == 0

    def test_组合COP_条件豁免(self):
        # 组合 COP：nesting_check 满足（composition 在位），validation 由 s6 补全
        cop = _load("cop-library/compositions/COMPOSED-走为上_围魏救赵.yaml")
        r = SA.alignment_report(cop, "compositions")
        assert r["completeness"] >= 90
        assert r["mapped_count"] >= 12


class TestBatchReport:
    def test_域全量_达标(self):
        for d in ("stratagems", "games", "scenario", "mechanism_design", "tdca_core", "compositions"):
            r = SA.batch_alignment_report(d)
            assert r["pass_rate"] == 100.0
            assert r["avg_completeness"] >= 90

    def test_百家库全量(self):
        r = SA.batch_alignment_report("hundred_schools")
        assert r["total"] == 203
        assert r["pass_rate"] == 100.0
        assert r["avg_completeness"] >= 90

    def test_七域汇总(self):
        s = SA.full_alignment_report()
        assert set(s.keys()) == {"stratagems", "games", "scenario", "mechanism_design",
                                 "tdca_core", "compositions", "hundred_schools"}
        for d, r in s.items():
            assert r["avg_completeness"] >= 90, f"{d}: {r['avg_completeness']}% < 90%"
