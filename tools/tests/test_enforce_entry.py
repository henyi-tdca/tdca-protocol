# FC-ID: TDCA-ENFORCE-ENTRY-SPEC-001 | enforce_entry.py 规则测试（R1~R10 + 链校验）
# 口径: 每个 FAIL 用例对应规格 §五 表格一行；合法基线两份（标准 Operator / 带中文备注）
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import enforce_entry as ee  # noqa: E402


def _base_doc(**over):
    doc = {
        "NCA-ID": "TDCA-ADMIT-20260822-001",
        "Operation-Type": "AdmissionNCA",
        "Operator": "alice-gh",
        "Timestamp": "2026-08-22T10:00:00+00:00",
        "Scope": "加入 TDCA 五元协作开源社区，成为 L1 缔约者",
        "Contractor": {"GitHub-ID": "alice-gh", "Legal-Name": "", "Contact": ""},
        "Base-Protocol-Acceptance": {
            "TDCA-CONST": True, "NSFL-V0.2": True,
            "TDCA-WORKING-SPEC-001": True, "TDCA-OPC-COMMUNITY-001": True,
            "Accepted": True,
        },
        "Red-Lines-Acknowledged": ["不发币、不承诺分红、不代币化（NSFL 负空间）"],
        "Provenance": {"Status": "Simulated"},
        "Human-Signature": {"Status": "Signed", "Signed-By": "alice-gh"},
    }
    doc.update(over)
    return doc


def _write(tmp_path: Path, doc, name="case.yaml", raw=None) -> Path:
    p = tmp_path / name
    p.write_text(raw if raw is not None else yaml.safe_dump(doc, allow_unicode=True),
                 encoding="utf-8")
    return p


@pytest.fixture()
def fuse_log(tmp_path, monkeypatch):
    """NSFL 熔断日志重定向到临时目录，避免污染真实档案库。"""
    d = tmp_path / ".nsfl-log"
    monkeypatch.setattr(ee, "NSFL_LOG", d)
    return d


# ---- 合法基线（规格 §五 第 1~2 行）----

def test_valid_standard_operator(tmp_path, fuse_log):
    ok, reasons = ee.check_file(_write(tmp_path, _base_doc()))
    assert ok, reasons


def test_valid_operator_with_cn_suffix(tmp_path, fuse_log):
    doc = _base_doc(Operator="alice-gh（缔约者·首批）")
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert ok, reasons


# ---- R1 结构 ----

def test_r1_missing_field(tmp_path, fuse_log):
    doc = _base_doc()
    del doc["Human-Signature"]
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any(r.startswith("R1") for r in reasons)


def test_r1_unparseable_yaml(tmp_path, fuse_log):
    p = _write(tmp_path, None, raw="NCA-ID: [unclosed\n  bad: : :")
    ok, reasons = ee.check_file(p)
    assert not ok and any("R1" in r for r in reasons)


# ---- R2 编号 ----

def test_r2_duplicate_id(tmp_path, fuse_log):
    doc = _base_doc()
    ok, reasons = ee.check_file(_write(tmp_path, doc),
                                existing_ids={"TDCA-ADMIT-20260822-001"})
    assert not ok and any("R2" in r and "冲突" in r for r in reasons)


def test_r2_bad_date(tmp_path, fuse_log):
    doc = _base_doc(**{"NCA-ID": "TDCA-ADMIT-20261340-001"})  # 13 月 40 日
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R2" in r and "日期" in r for r in reasons)


def test_r2_bad_format(tmp_path, fuse_log):
    doc = _base_doc(**{"NCA-ID": "ADMIT-20260822-1"})
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R2" in r and "格式" in r for r in reasons)


# ---- R4 身份一致性 ----

def test_r4_identity_mismatch(tmp_path, fuse_log):
    doc = _base_doc(Operator="bob-gh")
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R4" in r for r in reasons)


# ---- R5 基协议 ----

def test_r5_missing_protocol_item(tmp_path, fuse_log):
    doc = _base_doc()
    del doc["Base-Protocol-Acceptance"]["NSFL-V0.2"]
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R5" in r and "四项" in r for r in reasons)


def test_r5_not_accepted(tmp_path, fuse_log):
    doc = _base_doc()
    doc["Base-Protocol-Acceptance"]["Accepted"] = False
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R5" in r for r in reasons)


# ---- R6 红线 ----

def test_r6_empty_red_lines(tmp_path, fuse_log):
    doc = _base_doc(**{"Red-Lines-Acknowledged": []})
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R6" in r for r in reasons)


# ---- R7 真实态 ----

def test_r7_real_provenance_rejected(tmp_path, fuse_log):
    doc = _base_doc(Provenance={"Status": "Real"})
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R7" in r for r in reasons)


# ---- R8 代签 ----

def test_r8_proxy_signature_rejected(tmp_path, fuse_log):
    doc = _base_doc()
    doc["Human-Signature"]["Signed-By"] = "someone-else"
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R8" in r for r in reasons)


# ---- R10 NSFL 熔断 ----

def test_r10_forbidden_word_fuse(tmp_path, fuse_log):
    doc = _base_doc(Scope="加入社区并讨论发币计划")
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert not ok and any("R10" in r for r in reasons)
    log = (fuse_log / "fuse.log").read_text(encoding="utf-8")
    assert "发币" in log and "TDCA-ADMIT-20260822-001" in log


def test_r10_negation_exempt(tmp_path, fuse_log):
    """红线自述「不发币/不承诺分红」含禁词但属否定语境，不得熔断。"""
    doc = _base_doc(**{"Red-Lines-Acknowledged": [
        "不发币、不公售、不承诺分红、不代币化（NSFL 负空间一票否决）",
        "不拉踩其他协议",
    ]})
    ok, reasons = ee.check_file(_write(tmp_path, doc))
    assert ok, reasons


def test_new_draft_passes_own_check(tmp_path, fuse_log, archives, monkeypatch):
    """--new 生成的草稿必须 R1~R10 全过（工具不得自相矛盾）。"""
    monkeypatch.setattr("builtins.input", lambda _: "carol-gh")
    draft = ee.new_draft()
    ok, reasons = ee.check_file(draft)
    assert ok, reasons


# ---- --verify 链校验 ----

@pytest.fixture()
def archives(tmp_path, monkeypatch):
    d = tmp_path / "nca-archives"
    d.mkdir()
    monkeypatch.setattr(ee, "ARCHIVES", d)
    return d


def _put(archives: Path, nid: str, ts: str):
    doc = _base_doc(**{"NCA-ID": nid, "Timestamp": ts})
    (archives / f"{nid}.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True), encoding="utf-8")


def test_verify_chain_ok(archives):
    _put(archives, "TDCA-ADMIT-20260822-001", "2026-08-22T10:00:00+00:00")
    _put(archives, "TDCA-ADMIT-20260822-002", "2026-08-22T11:00:00+00:00")
    ok, msgs = ee.verify_chain()
    assert ok, msgs


def test_verify_chain_broken_seq(archives):
    _put(archives, "TDCA-ADMIT-20260822-001", "2026-08-22T10:00:00+00:00")
    _put(archives, "TDCA-ADMIT-20260822-003", "2026-08-22T11:00:00+00:00")
    ok, msgs = ee.verify_chain()
    assert not ok and any("断链" in m for m in msgs)


def test_verify_chain_timestamp_inversion(archives):
    _put(archives, "TDCA-ADMIT-20260822-001", "2026-08-22T12:00:00+00:00")
    _put(archives, "TDCA-ADMIT-20260822-002", "2026-08-22T11:00:00+00:00")
    ok, msgs = ee.verify_chain()
    assert not ok and any("倒挂" in m for m in msgs)


def test_verify_chain_duplicate_id(archives):
    _put(archives, "TDCA-ADMIT-20260822-001", "2026-08-22T10:00:00+00:00")
    dup = archives / "dup-copy.yaml"
    dup.write_text((archives / "TDCA-ADMIT-20260822-001.yaml").read_text(encoding="utf-8"),
                   encoding="utf-8")
    dup.rename(archives / "TDCA-ADMIT-20260823-001.yaml")  # 文件名不同、内容同号
    ok, msgs = ee.verify_chain()
    assert not ok and any("重复" in m for m in msgs)


def test_verify_empty_archive(archives):
    ok, msgs = ee.verify_chain()
    assert ok and "空档案库" in msgs[0]
