# TDCA-HANDOFF-COMMUNITY-RULE-001 · Kimi 落实指令（社区算力协议前置规则）

> 文档编号: TDCA-HANDOFF-COMMUNITY-RULE-001 ｜ 编制: 2026-08-24（Reasonix 制度层）｜ 状态: ✅ **READY（Kimi 落实）**
> 上游: NCA-067（规则制定：登录不影响 + TDCA 协议前置强制 + ¥10 余额阈值）｜ 创始人 2026-08-24（阈值定稿：日 ¥2 / 月 ¥8 + Flash-only 确认）
> 目标: tdca-community-playground 仓库（workflow + SECURITY.md）

---

## 〇、三动作（创始人定稿）

| # | 动作 | 内容 |
|---|---|---|
| 1 | 熔断阈值调整 | **日 ¥2 / 月 ¥8**（¥10 试验期，留 ¥2 安全垫；后续充值调整）|
| 2 | workflow 准入前置 | 调用前 enforce_check（AgentCard + 公理 6）→ 未过 fail-closed（零消耗）|
| 3 | SECURITY.md 声明 | 「使用即同意 TDCA 协议」（准入/审计/记账/熔断）|
| 4 | **Flash-only 强化** | 模型硬编码 deepseek-v4-flash + 账号权限仅 Flash（双保险）|

## 〇之二、Flash-only 可行性确认（✅ 可以做到）

**双重保障**：
1. **代码层**：community-compute.yml 模型硬编码 `deepseek-v4-flash`（无法通过参数换成其他模型）——已在工作流中
2. **账号层**：SKY 账号控制台**只授予 Flash 模型权限**（不启用 Pro 等）——即使请求被篡改，账号侧也拒绝非 Flash

**效果**：即使 Key 泄露，攻击者也只能用 Flash（成本极低），无法消耗 Pro/战略模型——¥10 试验期内最坏损失可控。

## 一、动作 1 · 熔断阈值调整（定稿：日 ¥2 / 月 ¥8）

- community-compute.yml 守卫常量：`DAILY_LIMIT=2`（¥）/ `MONTHLY_LIMIT=8`（¥）
- daily-obs 旁路阈值同步（tdca-protocol obs-daily D 组：日 ¥2 / 月 ¥8 → fail 告警 → 人工吊销）

## 二、动作 2 · workflow 准入前置（核心）

在调用 flash **之前**插入准入步骤（复用 core-go enforce / tdcad）：
```yaml
- name: TDCA protocol gate (enforce + axiom6)
  env:
    TDCAD: /path/to/tdcad   # 或 MCP 端点
  run: |
    # AgentCard 准入声明（调用者必须提供）
    # enforce_check PASS + 公理 6 机验通过 → 放行
    # 未通过 → exit 1（fail-closed：不调用 flash，零消耗）
```
**接入方式**（Kimi 选）：
- 方案 A：调用 tdcad enforce（本地二进制，playground 仓库可引用 core-go 产物）
- 方案 B：调用 tdca-protocol 的 MCP enforce_check 工具（远端）
- 注：AgentCard 由调用者随 dispatch input 提供（prompt 外新增 `agent_card` 输入）；准入失败 → 报错不执行

## 三、动作 3 · SECURITY.md 声明

新增「使用即同意」条款：
> 使用社区算力即表示您接受 TDCA 协议：① 准入声明（AgentCard + 公理 6 验证）② 匿名审计（NCA-COMMUNITY 存证）③ 模拟态记账（NCA + ERI，凭账本转实际结算）④ 熔断约束（日 ¥1 / 月 ¥8，超限吊销）。未加载 TDCA 协议 → 不可用（fail-closed）。

## 四、回报（Kimi → Reasonix）

| 项 | 要求 |
|---|---|
| 阈值调整 | commit + 数值确认 |
| 准入前置 | commit + **拦截实测**（未过协议调用 → 被拒零消耗）|
| SECURITY.md | commit + 条款确认 |

## 五、纪律

Key 永不落盘（含前缀）｜ 仅 Flash ｜ 匿名审计 ID92 ｜ 模拟态记账 ｜ 主算力零提及 V1.2 ｜ fail-closed（无协议不调用）

## 六、关联

- 上游: NCA-067 ｜ 创始人规则 2026-08-24 ｜ TDCA-COMMUNITY-LEDGER-001
- 存证: GSEQ-0429 ｜ NCA-TDCA-REASONIX-20260824-067

---

> 本指令为社区算力协议前置规则落实依据（三动作：阈值/准入/声明）；回报拦截实测。
