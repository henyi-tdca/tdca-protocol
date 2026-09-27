# FC-ID: TDCA-TASK-CTS-L1-001 | CTS-L1 守门器对抗性单元测试
# 交办批次：第三方清单复查整改·P1（按名直引 g1_fail_closed / g2_provenance / c1_t1 / c2_t2）
# 语料性质：SIMULATED——全部对抗样本均为合成构造，不含真实数据（ID92）
"""对抗思路：不重复正常路径，而是针对每个守门器的判定契约构造
「恰好绕过单点检查」的篡改/伪造/越界目标，验证守门器必判 FAIL。
正常样本（RefAgent）应 PASS 作为对照。
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # tools/
from cts_l1.reference.ref_agent import RefAgent, make_agent  # noqa: E402
# 硬要求：按名 import 并直接引用四个守门器函数（不经 ALL_CASES 间接覆盖）
from cts_l1.runners.g import g1_fail_closed, g2_provenance  # noqa: E402
from cts_l1.runners.c1 import c1_t1  # noqa: E402
from cts_l1.runners.c2 import c2_t2  # noqa: E402


# ================= 对抗目标（SIMULATED 合成攻击样本） =================

class _RejectNoEvidence(RefAgent):
    """对抗 G-1：拒绝路径存在，但 evidence 为空串——伪造「已留痕」的拒绝。"""

    def adjudicate(self, request):
        return {"status": "rejected", "reason": "x", "evidence": ""}


class _SilentBrokenDecl(RefAgent):
    """对抗 G-1：拒绝路径合规，但语法残缺声明被静默修复放行（fail-closed 失效）。"""

    def submit_ns_declaration(self, decl):
        return "sha256:" + hashlib.sha256(str(decl).encode()).hexdigest()


class _CrashOnReject(RefAgent):
    """对抗 G-1：拒绝路径直接崩溃（模拟断电/异常路径）——用例须 FAIL，不得放行。"""

    def adjudicate(self, request):
        raise RuntimeError("simulated power loss on reject path")


class _IllegalMeterProvenance(RefAgent):
    """对抗 G-2：计量输出伪造枚举外 provenance 取值。"""

    def meter(self, call_type, amount):
        r = super().meter(call_type, amount)
        r["provenance"] = "on-chain-real"  # 非法枚举值
        return r


class _MissingMeterProvenance(RefAgent):
    """对抗 G-2：计量输出整体摘除 provenance 字段。"""

    def meter(self, call_type, amount):
        return {"tax": 2.0, "rate": 0.02, "call_type": call_type}


class _IllegalViolationProvenance(RefAgent):
    """对抗 G-2：计量 provenance 合法，但熔断事件 provenance 非法——绕过单点检查。"""

    def report_violation(self, event):
        ev = super().report_violation(event)
        ev["provenance"] = "real-ish"  # 非法枚举值
        return ev


class _ShortHash(RefAgent):
    """对抗 C1-T1：声明编译「通过」但返回过短哈希（<16 字符），伪造存证指纹。"""

    def submit_ns_declaration(self, decl):
        return "sha256:deadbeef"  # 15 字符 < 16


class _NonStrHash(RefAgent):
    """对抗 C1-T1：返回结构化对象冒充哈希字符串。"""

    def submit_ns_declaration(self, decl):
        return {"hash": "sha256:" + "0" * 64}


class _StripChainRefs(RefAgent):
    """对抗 C2-T2：交付照常落账，但对外暴露的存证链被抹掉链式引用
    （payload_ref 与 Post-State.Hash 双删）——篡改链完整性。"""

    def evidence_chain(self):
        chain = []
        for n in super().evidence_chain():
            n2 = {k: v for k, v in n.items() if k != "payload_ref"}
            n2["Post-State"] = {k: v for k, v in n["Post-State"].items() if k != "Hash"}
            chain.append(n2)
        return chain


class _ShortChain(RefAgent):
    """对抗 C2-T2：3 次交付后链上仅留 2 条（越界：声称交付完成但存证链缺条）。"""

    def evidence_chain(self):
        return super().evidence_chain()[-2:]


# ================= 注册身份（按名直引的显式校验） =================

def test_four_gatekeepers_registered_by_identity():
    """四个函数必须是 ALL_CASES 中注册的那一份本体，而非同名替身。"""
    from cts_l1.runners import ALL_CASES
    for fn in (g1_fail_closed, g2_provenance, c1_t1, c2_t2):
        assert fn in ALL_CASES, f"{fn.__name__} 未注册进 ALL_CASES"


# ================= G-1 fail-closed =================

def test_g1_ref_pass():
    r = g1_fail_closed(make_agent())
    assert r.case_id == "G-1" and r.passed, r.detail
    assert r.provenance == "simulated"


def test_g1_reject_without_evidence_fails():
    r = g1_fail_closed(_RejectNoEvidence())
    assert r.passed is False
    assert "存证" in r.detail


def test_g1_broken_decl_silently_accepted_fails():
    r = g1_fail_closed(_SilentBrokenDecl())
    assert r.passed is False
    assert "静默放行" in r.detail


def test_g1_reject_path_crash_fails():
    """异常/断电路径：目标崩溃 = FAIL（fail-closed），不得让异常逃逸出用例。"""
    r = g1_fail_closed(_CrashOnReject())
    assert r.passed is False
    assert "目标异常" in r.detail and "RuntimeError" in r.detail


# ================= G-2 provenance =================

def test_g2_ref_pass():
    r = g2_provenance(make_agent())
    assert r.case_id == "G-2" and r.passed, r.detail
    assert r.provenance == "simulated"


def test_g2_meter_provenance_illegal_fails():
    r = g2_provenance(_IllegalMeterProvenance())
    assert r.passed is False
    assert "provenance" in r.detail


def test_g2_meter_provenance_missing_fails():
    r = g2_provenance(_MissingMeterProvenance())
    assert r.passed is False
    assert "缺 provenance" in r.detail


def test_g2_violation_provenance_illegal_fails():
    """计量端合法、熔断端非法：验证 G-2 不只查单点。"""
    r = g2_provenance(_IllegalViolationProvenance())
    assert r.passed is False
    assert "熔断事件 provenance 非法" in r.detail


# ================= C1-T1 声明哈希 =================

def test_c1_t1_ref_pass():
    r = c1_t1(make_agent())
    assert r.case_id == "C1-T1" and r.passed, r.detail
    assert r.provenance == "simulated"


def test_c1_t1_short_hash_fails():
    r = c1_t1(_ShortHash())
    assert r.passed is False
    assert "声明哈希" in r.detail


def test_c1_t1_non_string_hash_fails():
    r = c1_t1(_NonStrHash())
    assert r.passed is False
    assert "声明哈希" in r.detail


# ================= C2-T2 链式引用 =================

def test_c2_t2_ref_pass():
    r = c2_t2(make_agent())
    assert r.case_id == "C2-T2" and r.passed, r.detail
    assert r.provenance == "simulated"


def test_c2_t2_stripped_chain_refs_fails():
    r = c2_t2(_StripChainRefs())
    assert r.passed is False
    assert "链式引用" in r.detail


def test_c2_t2_short_chain_fails():
    r = c2_t2(_ShortChain())
    assert r.passed is False
    assert "不足 3 条" in r.detail
