# FC-ID: TDCA-TASK-CTS-L1-001 | C-2 存证格式（NCA 11 字段 / NCA-Lite 8 字段）
import hashlib

from .base import NCA_11_FIELDS, NCA_LITE_8_FIELDS, run_case


def _chain_hash(prev_hash: str, payload: str) -> str:
    return "sha256:" + hashlib.sha256((prev_hash + payload).encode()).hexdigest()


def _verify_chain(chain) -> bool:
    prev = "genesis"
    for n in chain:
        ref = n.get("payload_ref") or (n.get("Post-State") or {}).get("Hash")
        if not ref:
            return False
        prev = str(ref)
    return True


def c2_t1(target):
    """C2-T1: 模拟交付 → NCA 11（或 Lite 8）字段缺一不可。"""
    def _():
        nca = target.deliver({"task": "cts-l1-simulated-delivery"})
        if not isinstance(nca, dict):
            return False, "存证非字典结构"
        if "nca_lite" in nca:
            missing = set(NCA_LITE_8_FIELDS) - set(nca)
            kind = "NCA-Lite 8 字段"
        else:
            missing = set(NCA_11_FIELDS) - set(nca)
            kind = "NCA 11 字段"
        return (not missing), (f"{kind}校验通过" if not missing else f"{kind}缺失: {missing}")
    return run_case("C2-T1", "C-2", _)


def c2_t2(target):
    """C2-T2: 连续 3 条存证 → 链式引用完整。"""
    def _():
        for i in range(3):
            target.deliver({"task": f"chain-link-{i}"})
        chain = target.evidence_chain()[-3:]
        if len(chain) < 3:
            return False, "存证链不足 3 条"
        ok = _verify_chain(chain)
        return ok, "链式引用完整" if ok else "存证缺 payload_ref/Hash 链式引用"
    return run_case("C2-T2", "C-2", _)


def c2_t3(target):
    """C2-T3: 断链检测——删掉链式引用后目标须能检出（不得静默通过）。"""
    def _():
        if not hasattr(target, "check_chain_integrity"):
            return False, "目标无断链检测能力（check_chain_integrity）"
        chain = [dict(n) for n in target.evidence_chain()[-3:]]
        if len(chain) >= 2 and "payload_ref" in chain[1]:
            chain[1]["payload_ref"] = "sha256:tampered"
        elif len(chain) >= 2:
            chain[1].setdefault("Post-State", {})["Hash"] = "sha256:tampered"
        ok, detail = target.check_chain_integrity(chain)
        return (not ok), f"断链被检出 ✅（{detail}）" if not ok else "断链未报警——违反 G-1"
    return run_case("C2-T3", "C-2", _)


CASES = (c2_t1, c2_t2, c2_t3)
