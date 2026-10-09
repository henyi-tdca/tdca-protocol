# merchant_loop M1 交付报告 · 商家消费权益循环增值服务工具包

> 文档标识: TDCA-MERCHANTLOOP-M1-001 ｜ 状态: ✅ **M1 签批 FROZEN（2026-09-08 创始人验收签批，ID71）**
> 日期: 2026-09-08（+08）｜ 会话框: L1-SI-023-FE6B63 ｜ 立项: DCD-MERCHANT-LOOP-001（✅ ACCEPT 2026-09-07）
> 存证: GSEQ-1140（Delivery）+ **GSEQ-1141（SignOff 人类验收签批）**，双库 MD5 MATCH ｜ 落点: `tdca-toolchain/merchant_loop/`

---

## 一、交付物清单（DCD §二 四模块全交付）

| 模块 | 文件 | 功能 | DCD 验收 |
|---|---|---|---|
| **权益函数模板** | `engine.py`（validate_template/BenefitTemplate） | YAML 模板校验（六要素声明 NS-007 + 场景类型 + 预算平移约束）+ **否定感知红线词检测**（无资产化：升值/杠杆/保本/回购等——否定声明不误伤） | A-1 ✅ |
| **核销流水存证** | `engine.py`（redeem）+ `notary.py` | 核销事件→NCA 落证（NCA-MERCHANTLOOP-{date}-{seq}）+ **CCA 贡献值记账预留**（f 形式留 R-7 M3，不冒充定标）+ 双边不进 CLS（no_cls=True）+ 核销真实性证据位（LBS/小票/商家确认） | A-2 ✅ |
| **ROI 仪表盘** | `roi.py`（RoiService 三情景） | 悲观/中性/乐观三情景（核销率/毛利/复购/增量归因参数化）+ 预算平移对照 + **剔除资产升值因子**（无任何资产价格/转让收益项） | A-3 ✅ |
| **CLI** | `cli.py` | `publish --config <yaml>` / `redeem --benefit --event` / `roi-report --benefit-id ... --budget ... --audience ...`（均支持 `--notarize`） | 配套 ✅ |

**示例与打包**：`examples/benefit_cafe.yaml`（权益模板示例）｜ `value_services/__init__.py` 升 **V3.0.0-M1**（三服务：cog-align/util-value/merchant-loop 统一入口）

## 二、验收结果（DCD §三 A-1~A-4）

| # | 验收项 | 标准 | 结果 |
|---|---|---|---|
| A-1 | 权益发布 | 模板校验 + 落 NCA（六要素） | ✅ 测试 6 例 + CLI publish 实跑（NCA-1/2 落证） |
| A-2 | 核销闭环 | 核销事件→NCA→贡献值记账接口（CCA 预留位） | ✅ 测试 5 例 + CLI redeem 实跑（NCA-4 落证，net=13.0，channel=cca） |
| A-3 | ROI 报告 | 三情景与 DCA 框架对照（无资产升值因子） | ✅ 测试 3 例 + CLI roi-report 实跑（0.06/0.828/3.105 单调，NCA-6 落证） |
| A-4 | 回归 | 不破既有 util_value/cog_align | ✅ **toolchain 全量 321 passed**（merchant_loop 19 例 + value_services 更新） |

## 三、关键实现说明

1. **否定感知红线检测**（工程修正）：红线词（无资产化）检测若为朴素子串匹配会误伤合规否定声明（如六要素「无杠杆、不承诺升值」）。实现向前看否定前缀（无/不/非/禁/防/剥离/剔除/拒/零/未）——只有红线机制作**正向卖点/承诺**才拒绝。
2. **CCA 预留不越权**：核销结果带 `cca_contribution`（SIMULATED，f 形式标注「待 R-7 M3 定形」）——只记账位不冒充定标（对齐 ID92）。
3. **双边不进 CLS**：核销结果 `no_cls=True` + `channel="cca"`（M2 结算通道标记）；notary NCA 带 Boundary 字段声明。
4. **ID92 数据纪律**：CLI 默认 `--provenance SIMULATED`；真实商户数据接入须显式标注 real（e-CNY 前全模拟态）。

## 四、后续（M2 沙盒装配路径——M1 FROZEN 后）

- **M1 里程碑 FROZEN（2026-09-08 人类验收签批）** → merchant_loop M1 工具包 → **DCA-重塑版沙盒 M1 装配**（DCD-DCA-SANDBOX-001：merchant_loop M1 提供权益发布/核销/ROI 模块）→ 26 周模拟（核销率 ≥60% 连续 8 周出盒门槛）→ R-7 M3 混合市场扩展（λ_pair 定标 + CCA 资助检测实装）
- 边界维持：双边消费交易不进 CLS；无池/无杠杆/无升值承诺；真实资金流 e-CNY 接入前全模拟态

---
*merchant_loop M1 工具包交付完成并人类验收签批（GSEQ-1140/1141）——四模块 + 示例 + 19 测试 + CLI 三命令实跑 ｜ toolchain 321 全绿 ｜ **M1 FROZEN**，DCA-重塑版沙盒 M1 装配可启动*
