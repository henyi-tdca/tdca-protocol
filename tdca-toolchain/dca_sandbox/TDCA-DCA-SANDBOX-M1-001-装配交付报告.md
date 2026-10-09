# DCA-重塑版沙盒 M1 装配交付报告

> 文档标识: TDCA-DCA-SANDBOX-M1-001 ｜ 状态: ✅ **M1 装配签批 FROZEN（2026-09-08 创始人验收签批，ID71）**
> 日期: 2026-09-08（+08）｜ 会话框: L1-SI-023-FE6B63 ｜ 立项: DCD-DCA-SANDBOX-001（✅ ACCEPT 2026-09-07）
> 存证: GSEQ-1142（Delivery）+ **GSEQ-1143（SignOff 人类验收签批）**，双库 MD5 MATCH ｜ 装配件: merchant_loop M1（FROZEN，GSEQ-1141）
> 落点: `tdca-toolchain/dca_sandbox/`

---

## 一、交付物（DCD-DCA-SANDBOX-001 §四 M1：沙盒模型装配）

| 模块 | 文件 | 内容 | 状态 |
|---|---|---|---|
| 模拟引擎 | `engine.py` | DcaSandboxSimulation——Phase0 准入（merchant_loop validate 装配）→ P0 实验（周推进日清模拟：泊松到达/Knuth 采样/逐笔 redeem/现金零滞留）→ P1 评估（出盒指标检测器） | ✅ |
| 存证 | `notary.py` | DcaSandboxNotary（NCA-DCASANDBOX-{date}-{seq}，SIMULATED ID92） | ✅ |
| CLI | `cli.py` | `python -m dca_sandbox.cli run --weeks <n> --seed <n> [--notarize]` | ✅ |
| 装配方案 | `TDCA-DCA-SANDBOX-M1-ASSEMBLY-001-装配方案.md` | 方案定稿（含参数模型/纪律） | ✅ |
| 交付报告 | 本文件 | M1 装配交付 | ✅ |
| 测试 | `tests/test_dca_sandbox.py` | 10 例（装配/日清/指标/CLI） | ✅ 331 全绿 |

**装配原则**：merchant_loop M1（FROZEN）**只 import 不改写**——权益模板校验/核销闭环/让利计算全部复用其 FROZEN 逻辑（sim 内 `from merchant_loop.engine import ...`）。

## 二、验证结果

| 项 | 结果 |
|---|---|
| 装配 A1 | ✅ 2 商户权益模板经 merchant_loop validate（六要素/红线）——红线模板装配拒绝（Phase0 fail-closed） |
| 日清 A2 | ✅ 逐笔即时让利 → 现金零滞留（cashflow_balance=0）→ 零穿池恒真；客单价下限对齐 min_spend |
| 指标 A3 | ✅ 出盒检测器预埋全工作：核销率≥60% 连续 8 周/零穿池/0 金融化违例/激活系数>1.2 |
| 回归 A4 | ✅ **toolchain 全量 331 passed**（dca_sandbox 10 例新增，不破 merchant_loop/value_services/cog_align/util_value） |
| CLI 实跑 | ✅ `run --weeks 13` exit=0：13 周 13357 核销事件、零穿池、0 违例、NCA-DCASANDBOX 落证 |

**13 周短程运行读解（M1 验证语义）**：avg_redemption_rate≈29%、激活≈0.99（<1.2）——符合 M1 短程保守参数预期（arrival_rate 未校准）。**出盒门槛是 M2 26 周完整模拟的评估对象，M1 只验证检测器工作、不判出盒**（M1 若直接达标反而异常——参数未校准）。

## 三、纪律对照（DCD §三/§五）

- 纯模拟参数运行（SIMULATED ID92）——0 真实资金流/0 配置权真实调用（notary Boundary 字段声明）
- Δ 实时备案语义：CLI --notarize 每运行落 NCA（含 report hash）
- 红线内嵌：VIOLATION_TERMS 审计（0 违例）；BLOCKED 语义（Phase0 装配拒绝/审计命中）
- merchant_loop FROZEN 零改动（装配只读）

## 四、后续（M2 26 周模拟运行——M1 FROZEN 后）

- **M1 里程碑 FROZEN（2026-09-08 人类验收签批）** → **M2**：`python -m dca_sandbox.cli run --weeks 26 --seed <n> --notarize`——arrival_rate 等参数校准至核销率目标域 → 26 周完整模拟（零穿池/核销率 ≥60% 连续 8 周/0 金融化违例/CCA 响应率）
- **M3**：出盒报告（激活系数 >1.2 复核 + 人类签批 ID71）+ R-7 M3 混合市场扩展（λ_pair 定标 + CCA 资助检测实装）
- 红线贯穿：无资产交易/无保本/无资金池/无庞氏/e-CNY 前全模拟态

---
*DCA-重塑版沙盒 M1 装配交付完成并人类验收签批（GSEQ-1142/1143）——merchant_loop M1 FROZEN 装配 + 模拟引擎 + 10 测试 + CLI 实跑 ｜ toolchain 331 全绿 ｜ **M1 FROZEN**，M2 26 周模拟可启动*
