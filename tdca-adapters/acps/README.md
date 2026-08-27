# tdca-acps-adapter · TDCA × ACPs 制度层适配器

> 样板 1（TDCA-ADAPTER-001 SOP）：ACPs（AIP-PUB，北邮/电子标准院，GB/Z 185-2026 配套）→ TDCA 配置权坐标 + NCA 存证 + 可信交付/结算层
> 定位: 独立 Apache-2.0 组件（**不复制上游代码**，仅协议层对接 ACPs 公开接口契约）
> 上游 License: **Mulan PSL v2（宽松许可，合规 ✅）**——GitHub API 标 NOASSERTION 为检测未识别，非真实许可
> 接口契约: ACPs 九协议（AIC 身份码 / ACS 能力描述 / ADP 发现 / AIP 交互）；acps_sdk 模块 aic/acs/adp/aip

## 功能

| 模块 | 功能 | TDCA 映射 |
|---|---|---|
| `mapper.py` | AIC→配置权坐标；ACS→效用函数描述 | ID81 五元拓扑 / 单一场景效用函数 |
| `adapter.py` | `allocate()` 配置权调用（替代简单发现） | ID24 效用精灵 |
| `positivesum.py` | 正和博弈验证（调用正和→放行） | ID24/正和验证 |
| `nca.py` | NCA 六要素生成（目标/约束/先验/边界/分配/审计） | ID56/68 |
| `nsfl.py` | 负空间清单检查 + 熔断（BLOCK/PASS） | ID85/86 |
| `mou.py` | MOU 税收锚定记账（模拟态，无真实现金流） | ID79 |

## 使用

```python
from tdca_acps_adapter import TdcaAcpsAdapter

adapter = TdcaAcpsAdapter(negative_space=["违法工具", "歧视性服务"])
result = adapter.full_pipeline(
    task="查询可用的代码分析智能体",
    capability_tags=["code-analysis", "dependency-check"],
    aic="1.2.156.123456.789",
)
# result.nca / result.positive_sum / result.mou / result.coordinate
```

## 合规与纪律

- 只赋能不改码：不修改 ACPs 任何源码
- 不复制上游代码：数据结构为本包自建最小类型（基于公开协议规范）
- 分润模拟态：MOU 记账无真实现金流（ID92）
- License: Apache-2.0（本包）
