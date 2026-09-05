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

"""NCA 生成器 - Nested Cognitive Asset Generator
来源: TDCA-MEMO-006 步骤四
职责: 每次 FileMove/FileEdit/CodeGen/DirCreate 操作后生成不可篡改的微型 NCA
存储: .tdca-nca/TDCA-REASONIX-{YYYYMMDD}-{SEQUENCE}.yaml
实现 "操作即确权"。
"""
import os
import sys
import json
import datetime

try:
    import yaml
except ImportError:
    yaml = None

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "config"))
import tdca_config as TC

ensure_dirs = TC.ensure_dirs
NCA_DIR = TC.NCA_DIR
OPERATOR = TC.OPERATOR
NSFL_VERSION = TC.NSFL_VERSION


def _seq_file():
    """读取/维护当天序号计数"""
    today = datetime.datetime.now().strftime("%Y%m%d")
    seq_path = os.path.join(NCA_DIR, f".seq-{today}")
    seq = 0
    if os.path.isfile(seq_path):
        try:
            with open(seq_path, "r", encoding="utf-8") as f:
                seq = int(f.read().strip() or "0")
        except (ValueError, OSError):
            seq = 0
    seq += 1
    with open(seq_path, "w", encoding="utf-8") as f:
        f.write(str(seq))
    return today, seq


def _nca_id(today, seq):
    """NCA-ID: TDCA-REASONIX-{YYYYMMDD}-{SEQUENCE(3位)}"""
    return f"TDCA-REASONIX-{today}-{seq:03d}"


def _dump_yaml(obj, path):
    """安全写 YAML（使用 Python，符合编码安全规则）"""
    if yaml is not None:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False)
    else:
        # 降级: 手写 YAML
        with open(path, "w", encoding="utf-8") as f:
            f.write(_to_yaml(obj, 0))


def _to_yaml(obj, indent):
    """简易 YAML 序列化（无 pyyaml 时降级）"""
    pad = "  " * indent
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                out.append(f"{pad}{k}:")
                out.append(_to_yaml(v, indent + 1))
            elif v is None:
                out.append(f"{pad}{k}: null")
            elif isinstance(v, bool):
                out.append(f"{pad}{k}: {'true' if v else 'false'}")
            else:
                out.append(f"{pad}{k}: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                out.append(f"{pad}-")
                out.append(_to_yaml(item, indent + 1))
            else:
                out.append(f"{pad}- {item}")
    return "\n".join(out)


def generate_nca(
    operation_type,
    scope,
    pre_state,
    post_state,
    function_call_id,
    config_right_token=None,
    audit_steps=None,
    human_signature_status="Pending",
    nsfl_triggered=False,
    nsfl_trigger_reason=None,
    notes=None,
):
    """生成一条微型 NCA 并落盘
    参数:
      operation_type: FileMove / FileEdit / CodeGen / DirCreate ...
      scope: 操作范围
      pre_state: nsfl_runtime.pre_state() 返回的 dict
      post_state: nsfl_runtime.verify_post_state() 返回的 dict 或 None
      function_call_id: 关联的函数语料 ID
    返回: (nca_id, nca_path, nca_dict)
    """
    ensure_dirs()
    today, seq = _seq_file()
    nca_id = _nca_id(today, seq)
    ts = datetime.datetime.now().isoformat()
    nca = {
        "NCA-ID": nca_id,
        "Function-Call-ID": function_call_id,
        "Operation-Type": operation_type,
        "Operator": OPERATOR,
        "Timestamp": ts,
        "Scope": scope,
        "Pre-State": _state_dict(pre_state),
        "Post-State": _state_dict(post_state) if post_state else None,
        "Config-Right-Token": config_right_token or {
            "Scope": scope,
            "Granted-By": "TDCA-Executor-Self-Declare",
            "Expires": None,
        },
        "Audit-Trail": [
            {
                "Step": s.get("Step", "") if isinstance(s, dict) else str(s),
                "Time": s.get("Time", "") if isinstance(s, dict) else ts,
                "Evidence": s.get("Evidence", "") if isinstance(s, dict) else "",
            }
            for s in (audit_steps or [{"Step": operation_type, "Time": ts, "Evidence": pre_state.get("hash") if pre_state else None}])
        ],
        "Human-Signature": {
            "Status": human_signature_status,
            "Signed-By": None,
            "Signed-At": None,
        },
        "Negative-Space-Check": {
            "NSFL-Version": NSFL_VERSION,
            "Triggered": nsfl_triggered,
            "Trigger-Reason": nsfl_trigger_reason,
        },
    }
    if notes:
        nca["Notes"] = notes
    nca_path = os.path.join(NCA_DIR, f"{nca_id}.yaml")
    _dump_yaml(nca, nca_path)
    return nca_id, nca_path, nca


def _state_dict(state):
    """规范 Pre/Post State 字段"""
    if state is None:
        return None
    if isinstance(state, dict):
        return {
            "Path": state.get("path"),
            "Hash": state.get("hash"),
            "Size": state.get("size"),
            "Exists": state.get("exists"),
            "Backup": state.get("backup"),
        }
    return state


def list_ncas():
    """列出当前 NCA 目录下的 NCA 文件"""
    ensure_dirs()
    out = []
    for name in sorted(os.listdir(NCA_DIR)):
        if name.endswith(".yaml") and name.startswith("TDCA-REASONIX-"):
            out.append(os.path.join(NCA_DIR, name))
    return out


if __name__ == "__main__":
    ensure_dirs()
    # 演示: 生成一条 NCA
    nid, npath, ndict = generate_nca(
        operation_type="CodeGen",
        scope=".tdca-protocol (self-test)",
        pre_state={"path": "(virtual)", "hash": None, "size": 0, "exists": False, "backup": None},
        post_state=None,
        function_call_id="TDCA-FC-SELFTEST",
        notes="NCA 生成器自检样本",
    )
    print(f"NCA 生成: {nid}")
    print(f"路径: {npath}")
    print(f"当前 NCA 数量: {len(list_ncas())}")
