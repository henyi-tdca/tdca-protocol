# -*- coding: utf-8 -*-
"""NCA 生成器 - Nested Cognitive Asset Generator
来源: TDCA-MEMO-006 步骤四
职责: 每次 FileMove/FileEdit/CodeGen/DirCreate 操作后生成不可篡改的微型 NCA
存储: .tdca-nca/TDCA-REASONIX-{YYYYMMDD}-{SEQUENCE}.yaml
实现 "操作即确权"。

## 编号纪律（GSEQ-0544 补丁 · 选项 B+C 固化）
编号仅由 generate_nca 统一生成，禁止手动预分配编号。人工获取 NCA 必须通过
调用 generate_nca（API）触发，不得手工指定编号。落盘前扫描 .tdca-nca 目录，
目标编号若被占用则自动顺延；GSEQ-0551 口径：追加至 max+1 保留缺口（编号=
事实存证时间序，缺口=历史事故/并发痕迹，不可回填，O_EXCL 原子预约，并发安全）。
"""
import os
import re
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

# 编号纪律常量：编号仅由 generate_nca 统一生成，禁止手动预分配
NCA_NUMBERING_DISCIPLINE = (
    "编号仅由 generate_nca 统一生成；禁止手动预分配编号。"
    "人工获取 NCA 应通过调用 generate_nca（API）触发，不得手工指定编号。"
)
_GENERATED_BY = "nca_generator.generate_nca"
_NCA_FILE_RE = re.compile(r"^TDCA-REASONIX-(\d{8})-(\d+)\.yaml$")


def _today():
    return datetime.datetime.now().strftime("%Y%m%d")


def _nca_id(today, seq):
    """NCA-ID: TDCA-REASONIX-{YYYYMMDD}-{SEQUENCE}（至少 3 位，超界自然扩展）"""
    return f"TDCA-REASONIX-{today}-{seq:03d}"


def _existing_seqs(today):
    """扫描目录，返回当天已存在的编号集合（用于定位首个空闲位）"""
    existing = set()
    if not os.path.isdir(NCA_DIR):
        return existing
    prefix = f"TDCA-REASONIX-{today}-"
    for name in os.listdir(NCA_DIR):
        if not name.startswith(prefix) or not name.endswith(".yaml"):
            continue
        m = _NCA_FILE_RE.match(name)
        if m and m.group(1) == today:
            existing.add(int(m.group(2)))
    return existing


def _reserve_free_nca_slot(today):
    """扫描目录，原子预约下一编号（选项 B：占用顺延；GSEQ-0551 口径：max+1 保留缺口）

    扫描当天已存在的编号，取 max(existing)+1 作为候选（缺口保留，不回填——
    编号=事实存证时间序，缺口=历史事故/并发痕迹，属审计线索）。再用
    os.open(O_CREAT|O_EXCL) 原子创建占位文件。若并发下该位被其他进程抢先占用
    （FileExistsError），则顺延到下一个编号。返回 (today, seq, nca_path)。
    """
    existing = _existing_seqs(today)
    candidate = (max(existing) if existing else 0) + 1
    while True:
        nca_id = _nca_id(today, candidate)
        path = os.path.join(NCA_DIR, f"{nca_id}.yaml")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            # 并发下该位被抢：顺延下一空闲位（同时记入 existing 避免重复扫描）
            existing.add(candidate)
            candidate += 1
            while candidate in existing:
                candidate += 1
            continue
        os.close(fd)  # 已原子预约占位，随后由 _dump_yaml 覆盖写入真实内容
        # 兼容遗留计数器文件（仅作提示，编号权威来自目录扫描）
        try:
            with open(os.path.join(NCA_DIR, f".seq-{today}"), "w", encoding="utf-8") as f:
                f.write(str(candidate))
        except OSError:
            pass
        return today, candidate, path


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
    explicit_seq=None,
):
    """生成一条微型 NCA 并落盘（编号自动、占用顺延、并发安全）

    参数:
      operation_type: FileMove / FileEdit / CodeGen / DirCreate ...
      scope: 操作范围
      pre_state: nsfl_runtime.pre_state() 返回的 dict
      post_state: nsfl_runtime.verify_post_state() 返回的 dict 或 None
      function_call_id: 关联的函数语料 ID
      explicit_seq: 【纪律禁止】手工指定编号。任何非 None 值都会触发
          ValueError（选项 C：禁止手动预分配编号）。
    返回: (nca_id, nca_path, nca_dict)
    """
    if explicit_seq is not None:
        # 选项 C：编号仅由 generate_nca 统一生成，人工仅 API 触发
        raise ValueError(
            "禁止手动预分配编号：编号仅由 generate_nca 统一生成；"
            "人工获取 NCA 应通过调用 generate_nca（API）触发，不得手工指定编号"
            f"（收到 explicit_seq={explicit_seq!r}）。"
        )
    os.makedirs(NCA_DIR, exist_ok=True)
    today, seq, nca_path = _reserve_free_nca_slot(today=_today())
    nca_id = _nca_id(today, seq)
    ts = datetime.datetime.now().isoformat()
    nca = {
        "NCA-ID": nca_id,
        "Generated-By": _GENERATED_BY,
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
    try:
        _dump_yaml(nca, nca_path)
    except Exception:
        # 写入失败则尽力释放已预约的空占位文件，避免留下孤儿
        try:
            if os.path.getsize(nca_path) == 0:
                os.unlink(nca_path)
        except OSError:
            pass
        raise
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


def list_ncas(nca_dir=None):
    """列出当前 NCA 目录下的 NCA 文件"""
    d = nca_dir or NCA_DIR
    os.makedirs(d, exist_ok=True)
    out = []
    for name in sorted(os.listdir(d)):
        if name.endswith(".yaml") and name.startswith("TDCA-REASONIX-"):
            out.append(os.path.join(d, name))
    return out


def verify_numbering_discipline(nca_dir=None, require_marker=True):
    """编号纪律校验（选项 C 的验证/CI 入口）

    扫描 nca_dir（默认 NCA_DIR）下所有 TDCA-REASONIX-*.yaml：
      - 文件名可被解析为 (date, seq) 格式（否则 malformed 违规）
      - 文件内 NCA-ID 与文件名一致（否则 tamper/collision 违规）
      - 全局无重复 (date, seq)（否则 collision 违规）
      - require_marker=True 时：缺少 Generated-By=nca_generator.generate_nca
        的文件标记为「疑似手动预分配」（legacy 文件祖父条款：本函数仅报告，不删除）
    返回: {"ok": bool, "scanned": int, "violations": [str, ...]}
    """
    d = nca_dir or NCA_DIR
    violations = []
    seen = {}
    if not os.path.isdir(d):
        return {"ok": True, "scanned": 0, "violations": []}
    for name in sorted(os.listdir(d)):
        if not (name.startswith("TDCA-REASONIX-") and name.endswith(".yaml")):
            continue
        m = _NCA_FILE_RE.match(name)
        if not m:
            violations.append(f"malformed filename: {name}")
            continue
        date_s, seq_s = m.group(1), m.group(2)
        key = (date_s, seq_s)
        if key in seen:
            violations.append(f"duplicate (date,seq): {name} 与 {seen[key]}")
        else:
            seen[key] = name
        path = os.path.join(d, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            violations.append(f"unreadable: {name}")
            continue
        inner_id = _grep_field(text, "NCA-ID")
        if inner_id and inner_id != f"TDCA-REASONIX-{date_s}-{seq_s}":
            violations.append(f"id mismatch: 文件内 NCA-ID={inner_id} != 文件名 {name}")
        if require_marker and _grep_field(text, "Generated-By") != _GENERATED_BY:
            violations.append(f"疑似手动预分配（缺 Generated-By 标记）: {name}")
    return {"ok": len(violations) == 0, "scanned": len(seen), "violations": violations}


def _grep_field(text, field):
    """极简字段提取（避免强依赖 yaml；仅取顶层 key 的值）"""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(f"{field}:"):
            return s.split(":", 1)[1].strip()
    return None


if __name__ == "__main__":
    os.makedirs(NCA_DIR, exist_ok=True)
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
