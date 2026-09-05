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

"""batch_pipeline.py 测试（P1 批产管线 M1 交付物 + M2 任务①③）
覆盖: 域清单 / 单域编译 / 全域编译 / 72 文件复现 / 验收阈值 / NCA 独立存证链 / 百家库全量 215 / 强制门
溯源: TDCA-TP-S3-001 §四 + 白皮书 §7 + 承接指令 P1 验收 + DCD-COPCOMPILER-M2-001
"""
import json
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
import batch_pipeline as BP
import semantic_layer as SL

BATCH_OUT = BP.BATCH_OUT


@pytest.fixture(scope="module", autouse=True)
def _clean_batch_output():
    """测试前仅清理 COP 输出子目录（保留交付报告 md/json 等交付物，避免误删）"""
    import shutil
    keep = {"BATCH-REPORT.json", "E-CALIBRATION-SIM.json"}
    # 交付报告前缀（md 交付物保留）
    keep_prefixes = ("TDCA-COPCOMPILER-M1-REPRO-001", "TDCA-COPCOMPILER-M1-ACCEPT-001",
                     "TDCA-COPCOMPILER-M1-WIRING-001", "TDCA-COPCOMPILER-E-CALIBRATION-001")
    if os.path.isdir(BATCH_OUT):
        for name in os.listdir(BATCH_OUT):
            p = os.path.join(BATCH_OUT, name)
            if os.path.isdir(p) and name not in ("nca",):
                shutil.rmtree(p)
            elif os.path.isfile(p) and name not in keep and not any(name.startswith(k) for k in keep_prefixes):
                os.remove(p)
    yield


class TestDomainListing:
    def test_七域配置(self):
        assert set(BP.DOMAINS.keys()) == {
            "stratagems", "games", "scenario", "mechanism_design",
            "tdca_core", "compositions", "hundred_schools",
        }

    def test_36计域_36文件(self):
        files = BP.list_domain_cops("stratagems")
        assert len(files) == 36

    def test_百家库域_数量(self):
        files = BP.list_domain_cops("hundred_schools")
        assert len(files) >= 200  # 215 总含 manifest，COP ≥200

    def test_manifest被排除(self):
        files = BP.list_domain_cops("hundred_schools")
        assert not any("manifest" in os.path.basename(f) for f in files)

    def test_M2_百家库全量215(self):
        # M2 任务①: 百家库 215 = 203 COP + 12 manifest 全量纳入
        rep = BP.compile_domain("hundred_schools", emit_nca_flag=False)
        assert rep["ok"] == 203
        assert rep["manifests"]["total"] == 12
        assert rep["manifests"]["ok"] == 12
        assert rep["all_files"] == 215

    def test_manifest_校验(self):
        man_total, man_ok, issues = BP.verify_manifests("hundred_schools")
        assert man_total == 12
        assert man_ok == 12
        assert issues == []


class TestAdmissionGate:
    def test_M2_强制门_前置检查通过(self):
        g = BP.admission_gate_precheck()
        assert g["gate_open"] is True
        assert g["mandatory_core_id"] == "TDCA-CORE-20260815-01"
        assert g["core_base_present"] is True
        assert g["core_cop_id_matches"] is True
        assert g["manifests_base_protocol_ok"] is True

    def test_M2_强制门_核心缺失关闭(self, monkeypatch):
        # 模拟核心基协议缺失 → 强制门关闭（生产化拒绝路径）
        monkeypatch.setattr(BP, "CORE_BASE_FILE", "不存在.yaml")
        g = BP.admission_gate_precheck()
        assert g["gate_open"] is False
        assert g["deny_reason"] is not None


class TestSceneIntegration:
    """M3 任务①: SCEN-COP 场景库联合生产化（U_CDE 接入批产全流程）"""

    def test_SCEN_COP_联合生产化(self):
        scene = {"scene_vector": [0.7, 0.3, 0.8, 0.6, 0.4], "sc": SL.sc_scene(0.8, 0.8, 0.8, 0.1)}
        rep = BP.compile_domain("scenario", emit_nca_flag=False, scene_mode=scene)
        assert rep["ok"] == 7
        assert rep["u_cde"]["coverage"] == 100.0
        assert rep["u_cde"]["computed"] == 7

    def test_产物含u_cde字段(self):
        scene = {"scene_vector": [0.7, 0.3, 0.8, 0.6, 0.4], "sc": SL.sc_scene(0.8, 0.8, 0.8, 0.1)}
        BP.compile_domain("scenario", emit_nca_flag=False, scene_mode=scene)
        import yaml as _yaml
        p = os.path.join(BP.BATCH_OUT, "scenario", "第01场景-场景思维协议.yaml")
        with open(p, "r", encoding="utf-8") as f:
            cop = _yaml.safe_load(f)
        ucde = cop["semantic"]["u_cde"]
        assert set(["u0", "sc", "a", "u_cde", "negative_u_handling"]).issubset(ucde.keys())
        assert 0 <= ucde["u_cde"] <= 1

    def test_attach_u_cde_独立入口(self):
        # semantic_layer.attach_u_cde 便捷入口（未 attach_semantic 时自动补）
        import yaml as _yaml
        src = os.path.join(BP.LIB, "scenario", "第01场景-场景思维协议.yaml")
        with open(src, "r", encoding="utf-8") as f:
            cop = _yaml.safe_load(f)
        SL.attach_u_cde(cop, [0.7, 0.3, 0.8, 0.6, 0.4], 0.8)
        assert "semantic" in cop and "u_cde" in cop["semantic"]

    def test_博弈_组合_全量U_CDE(self):
        # M3 任务②: 批产扩展到博弈（games 4）+ 组合（compositions 13）全量场景模式
        scene = {"scene_vector": [0.7, 0.3, 0.8, 0.6, 0.4], "sc": SL.sc_scene(0.8, 0.8, 0.8, 0.1)}
        for d, expect in (("games", 4), ("compositions", 13)):
            rep = BP.compile_domain(d, emit_nca_flag=False, scene_mode=scene)
            assert rep["ok"] == expect
            assert rep["u_cde"]["coverage"] == 100.0
            assert rep["u_cde"]["computed"] == expect

    def test_M4_七域全量U_CDE(self):
        # M4 任务②: U_CDE 场景库全量接入——7 域全量场景模式（含百家库嵌套子目录递归统计）
        scene = {"scene_vector": [0.7, 0.3, 0.8, 0.6, 0.4], "sc": SL.sc_scene(0.8, 0.8, 0.8, 0.1)}
        total_cop = total_ucde = 0
        for d in BP.DOMAINS:
            rep = BP.compile_domain(d, emit_nca_flag=False, scene_mode=scene)
            total_cop += rep["ok"]
            total_ucde += rep["u_cde"]["computed"]
            assert rep["u_cde"]["coverage"] == 100.0
        assert total_cop == 267 and total_ucde == 267

    def test_M4_字段标准化(self):
        # U_CDE 字段标准化（u0/sc/a/u_cde/negative_u_handling 五字段 + formula/scene_vector）
        scene = {"scene_vector": [0.7, 0.3, 0.8, 0.6, 0.4], "sc": SL.sc_scene(0.8, 0.8, 0.8, 0.1)}
        BP.compile_domain("stratagems", emit_nca_flag=False, scene_mode=scene)
        import yaml as _yaml
        p = os.path.join(BP.BATCH_OUT, "stratagems", "第36计-走为上.yaml")
        with open(p, "r", encoding="utf-8") as f:
            cop = _yaml.safe_load(f)
        ucde = cop["semantic"]["u_cde"]
        assert set(["u0", "sc", "a", "u_cde", "negative_u_handling"]).issubset(ucde.keys())
        assert "formula" in ucde and "scene_vector" in ucde


class TestECalibration:
    def test_E定标实证_数据完整(self):
        import e_calibration_sim as EC
        ev = EC.run_evidence()
        assert ev["status"] == "SIMULATED"
        assert "E-1_负U阈值" in ev["e"] and "E-2_退化SC阈值" in ev["e"] and "E-3_U0权重" in ev["e"]
        # E-1: 阈值候选 0.15
        assert ev["e"]["E-1_负U阈值"]["threshold_candidate"] == 0.15
        # E-2: 阈值候选 0.2 + 极端退化样本全归零
        e2 = ev["e"]["E-2_退化SC阈值"]
        assert e2["threshold_candidate"] == 0.2
        assert e2["extreme_zeroed_at_0.2"] == 4
        assert e2["zeroed_at_0.2"] == 0
        # E-3: 权重候选 0.5-0.3-0.2 + 267 样本
        e3 = ev["e"]["E-3_U0权重"]
        assert e3["weights_candidate"] == {"objective": 0.5, "primitive": 0.3, "negative": 0.2}
        assert e3["sample_count"] >= 260

    def test_E定标_样本分布合理(self):
        import e_calibration_sim as EC
        ev = EC.run_evidence()
        e3 = ev["e"]["E-3_U0权重"]
        assert 0 < e3["u0_min"] <= e3["u0_max"] <= 1
        assert e3["u0_mean"] > 0.5

    def test_E定标_落盘(self, tmp_path):
        import e_calibration_sim as EC
        # main 落盘路径（E-CALIBRATION-SIM.json 写入 batch-output）
        ev = EC.main()
        out = os.path.join(BP.BATCH_OUT, "E-CALIBRATION-SIM.json")
        assert os.path.isfile(out)
        import json as _json
        with open(out, "r", encoding="utf-8") as f:
            data = _json.load(f)
        assert data["status"] == "SIMULATED"

    def test_E定标_常量生效(self):
        # 人类批准暂定生效（T-068 阶段 4）：E-1=0.15 / E-2=0.2 / E-3=0.5-0.3-0.2
        assert SL.NEGATIVE_U_THRESHOLD == 0.15
        assert SL.DEGENERATE_SC_THRESHOLD == 0.2
        assert SL.U0_W == {"objective": 0.5, "primitive": 0.3, "negative": 0.2}
        assert SL.E_CALIBRATION["version"] == "V1.0-TENTATIVE"

    def test_E2_退化归零判定(self):
        assert SL.degenerate_sc_check(0.12)["zeroed"] is True
        assert SL.degenerate_sc_check(0.25)["zeroed"] is False

    def test_E3_权重生效于U0(self):
        # 0.5-0.3-0.2 权重落地计算
        assert SL.u0_semantic(1.0, 5, 1.0) == pytest.approx(1.0)
        assert SL.u0_semantic(0.8, 1, 0.9) == pytest.approx(0.640)

    def test_E定标_动态调整通道(self):
        # 暂定值支持运行时覆盖（沙盒运营动态调整通道；正式修订须人类批准）
        r = SL.update_calibration(negative_u_threshold=0.12, note="沙盒运营测试覆盖")
        assert r["effective"]["E-1_negative_u_threshold"] == 0.12
        assert "override" in r and r["override"]["E-1_negative_u_threshold"] == 0.12
        # 还原正式定标值（避免污染其他测试）
        SL.update_calibration(negative_u_threshold=0.15)
        assert SL.NEGATIVE_U_THRESHOLD == 0.15

    def test_M3_U_CDE沙盒运营实证(self):
        # M3 任务④: 3 场景 × 7 域全量 U_CDE 分布 + E 定标调整输入
        import e_calibration_sim as EC
        ev = EC.run_operations_evidence()
        assert set(ev["scenes"].keys()) == {"商业转型", "军事撤退", "合规审查"}
        for sname, sdata in ev["scenes"].items():
            assert sdata["sample_count"] == 267
            assert 0 <= sdata["u_cde_min"] <= sdata["u_cde_max"] <= 1
        # 低 SC 场景（合规审查）应触发 E-1 熔断（U_CDE < 0.15）
        assert ev["scenes"]["合规审查"]["fuse_trigger_count"] > 0
        # E 定标调整输入在位（当前生效值 + T-068 流程说明）
        assert ev["e_calibration_input"]["current"]["E-1_negative_u_threshold"] == 0.15

    def test_M3_U_CDE运营数据落盘(self):
        # 落盘 U-CDE-OPERATIONS-SIM.json（沙盒运营数据积累）
        import e_calibration_sim as EC
        import json as _json
        ev = EC.run_operations_evidence()
        out = os.path.join(BP.BATCH_OUT, "U-CDE-OPERATIONS-SIM.json")
        os.makedirs(BP.BATCH_OUT, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            _json.dump(ev, f, ensure_ascii=False, indent=2)
        assert os.path.isfile(out)
        with open(out, "r", encoding="utf-8") as f:
            data = _json.load(f)
        assert data["status"] == "SIMULATED"
        assert data["scenes"]["商业转型"]["sample_count"] == 267


class TestCompileDomain:
    def test_单域编译_产出增强COP(self):
        rep = BP.compile_domain("stratagems", emit_nca_flag=False)
        assert rep["ok"] == 36 and rep["fail"] == 0
        # 产出物含语义层字段
        sample = os.path.join(BATCH_OUT, "stratagems", "第01计-瞒天过海.yaml")
        assert os.path.isfile(sample)
        with open(sample, "r", encoding="utf-8") as f:
            cop = yaml.safe_load(f)
        assert "semantic" in cop and cop["semantic"]["u0"] > 0

    def test_单域时延_达标(self):
        rep = BP.compile_domain("games", emit_nca_flag=False)
        assert rep["avg_ms"] < 100
        assert rep["p95_ms"] < 200

    def test_源库未被改写(self):
        # REUSE-001 纪律：cop-library 只读，批产不改写源文件
        src = os.path.join(BP.LIB, "stratagems", "第36计-走为上.yaml")
        with open(src, "r", encoding="utf-8") as f:
            before = f.read()
        BP.compile_domain("stratagems", emit_nca_flag=False)
        with open(src, "r", encoding="utf-8") as f:
            after = f.read()
        assert before == after


class TestCompileAll:
    def test_全域编译(self):
        rep = BP.compile_all(emit_nca_flag=False)
        assert rep["total"] >= 260
        assert rep["fail"] == 0
        assert set(rep["domains"].keys()) == set(BP.DOMAINS.keys())

    def test_72文件复现(self):
        # 先产出 36 计域，再验证 72 文件口径
        BP.compile_domain("stratagems", emit_nca_flag=False)
        v = BP.verify_72_files()
        assert v["cop_count"] == 36
        assert v["total_files"] == 72
        assert v["reproduced"] is True


class TestAcceptance:
    def test_验收阈值_全达标(self):
        acc = BP.acceptance()
        assert acc["correct_rate"] > 95
        assert acc["threshold_correct"] is True
        assert acc["threshold_p95"] is True
        assert acc["threshold_avg"] is True
        assert acc["coverage"] >= 90
        assert acc["threshold_coverage"] is True
        assert acc["72_files"]["reproduced"] is True


class TestNCAChain:
    def test_独立NCA存证链(self):
        rep = BP.compile_domain("mechanism_design", emit_nca_flag=True)
        assert rep["ok"] == 1
        nca_dir = os.path.join(BATCH_OUT, "nca")
        ncas = [f for f in os.listdir(nca_dir) if f.endswith(".yaml")]
        assert len(ncas) >= 1
        # NCA 含语义层信息
        with open(os.path.join(nca_dir, "mechanism_design-001.yaml"), "r", encoding="utf-8") as f:
            nca = yaml.safe_load(f)
        assert nca["NCA-ID"].startswith("NCA-COPCOMPILER-")
        assert "U0" in nca["Notes"]


class TestReport:
    def test_批产报告落盘(self):
        rep, acc = BP.run_batch()
        report_path = os.path.join(BATCH_OUT, "BATCH-REPORT.json")
        assert os.path.isfile(report_path)
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "batch" in data and "acceptance" in data
        assert data["acceptance"]["correct_rate"] > 95
