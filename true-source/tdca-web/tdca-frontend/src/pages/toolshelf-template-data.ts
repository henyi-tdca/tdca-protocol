// TPL-FIX-001 段B/段D + TPL-FIX-D-001：模板区指路数据（单一数据源，内容逐字取自公开包 tdca-templates-v1.0.zip）
// 口径：只指路＋包下载链接；治理记录 12 份允许展开正文（筛单 12/12 通过，包哈希 B318A3A827E5D317）
// SPDX-License-Identifier: TDCA-Internal

export const TPL_PACKAGE = {
  name: 'tdca-templates-v1.0.zip',
  href: '/downloads/tdca-templates-v1.0.zip',
} as const

export const CONTRACT_TEMPLATES = [
  {
    name: 'TDCA-CONTRACTS-TEMPLATES-001-智能合约模板集公开页草案',
    purpose: '智能合约模板集公开页草案：宪法条款与经济模型编码为合约硬约束的规范模板（制度即代码）',
    path: 'tdca-templates-v1.0/contracts/TDCA-CONTRACTS-TEMPLATES-001-智能合约模板集公开页草案.md',
  },
  {
    name: 'contract-templates-v1.0',
    purpose: '合约模板集机读件（CONST-ENFORCE-001 宪法强制执行等 C01-C16 映射表）',
    path: 'tdca-templates-v1.0/contracts/contract-templates-v1.0.yaml',
  },
  {
    name: 'copyright-event-templates-v1.0',
    purpose: '版权事件模板（权属登记事件＝登记／变更／注销；期一内部运行，SIMULATED 硬标注）',
    path: 'tdca-templates-v1.0/contracts/copyright-event-templates-v1.0.yaml',
  },
] as const

export const SIX_ELEMENTS_TEMPLATES = [
  {
    name: 'six-elements-template',
    purpose: '六要素标准模板（L1 通用开发六要素声明：目标函数／约束矩阵／先验分布／配置权边界／预期分配／审计轨迹）',
    path: 'tdca-templates-v1.0/six-elements/six-elements-template.md',
  },
] as const

// TPL-FIX-D-001 须随件标示（一句·逐字）
export const GOV_REC_NOTICE =
  '下列 12 份为通用记录模板（字段占位＋必填标注），示例号为通用形式；使用时请替换为实际记录号与存证号。'

export interface GovRecord { code: string; file: string; path: string; content: string }
export const GOV_RECORDS: GovRecord[] = [
  {
    code: 'GK-01 试验门记录模板',
    file: 'gk-01-trial.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-01-trial.yaml',
    content: `# GK-01 试验门记录模板（独立版）——必填字段标注 [R]
trial_id: TRIAL-2026-0001          # [R] 试验记录号
new_capability: ""                # [R] 新能力名称
objective: ""                     # [R] 目标一句话
core_hypothesis: ""               # [R] 核心假设（可证伪表述）
falsification_criterion: ""       # [R] 可证伪判据：出现 X 证据即证伪
sandbox_scope: ""                 # [R] 隔离范围/模拟数据
precheck:
  coalition_feasible: ""          # [R] 合作可行性（各成员收益≥保留收益）：PASS/FAIL
  negative_space: ""              # [R] 负空间检查：未触/触发
trial_data:
  run_summary: ""                 # [R] 试跑摘要
  observations: []                # 关键观察（如实，含失败）
verdict: ""                       # [R] 证伪→否决或重构｜证实→进入灰度门
conclusion: ""                    # 结论与依据
record_ref: ""                    # [R] 存证号（无存证=未试验）
data_provenance: ""               # [R] real / simulated 如实
`,
  },
  {
    code: 'GK-02 灰度门记录模板',
    file: 'gk-02-canary.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-02-canary.yaml',
    content: `# GK-02 灰度门记录模板（独立版）——必填字段标注 [R]
canary_id: CANARY-2026-0001       # [R] 灰度记录号
change: ""                        # [R] 变更内容
risk_tier: ""                     # [R] 低/中/高
canary_params:                    # [R]
  ratio_start: 0.05               # [R] 起始比例
  observe_days: 7                 # [R] 观察期（天）
  rollback_condition: ""          # [R] 回滚条件
observe_data:                     # 观察期指标数据
  metric: ""                      # 指标名
  value: ""                       # 实测值
result: ""                        # [R] 达标放量（含终比例）/ 回滚（含原因）
record_ref: ""                    # [R] 存证号（无存证=未灰度）
data_provenance: ""               # [R] real / simulated 如实
`,
  },
  {
    code: 'GK-03 可靠性检查单记录模板',
    file: 'gk-03-reliability.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-03-reliability.yaml',
    content: `# GK-03 可靠性检查单记录模板（独立版）——必填字段标注 [R]
reliability_check: RELIABILITY-2026-0001  # [R] 检查单号
system: ""                        # [R] 受检系统
checks:                           # [R] 三查 9 项（通过/N-A/未过）
  redundancy:
    backup_path: ""               # 查1-① 关键路径备选
    dual_record: ""               # 查1-② 双副本冗余
    data_restore: ""              # 查1-③ 数据备份/恢复
  circuit_breaker:
    condition_defined: ""         # 查2-① 熔断条件定义
    fail_closed: ""               # 查2-② 熔断 fail-closed
    recovery_path: ""             # 查2-③ 恢复/重试路径
  fail_closed:
    unregistered_rejected: ""     # 查3-① 未注册默认拒绝
    no_record_not_done: ""        # 查3-② 无存证视为未发生
    insufficient_denied: ""       # 查3-③ 权限不足拒绝
verdict: ""                       # [R] 可上线 / 不可上线（含未过项）
record_ref: ""                    # [R] 存证号（无存证=未检查）
`,
  },
  {
    code: 'GK-04 统一结算记录模板',
    file: 'gk-04-settlement.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-04-settlement.yaml',
    content: `# GK-04 统一结算记录模板（独立版）——必填字段标注 [R]
settlement: SETTLE-2026-0001      # [R] 结算记录号
transaction: ""                   # [R] 交易标识
fee: 0                            # [R] 服务费
pools:                            # [R] 三池分流
  infra: 0                        # 基础设施池
  creator: 0                      # 贡献者分成池
  reserve: 0                      # 治理储备池
record_ref: ""                    # [R] 存证号
data_provenance: ""               # [R] simulated / real 如实（模拟态：不产生现金）
`,
  },
  {
    code: 'GK-05 效用归零记录模板',
    file: 'gk-05-mouzero.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-05-mouzero.yaml',
    content: `# GK-05 效用归零记录模板（独立版）——必填字段标注 [R]
mouzero: MOUZERO-2026-0001        # [R] 归零记录号
event: ""                         # [R] 调用/协作标识
utility_anchor: 0                 # [R] 0=归零 / >0=确认（地板信号，非效用近似）
breaker_triggered: false          # [R] 熔断触发
fee_charged: 0                    # [R] 0=不收费 / 正常
meter_log_written: false          # 是否入有效账本（归零=不入，仅审计存证）
record_ref: ""                    # [R] 存证号（无存证=未处置）
data_provenance: ""               # [R] simulated / real 如实
`,
  },
  {
    code: 'GK-06 快慢双层记录模板',
    file: 'gk-06-fastslow.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-06-fastslow.yaml',
    content: `# GK-06 快慢双层记录模板（独立版）——必填字段标注 [R]
fastslow: FASTSLOW-2026-0001      # [R] 记录号
auto_handled: []                  # [R] 自动层处理项
escalated:                        # 上报人工项
  case: ""                        # 情形
  evidence_pack: ""               # 证据包（触发记录/指标/存证）
human_ruling: ""                  # 人工裁决结果（回写规则）
record_ref: ""                    # [R] 存证号
`,
  },
  {
    code: 'GK-07 运维分级记录模板',
    file: 'gk-07-ops.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-07-ops.yaml',
    content: `# GK-07 运维分级处置记录模板（独立版）——必填字段标注 [R]
ops_entry: OPS-2026-0001          # [R] 处置记录号
source: ""                        # [R] 自动观察/哨兵/人工巡查
finding: ""                       # [R] 观察项 + 实测值/状态
tier: ""                          # [R] 🔴/🟡/🟢
disposition: ""                   # [R] 升级负责人/登记待办/复核修正
record_ref: ""                    # [R] 存证号（无存证=未处置）
data_provenance: ""               # [R] real / simulated 如实
`,
  },
  {
    code: 'GK-08 优化周快照记录模板',
    file: 'gk-08-weekly.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-08-weekly.yaml',
    content: `# GK-08 优化周快照记录模板（独立版）——必填字段标注 [R]
weekly_snapshot: WS-36-2026       # [R] 快照号（ISO 周）
utility_anchor_rate: ""           # [R] 效用锚定率（值+环比）
test_green: ""                    # [R] 测试健康
dual_consistent: ""               # [R] 双副本一致（哈希对拍）
record_closure_rate: ""           # [R] 存证闭环率
ecosystem_activity: ""            # [R] 生态活跃（趋势，如实）
below_target: []                  # [R] 未达标清单（指标+gap+处置）
record_ref: ""                    # [R] 存证号（无存证=未观察）
`,
  },
  {
    code: 'GK-09 创新双通道记录模板',
    file: 'gk-09-innovation.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-09-innovation.yaml',
    content: `# GK-09 创新双通道提案模板（独立版）——必填字段标注 [R]
innovation_id: INNOV-2026-0001    # [R] 提案号
channel: ""                       # [R] innovation / micro-innovation
title: ""                         # [R] 提案标题
task_statement:                   # [R] 任务声明
  objective: ""                   # 目标
  constraint: ""                  # 约束
  prior: ""                       # 先验
  config_boundary: ""             # 边界
  allocation: ""                  # 预期分配
  audit: ""                       # 审计轨迹
falsification_prediction: ""      # [R] 证伪预判
minimalism_check: ""              # [R] 已有成熟方案？复用/新建
negative_space_check: ""          # [R] 未触 / 触发（触发即否决）
risk_tier: ""                     # [R] 低/中/高
record_ref: ""                    # [R] 存证号
`,
  },
  {
    code: 'GK-10 零自研对接记录模板',
    file: 'gk-10-stack.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-10-stack.yaml',
    content: `# GK-10 零自研对接记录模板（独立版）——必填字段标注 [R]
stack_item: STACK-2026-0001       # [R] 对接记录号
need: ""                          # [R] 需求
solution: ""                      # [R] 现成方案
mode: ""                          # [R] 调用/配置/复用
zero_selfbuild: true              # [R] 零自研声明
record_ref: ""                    # [R] 存证号（无存证不交付）
`,
  },
  {
    code: 'GK-11 编排闭环记录模板',
    file: 'gk-11-orch.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-11-orch.yaml',
    content: `# GK-11 编排闭环记录模板（独立版）——必填字段标注 [R]
orch_task: ORCH-2026-0001         # [R] 任务号
dispatch:                         # [R]
  instruction: ""                 # 指令（落盘）
  record_ref: ""                  # 分发存证
executor: ""                      # [R] 施工方/发布方
execution:                        # [R]
  deliverables: []                # 交付物清单
  data_provenance: ""             # 数据性质（real/simulated）
verification:                     # 审核结论（制度层）
  verdict: ""                     # 通过/退回
record_chain: []                  # [R] [分发, 交付物, 审核]
status: ""                        # [R] closed / pending（fail-closed：未全存证=未完成）
`,
  },
  {
    code: 'GK-12 三重门全链记录模板',
    file: 'gk-12-gatechain.yaml',
    path: 'tdca-templates-v1.0/gov-kit/templates/gk-12-gatechain.yaml',
    content: `# GK-12 三重门全链记录模板（独立版）——必填字段标注 [R]
gate_chain: GATECHAIN-2026-0001   # [R] 全链记录号
change: ""                        # [R] 变更内容
gates:                            # [R] 三门（缺一即不上线）
  trial:
    status: ""                    # PASS/FAIL
    record_ref: ""                # TRIAL 存证
  canary:
    status: ""                    # PASS/ROLLBACK
    record_ref: ""                # CANARY 存证
  reliability:
    status: ""                    # PASS(8/9+)/FAIL
    record_ref: ""                # RELIABILITY 存证
verdict: ""                       # [R] 全量放行/否决/回滚
record_ref: ""                    # [R] 全链收口存证
`,
  },
]
