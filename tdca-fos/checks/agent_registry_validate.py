# -*- coding: utf-8 -*-
"""
TDCA 智能体注册表校验器 — AGENTDEF5-001 段B（独立校验器，不改既有门禁）
制度锚定: TDCA-AGENT-EXEC-001 | TDCA-PUB-CORPUS-048 条例机读版
         | TDCA-TERMINOLOGY-REGISTRY T-031 | AGENTDEF5-001
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

四断言:
  B-1 asset_temporality ∈ {连续运行, 离散}（反例：「形式化离散」/空值）
  B-2 derivation.source=派生 ⟹ from 非空且不得自指（from != 本 agent 名）
  B-3 usage_mode 缺失 ⟹ 拒跑，不取默认（缺字段即违例，含空字符串）
  B-4 tax_base 与在册 T-031 口径不互抵：
      若登记税率字段 tax_rate_layer/tax_rate_pct，其层必须与 tax_base 相容
      （L1_交易 税基不得挂 L2_调度 税率；T-031 调度税口径 1~3%，默认 2%）

tax_base 归并暂定，判定序 R-1~R-4 见 TDCA-RULING-L1SI199-AGENTDEF5-TAXBASE-001；⛔ 视为制度明文。
  R-1 单笔交易计税收费结算→L1_交易／R-2 配置权调度定价场景配置→L2_调度
  ／R-3 其余含跨层→双／R-4 判不准→双 记「暂定·待明」。

退出码: 0 = 全过 | 1 = 断言违例 | 2 = 用法/文件错误
输出仅依赖输入文件内容（无时间戳/环境读数），同输入两次运行输出一致。
NSFL-Declaration:
  - 只读校验，不修改任何源文件
SPDX-License-Identifier: TDCA-Internal
"""

import sys

import yaml

# B-1 时间型枚举（条例机读版 temporal_typing；「形式化离散」是时间窗概念，禁混用）
TEMPORALITY_ENUM = ("连续运行", "离散")

# B-2 来源枚举（条例机读版 genesis：原生 NATIVE / 非原生 NON_NATIVE，派生走再登记）
DERIVATION_SOURCE_ENUM = ("原生", "派生")

# B-3 使用方式枚举（被使用 / 非被使用；兼有者填被使用并在 note 记自运行面）
USAGE_MODE_ENUM = ("被使用", "非被使用")

# B-4 税基枚举（条例 tax 两层：L1 交易税 / L2 配置权调度税）
TAX_BASE_ENUM = ("L1_交易", "L2_调度", "双")

# T-031 在册口径：通用配置权调度税 1~3%（默认 2%）
T031_L2_RATE_MIN_PCT = 1.0
T031_L2_RATE_MAX_PCT = 3.0
T031_L2_RATE_DEFAULT_PCT = 2.0


def _failures(registry_path: str) -> "tuple[list[str], str | None]":
    """逐断言检查，返回 (违例列表, 错误信息)；错误信息非空表示文件/用法层错误。"""
    try:
        with open(registry_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return [], "文件不存在: %s" % registry_path
    except yaml.YAMLError as exc:
        return [], "YAML 解析失败: %s" % exc

    if not isinstance(data, dict) or not isinstance(data.get("agents"), list):
        return [], "结构错误: 顶层须为含 agents 列表的映射"

    fails = []
    seen = set()
    for idx, entry in enumerate(data["agents"]):
        name = entry.get("agent", "<第%d条>" % (idx + 1)) if isinstance(entry, dict) else "<第%d条>" % (idx + 1)
        if not isinstance(entry, dict):
            fails.append("[%s] 条目不是映射" % name)
            continue
        if entry.get("agent") in seen:
            fails.append("[%s] agent 名重复" % name)
        seen.add(entry.get("agent"))

        # ---- B-1 时间型枚举 ----
        temporality = entry.get("asset_temporality")
        if temporality not in TEMPORALITY_ENUM:
            fails.append(
                "[%s] B-1: asset_temporality=%r 不在枚举 %s（形式化时间窗之「离散」禁混用）"
                % (name, temporality, list(TEMPORALITY_ENUM)))

        # ---- B-2 派生来源自洽 ----
        derivation = entry.get("derivation")
        if not isinstance(derivation, dict):
            fails.append("[%s] B-2: derivation 缺失或非映射" % name)
        else:
            source = derivation.get("source")
            if source not in DERIVATION_SOURCE_ENUM:
                fails.append("[%s] B-2: derivation.source=%r 不在枚举 %s"
                             % (name, source, list(DERIVATION_SOURCE_ENUM)))
            if source == "派生":
                from_agent = derivation.get("from")
                if not from_agent:
                    fails.append("[%s] B-2: 派生来源 from 不得为空" % name)
                elif from_agent == entry.get("agent"):
                    fails.append("[%s] B-2: 派生来源 from=%r 自指（禁自派生）"
                                 % (name, from_agent))

        # ---- B-3 使用方式缺失即拒跑，不取默认 ----
        if "usage_mode" not in entry:
            fails.append("[%s] B-3: usage_mode 缺失——拒跑，禁止取默认" % name)
        else:
            usage_mode = entry.get("usage_mode")
            if usage_mode not in USAGE_MODE_ENUM:
                fails.append("[%s] B-3: usage_mode=%r 不在枚举 %s"
                             % (name, usage_mode, list(USAGE_MODE_ENUM)))

        # ---- B-4 税基与 T-031 税率口径不互抵 ----
        tax_base = entry.get("tax_base")
        if tax_base not in TAX_BASE_ENUM:
            fails.append("[%s] B-4: tax_base=%r 不在枚举 %s"
                         % (name, tax_base, list(TAX_BASE_ENUM)))
        if "tax_rate_layer" in entry or "tax_rate_pct" in entry:
            layer = entry.get("tax_rate_layer")
            pct = entry.get("tax_rate_pct")
            if layer == "L2_调度" and tax_base == "L1_交易":
                fails.append("[%s] B-4: tax_base=L1_交易 却挂 T-031 调度税率（互抵）"
                             % name)
            if layer == "L1_交易" and tax_base == "L2_调度":
                fails.append("[%s] B-4: tax_base=L2_调度 却挂 L1 交易税率（互抵）"
                             % name)
            if layer == "L2_调度" and isinstance(pct, (int, float)):
                if not (T031_L2_RATE_MIN_PCT <= pct <= T031_L2_RATE_MAX_PCT):
                    fails.append(
                        "[%s] B-4: L2_调度 税率 %s%% 越出 T-031 口径 1~3%%（默认 2%%）"
                        % (name, pct))

    return fails, None


def main(argv: list) -> int:
    if len(argv) != 2:
        print("用法: python agent_registry_validate.py <agent_registry.yaml>")
        return 2
    fails, err = _failures(argv[1])
    if err is not None:
        print("ERROR: %s" % err)
        return 2
    for line in fails:
        print("FAIL: %s" % line)
    if fails:
        print("共 %d 条违例" % len(fails))
        return 1
    print("PASS: agent_registry 四断言全过（B-1 时间型枚举 / B-2 派生自洽 / "
          "B-3 使用方式必填 / B-4 税基-T031 相容）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
