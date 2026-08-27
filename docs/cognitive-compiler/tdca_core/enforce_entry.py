# -*- coding: utf-8 -*-
"""TDCA 生态准入强制加载机制
用户规则: 凡是加入 TDCA 生态的主体, 必须加载 TDCA 思维协议 (基协议 TDCA-CORE-20260815-01)。

提供:
  MANDATORY_CORE_ID        -> 强制基协议 ID
  load_core_base()         -> 读取基协议 (断言存在)
  require_core_loaded()    -> 断言已加载基协议, 否则抛 AdmissionDenied (准入门)
  ecosystem_admit()        -> 准入一个主体, 成功则发射 NCA; 未加载基协议则拒绝
  check_loaded_in_set()    -> 供 composer/engine/connector 在协作入口处调用

生产接线: 任何生态入口(组合解析/搜索比配/连接器加载候选)应先调用
  require_core_loaded(agent_loaded_core_ids)  未加载则拒绝, 实现"加入即加载基协议"。
编码: 全中文 utf-8; open(encoding='utf-8'); 遵守 NSFL R2
"""
import os
import re
import sys
import datetime
import hashlib

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "config"))
sys.path.insert(0, os.path.join(_THIS, "..", "..", "nca-generator"))
sys.path.insert(0, _THIS)

import yaml
import tdca_config as TC
import nca_generator as NCA

MANDATORY_CORE_ID = "TDCA-CORE-20260815-01"
CORE_DIR = _THIS


class AdmissionDenied(Exception):
    """未加载 TDCA 思维协议基协议, 拒绝准入"""
    pass


def load_core_base():
    p = os.path.join(CORE_DIR, "第01核心-生态准入与可信协作基协议.yaml")
    if not os.path.isfile(p):
        raise FileNotFoundError("TDCA 基协议缺失: %s (请先运行 compile_tdca_core.py)" % p)
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def require_core_loaded(loaded_ids):
    """准入门: 任何主体加入生态必须已加载基协议, 否则拒绝"""
    if MANDATORY_CORE_ID not in (loaded_ids or []):
        raise AdmissionDenied(
            "准入拒绝: 主体未加载 TDCA 思维协议基协议 (%s)。"
            "凡是加入 TDCA 生态, 必须加载 TDCA 思维协议。" % MANDATORY_CORE_ID)
    return True


def check_loaded_in_set(loaded_ids):
    """供 composer/engine/connector 调用: 返回是否通过强制加载门"""
    return MANDATORY_CORE_ID in (loaded_ids or [])


def ecosystem_admit(entity, loaded_ids=None, note="生态准入核验"):
    """准入一个主体: 必须加载基协议, 否则拒绝; 准入成功发射 NCA"""
    loaded_ids = loaded_ids or []
    require_core_loaded(loaded_ids)  # 未加载 -> AdmissionDenied
    base = load_core_base()
    nid, npath, _ = NCA.generate_nca(
        operation_type="EcosystemAdmit",
        scope=".tdca-protocol/cognitive-compiler/tdca_core (生态准入 %s)" % entity,
        pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
        post_state={"path": None, "hash": None, "size": 0, "exists": True, "backup": None},
        function_call_id="TDCA-FC-ADMIT-%s" % entity,
        notes="%s 已加载 TDCA 思维协议基协议 %s, 准入生态; 规则: 加入即加载基协议" % (entity, MANDATORY_CORE_ID),
    )
    return {"entity": entity, "admitted": True, "core_base": MANDATORY_CORE_ID,
            "nca_id": nid, "nca_path": npath}


# ===================== v2 可转化准入态 (GSEQ-0528 签批) =====================
# 设计: 未加载基协议的主体不再被硬性拒绝, 而是进入 PENDING_LOAD 零权利态,
# 由组织者预置引导加载材料, 待其提供 loaded_core 机读证据后重跑准入。
# 三硬约束: ① 零权利态(不发射NCA/不落盘/无联盟资格/无配置权)
#           ② loaded_core 机读证据(response+sha256哈希+来源标注)
#           ③ NSFL 语义不变(零熔断豁免; 引导材料须过 NSFL)
# 另: VB 锚定升级 -> anchor_vb_to_cop 以"实跑出 1 COP"替代自报基值
PENDING_LOAD = "PENDING_LOAD"

# NSFL 负空间标记集合(与 COP ⊗ 标记 / nsfl_version 体系一致, 声明式)
NSFL_NEGATIVE_SPACE = ["data-integrity", "encoding-safety", "ethics-legal", "cognitive-safety"]


class CoreEvidenceInvalid(Exception):
    """loaded_core 机读证据无效(缺失/伪造/未标来源)"""
    pass


class NSFLTripped(Exception):
    """命中 NSFL 负空间, 熔断(零豁免)"""
    pass


def sha256_of(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_core_evidence(evidence):
    """loaded_core 机读证据校验: response+hash 匹配 + source 标注; 无效则抛 CoreEvidenceInvalid"""
    if not isinstance(evidence, dict):
        raise CoreEvidenceInvalid("机读证据缺失(非字典)")
    resp = evidence.get("response")
    h = evidence.get("hash")
    src = evidence.get("source")
    if resp is None or h is None:
        raise CoreEvidenceInvalid("机读证据缺失 response/hash")
    if not src:
        raise CoreEvidenceInvalid("机读证据未标注来源 source")
    if sha256_of(resp) != h:
        raise CoreEvidenceInvalid("机读证据哈希不匹配(疑似伪造)")
    return True


def check_nsfl(matter_flags):
    """NSFL 负空间熔断检查: 零豁免。命中任一负空间标记即熔断。返回 (ok, hits)"""
    hits = [f for f in (matter_flags or []) if f in NSFL_NEGATIVE_SPACE]
    if hits:
        return (False, hits)
    return (True, [])


def generate_guidance(entity):
    """引导加载材料: 指引加载 TDCA-CORE; 必须过 NSFL(零豁免, 防御性)"""
    guidance = {
        "entity": entity,
        "action": "引导加载 TDCA-CORE 基协议 (%s)" % MANDATORY_CORE_ID,
        "steps": ["读取 TDCA-CORE 基协议 yaml",
                  "在 Agent 配置声明 loaded_core=True",
                  "提供机读证据(response+sha256哈希+source)",
                  "重跑 ecosystem_admit_v2 触发准入"],
        "flags": [],  # 纯加载指引, 不命中任何 NSFL 负空间
    }
    ok, hits = check_nsfl(guidance["flags"])
    if not ok:
        raise NSFLTripped("引导材料命中 NSFL 负空间: %s" % hits)
    return guidance


def _admit(entity, note, evidence=None):
    """内部: 发射准入 NCA (仅当已有加载证据时调用)"""
    base = load_core_base()
    src = (evidence or {}).get("source", "loaded_ids") if isinstance(evidence, dict) else "loaded_ids"
    nid, npath, _ = NCA.generate_nca(
        operation_type="EcosystemAdmit",
        scope=".tdca-protocol/cognitive-compiler/tdca_core (生态准入 %s)" % entity,
        pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
        post_state={"path": None, "hash": None, "size": 0, "exists": True, "backup": None},
        function_call_id="TDCA-FC-ADMIT-%s" % entity,
        notes="%s 已加载 TDCA 思维协议基协议 %s, 准入生态 (v2 可转化态); 证据来源=%s"
              % (entity, MANDATORY_CORE_ID, src),
    )
    return {"entity": entity, "admitted": True, "core_base": MANDATORY_CORE_ID,
            "nca_id": nid, "nca_path": npath, "evidence_source": src}


def ecosystem_admit_v2(entity, loaded_ids=None, core_evidence=None, note="v2 可转化准入"):
    """v2 准入: PENDING_LOAD 分支(零权利态) + 机读证据确认 + NSFL 钩子。
    - 已有加载证据(loaded_ids 含 CORE 或 有效 core_evidence) -> 准入发射 NCA
    - 无证据 -> PENDING_LOAD 零权利态(不发射NCA/不落盘/无联盟资格/无配置权), 返回引导材料
    """
    loaded_ids = loaded_ids or []
    # 1. 向后兼容 v1: loaded_ids 已含 CORE -> 直接准入
    if MANDATORY_CORE_ID in loaded_ids:
        return _admit(entity, note=note)
    # 2. v2 机读证据路径: 校验有效 -> 准入
    if core_evidence is not None:
        verify_core_evidence(core_evidence)  # 无效则抛 CoreEvidenceInvalid(零权利, 调用方捕获)
        return _admit(entity, note=note, evidence=core_evidence)
    # 3. 无证据 -> PENDING_LOAD 零权利态
    guidance = generate_guidance(entity)  # 内部过 NSFL(零豁免)
    return {"entity": entity, "state": PENDING_LOAD, "admitted": False,
            "rights": {"nca": False, "disk_write": False,
                       "coalition": False, "config_right": False},
            "guidance": guidance,
            "note": "零权利态: 不发射NCA/不落盘/无联盟资格/无配置权; 引导加载后重跑准入"}


def anchor_vb_to_cop(cop_path):
    """VB 锚定升级: 实跑出 1 COP 替代自报基值。返回锚定结果或 None(退化, 需自报/待定)"""
    if not cop_path or not os.path.isfile(cop_path):
        return None
    try:
        with open(cop_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return None
    # 容忍 DeepSeek 在 YAML 外套 ```yaml 代码块标记(违反 system prompt 但时有发生);
    # provenance 注释可能在闭合围栏之后, 故提取首个代码块内容即可
    fm = re.search(r"```[a-zA-Z]*\s*\n(.*?)\n```", raw, re.S)
    if fm:
        raw = fm.group(1)
    try:
        d = yaml.safe_load(raw)
    except Exception:
        d = None
    if isinstance(d, dict):
        bp = (d.get("soul") or {}).get("base_protocol")
        base_ok = bp == MANDATORY_CORE_ID or d.get("base_protocol") == MANDATORY_CORE_ID
        has_neg = bool(d.get("negative_space") or d.get("nsfl_version"))
        if base_ok and has_neg:
            return {"anchored": True, "cop_path": cop_path,
                    "vb": "实跑产出可验证COP(正和信号)", "unverified": False}
        return None
    # 容错: DeepSeek 常在 primitive 行写带类型注解冒号的函数签名(非法 YAML),
    # 退化为正则核验锚点条件(base_protocol 匹配 + 含 negative_space), 仍算锚定成功
    bp_ok = bool(re.search(r"base_protocol:\s*TDCA-CORE-20260815-01", raw))
    has_neg = ("negative_space" in raw) or ("nsfl_version" in raw)
    if bp_ok and has_neg:
        return {"anchored": True, "cop_path": cop_path,
                "vb": "实跑产出可验证COP(正和信号, 正则容错解析)",
                "unverified": False, "parse_fallback": True}
    return None


if __name__ == "__main__":
    print("===== TDCA 生态准入强制加载机制演示 =====")
    # 1. 未加载基协议 -> 拒绝
    try:
        ecosystem_admit("外部Agent-X", loaded_ids=[])
        print("[FAIL] 应拒绝未加载基协议的主体")
    except AdmissionDenied as e:
        print("[OK] 拒绝未加载基协议: %s" % e)
    # 2. 已加载基协议 -> 准入
    rec = ecosystem_admit("联盟智能体-Y", loaded_ids=[MANDATORY_CORE_ID, "SCEN-COP-20260814-01"])
    print("[OK] 准入: %s -> NCA %s" % (rec["entity"], rec["nca_id"]))
    print("===== 演示完成 (基协议 ID=%s) =====" % MANDATORY_CORE_ID)
