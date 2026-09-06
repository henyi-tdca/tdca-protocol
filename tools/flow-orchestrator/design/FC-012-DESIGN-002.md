# TDCA-FC-012 9 Phase 状态机详细设计（C-2）

> **文档编号：** TDCA-FC-012-DESIGN-002  
> **版本：** V1.0  
> **编制：** TDCA 制度层  
> **前置：** TDCA-FC-012-PRES-001（预研框架，已归档）  
> **制度依据：** TDCA-FLOW-001、ID84（停机定理）、ID89（化学热力学）、ID71（快慢系统）、宪法十六条  
> **存证路径：** `.tdca-nca/nca/DEV-TASK-003-C2/`

---

## 一、状态机形式化定义

### 1.1 状态集合

```
S = { P0, P1, P2, P3, P4, P5, P6, P7, P8,        # 9 个 Phase
      FUSE,                                        # 熔断态（含子状态）
      COMPLETED,                                   # 完成态（终态）
      TERMINATED }                                 # 终止态（终态）
```

### 1.2 事件集合

```
E = { START, ADVANCE, FUSE, ROLLBACK, RETRY,
      HUMAN_APPROVE, HUMAN_REJECT, COMPLETE, TERMINATE }
```

### 1.3 状态转移函数 δ: S × E → S

```
δ(Pi, ADVANCE) = Pi+1     (条件满足时)
δ(Pi, FUSE)    = FUSE     (任意 Phase)
δ(FUSE, RETRY) = Pi       (软熔断重试，≤3次)
δ(FUSE, ROLLBACK) = Pj    (回退至指定 Phase，j < i)
δ(FUSE, HUMAN_REJECT) = TERMINATED
δ(P8, COMPLETE) = COMPLETED (人类签名 + MOU 闭环后)
```

---

## 二、逐 Phase 详细设计

### 2.1 P0 意图孕育（L5 H-H，最慢）

| 项 | 内容 |
|----|------|
| **目标** | 人类在人际网络形成协作意图共识 |
| **输入** | 参与者 DID 列表、连接权重、意图描述 |
| **穿越条件→P1** | ① 连接权重 > 0.5 ② 意图明确（非模糊需求）③ 无负空间触碰 |
| **熔断点** | 连接权重不足 / 意图模糊 / 触碰 ⊗ |
| **NCA-0** | 生成人际网络记录（参与者/共识哈希/原始意图） |
| **宪法锚定** | 第1条可观测性（意图必须可记录） |

### 2.2 P1 意图编译（L4 H-M，慢）

| 项 | 内容 |
|----|------|
| **目标** | 大模型（Protocolizer）将意图编译为六要素函数语料 |
| **输入** | 原始意图、场景上下文、私有资产库 |
| **处理** | FC-004A 编译器 + FC-004B 约束解释器（负空间检查） |
| **穿越条件→P2** | ① 六要素完成 ② 意图置信度 ≥ 0.7 ③ NSFL 通过 |
| **熔断点** | 六要素不完整 / 置信度不足 / 负空间触碰 |
| **NCA-1** | 六要素编译记录（FunctionSpec 快照） |
| **宪法锚定** | 第2条正和博弈（意图须正和） |

### 2.3 P2 协议编译（L2 M-L，快）

| 项 | 内容 |
|----|------|
| **目标** | 编译器将函数语料编译为可执行协议（IR） |
| **输入** | 六要素 FunctionSpec |
| **处理** | FC-004A（IR 生成 + 接口熵=0 验证）+ FC-002（Token 签发） |
| **穿越条件→P3** | ① constraints.failed 为空 ② Token 有效（FC-002 validate_token） |
| **熔断点** | 接口熵≠0 / Token 无效 / 硬约束失败 |
| **NCA-2** | IR 哈希 + Token 签发记录 |
| **宪法锚定** | 第6条配置权第三极（Token 边界） |

### 2.4 P3 沙盒验证（L3 H-L，中快）

| 项 | 内容 |
|----|------|
| **目标** | 人类在沙盒验证协议参数与约束合理性 |
| **输入** | IR 协议、约束矩阵、沙盒参数 |
| **处理** | FC-004B（约束解释）+ FC-003A（MOU 预估）+ 反函数求解（FC-004） |
| **穿越条件→P4** | ① 沙盒验证通过 ② 正和博弈验证（ΔU≥0） |
| **熔断点** | 沙盒失败 / 正和未通过 |
| **NCA-3** | 沙盒验证报告（参数/约束/正和结果） |
| **宪法锚定** | 第5条负空间保护（沙盒隔离） |

### 2.5 P4 节点锚定（L1 L-L，最快）

| 项 | 内容 |
|----|------|
| **目标** | 智能体与物理通知机硬件绑定 |
| **输入** | 节点申请、PUF 指纹、四元绑定信息 |
| **处理** | 通知机硬件接口（PUF 采集 + TDID 签发） |
| **穿越条件→P5** | ① PUF 绑定完成 ② 四元绑定（地址-线路-硬件-主体） |
| **熔断点** | PUF 校验失败 / 四元绑定冲突 |
| **NCA-4** | 节点锚定记录（TDID/PUF/四元绑定） |
| **宪法锚定** | 第5条负空间保护（硬件可信根） |

### 2.6 P5 上链确权（L1 L-L，最快）

| 项 | 内容 |
|----|------|
| **目标** | 版权资产写入区块链完成确权 |
| **输入** | 版权资产元数据、创作者 DID |
| **处理** | TDCA 链存证合约 + 国家可信版权链对接 |
| **穿越条件→P6** | ① 版权确权完成 ② NCA 存证上链 |
| **熔断点** | 确权失败 / 存证冲突 |
| **NCA-5** | 版权确权凭证（链上哈希） |
| **宪法锚定** | 第6条配置权第三极（确权登记） |

### 2.7 P6 接口发布（L1 L-L，最快）

| 项 | 内容 |
|----|------|
| **目标** | 智能体向协议网络发布可调用接口 |
| **输入** | 函数签名、配置权声明、定价 |
| **处理** | FC-001（NCA 生成）+ FC-002（配置权上架） |
| **穿越条件→P7** | ① 接口注册成功 ② 网络广播完成 |
| **熔断点** | 接口冲突 / 配置权边界模糊 |
| **NCA-6** | 接口发布记录（函数签名 + 配置权） |
| **宪法锚定** | 第6条配置权第三极（接口上架） |

### 2.8 P7 正和求解（L1 L-L，最快）

| 项 | 内容 |
|----|------|
| **目标** | 多智能体自动寻求正和满意解 |
| **输入** | 参与者、目标函数、约束矩阵、保留效用 |
| **处理** | FC-004 效用精灵 PositiveSumSolver |
| **穿越条件→P8** | ① ERI > CCI（正和）② 满意解存在（ID84） |
| **熔断点** | 负和 / 无满意解（触发反函数重求解） |
| **NCA-7** | 正和求解记录（ERI/CCI/Shapley 分配） |
| **宪法锚定** | 第2条正和博弈（ERI>CCI） |

### 2.9 P8 智能合约交付（L1 L-L，最快）

| 项 | 内容 |
|----|------|
| **目标** | 数字人民币智能合约执行交付 + MOU 税收锚定 |
| **输入** | 交付结果、实际税收数据、人类签名 |
| **处理** | FC-003A（MOU 记录）+ 数字人民币智能合约 + ID70/MCT |
| **穿越条件→COMPLETED** | ① MOU 闭环（Tax_in + Tax_out > 0）② 人类最终签名 |
| **熔断点** | MOU 未闭环 / 人类拒绝签名 |
| **NCA-8** | 交付确认 + MOU 锚定记录 |
| **宪法锚定** | 第3条自证清白（MOU 闭环）+ 第4条人类签名权 |

---

## 三、状态转移矩阵（完整版）

```
           事件:  ADVANCE  FUSE   RETRY  ROLLBACK  HUMAN_APPROVE  HUMAN_REJECT  COMPLETE  TERMINATE
当前状态
P0            P1      FUSE    —      —        —            —           —          —
P1            P2      FUSE    —      P0       —            —           —          —
P2            P3      FUSE    —      P1       —            —           —          —
P3            P4      FUSE    —      P2       —            —           —          —
P4            P5      FUSE    —      P3       —            —           —          —
P5            P6      FUSE    —      P4       —            —           —          —
P6            P7      FUSE    —      P5       —            —           —          —
P7            P8      FUSE    —      P6       —            —           —          —
P8            —       FUSE    —      P7       COMPLETED     —           —          —
FUSE(Level-1)  —       —       Pi     Pj       —            TERMINATED  —          —
FUSE(Level-2)  —       —       —      Pj(≤3)   —            TERMINATED  —          —
FUSE(Level-3)  —       —       —      —        —            TERMINATED  —          —
COMPLETED      —       —       —      —        —            —           —          —
TERMINATED     —       —       —      —        —            —           —          —
```

---

## 四、数据模型定义

### 4.1 FlowState

```python
class FlowState:
    flow_id: str              # 生命周期唯一 ID
    phase: str                # 当前 Phase（P0-P8/FUSE/COMPLETED/TERMINATED）
    phase_seq: list           # 已完成的 Phase 序列
    nca_records: list         # 每 Phase 生成的 NCA
    context: dict             # 全流程上下文（六要素/参数/结果）
    fuse_history: list        # 熔断历史
    created_at: str
    updated_at: str
```

### 4.2 PhaseTransition（穿越条件）

```python
class PhaseTransition:
    from_phase: str
    to_phase: str
    conditions: list           # 条件检查函数列表
    fuse_level: str            # 不满足时熔断级别
    requires_human: bool       # 是否需人类确认
```

---

## 五、宪法十六条 → Phase 映射（LIM-FC012-001 补充）

| 宪法条款 | 内容 | 映射 Phase |
|---------|------|-----------|
| 第1条 | 可观测性 | P0~P8（每阶段生成 NCA） |
| 第2条 | 正和博弈 | P1/P7（ERI>CCI 验证） |
| 第3条 | 自证清白 | P8（MOU 闭环验证） |
| 第4条 | 人类最终签名权 | P8→COMPLETED |
| 第5条 | 负空间保护 | P1/P3/P4（Level-2/3 熔断） |
| 第6条 | 配置权第三极 | P2/P5/P6（Token/确权/上架） |
| 第7~16条 | 其余条款 | 按 Phase 上下文动态锚定 |

---

## 六、C-3 原型实现接口预留

```
tdca-flow-orchestrator/src/phase_machine.py:
  class PhaseMachine:
    def __init__(self):         # 加载状态转移表 + 穿越条件
    def transition(self, state, event, context) -> (new_state, nca_record, fuse)
    def get_conditions(self, from_phase, to_phase) -> list

tdca-flow-orchestrator/src/flow_engine.py:
  class FlowEngine:
    def start(self, intent) -> FlowState
    def advance(self, context) -> FlowState
    def fuse(self, reason, level) -> FlowState
    def rollback(self, target_phase) -> FlowState
    def trajectory(self) -> list
```

---

## 七、设计结论

1. **状态机完备**：9 Phase + FUSE + COMPLETED + TERMINATED 共 12 状态，8 类事件，转移矩阵完整
2. **宪法锚定**：16 条宪法已映射至各 Phase（LIM-FC012-001 补充落实）
3. **熔断体系**：Level-1/2/3 三档（ID89），RETRY/ROLLBACK/TERMINATE 三退出路径
4. **ID70/MCT**：P8 数字人民币锚定已补充（LIM-FC012-002）
5. **可编码**：PhaseMachine/FlowEngine 接口已预留，可直接进入 C-3 原型

---

> **本文件：** 设计文档（归档件对应版）  
> **存证路径：** `.tdca-nca/nca/DEV-TASK-003-C2/`
