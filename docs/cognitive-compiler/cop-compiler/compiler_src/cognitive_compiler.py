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

"""思维协议编译器 - Cognitive Protocol Compiler (T1 骨架)
来源: TDCA-DEV-TASK-COGCOMPILER-001 任务书 T1
职责: 把领域专家 SOUL (agent md) 编译为可执行思维协议 COP
五阶段流水线:
  S1 知识获取  - 读专家 agent md
  S2 结构化    - 方法论原子化为思维单元块
  S3 函数化    - 编译为思维原语 CP (函数签名)
  S4 协议生成  - 组装 COP (soul + primitives + dispatch + decision + negative_space)
  S5 验证      - 自检 (CP 数≥1, 签名完整)
输出: COP (YAML), 供 Executor 调度 skill
"""
import os
import re
import sys
import datetime

try:
    import yaml
except ImportError:
    yaml = None

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "config"))
import tdca_config as TC

ensure_dirs = TC.ensure_dirs
NSFL_VERSION = TC.NSFL_VERSION


# ---------- S1 知识获取 ----------
def s1_acquire(expert_md_path):
    """读取专家 agent md 全文"""
    with open(expert_md_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_frontmatter(text):
    """提取 agent md frontmatter (name/description/displayName/profession)"""
    m = re.search(r"^---\n(.*?)\n---", text, re.S | re.M)
    fm = {}
    if not m:
        return fm
    cur = None
    for line in m.group(1).split("\n"):
        if line.startswith(" ") and cur:
            fm[cur] += "\n" + line.strip()
        elif ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
            cur = k.strip()
    return fm


# ---------- S2 + S3 结构化 & 函数化 ----------
def s2s3_tokenize_and_functionize(text):
    """方法论原子化 + 编译为思维原语 CP
    按数字编号 **方法论名** 分块, 每块提取所有 fn 签名 + 前置/后置/⊗
    """
    primitives = []
    # 按 "\n数字. **" 分割方法论块
    blocks = re.split(r"\n\d+\.\s+\*\*", text)
    for block in blocks[1:]:
        name_m = re.match(r"(.+?)\*\*", block)
        method_name = name_m.group(1).strip() if name_m else ""
        # 提取所有函数签名: `fn name(params) -> ret`
        fns = re.findall(r"`fn\s+(\w+)\(([^)]*)\)\s*->\s*(.+?)`", block)
        # 提取前置/后置/⊗ 约束
        precond = postcond = neg = ""
        for raw in block.split("\n"):
            line = raw.strip().lstrip("- ").strip()
            if line.startswith("前置"):
                precond = line.split("：", 1)[-1].strip() if "：" in line else ""
            elif line.startswith("后置"):
                postcond = line.split("：", 1)[-1].strip() if "：" in line else ""
            elif "⊗" in line:
                neg = line.replace("⊗", "").lstrip("约束：").strip("： ").strip()
        for fn_name, params, returns in fns:
            primitives.append({
                "name": fn_name,
                "method": method_name,
                "signature": f"fn {fn_name}({params}) -> {returns}",
                "precond": precond,
                "postcond": postcond,
                "negative_space": neg,
                "nca_emit": True,
            })
    return primitives


# ---------- S4 协议生成 ----------
def s4_assemble_cop(fm, primitives):
    """组装思维协议 COP"""
    cop = {
        "COP-ID": f"MCKINSEY-COP-{datetime.datetime.now().strftime('%Y%m%d')}-001",
        "source_expert": fm.get("name", "unknown"),
        "compiled_at": datetime.datetime.now().isoformat(),
        "soul": {
            "identity": "麦肯锡管理咨询顾问",
            "core": "假设驱动、MECE分解、金字塔表达",
            "role": "思维协议编译器知识编译主体",
            "display_name": fm.get("displayName", ""),
            "profession": fm.get("profession", ""),
        },
        "primitives": primitives,
        "dispatch": {
            "main_pipeline": "seven_step_solve",
            "graph": [
                {"from": "seven_step_solve", "to": [p["name"] for p in primitives if p["name"] != "seven_step_solve"]},
            ],
            "note": "七步法为主线, 调度其余原语",
        },
        "decision": [
            {"if": "问题需分解", "call": "mece_decompose"},
            {"if": "需验证假设", "call": "hypothesis_test"},
            {"if": "需结构化表达", "call": "pyramid_build"},
            {"if": "组织诊断", "call": "seven_s_audit"},
            {"if": "叙事定调", "call": "scp_frame"},
        ],
        "skills": [],
        "negative_space": [
            "禁止确认偏误: 假设验证须主动找反证",
            "禁止过度分解: MECE 深度≤3 层",
            "禁止无据结论: 每论点须有证据",
        ],
        "nsfl_version": NSFL_VERSION,
    }
    return cop


# ---------- S5 验证 ----------
def s5_validate(cop):
    issues = []
    if not cop.get("primitives"):
        issues.append("无思维原语")
    for cp in cop["primitives"]:
        if not cp.get("signature") or "fn " not in cp["signature"]:
            issues.append(f"原语 {cp.get('name')} 缺函数签名")
    cop["validation"] = {"passed": len(issues) == 0, "issues": issues, "primitive_count": len(cop.get("primitives", []))}
    return issues


# ---------- 主流程 ----------
def compile(expert_md_path, output_dir=None):
    """五阶段流水线主控"""
    ensure_dirs()
    # S1
    text = s1_acquire(expert_md_path)
    fm = parse_frontmatter(text)
    # S2+S3
    primitives = s2s3_tokenize_and_functionize(text)
    # S4
    cop = s4_assemble_cop(fm, primitives)
    # S5
    s5_validate(cop)
    # 输出
    if output_dir is None:
        output_dir = _THIS
    out_path = os.path.join(output_dir, "麦肯锡思维协议.yaml")
    _dump_yaml(cop, out_path)
    return cop, out_path


def _dump_yaml(obj, path):
    if yaml is not None:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(obj))


if __name__ == "__main__":
    expert_md = os.path.expanduser(
        r"~/.workbuddy/plugins/marketplaces/my-experts/plugins/mckinsey-management-consultant/agents/mckinsey-management-consultant.md"
    )
    cop, out = compile(expert_md)
    print("编译完成:", out)
    print("COP-ID:", cop["COP-ID"])
    print("思维原语数:", len(cop["primitives"]))
    print("原语:", [p["name"] for p in cop["primitives"]])
    print("验证:", cop["validation"])
