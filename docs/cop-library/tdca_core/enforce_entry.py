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
import sys
import datetime

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
