# {场景名称} 场景定价规则
# 版本: SCENE-PRICING-v1.0.0
# 关联 TDCA 定价: UPDA-v2.0
# ID92 模拟态标注: 本模板为可复制产物，不构成真实配置权执行路径

## 一、UPDA 兼容性声明

本场景定价规则**兼容 UPDA-v2.0 基础框架**（效用函数 U = f(IP, Knowledge, Exchange, Scenario_weight)），不改变 MOU 硬下限（进项+出项税收）。

## 二、场景定价维度扩展

```yaml
scene_pricing:
  base_framework: "UPDA-v2.0"
  extended_dimensions:
    - id: PRICE-001
      name: "{场景定价维度 1}"
      weight: "{权重 0~1}"
      description: "{维度说明}"
    - id: PRICE-002
      name: "{场景定价维度 2}"
      weight: "{权重 0~1}"
      description: "{维度说明}"
  mou_anchor:
    status: "Simulated"
    note: "真实税收锚定待 DCEP 接入（模拟态裁决 D-011）"
```

## 三、定价约束

- 场景定价不得低于 MOU 硬下限
- 场景定价维度不得引入零和博弈（ID77：禁止"标准授权费"）
- 定价调整需场景制度委员会签批并登记 NCA
