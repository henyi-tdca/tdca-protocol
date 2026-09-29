# TDCA 效用精灵（Utility Genie）

> **版本：** 1.0.0  
> **制度锚定：** 效用精灵九大能力, 协作停机定理, 函数隐喻四定律, NIA-MACM 3.0, MOU原理, MCT原理  
> **Function-Call-ID：** TDCA-FC-20260802-004

## 一、定位

效用精灵位于 **L3 效用计量层**，是连接"配置权调用"与"经济价值实现"的核心计算引擎。

```
工具链（合规性）: Token → NCA → MOU → Verify   （有没有做、做没做错）
效用精灵（质量与价值）: 正和求解 → 反函数 → 能力塑造 → 效用确认 （做得好不好、值不值得做）
```

## 二、四大功能

| 功能 | 类 | 制度锚定 | 回答的问题 |
|------|-----|---------|-----------|
| 正和满意解 | `PositiveSumSolver` | 停机定理 | 各方都满意的充分解是什么？ |
| 反函数求解 | `InverseFunctionSolver` | 反函数 | 给定效果目标，需要什么配置？ |
| 能力塑造 | `AgentCapabilityShaper` | 能力塑造 | 如何调整智能体的认知状态？ |
| 交付确认 | `ContractDeliveryValidator` | MOU+MCT | 合约执行是否达标且税收可验证？ |

## 三、安装与使用

```bash
cd tdca-utility-genie
pip install pyyaml
# 可选: pip install scipy sentence-transformers
```

```python
from tdca_utility_genie import TDCAUtilityGenie
from solvers.positive_sum_solver import Agent

genie = TDCAUtilityGenie()

# 功能A: 正和满意解
solution = genie.solve_positive_sum(
    participants=[Agent('A', 1.0), Agent('B', 1.0)],
    objective_functions=[lambda x: x*2, lambda x: x*2],
    constraint_matrix=[],
    reservation_utilities=[5.0, 5.0],
    time_budget=1.0,
)
```

## 四、与工具链集成

```
输入接口:
  FC-002 → Config-Right-Token (配置权边界)
  FC-001 → NCA 历史
  FC-003 → MOU 税收锚定

输出接口:
  求解过程 → 生成 NCA (FC-001)
  效用确认 → 生成 MOU (FC-003)
  能力塑造 → 生成 Token (FC-002)
```

## 五、NSFL 约束

- 效用精灵不替代人类价值判断，仅提供计算支持
- 满意解 ≠ 最优解，人类保有最终决策权
- 反函数求解超出配置权边界时熔断并上报
- 能力塑造需人类审批，不得强制修改智能体参数
- MOU 税收锚定是唯一硬验证标准
- 禁止用效用最大化替代制度约束

## 六、目录结构

```
tdca-utility-genie/
├── tdca_utility_genie.py           # 主类
├── solvers/                        # 求解器
│   ├── positive_sum_solver.py      #   正和满意解
│   └── inverse_function_solver.py  #   反函数
├── shapers/agent_capability_shaper.py  # 能力塑造
├── validators/contract_delivery_validator.py  # 交付确认
├── math_engines/                   # 数学引擎
│   ├── optimization_engine.py      #   优化 (模拟退火/NSGA-II简化)
│   ├── bayesian_engine.py          #   贝叶斯 (后验更新/EI)
│   └── game_theory_engine.py       #   博弈论 (Shapley/纳什/正和)
├── tests/                          # 单元测试 (覆盖率88%)
└── examples/                       # 示例
```
