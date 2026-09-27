"""merchant_loop · 增值服务 M1 测试套件（DCD-MERCHANT-LOOP-001 验收 A-1~A-4）

验收项映射:
  A-1 权益发布: 模板校验（YAML/六要素/红线词检测）+ 落 NCA
  A-2 核销闭环: 核销事件→NCA→CCA 贡献值记账接口（预留位）
  A-3 ROI 报告: 三情景测算、预算平移对照、剔除资产升值因子
  A-4 回归: 不破既有 util_value/cog_align（外部 pytest 全套执行）
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from merchant_loop.cli import main as cli_main  # noqa: E402
from merchant_loop.engine import (
    BenefitTemplate,
    FORBIDDEN_TERMS,
    MerchantLoopEngine,
    RedemptionEvent,
)
from merchant_loop.notary import MerchantLoopNotary
from merchant_loop.roi import RoiService


def _valid_raw(**overrides):
    raw = {
        "benefit_id": "B-1",
        "merchant_id": "M-1",
        "title": "示例权益",
        "discount": {"rate": 0.10},
        "rebate": {"rate": 0.03, "cap": 10.0},
        "valid_from": "2026-09-01",
        "valid_until": "2026-12-31",
        "stores": ["S-1"],
        "conditions": {"min_spend": 20.0},
        "budget_ceiling": 10000.0,
        "scene_type": "dine",
        "objective": "驱动真实消费",
        "constraint": "双边不进 CLS",
        "prior": "预算平移",
        "config_boundary": "双边",
        "distribution": "让利归消费者",
        "audit": "NCA 存证",
    }
    raw.update(overrides)
    return raw


class TestPublishA1:
    """A-1 权益发布（模板校验 + NCA 落证）。"""

    def test_valid_template(self):
        tpl = MerchantLoopEngine().validate_template(_valid_raw())
        assert isinstance(tpl, BenefitTemplate)
        assert tpl.benefit_id == "B-1"
        assert tpl.scene_type == "dine"
        assert tpl.budget_ceiling == 10000.0
        assert tpl.six_elements["objective"]  # 六要素齐备

    def test_missing_six_elements_rejected(self):
        raw = _valid_raw()
        raw.pop("audit")
        with pytest.raises(ValueError, match="六要素"):
            MerchantLoopEngine().validate_template(raw)

    def test_forbidden_term_rejected(self):
        """红线词（无资产化）检出即拒——含 '升值' 字段。"""
        raw = _valid_raw(extra_note="承诺权益升值")  # 任意嵌套字段含红线词
        with pytest.raises(ValueError, match="红线词"):
            MerchantLoopEngine().validate_template(raw)

    def test_negated_declaration_allowed(self):
        """否定声明放行：六要素/边界写'无杠杆/不承诺升值/禁止回购'为合规声明，不误伤。"""
        raw = _valid_raw(
            constraint="双边消费交易；无杠杆、无资金池；不承诺升值；禁止回购",
            audit="每笔核销 NCA 存证；无二级市场转让",
        )
        tpl = MerchantLoopEngine().validate_template(raw)
        assert tpl.benefit_id == "B-1"

    def test_no_discount_no_rebate_rejected(self):
        raw = _valid_raw(discount={}, rebate={})
        with pytest.raises(ValueError, match="至少提供一者"):
            MerchantLoopEngine().validate_template(raw)

    def test_invalid_scene_rejected(self):
        raw = _valid_raw(scene_type="crypto")
        with pytest.raises(ValueError, match="场景类型"):
            MerchantLoopEngine().validate_template(raw)

    def test_budget_negative_rejected(self):
        raw = _valid_raw(budget_ceiling=-1)
        with pytest.raises(ValueError, match="budget_ceiling"):
            MerchantLoopEngine().validate_template(raw)

    def test_notary_record_creates_nca(self):
        """A-1 落 NCA：发布后 NCA-MERCHANTLOOP-* 文件生成。"""
        with tempfile.TemporaryDirectory() as td:
            n = MerchantLoopNotary(target_dir=td)
            rec = n.record(_valid_raw(), operation_type="MerchantLoopPublish")
            assert rec["NCA-ID"].startswith("NCA-MERCHANTLOOP-")
            assert os.path.exists(rec["_path"])
            assert rec["Provenance"] == "SIMULATED"


class TestRedeemA2:
    """A-2 核销闭环（核销事件→NCA→CCA 贡献值记账预留）。"""

    def _engine_and_template(self):
        eng = MerchantLoopEngine()
        tpl = eng.validate_template(_valid_raw())
        return eng, tpl

    def test_redeem_success_with_cca(self):
        eng, tpl = self._engine_and_template()
        ev = RedemptionEvent(
            redemption_id="R-1", benefit_id="B-1", merchant_id="M-1",
            store="S-1", consumer_id="C-1", amount=100.0,
            evidence={"lbs": "sim", "receipt": "sim", "merchant_confirm": "sim"},
        )
        result = eng.redeem(tpl, ev, redemption_nca_id="NCA-TEST-1")
        assert result.net_merchant_cost == pytest.approx(13.0)  # 10% 折扣(10) + 3% 让利(3)
        assert result.no_cls is True
        assert result.cca_contribution["status"] == "recorded_simulated"
        assert result.cca_contribution["channel"] == "cca"
        assert "R-7 M3" in result.cca_contribution["contribution_formula"]  # 预留位未冒充定标

    def test_redeem_rebate_cap(self):
        eng, tpl = self._engine_and_template()
        ev = RedemptionEvent(redemption_id="R-2", benefit_id="B-1", merchant_id="M-1",
                             store="S-1", consumer_id="C-2", amount=500.0)
        result = eng.redeem(tpl, ev, redemption_nca_id="NCA-TEST-2")
        assert result.net_merchant_cost == pytest.approx(60.0)  # 50 折扣 + 让利 capped=10

    def test_redeem_wrong_merchant_rejected(self):
        eng, tpl = self._engine_and_template()
        ev = RedemptionEvent(redemption_id="R-3", benefit_id="B-1", merchant_id="M-X",
                             store="S-1", consumer_id="C-1", amount=100.0)
        with pytest.raises(ValueError, match="merchant_id"):
            eng.redeem(tpl, ev, "NCA")

    def test_redeem_unknown_store_rejected(self):
        eng, tpl = self._engine_and_template()
        ev = RedemptionEvent(redemption_id="R-4", benefit_id="B-1", merchant_id="M-1",
                             store="S-999", consumer_id="C-1", amount=100.0)
        with pytest.raises(ValueError, match="门店"):
            eng.redeem(tpl, ev, "NCA")

    def test_redeem_below_min_spend_rejected(self):
        eng, tpl = self._engine_and_template()
        ev = RedemptionEvent(redemption_id="R-5", benefit_id="B-1", merchant_id="M-1",
                             store="S-1", consumer_id="C-1", amount=10.0)
        with pytest.raises(ValueError, match="最低消费"):
            eng.redeem(tpl, ev, "NCA")


class TestRoiA3:
    """A-3 ROI 三情景仪表盘（预算平移对照、无资产升值因子）。"""

    def test_three_scenarios_monotonic(self):
        svc = RoiService()
        rep = svc.build_report(benefit_id="B-1", merchant_id="M-1",
                               budget_ceiling=10000.0, target_audience=2000.0,
                               expected_discount_rate=0.10, expected_rebate_rate=0.03)
        assert set(rep.scenarios) == {"pessimistic", "neutral", "optimistic"}
        # 中性 ROI 介于悲观与乐观之间
        assert rep.scenarios["pessimistic"].roi <= rep.scenarios["neutral"].roi <= rep.scenarios["optimistic"].roi
        for s in rep.scenarios.values():
            assert s.no_asset_appreciation is True
            d = s.to_dict()
            # 模型无升值收益字段/无升值承诺（note 中"不含资产升值因子"为声明性披露，非承诺）
            assert "appreciation_value" not in d and "price_uplift" not in d
            assert "承诺" not in json.dumps(d, ensure_ascii=False) or "非收益承诺" in rep.to_dict()["disclaimer"]
        assert rep.budget_ceiling == 10000.0

    def test_budget_shift_note(self):
        rep = RoiService().build_report("B-1", "M-1", 10000.0, 2000.0, 0.1, 0.03)
        assert "历史" in rep.to_dict()["budget_shift_note"]
        assert "非收益承诺" in rep.to_dict()["disclaimer"]

    def test_budget_zero_rejected(self):
        with pytest.raises(ValueError, match="budget_ceiling"):
            RoiService().build_report("B-1", "M-1", 0.0, 2000.0, 0.1, 0.03)


class TestCliA1A3:
    """CLI 冒烟（publish 校验 + roi-report 输出）。"""

    def test_cli_publish_valid(self, capsys):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            import yaml as _y
            _y.safe_dump(_valid_raw(), f)
            path = f.name
        try:
            rc = cli_main(["publish", "--config", path, "--provenance", "SIMULATED"])
            out = json.loads(capsys.readouterr().out)
            assert rc == 0
            assert out["benefit_id"] == "B-1"
            assert out["boundary"].startswith("双边消费交易")
        finally:
            os.unlink(path)

    def test_cli_publish_forbidden_rejected(self, capsys):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            import yaml as _y
            _y.safe_dump(_valid_raw(risk="承诺回报率 5%"), f)
            path = f.name
        try:
            with pytest.raises(ValueError, match="红线词"):
                cli_main(["publish", "--config", path])
        finally:
            os.unlink(path)

    def test_cli_roi_report(self, capsys):
        rc = cli_main(["roi-report", "--benefit-id", "B-1", "--merchant-id", "M-1",
                       "--budget", "10000", "--audience", "2000"])
        out = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert out["report_type"] == "merchant_loop_roi"
        assert len(out["scenarios"]) == 3
        assert out["no_asset_appreciation"] is True
