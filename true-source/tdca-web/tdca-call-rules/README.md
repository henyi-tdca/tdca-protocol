# TDCA 商业调用规则（tdca-call-rules/）

> 依据: TDCA-PRICING-001-V1.0（定价原则，人类已确认）+ TDCA-PRINCIPLE-ENG-010（运行原理，人类已确认）
> 状态: V1.0 待人类签批 | NCA: TDCA-NCA-20260811-008-CALL-RULES

## 内容

| 路径 | 说明 |
|------|------|
| `TDCA-CALL-001-商业调用规则.md` | 规则主文档（六要素 + 调用类型/定价/验证/流程/税收/审计） |
| `engine/call_rules_engine.py` | 可执行规则引擎（日抛判定 / MOU 归零 / 正和验证 / L3 税收计算） |
| `tests/test_call_rules.py` | 8 用例（8/8 全绿） |

## 快速使用

```bash
# 日抛调用（物理叠加可覆盖）
python engine/call_rules_engine.py --caller u1 --scene s1 --value 1000 --tax 200

# 化合调用（物理叠加不可覆盖，触发三条件后）
python engine/call_rules_engine.py --caller u1 --scene s1 --value 1000 --tax 200 --no-stack

# MOU 归零演示（T(y_t) <= 0）
python engine/call_rules_engine.py --caller u1 --scene s1 --value 1000 --tax 0

# 负空间熔断演示
python engine/call_rules_engine.py --caller u1 --scene s1 --value 1000 --tax 200 --violates-nsfl
```

## 核心规则速览

- **日抛优先**：物理叠加可覆盖 → 日抛；不可 → 化合（三条件全过）
- **MOU 归零**：T(y_t) ≤ 0 → 配置权价格强制归零（数据源模拟态，待 DCEP 回填）
- **L3 税收**（PRICING-001）：调度税 1-3%（默认 2% 中点）+ 版税 5-10%（默认 7.5% 中点，可经 ERI/CCI 调节）+ 手续费 0.5-1%（默认 0.75% 中点）
- **模拟态**：税收为模拟计算，真实 DCEP 接入后转硬数据

## 兼容性矩阵（版本锁定）

| 依赖 | 最低版本 |
|------|---------|
| TDCA-DUAL-PROTOCOL-001 | ≥ V1.0（化合产物 dual-nca.json 为调用标的） |
| TDCA-PACK-001 | ≥ V1.3（六要素模板为调用前置） |

> 联动闭环: dual_protocol_compiler.py（002）→ call_rules_engine.py（003）→ nca_generator.py（002）→ MOU-Anchor 回写

> 关联: TDCA-DUAL-PROTOCOL-001（双协议架构包）+ TDCA-PACK-001（单协议基础包）
