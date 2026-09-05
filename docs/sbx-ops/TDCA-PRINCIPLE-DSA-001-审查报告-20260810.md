# TDCA-PRINCIPLE-DSA-001 审查报告

> 审查对象: TDCA-PRINCIPLE-DSA-001《动态安全三空间循环机制》（用户粘贴稿）
> 审查日期: 2026-08-10 | 审查方式: 与 TDCA 制度基准一致性核对（只读，未改工程/任务书）
> 基准: 任务书 FROZEN / KB-ECON-001 §7 / KB-INST-001 / KB-INST-020 / kg-instances-v1.0.yaml / tdca-official-kb 全库
> 结论: **修正后落盘**（C1 已修正；C2~C4 待核，不阻塞归档）

---

## 一、核对结果总表

| # | DSA-001 声称 | 制度基准 | 结论 |
|---|-------------|---------|------|
| C1 | 激活系数 = 政府 PCR 投入 / (出盒税收+就业社保) > 1.2 | KB-ECON-001 §7 + 任务书 F3 + SBX-OPS `activation_engine.py`: α = (出盒税收贡献+就业社保) / 政府初始 PCR 投入 > 1.2 | 🔴 **公式方向颠倒** → **已修正** |
| C2 | SBX-SUSPENDED / SBX-BANNED 回退状态 | SBX-OPS 状态机仅 Phase0/P0/P1/Exit/Closed，无回退/休眠态 | 🟡 工程缺口（待核） |
| C3 | ID36（制度-技术动态均衡） | tdca-official-kb 全库检索无 ID36 编号 | 🟡 编号存疑（待核） |
| C4 | AiTM（跨 Agent 消息 NCA 指纹不匹配） | 官方知识库未检索到该术语 | 🟡 术语待核 |
| C5 | ERI/CCI 正和验证 | KB-INST-001「ERI-CCI 指数」+ REPO-007 效用精灵算法库 | ✅ 有出处 |
| C6 | MOU 连续 t 期归零 → 熔断 | ID79「MOU 最低可见效用：连续无税收则场景权重归零」 | ✅ 有出处 |
| C7 | ID33 OTA 活宪法升级 | kg-instances / governance 有 ID33 | ✅ 有出处 |
| C8 | 宪法十六条分布式执行（可观测/正和/自证/熔断） | KB-INST-020 C01/C02/C03 | ✅ 有出处 |
| C9 | CHEM 同构（正向/反向/催化剂/NSFL 抑制剂） | KB-ECON-001 §8 + 任务书 F5 | ✅ 有出处 |
| C10 | 三空间结构（负空间/沙盒/配置权市场） | NS-OPS + SBX-OPS + L2 市场（宪法 C04） | ✅ 结构成立 |
| C11 | NSFL-CERT / PCM-ENTRY 证书化准入 | 与 NS-OPS F3（声明-行为校验）+ 任务书 S-Right 方向一致 | ✅ 方向一致 |
| C12 | "配置权调用即纳税"（MOU 实时性） | 任务书 F2/F6 + DCEP 合约；SBX-OPS M4 边界项 | ✅ 与工程 M4 边界互补 |

## 二、C1 修正说明（已落盘）

- 修正前（用户稿）: `激活系数 = 政府初始PCR投入 / (出盒税收贡献+就业社保) > 1.2`
- 修正后（落盘版）: `激活系数 α = (出盒税收贡献 + 就业社保) / 政府初始PCR投入 > 1.2`
- 依据: KB-ECON-001 §7 权威公式 + 任务书 §二 F3 + SBX-OPS 工程 `activation_engine.py:68`（`coefficient = (tax_revenue + employment_ss) / pcr_input`）
- 影响: 按原稿字面，α>1.2 意味着政府 PCR 投入为税收 12 倍——财政不可持续却判"可出盒"，出盒条件语义完全反转。

## 三、待核项（C2~C4，不阻塞归档）

### C2 SBX-SUSPENDED / SBX-BANNED 与工程状态机
- SBX-OPS M1 状态机: Phase0 → P0 → P1 → Exit / Closed（Closed 承载熔断/终止）
- DSA-001 引入: SBX-SUSPENDED（回退重整）/ SBX-BANNED（永久休眠）
- 若 DSA-001 采纳为制度，SBX-OPS 状态机须扩展回退/休眠态 —— **建议列入 M2 范围决策**（任务书 M2 口径 F2+F6+F5 未含此项，需 DCD/人类签批确认）

### C3 ID36 编号存疑
- tdca-official-kb 全库无 "ID36" 或 "制度-技术动态均衡" 记录
- 可能来源: 未收录的论丛/专著章节，或新编号提案
- 建议: 核对 TDCA 官方 ID 编号表（tdca-fos / 归档文件夹）后确认或改引其他权威条款

### C4 AiTM 术语待核
- "跨 Agent 消息 NCA 指纹不匹配（AiTM 检测）" 在官方知识库无出处
- 概念与 NCA 链式校验（SBX-OPS nca_logger.verify_chain）方向一致，但术语需溯源

## 四、归档声明

- DSA-001 修正版已落盘: `tdca-sbx-ops/TDCA-PRINCIPLE-DSA-001-动态安全三空间循环机制.md`
- 工程代码（SBX-OPS/NS-OPS）与任务书 FROZEN **未改动**
- C1 修正已在落盘版头部标注；C2~C4 待核项随制度流程（DCD/ID 编号表核对）处理
- 制度基线核验: 本审查仅核对一致性，未作制度裁决（裁决权归人类裁决 A）
