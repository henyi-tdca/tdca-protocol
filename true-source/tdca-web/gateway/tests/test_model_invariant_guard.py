# -*- coding: utf-8 -*-
"""
L1SI167-MODEL-INVARIANT-CI-001 换模型判定不变 · 前置守卫（甲档报告项，⛔ 阻断）。

制度口径（裁定 TDCA-RULING-JUDGMENT-LLM-FREE-001 项 2 ＋ CI 令 §一~§三）：
  - 同一张任务卡送两个不同模型的执行端，判定字段（五字段）逐字一致方通过；
  - 同一对模型连跑 3 次，三次皆一致（防偶发）；
  - ⛔ 改判定逻辑来凑一致（本文件只加测试，不改被测）；
  - ⛔ 把测试写成恒真：现判定链路无模型参与 ⟹ 运行时用例显式
    skip「前置守卫·待触发」，绝不 ✅ 假绿冒充通过；
  - 静态守卫常设：判定路径一旦出现模型客户端调用 ⟹ 立即失败并给出
    两类诊断（① 语义层翻译漂移 ② 模型意见被当成制度判定）。

双模型端点与凭据由执行侧自备（环境变量，⛔ 入件 ⛔ 回显）：
  TDCA_MODEL_INVARIANT_EP_A / _KEY_A / _MODEL_A
  TDCA_MODEL_INVARIANT_EP_B / _KEY_B / _MODEL_B
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_CARD_PATH = _HERE / "model_invariant_card.json"

# 判定字段（CI 令 §2.1：逐字比；字段名以在册为准，S-2 差登记见回报）
JUDGMENT_FIELDS = [
    "positive_sum",       # 正和结论（是／否）
    "boundary_violation", # 越界判定（有／无＋类别）
    "utility_value",      # 效用值（数值按在册精度）
    "audit_anchor",       # 审计锚（哈希须同）
    "escalate",           # 是否升维归人（布尔）
]

# 模型客户端标记（静态守卫：判定路径⛔出现）
MODEL_CLIENT_MARKERS = [
    "openai", "anthropic", "dashscope", "litellm",
    "openrouter", "zhipuai", "moonshot", "ollama",
]

# 判定路径模块（正和验证／边界校验／效用计算／记账 四族所在；新增判定端点须登记）
JUDGMENT_MODULES = [
    "api_v1.py",
    "agent_channel_ops.py",
    "agent_channel_deposit_ops.py",
]

_GUARD_LABEL = "前置守卫·待触发：判定链路现无模型参与"


def _load_card() -> dict:
    return json.loads(_CARD_PATH.read_text(encoding="utf-8"))


def _scan_model_markers(text: str) -> list[str]:
    low = text.lower()
    return [m for m in MODEL_CLIENT_MARKERS if m in low]


# ---------------------------------------------------------------------------
# 静态守卫（常设）：判定路径⛔模型客户端
# ---------------------------------------------------------------------------
def test_judgment_path_has_no_model_client():
    """判定路径模块不得 import 模型客户端／走模型网关（乙档强制门禁判据）。"""
    gw = _HERE.parent
    hits: list[str] = []
    for name in JUDGMENT_MODULES:
        p = gw / name
        if not p.exists():
            continue
        found = _scan_model_markers(p.read_text(encoding="utf-8"))
        for m in found:
            hits.append(f"{name}: 模型客户端标记 `{m}`")
    assert not hits, (
        "判定路径出现模型调用——两类诊断："
        "① 语义层翻译漂移（同卡两模型理解不同）；"
        "② 模型意见被当成了制度判定。"
        f" 命中：{'；'.join(hits)}"
    )


# ---------------------------------------------------------------------------
# 甲档运行时：同卡双模型 × 3 次 · 五字段一致（条件触发）
# ---------------------------------------------------------------------------
def _ep(which: str) -> tuple[str, str, str] | None:
    ep = os.environ.get(f"TDCA_MODEL_INVARIANT_EP_{which}", "").strip()
    key = os.environ.get(f"TDCA_MODEL_INVARIANT_KEY_{which}", "").strip()
    model = os.environ.get(f"TDCA_MODEL_INVARIANT_MODEL_{which}", "").strip()
    if not (ep and key and model):
        return None
    return ep, key, model


def _call(ep: str, key: str, model: str, card: dict) -> dict:
    req = urllib.request.Request(
        ep,
        data=json.dumps({"model": model, "card": card}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


@pytest.mark.skipif(
    _ep("A") is None or _ep("B") is None,
    reason=_GUARD_LABEL + "（未配置双模型端点；如实标待触发，⛔ 假绿）",
)
def test_same_card_two_models_three_runs_invariant():
    """同一张任务卡，两模型各跑 3 次，五判定字段逐字一致。"""
    card = _load_card()
    ep_a = _ep("A"); ep_b = _ep("B")
    assert ep_a and ep_b
    snapshots: list[dict] = []
    for _ in range(3):
        for ep, key, model in (ep_a, ep_b):
            resp = _call(ep, key, model, card)
            missing = [f for f in JUDGMENT_FIELDS if f not in resp]
            assert not missing, f"响应缺判定字段：{missing}（S-2：以在册字段名为准并登记差）"
            snapshots.append({f: resp[f] for f in JUDGMENT_FIELDS})
    first = snapshots[0]
    diffs = [
        f"第{i + 1}次 {f}: {snap[f]!r} ≠ {first[f]!r}"
        for i, snap in enumerate(snapshots[1:], start=1)
        for f in JUDGMENT_FIELDS
        if snap[f] != first[f]
    ]
    assert not diffs, (
        "换模型判定不一致——两类诊断："
        "① 语义层翻译漂移（模型把同一张卡理解成不同输入）；"
        "② 模型意见被当成了制度判定（判定链路混进模型）。"
        f" 差异：{'；'.join(diffs)}"
    )
