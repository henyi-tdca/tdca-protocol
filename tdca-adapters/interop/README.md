# TDCA Adapters · 国标对接与身份管理适配层（Python）

> TDCA 协议能力面向**智能体互联国家标准体系（GB/Z 185 系列）与国际连接协议（MCP / A2A / ATH）**的适配层实现。
> 许可: Apache-2.0 ｜ 数据性质: 全部为**模拟态**（不构成真实注册/资金/税务操作）

## 模块概览

| 模块 | 职责 |
|---|---|
| `identity_bridge` | 身份桥接：范围外身份码（OID）与范围内身份（TDID）双向映射；映射即存证；失效同步 |
| `tool_call_right` | 场景配置权调用（S-Right）：185.7 三子流程 → 经济索引 / 边界变更事件 / 14 步调用（CCV 五层 + 正和评估 + Shapley 分配 + 计税 + 存证） |
| `national_format` | 国标格式输出：185.7 工具属性描述六字段 + 185.4 智能体描述；制度属性以 `x-tdca-*` 前缀隔离（不破坏国标格式规范性，双向可逆） |
| `contract_interop` | 交互 × 合约 × 计税：185.6 三模式交互 → 交互日志（税收事件触发器）→ 合约调用意图 → 结算；幂等/熔断 |
| `inheritance` | 权益承接：遗嘱优先（可撤回重签）/ 沿创建链回退 / 遗产标的界定 / 存证永续 / 人类裁决兜底 / 承接计税 / 幂等防重 |
| `layer_interop` | 层间接口：A2A Agent Card ↔ 配置权发现（CDP）；ATH 令牌 → 配置权边界瞬时切片（非等价物，转调用权须经 CCV） |

## 依赖契约（可注入）

本层与 TDCA 侧两个组件解耦，**可通过注入自实现替代**：

| 契约 | 必需方法 | 说明 |
|---|---|---|
| NCA 生成器 | `generate(type, layer, content)->obj`（`obj` 含 `nca_id`/`seal`）、`verify_seal(obj)->bool`、`get(ref)->obj` | 存证层；**映射/调用/继承等行为无存证即拒绝**（fail-closed） |
| 正和引擎（可选） | `positive_sum_check(coalition, independents)->(bool, float)`、`shapley_value(participants, value_fn)->dict` | 不注入时使用内置同准则回退（结果中标注来源，不虚报） |

```python
class MyNCA:                      # 最小适配示例
    def __init__(self): self.db = {}
    def generate(self, type, layer, content):
        import uuid
        nca = type("N", (), {"nca_id": f"NCA-{uuid.uuid4().hex[:12]}", "seal": "..."} )()
        self.db[nca.nca_id] = nca
        return nca
    def verify_seal(self, nca): return True
    def get(self, ref): return self.db.get(ref)

class MyEngine:
    def positive_sum_check(self, coalition, independents):
        d = coalition - sum(independents); return (d > 0, d)
    def shapley_value(self, participants, value_fn):
        n = len(participants); return {p: value_fn({p}) / n for p in participants}
```

## 快速开始

```bash
# 将本目录加入 PYTHONPATH（各模块以平铺目录组织）
export PYTHONPATH=/path/to/tdca-adapters-public:$PYTHONPATH   # Windows: set PYTHONPATH=...

python - <<'PY'
import sys; sys.path.insert(0, "identity_bridge")     # 依模块逐一加入
from identity_bridge import IdentityBridge
b = IdentityBridge(nca_generator=MyNCA())
link = b.link("TDID-<32位大写十六进制>", "1.2.156.<arc>.<arc>.<arc>")
print(link.status, link.nca_ref)
PY
```

## 设计纪律（本层核心）

1. **模拟态标注**：所有输出显式标注 `simulated`；不构成真实注册/资金/税务操作
2. **前缀隔离**：嵌入国标结构时，本体系扩展字段一律 `x-tdca-*` 前缀（保持国标字段纯度，双向可逆）
3. **来源可信 ≠ 正和可信**：签名只证明来源；正和性须经效用评估（两个字段分离，不混淆）
4. **边界切片非等价物**：外部握手/令牌给出的是"能连、能谈什么"的瞬时切片；**转为调用权必须经 CCV 五层 + 正和评估**
5. **fail-closed**：无存证不建立映射 / 不授予调用 / 不执行承接
6. **人类兜底**：人类裁决事项由人类裁决登记，本层不代行

## 测试规格摘要

随包模块的完整测试（80 用例）在内部保留；用例覆盖摘要：
身份映射（双向解析/幂等/双冲突/格式校验/存证校验/失效同步/主键嵌入）· S-Right（三子流程/Token 五类拒绝/CCV 五层/正和拒绝/预算/负空间/Shapley 分配/边界联动复查/MCP 映射计划）· 国标格式（六字段/Schema 形态/前缀纪律/反向还原/必填 fail-closed）· 交互合约（三模式/幂等/日志即税触发/结算/熔断）· 继承（遗嘱+撤回/沿链回退/计税/幂等/争议裁决/处置三态）· 层间（卡片兼容/来源与正和分离/令牌切片/会话不授予调用权/切片经 CCV）· 全链路集成（身份→交互→调用→税收→格式→存证）。

## 装配口径

跨模块集成时**共享同一存证层实例**（单一 NCA 生成器），否则各模块存证彼此不可见。

---
*TDCA Adapters（模拟态）· Apache-2.0 —— 与任何外部标准组织/厂商无隶属或背书关系*
