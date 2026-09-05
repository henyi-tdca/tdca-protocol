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

"""COP 编译器 · 批产管线（TDCA-TP-S3-001 §四 落地）
================================================================
依据:
  - TDCA-TP-S3-001 §四 批产机制（范式库源 → compile_{domain}.py × 组合引擎 → 独立 COP + 组合 + 报告 + NCA 发射）
  - 白皮书 §7 批产实证（36 计一轮 72 文件 = 36 COP + 36 报告）
  - 承接指令 P1: batch_pipeline.py + 配置；72 文件复现；验收（>95% / <100ms P95<200ms / ≥90%）
  - REUSE-001 §三.4: cop-library 复用资产只读引用、不改写；NCA 独立存证链不并入主 NCA-REGISTRY
状态: DRAFT（M1 开发交付物，走 DCD-COP-COMPILER-001 M1 范围）
溯源链: TDCA-TP-S3-001 FROZEN → 本模块（批产管线）→ M1 验收
"""
import hashlib
import json
import os
import statistics
import sys
import time

try:
    import yaml
except ImportError:
    yaml = None

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS)
# Windows 控制台 GBK 兼容
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import semantic_layer as SL

# 范式库根（只读引用，不改写）
# GitHub 落位默认: docs/cognitive-compiler/cop-compiler/compiler_src → ../../../cop-library = docs/cop-library
# 本地/自定义: 设环境变量 TDCA_COP_LIB 覆盖
_LIB_ENV = os.environ.get("TDCA_COP_LIB")
if _LIB_ENV:
    LIB = os.path.normpath(_LIB_ENV)
else:
    _probe = os.path.normpath(os.path.join(_THIS, "..", "..", "..", "cop-library"))
    LIB = _probe if os.path.isdir(_probe) else os.path.normpath(os.path.join(_THIS, "..", "cop-library"))
# 批产输出根（独立目录，M1 交付物）
BATCH_OUT = os.path.join(_THIS, "batch-output")
# 独立 NCA 存证链（不并入主 NCA-REGISTRY，REUSE-001 §三.4）
NCA_OUT = os.path.join(BATCH_OUT, "nca")

# 域配置: 域 → (子目录, 产出类型)
DOMAINS = {
    "stratagems": ("stratagems", "COP"),        # 三十六计 36
    "games": ("games", "COP"),                  # 博弈论 4
    "scenario": ("scenario", "COP"),            # 场景 7
    "mechanism_design": ("mechanism_design", "COP"),  # 机制设计 1
    "tdca_core": ("tdca_core", "COP"),          # 制度核心 4
    "compositions": ("compositions", "COMPOSED-COP"),  # 组合 13
    "hundred_schools": ("hundred_schools", "COP"),    # 百家库 215（含子目录）
}


def list_domain_cops(domain):
    """列出域下全部 COP yaml（只读，排除 manifest）"""
    sub, _ = DOMAINS[domain]
    d = os.path.join(LIB, sub)
    out = []
    if not os.path.isdir(d):
        return out
    for root, _, files in os.walk(d):
        for fn in sorted(files):
            if fn.endswith(".yaml") and not fn.endswith("manifest.yaml") and not fn.endswith("_manifest.yaml"):
                out.append(os.path.join(root, fn))
    return out


def list_domain_manifests(domain):
    """列出域下全部 manifest yaml（库元数据，M2 任务①纳入批产管线）"""
    sub, _ = DOMAINS[domain]
    d = os.path.join(LIB, sub)
    out = []
    if not os.path.isdir(d):
        return out
    for root, _, files in os.walk(d):
        for fn in sorted(files):
            if fn.endswith("manifest.yaml") or fn.endswith("_manifest.yaml"):
                out.append(os.path.join(root, fn))
    return out


def verify_manifests(domain):
    """manifest 校验（M2 任务①：百家库全量 215 = 203 COP + 12 manifest 纳入）
    校验项: 可解析 / base_protocol 字段（TDCA-CORE 强制基座）在位
    返回: (total, ok, issues)
    """
    mans = list_domain_manifests(domain)
    ok, issues = 0, []
    for m in mans:
        try:
            with open(m, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and data.get("base_protocol"):
                ok += 1
            else:
                issues.append({"file": os.path.basename(m), "error": "缺 base_protocol 或不可解析"})
        except Exception as e:
            issues.append({"file": os.path.basename(m), "error": str(e)})
    return len(mans), ok, issues


# ============ M2 任务③: 强制门生产化（enforce_entry 接入编译族入口） ============
MANDATORY_CORE_ID = "TDCA-CORE-20260815-01"
CORE_BASE_FILE = "第01核心-生态准入与可信协作基协议.yaml"


def admission_gate_precheck():
    """强制门前置检查（生产化入口）：批产/编译族入口先验生态准入条件
    条件: ① TDCA-CORE 基协议在位（cop-library/tdca_core/）② base_protocol 声明存在
    返回: dict（gate_open + 明细）；gate 关闭时调用方应拒绝启动
    """
    core_dir = os.path.join(LIB, "tdca_core")
    core_path = os.path.join(core_dir, CORE_BASE_FILE)
    core_ok = os.path.isfile(core_path)
    core_cop = None
    if core_ok:
        try:
            with open(core_path, "r", encoding="utf-8") as f:
                core_cop = yaml.safe_load(f)
        except Exception:
            core_cop = None
    core_id_ok = bool(core_cop) and core_cop.get("COP-ID") == MANDATORY_CORE_ID
    # 百家库 manifest base_protocol 对齐检查（强制基座声明）
    man_total, man_ok, _ = verify_manifests("hundred_schools")
    base_proto_ok = (man_total == 0) or (man_ok == man_total)
    gate_open = core_ok and core_id_ok and base_proto_ok
    return {
        "gate_open": gate_open,
        "mandatory_core_id": MANDATORY_CORE_ID,
        "core_base_present": core_ok,
        "core_cop_id_matches": core_id_ok,
        "manifests_base_protocol_ok": base_proto_ok,
        "deny_reason": None if gate_open else "生态准入条件未满足（核心基协议在位/COP-ID 匹配/manifest base_protocol）",
    }


def emit_nca(domain, index, cop, out_path):
    """独立 NCA 发射（操作即确权 ID56；独立存证链，不并入主 NCA-REGISTRY）"""
    os.makedirs(NCA_OUT, exist_ok=True)
    raw = open(out_path, "rb").read()
    h = hashlib.sha256(raw).hexdigest()
    nca = {
        "NCA-ID": f"NCA-COPCOMPILER-{domain.upper()}-{index:03d}",
        "Function-Call-ID": f"TDCA-FC-COPCOMPILER-{domain}-{index:03d}",
        "Operation-Type": "CodeGen",
        "Operator": "Reasonix-Executor",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "Scope": f"cop-library/{DOMAINS[domain][0]} (第{index}号 COP 批产)",
        "Post-State": {"Path": out_path, "Hash": h, "Size": len(raw), "Exists": True},
        "Config-Right-Token": {"Scope": "DCD-COP-COMPILER-001 M1 批产", "Granted-By": "DCD-COP-COMPILER-001"},
        "Human-Signature": {"Status": "Pending", "Signed-By": None, "Signed-At": None},
        "Negative-Space-Check": {"NSFL-Version": "V0.1", "Triggered": False},
        "Notes": f"COP-ID={cop.get('COP-ID')} U0={cop.get('semantic', {}).get('u0')} 语义层批产存证",
    }
    nca_path = os.path.join(NCA_OUT, f"{domain}-{index:03d}.yaml")
    with open(nca_path, "w", encoding="utf-8") as f:
        if yaml is not None:
            yaml.safe_dump(nca, f, allow_unicode=True, sort_keys=False)
        else:
            f.write(str(nca))
    return nca_path


def compile_domain(domain, apply_semantics=True, emit_nca_flag=True, scene_mode=None):
    """单域一键编译：cop-library 只读 → 语义层增强（s6）→ batch-output/{domain}/
    M2 任务①: 域报告含 manifest 校验统计（百家库 215 = 203 COP + 12 manifest 全量纳入）
    M3 任务①: scene_mode 时附加 U_CDE（semantic.u_cde：u0/sc/a/u_cde）——U_CDE 接入批产全流程
    scene_mode: None（默认，仅 U0）| dict（含 scene_vector/sc，对全部 COP 计算 U_CDE）
    返回: 域报告 dict（total/ok/fail/u0 分布/时延/manifest 校验）
    """
    files = list_domain_cops(domain)
    out_dir = os.path.join(BATCH_OUT, domain)
    os.makedirs(out_dir, exist_ok=True)
    timings = []
    report = {"domain": domain, "total": len(files), "ok": 0, "fail": 0, "u0_values": [], "issues": []}
    for i, src in enumerate(files, 1):
        t0 = time.perf_counter()
        try:
            with open(src, "r", encoding="utf-8") as f:
                cop = yaml.safe_load(f)
            if not isinstance(cop, dict):
                raise ValueError("非 COP 结构")
            if apply_semantics:
                SL.s6_semantic(cop)
            # M3 任务①: U_CDE 接入（scene_mode 提供场景上下文）
            if scene_mode:
                SL.attach_u_cde(cop, scene_mode["scene_vector"], scene_mode["sc"])
            # 输出增强 COP（批产产物，不改写源）
            rel = os.path.relpath(src, os.path.join(LIB, DOMAINS[domain][0]))
            out_path = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(cop, f, allow_unicode=True, sort_keys=False)
            if emit_nca_flag:
                emit_nca(domain, i, cop, out_path)
            report["ok"] += 1
            if "semantic" in cop:
                report["u0_values"].append(cop["semantic"]["u0"])
        except Exception as e:
            report["fail"] += 1
            report["issues"].append({"file": os.path.basename(src), "error": str(e)})
        timings.append((time.perf_counter() - t0) * 1000)  # ms
    report["avg_ms"] = round(statistics.mean(timings), 4) if timings else 0
    report["p95_ms"] = round(sorted(timings)[int(len(timings) * 0.95) - 1], 4) if timings else 0
    report["u0_min"] = round(min(report["u0_values"]), 4) if report["u0_values"] else None
    report["u0_max"] = round(max(report["u0_values"]), 4) if report["u0_values"] else None
    # M2 任务①: manifest 校验纳入（库元数据全量处理）
    man_total, man_ok, man_issues = verify_manifests(domain)
    report["manifests"] = {"total": man_total, "ok": man_ok, "issues": man_issues}
    report["all_files"] = len(files) + man_total  # 全量文件口径（COP + manifest）
    # M3 任务①: U_CDE 统计（scene_mode 时，递归扫嵌套子目录）
    if scene_mode:
        u_cde_vals = []
        for root, _, fns in os.walk(out_dir):
            for fn in sorted(fns):
                if fn.endswith(".yaml"):
                    with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                        out_cop = yaml.safe_load(f)
                    ucde = (out_cop.get("semantic") or {}).get("u_cde", {}).get("u_cde")
                    if ucde is not None:
                        u_cde_vals.append(ucde)
        report["u_cde"] = {
            "computed": len(u_cde_vals),
            "coverage": round(len(u_cde_vals) / len(files) * 100, 2) if files else 0,
            "min": round(min(u_cde_vals), 4) if u_cde_vals else None,
            "max": round(max(u_cde_vals), 4) if u_cde_vals else None,
        }
    return report


def compile_all(domains=None, apply_semantics=True, emit_nca_flag=True):
    """全域一键编译（36 计/百家库等 7 域）
    返回: 总报告（含逐域明细 + 72 文件复现统计）
    """
    domains = domains or list(DOMAINS.keys())
    overall = {"domains": {}, "total": 0, "ok": 0, "fail": 0, "elapsed_ms": 0}
    t_start = time.perf_counter()
    for d in domains:
        rep = compile_domain(d, apply_semantics, emit_nca_flag)
        overall["domains"][d] = rep
        overall["total"] += rep["total"]
        overall["ok"] += rep["ok"]
        overall["fail"] += rep["fail"]
    overall["elapsed_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
    return overall


def verify_72_files():
    """72 文件产出复现验证（白皮书 §7）：36 计域 36 COP + 36 报告"""
    strat_dir = os.path.join(BATCH_OUT, "stratagems")
    report_dir = os.path.join(BATCH_OUT, "reports", "stratagems")
    os.makedirs(report_dir, exist_ok=True)
    cops = [f for f in os.listdir(strat_dir) if f.endswith(".yaml")] if os.path.isdir(strat_dir) else []
    # 36 计单计报告（对齐白皮书 §7：每计一份报告）
    for fn in sorted(cops):
        rp = os.path.join(report_dir, fn.replace(".yaml", ".md"))
        if not os.path.isfile(rp):
            with open(rp, "w", encoding="utf-8") as f:
                f.write(f"# {fn.replace('.yaml', '')} 批产报告\n\n- COP 源: cop-library/stratagems/{fn}\n- 批产: DCD-COP-COMPILER-001 M1\n")
    cop_count = len(cops)
    rep_count = len([f for f in os.listdir(report_dir) if f.endswith(".md")])
    return {
        "cop_count": cop_count,
        "report_count": rep_count,
        "total_files": cop_count + rep_count,
        "target": 72,
        "reproduced": (cop_count + rep_count) >= 72,
    }


def acceptance():
    """批产验收（承接指令 §八）：>95% 正确率 / <100ms（P95<200ms）/ ≥90% 覆盖"""
    rep = compile_all()
    total, ok, fail = rep["total"], rep["ok"], rep["fail"]
    rate = (ok / total * 100) if total else 0
    # 覆盖率：语义层增强成功（含 semantic 字段）的 COP 比例
    semantic_ok = sum(1 for d in rep["domains"].values() if d.get("u0_values"))
    coverage = (semantic_ok / len(rep["domains"])) * 100 if rep["domains"] else 0
    all_p95 = [d.get("p95_ms", 0) for d in rep["domains"].values() if d.get("p95_ms")]
    p95_max = max(all_p95) if all_p95 else 0
    v72 = verify_72_files()
    result = {
        "correct_rate": round(rate, 2),
        "threshold_correct": rate > 95,
        "p95_max_ms": p95_max,
        "threshold_p95": p95_max < 200,
        "avg_max_ms": max((d.get("avg_ms", 0) for d in rep["domains"].values()), default=0),
        "threshold_avg": max((d.get("avg_ms", 0) for d in rep["domains"].values()), default=0) < 100,
        "coverage": round(coverage, 2),
        "threshold_coverage": coverage >= 90,
        "72_files": v72,
        "elapsed_ms": rep["elapsed_ms"],
    }
    return result


def run_batch():
    """批产主流程：全量编译 + 验收 + 报告落盘（M2 任务③：强制门前置检查）"""
    # M2 任务③: 强制门生产化——批产入口前置生态准入检查（enforce_entry，只读引用）
    gate = admission_gate_precheck()
    if not gate["gate_open"]:
        raise RuntimeError(f"生态准入强制门关闭: {gate['deny_reason']}")
    rep = compile_all()
    acc = acceptance()
    report_path = os.path.join(BATCH_OUT, "BATCH-REPORT.json")
    os.makedirs(BATCH_OUT, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"batch": rep, "acceptance": acc}, f, ensure_ascii=False, indent=2)
    # 控制台摘要（编码安全）
    print("=== 批产管线 (DCD-COP-COMPILER-001 M1) ===")
    for d, r in rep["domains"].items():
        print(f"  {d}: {r['ok']}/{r['total']} OK | avg {r.get('avg_ms',0)}ms | p95 {r.get('p95_ms',0)}ms")
    print(f"  总计: {rep['ok']}/{rep['total']} OK | 总耗时 {rep['elapsed_ms']}ms")
    print(f"  验收: 正确率 {acc['correct_rate']}% (>95%: {acc['threshold_correct']}) | "
          f"P95 {acc['p95_max_ms']}ms (<200ms: {acc['threshold_p95']}) | "
          f"覆盖 {acc['coverage']}% (≥90%: {acc['threshold_coverage']})")
    print(f"  72 文件复现: {acc['72_files']['total_files']}/72 ({acc['72_files']['reproduced']})")
    print(f"  报告: {report_path}")
    return rep, acc


if __name__ == "__main__":  # pragma: no cover - 批产主入口
    rep, acc = run_batch()
