# TDCA-HANDOFF-KIMI-ECOSCAN-COMMENT-M1-001 · Kimi 施工指令：ecoscan 评论模式 M1

> 文档编号: TDCA-HANDOFF-KIMI-ECOSCAN-COMMENT-M1-001 ｜ 编制: 2026-08-28（Reasonix 制度层）｜ 状态: ✅ **已下令**（创始人批准 DCD-ECOSCAN-COMMENT-001）
> 依据: DCD-ECOSCAN-COMMENT-001（已批准）｜ TDCA-COMMENT-INVITE-001（话术模板）
> 存证: GSEQ-0598

---

## M1 施工（模式扩展）

对 `tdca-ecoscan` inviter 模块新增 **Comment 评论模式**（discussion 模式零改动）：

| 项 | 内容 |
|---|---|
| ① comment 路径 | `POST /repos/{owner}/{repo}/issues/{n}/comments`（他人仓评论，无需目标仓权限） |
| ② 话术接入 | 对接 TDCA-COMMENT-INVITE-001 三段式模板（500 字，逐目标定制诊断段） |
| ③ ECOACT 存证 | **每条评论前强制 NCA-ECOACT 七字段存证（fail-closed，无存证不发送）** |
| ④ 频率闸 | ≤2 条/周/目标（评论=触达计数，超限拒绝） |
| ⑤ 台账 | 评论记录（repo_full/issue_n/url/时间/response_status）回填 ledger |
| ⑥ 测试 | ≥10 用例（评论发送/频率闸/存证前置/无 token 拒绝/500 字校验） |

## M2 试点（待触发）

- **依赖**：8-31 09:17 巡查诊断 → 目标清单 → **创始人批准** → 2-3 目标实发
- 本指令不包含 M2 试点执行（目标未定）

## 纪律（红线不变）

- 无敏感词 ｜ 算力零提及 ｜ 分润模拟态（15% NCA 记账）｜ 不点名 ｜ 只赋能不改码 ｜ 明确拒绝即停止
- 评论 500 字左右不超 700 字 ｜ 有增量价值（点评+邀请，非广告）

## 回报

M1 完成后回报：① comment 模式实现说明 ② 测试结果（≥10 绿）③ NCA 存证号 ④ 台账结构。

---

> 本指令为 ecoscan 评论模式 M1 施工唯一执行依据；M2 试点另发指令（目标批准后）。
> 关联: [[tdca-session-20260828]] ｜ DCD-ECOSCAN-COMMENT-001 ｜ TDCA-COMMENT-INVITE-001
