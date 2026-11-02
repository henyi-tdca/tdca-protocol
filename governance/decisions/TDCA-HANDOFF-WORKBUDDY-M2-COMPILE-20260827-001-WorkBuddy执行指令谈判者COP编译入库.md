# TDCA-HANDOFF-WORKBUDDY-M2-COMPILE-20260827-001 · WorkBuddy 执行指令：谈判者 COP 编译入库

> 文档编号: TDCA-HANDOFF-WORKBUDDY-M2-COMPILE-20260827-001 ｜ 编制: 2026-08-27（Reasonix）｜ 状态: ✅ READY，待 WorkBuddy 执行
> 承自: TDCA-EMISSARY-M2-001（谈判者 COP 设计，GSEQ-0537）｜ TDCA-EMISSARY-KICKOFF-001（v3 M2）
> 存证: GSEQ-0538（本指令）｜ 编译目标: 认知编译器工作区思维协议库

---

## 背景（一句话）

v3 特使矩阵 M2 谈判者 COP 设计已落盘（`TDCA-EMISSARY-M2-001`，含 COP 本体 + 六类话术 + 纪律）。现编译入库——使谈判者成为可被编排器调用的正式 COP。

## 动作 1 · 编译入库

- 按设计文档 §一 COP 本体编译为正式 COP yaml（cognitive-compiler 编译流程）
- 入库位置：新建子库 `emissary/`（或按既有子库组织惯例并入，命名 `谈判者-特使-001.yaml`）
- 编译产物 NCA 落链（nca_generator，Operation-Type=COPCompile）

## 动作 2 · schema 校验（编译门槛）

- 全字段核验：stratum / verse / core / origin / negative_space / primitive / soul.base_protocol / dispatch / decision / topic
- `base_protocol` 必须 = `TDCA-CORE-20260815-01`
- negative_space ≥5 条（设计文档 §一 已有 5 条，不得删减）
- 编译失败即停，报 Reasonix 修订设计，不自行改 COP 语义

## 动作 3 · 话术表核验（口径）

- 六类话术落地为可调用响应（设计 §二）
- 口径核验：分润=模拟态（**不承诺打款**）｜ 邀请非要求 ｜ 不点名 ｜ 算力零提及 ｜ 凭证零落盘
- 逐条过 NSFL（负空间命中即熔断）

## 动作 4 · 端到端实测 1 条

- 模拟对方提问（如"分润怎么算？"）→ 谈判者响应 → NCA-ECOACT 存证提醒
- 记录：输入问题 / 响应话术 / NSFL 结果 / 存证提醒触发

## 纪律

模拟态口径（不承诺打款）｜ 不强制诱导 ｜ 不点名 ｜ 凭证零落盘 ｜ 算力零提及 ｜ 无 NCA-ECOACT 存证不动作 ｜ NSFL 先于一切 ｜ 产物不推送（待签批走 PR）

## 回报要求

① 编译产物路径 + NCA 编号 ② schema 校验结果（全字段 ✅/❌）③ 话术核验记录（6 条口径逐条）④ 端到端实测 1 条 ⑤ 编译清单更新（335 原生 → +1 = 336，或按既有口径登记）→ Reasonix 见证

---

> 关联: [[tdca-session-20260827]] ｜ GSEQ-0537（M2 设计）
