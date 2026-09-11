# TDCA Adapters · 国标对接与身份管理适配层（Python）

> TDCA 协议能力面向**智能体互联国家标准体系（GB/Z 185 系列）与国际连接协议（MCP / A2A / ATH）**的适配层实现。
> 许可: Apache-2.0 ｜ 数据性质: 全部为**模拟态**（不构成真实注册/资金/税务操作）
> **版本: V1.3**（口径 A 版本化重推批次）— 与上一发布版相比：新增身份管理全链、配置权调用深化、交互对接深化与国标格式纠偏

## 模块概览

| 模块 | 职责 |
|---|---|
| `identity_bridge` | 身份桥接：范围外身份码（OID）与范围内身份（TDID）双向映射；映射即存证；失效同步 |
| `tool_call_right` | 场景配置权调用（S-Right）：185.7 三子流程 → 经济索引 / 边界变更事件（含**受影响调用方通知**）/ 14 步调用（CCV 五层 + 正和评估 + Shapley 分配 + **声明结构化** + 计税 + 存证）；`pcr_carrier` 令牌交换载体（进程内 / 文件 / 网络占位）；`settlement_bridge` 分配落地结算；`cli_transport` 工具调用通道（真实/计划态分流） |
| `national_format` | 国标格式输出：185.7 工具属性描述六字段 + 185.4 智能体描述（**字段名对齐国标原文**）+ 批量报送包与**入向解析**（外部文档接收）；制度属性以 `x-tdca-*` 前缀隔离（不破坏国标格式规范性，双向可逆） |
| `contract_interop` | 交互 × 合约 × 计税：185.6 三模式与**交互内容元素**（数据/消息/任务/会话）→ 交互日志（税收事件触发器）→ 合约族装配（条款核验）→ 结算（净额/定向支付）；群组/混合参与方权限与多角色隔离 |
| `inheritance` | 权益承接全链：遗嘱优先（可撤回重签）/ 沿创建链回退 / 遗产标的界定 / 存证永续 / 人类裁决兜底 / 承接计税 / 幂等防重 / **休眠态状态机** / **份额计算与争议流程** / **过渡期分润记账** / **无主权益托管（社区公共品）** / **身份链接失效同步** |
| `layer_interop` | 层间接口：A2A Agent Card ↔ 配置权发现（CDP）；ATH 令牌 → 配置权边界瞬时切片（非等价物，转调用权须经 CCV） |

## 依赖契约（可注入）

本层与 TDCA 侧组件解耦，**可通过注入自实现替代**：

| 契约 | 必需方法 | 说明 |
|---|---|---|
| NCA 生成器 | `generate(type, layer, content)->obj`（`obj` 含 `nca_id`/`seal`）、`verify_seal(obj)->bool`、`get(ref)->obj` | 存证层；**映射/调用/继承等行为无存证即拒绝**（fail-closed） |
| 正和引擎（可选） | `positive_sum_check(coalition, independents)->(bool, float)`、`shapley_value(participants, value_fn)->dict` | 不注入时使用内置同准则回退（结果中标注来源，不虚报）。**注意**：分配落地结算要求引擎的 Shapley 分配满足 **Σ分配 = 联盟总效用**；内置回退不满足该口径，结算场景请注入符合口径的引擎（否则按守恒校验明确拒绝） |
| 结算管线（可选） | `CLSTaxAdapter.compute_for_settlement(...)`、`CLSLedgerAdapter.record_settlement/aggregate_mou/total_settled`、`CLSNCAAdapter.from_settlement`、`CLSEngine`（netting 模式） | 分配落地结算与交互结算的记账/计税/存证；不注入时使用内置最小实现（**仅 direct 模式**；netting 须注入，否则明确报错） |
| 合约模板权威源（可选） | YAML 模板集（`contract_id`/`type`/`anchor`/`functions` 结构） | 合约族装配与条款核验的权威源；通过 `ContractFamily(templates_path=...)` 注入，默认在包外层目录查找同名文件（缺失则构造时明确报错） |

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

class MyEngine:                   # 符合结算守恒口径的正和/分配引擎示例
    from itertools import combinations
    from math import factorial
    def positive_sum_check(self, coalition, independents):
        d = coalition - sum(independents); return (d > 0, d)
    def shapley_value(self, participants, value_fn):
        n = len(participants); out = {}
        for p in participants:
            others = [q for q in participants if q != p]; s = 0.0
            for k in range(len(others) + 1):
                for sub in self.combinations(others, k):
                    S = set(sub)
                    w = self.factorial(k) * self.factorial(n - k - 1) / self.factorial(n)
                    s += w * (value_fn(S | {p}) - value_fn(S))
            out[p] = round(s, 6)
        return out
```

## 快速开始

```bash
# 将本目录及各模块目录加入 PYTHONPATH（各模块以平铺目录组织）
export PYTHONPATH=/path/to/tdca-adapters-public:/path/to/tdca-adapters-public/identity_bridge:$PYTHONPATH
# Windows: set PYTHONPATH=...

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
3. **字段名权威**：国标结构字段名与国标原文逐字一致，**不自造**；外部输入缺失即如实标注，不推测填补
4. **来源可信 ≠ 正和可信**：签名只证明来源；正和性须经效用评估（两个字段分离，不混淆）
5. **边界切片非等价物**：外部握手/令牌给出的是"能连、能谈什么"的瞬时切片；**转为调用权必须经 CCV 五层 + 正和评估**
6. **fail-closed**：无存证不建立映射 / 不授予调用 / 不执行承接；**未就绪即拒**（不虚报执行）
7. **人类兜底**：人类裁决事项由人类裁决登记，本层不代行；涉争议事项在取得**可验证正式文件**前不作处分
8. **守恒与可控**：分配落地结算须满足守恒（Σ分配 = 联盟总效用；Σ净额 + Σ税 = Σ分配；无负额）；结算须无自由转账、异常不中断

## 测试规格摘要

随包模块的完整测试在内部保留；用例覆盖摘要：
身份映射（双向解析/幂等/双冲突/格式校验/存证校验/失效同步/**主体消亡联动**/主键嵌入）· S-Right（三子流程/Token 五类拒绝/**交换载体三态**/CCV 五层/正和拒绝/预算/负空间/Shapley 分配/**分配落地结算守恒**/**声明结构化**/边界联动复查 + **调用方通知与确认**/MCP 映射计划 + **通道分流**）· 国标格式（六字段/智能体 15 字段/Schema 形态/前缀纪律/反向还原/必填 fail-closed/**批量报送与入向解析**）· 交互合约（三模式/**四内容元素**/幂等/日志即税触发/**合约族条款核验**/**群组与混合参与方权限**/**多角色隔离**/结算/**结算接管线**/熔断）· 继承（遗嘱+撤回/沿链回退/计税/幂等/争议裁决/处置三态/**休眠状态机**/**份额与争议流程**/**过渡期记账**/**无主权益托管**）· 层间（卡片兼容/来源与正和分离/令牌切片/会话不授予调用权/切片经 CCV）· 集成（身份→交互→调用→税收→格式→存证；单次共 160+ 用例全绿）。

## 版本记录

| 版本 | 变更 |
|---|---|
| **V1.3**（本版） | ①**国标格式纠偏**：185.4 智能体描述字段名与能力画像字段对齐国标原文（含 15 字段全集），新增批量报送包与入向解析；②**身份管理全链**：休眠状态机 / 份额与争议流程 / 过渡期记账 / 无主权益托管（社区公共品）/ 主体消亡与身份链接失效同步；③**配置权调用深化**：令牌交换载体、分配落地结算（守恒 + 不变量）、调用链步 3/6 结构化声明、工具调用通道（真实/计划态如实分流）、边界变更跨主体通知；④**交互对接深化**：185.6 交互内容元素完整映射、合约族装配与条款三态核验、群组/混合参与方权限与多角色隔离、结算接闭环管线 |
| V1.2 | 层间接口与国标格式首版；身份桥接与交互合约基础实现 |
| V1.0/V1.1 | 首个发布版（身份桥接 / S-Right / 国标格式 / 交互合约 / 继承最小实现 / 层间） |

## 装配口径

跨模块集成时**共享同一存证层实例**（单一 NCA 生成器），否则各模块存证彼此不可见。

---

*TDCA Adapters V1.3（模拟态）· Apache-2.0 —— 与任何外部标准组织/厂商无隶属或背书关系*
