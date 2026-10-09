# DCA-重塑版沙盒 M2 参数校准与 26 周模拟运行方案

> 文档标识: TDCA-DCA-SANDBOX-M2-001 ｜ 日期: 2026-09-08（+08）｜ 会话框: L1-SI-023-FE6B63
> 上游: DCD-DCA-SANDBOX-001（M1 FROZEN GSEQ-1143 → M2 26 周模拟运行）｜ M1 短程数据（GSEQ-1142 交付报告）
> 状态: ✅ 方案定稿（校准执行中）

---

## 一、校准目标与 M1 基线

**出盒门槛（DCD §二）**：核销率 ≥60% 连续 8 周（26 周窗口内）｜ 零穿池 ｜ 0 金融化违例 ｜ CCA 响应率 ≥ 阈值 ｜ 激活系数 >1.2

**M1 短程基线（13 周，arrival_rate 未校准 0.25~0.30）**：
- avg_redemption_rate ≈ 0.29（<60%——M1 只验证检测器，未判出盒，符合预期）
- 零穿池 ✅ ｜ 0 违例 ✅ ｜ 激活 0.99（<1.2）

**校准关键量**：模拟器周核销率 ≈ 周到达率 arrival_rate（核销事件 = poisson(arrival_rate×customer_base) 且 redemption_rate = events/customer_base）→ **arrival_rate 直接决定核销率水平**。达 60% 目标域需 arrival_rate ≥ 0.62（留波动余量取 **0.65 目标域**；0.65² 尾部仍 ≥60% 概率高）。

## 二、校准参数（SIMULATED——ID92 标注，M2 校准域）

| 参数 | M1 值 | M2 校准域 | 校准依据 |
|---|---|---|---|
| arrival_rate（周到达率） | 0.25~0.30 | **0.65（目标域）** | 核销率 ≈ arrival_rate；60% 门槛 → ≥0.62，取 0.65 余量 |
| customer_base | 2000/1500 | 不变 | 语义=周触达，与 arrival_rate 乘积 = 周核销期望 |
| avg_ticket | 100/120 | 不变 | 客单（让利/日清结构不敏感） |
| 其余（discount/rebate/margin） | 同 M1 | 不变 | merchant_loop FROZEN 权益不动 |

> 校准诚实性声明：模拟态参数全 SIMULATED；arrival_rate 0.65 =「营销活动周核销转化率」的 SIMULATED 假设（DCA 素材核销率同域），非真实测量——M3 出盒仍须人类签批（ID71）+ 真实数据回填校验。

## 三、26 周模拟运行设计

1. **主运行**：`run --weeks 26 --arrival-rate 0.65 --seed <n> --notarize`——3 seed（20260908/101/202）稳定性检验
2. **判定**（26 周窗口）：
   - 核销率 ≥60% 连续 8 周（max consecutive ≥8）
   - 26 周零穿池（cashflow 无负）
   - 0 金融化违例（violations 空）
   - CCA 响应率（占位信号——M3 完整评估）
   - 激活系数 >1.2
3. **多 seed 稳健性**：三 seed 均达标 → M2 判定通过；任一 seed 未达标 → 记录并上报（不自动出盒，出盒=ID71）

## 四、产出

- 本方案 + 26 周运行记录（三 seed 汇总表 → M2 模拟运行报告 TDCA-DCA-SANDBOX-M2-001）
- NCA 存证（GSEQ-1144：M2 模拟运行交付）
- 出盒评估材料供 M3（激活系数 >1.2 复核 + 人类签批 ID71）

## 五、纪律

- merchant_loop M1 / dca_sandbox M1 **零改动**——校准通过 CLI 参数注入（--arrival-rate），不改装配件代码
- 全 SIMULATED（ID92）；0 真实资金/0 配置权调用；红线审计内嵌
- 出盒门槛判定 M2 只做检测，**出盒授权 = M3 人类签批（ID71）**

---
*DCA-重塑版沙盒 M2 参数校准方案定稿——arrival_rate 0.65 目标域 + 26 周 × 3 seed ｜ 执行中*
