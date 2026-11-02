# TDCA-HANDOFF-WORKBUDDY-V01-20260827-001 · WorkBuddy 执行指令：MVP V0.1 首个普通用户实测

> 文档编号: TDCA-HANDOFF-WORKBUDDY-V01-20260827-001 ｜ 编制: 2026-08-27（Reasonix）｜ 状态: ✅ READY，待 WorkBuddy 执行
> 承自: TDCA-COLDSTART-MVP-001（V0.1 验收）｜ TDCA-IDENTITY-TEMPLATE-001（交付物 1）｜ TDCA-COP-TEMPLATES-001（交付物 2）
> 存证: GSEQ-0553（本指令）

---

## 背景（一句话）

MVP 两交付物 READY（IDENTITY.md 模板 + 三套 COP 模板）。**V0.1 验收 = WorkBuddy 扮演第一个普通用户**，不读 TDCA 哲学、仅"界面化操作"（选模板 + 提交）跑通注册→选模板→派智能体→缔约——跑通则用户自助化 V0.1 完成。

## 流程（四步，模拟普通用户视角）

### 动作 1 · 注册（IDENTITY.md）
- 按 `TDCA-IDENTITY-TEMPLATE-001`：生成密钥 → 取指纹 → 填 4 字段 → 提交 `IDENTITY-WORKBUDDY.md`
- 预期：enforce_entry 校验通过 → 获得发射权

### 动作 2 · 选模板（COP 三套选一）
- 从 `TDCA-COP-TEMPLATES-001` 选 1 套（如科研协作）
- 填 3 变量：`{{purpose}}` `{{parties}}` `{{data_constraints}}`
- 预期：系统生成六要素预填的联盟 COP

### 动作 3 · 派智能体（特使矩阵）
- 以普通用户身份触发缔约（选模板即派特使）
- 预期：扫描→评估→信使→谈判者（M2 COP）→落地者全自动

### 动作 4 · 缔约
- 准入（v2）→ 沙盒（form_coalition+shapley，只算不写）→ 生产（CoalitionCommit + COPCompile + 贡献 COP 落盘）

## 验收判定（V0.1 完成标准）

- [ ] WorkBuddy 以"普通用户"视角完成四步（不读哲学、仅选模板+填变量+提交）
- [ ] 全链 NCA 落链（准入/联盟/生产）
- [ ] 产出：贡献 COP + IDENTITY-WORKBUDDY.md 注册记录

## 纪律

凭证零落盘 ｜ mixed 口径强制（self-hosted UNVERIFIED 直至实跑 COP 落链）｜ 分润模拟态 ｜ 预算 ¥100 余额内 ｜ NCA 编号走 generate_nca（max+1，GSEQ-0551）｜ 产物不推送（待签批走 PR）｜ NSFL 先于一切

## 回报要求

① IDENTITY 注册校验结果 ② 所选模板 + 生成 COP ③ 全链 NCA 编号 ④ 贡献 COP 路径 ⑤ V0.1 验收判定 → Reasonix 见证

---

> 关联: [[tdca-session-20260827]] ｜ GSEQ-0549（两交付物）
