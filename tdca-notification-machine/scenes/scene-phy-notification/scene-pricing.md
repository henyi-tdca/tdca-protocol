# 通知机物理锚点场景定价（scene-phy-notification）
# 版本: SCENE-PRICING-v1.0.0
# 关联: CALL-RULES V1.2（TaxRates 三档：调度税 2%/版税 7.5%/交易费 0.75%）
# 交付: 通知机规范包（层 3 场景化合，FC-SPEC §4）
# 模拟态标注: 模拟态 D-011 cbdc_anchor 参数；真实 DCEP 接入后转硬数据；通知机硬件未投产部署，本场景为 SIL 模拟

## 一、硬件调用类型 → 计量映射（FC-SPEC §4.1）

| 硬件调用 | 调用类型 | 计量依据 | 税收（L3） |
|---------|---------|---------|-----------|
| 事实哈希上链 | 日抛调用（DISPOSABLE） | 物理叠加通道 | 调度税 1-3%（模拟 2%） |
| 通话确权（商务确认函） | 化合调用（COMPOUND） | NCA 化合产物 | 调度税 + 版税 5-10%（模拟 7.5%） |
| 跨节点迁移（TIMA-PHY-001） | 化合调用（COMPOUND） | 化合产物 | 调度税 + 版税 |
| 节点认证/品类认证 | 服务调用（L2） | 年度合同 | 服务费（模拟 5%） |

## 二、MOU 归零规则

- 硬件调用的可验证税收锚定 `T(y_t) > 0` 才有效（模拟态 D-011）
- T(y_t) ≤ 0 → 调用价格强制归零（与 CALL-RULES `validate_mou` 一致）
- 数字人民币硬件钱包：自动扣缴配置权调度税（白皮书 M3 里程碑，真实 DCEP 后转硬数据）

## 三、定价参数快照（config/call-rules.json 同步）

```yaml
call_rules_snapshot:
  dispatch_tax: 0.02      # 调度税（模拟态，D-010 校准后转真实）
  royalty: 0.075          # 版税（模拟态）
  transaction_fee: 0.0075 # 交易费（模拟态）
  service_fee: 0.05       # L2 服务费（模拟态）
  mou_mode: "simulated"   # D-011
  nsfl_version: "V0.2"
```
