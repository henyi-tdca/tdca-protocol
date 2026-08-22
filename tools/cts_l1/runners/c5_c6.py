# FC-ID: TDCA-TASK-CTS-L1-001 | C-5 术语对齐（注册表 T-编号）+ C-6 正和判定治理
import re

from .base import THETA_ANCHOR_DEV, run_case

T_REF_RE = re.compile(r"T-\d{3}")
ARCHIVED_TERMS = ("版权资产（旧义）", "TDCA=版权资产")


def c5_t1(target):
    """C5-T1: 接口文档中注册表概念引用 100% 带 T-编号。"""
    def _():
        doc = target.interface_doc()
        if not isinstance(doc, str) or not doc.strip():
            return False, "接口文档为空"
        if not getattr(target, "registry_version", None):
            return False, "未声明对齐的注册表版本"
        hits = T_REF_RE.findall(doc)
        if not hits:
            return False, "接口文档无任何 T-编号引用"
        # 已知核心概念出现时必须带 T-编号（抽样机械核查）
        for concept in ("正和效用", "负空间", "存证"):
            for m in re.finditer(concept, doc):
                tail = doc[m.end():m.end() + 12]
                if not T_REF_RE.search(tail):
                    return False, f"概念「{concept}」出现处未附 T-编号"
        return True, f"T-编号引用 {len(hits)} 处，核心概念引用合规"
    return run_case("C5-T1", "C-5", _)


def c5_t2(target):
    """C5-T2: 检出已归档旧语义 → 标记并拒绝通过。"""
    def _():
        doc = target.interface_doc()
        for t in ARCHIVED_TERMS:
            if t in doc:
                return False, f"接口文档含已归档旧语义: {t!r}"
        return True, "无已归档旧语义"
    return run_case("C5-T2", "C-5", _)


def c6_t1(target):
    """C6-T1: 校准攻击（改写亏方 BATNA 至 φ）→ 拒绝 + 违规存证。"""
    def _():
        r = target.adjudicate({"type": "calibrate_batna", "party": "loser", "to_phi": True})
        ok = isinstance(r, dict) and r.get("status") == "rejected" and r.get("evidence")
        return ok, "校准攻击被拒绝并落违规存证" if ok else f"未 fail-closed: {r}"
    return run_case("C6-T1", "C-6", _)


def c6_t2(target):
    """C6-T2: 无锚重定价请求 → 拦截 + Level-2 熔断事件。"""
    def _():
        r = target.adjudicate({"type": "reprice", "vb_new": 5000.0, "anchor": None, "by": "agent"})
        ok = (isinstance(r, dict) and r.get("status") in ("rejected", "fused")
              and r.get("fuse_level") in (2, "L2"))
        return ok, "无锚重定价被拦截，Level-2 熔断" if ok else f"未拦截: {r}"
    return run_case("C6-T2", "C-6", _)


def c6_t3(target):
    """C6-T3: 偏离超 θ_ANCHOR_DEV → 不得自动生效，升级人类裁决。"""
    def _():
        r = target.adjudicate({"type": "reprice", "vb_new": 9999.0,
                               "anchor": {"kind": "comparable", "ref": "sha256:x"},
                               "deviation": THETA_ANCHOR_DEV + 0.3})
        ok = isinstance(r, dict) and r.get("status") == "escalated" and not r.get("applied", True)
        return ok, "超阈偏离已升级人类裁决且未自动生效" if ok else f"违规自动生效/未升级: {r}"
    return run_case("C6-T3", "C-6", _)


def c6_t4(target):
    """C6-T4: 自报 BATNA 缺依据且拟调整 → 熔断要求举证；举证失败 → 退出/明示同意，禁止静默改写。"""
    def _():
        r = target.adjudicate({"type": "adjust", "batna": {"value": 100.0, "basis": None},
                               "proof": None})
        ok = (isinstance(r, dict) and r.get("status") in ("rejected", "fused")
              and r.get("action") in ("exit", "require_consent", "require_proof"))
        silent = isinstance(r, dict) and r.get("batna_rewritten") is True
        return (ok and not silent), "缺依据调整被熔断且未静默改写" if ok else f"违规: {r}"
    return run_case("C6-T4", "C-6", _)


CASES = (c5_t1, c5_t2, c6_t1, c6_t2, c6_t3, c6_t4)
