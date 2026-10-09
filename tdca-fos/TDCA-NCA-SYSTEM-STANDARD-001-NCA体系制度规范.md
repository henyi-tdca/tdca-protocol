# TDCA NCA 体系制度规范（系统化整合版）

> 文档标识: TDCA-NCA-SYSTEM-STANDARD-001 ｜ 版本: V1.0 ｜ 状态: ✅ ACTIVE（创始人指令系统化整理）
> 编制: 2026-08-28（Reasonix 制度层）｜ 存证: GSEQ-0571
> 整合来源: TDCA-NCA-LIFECYCLE-STANDARD-001（V1.0，五环节）+ TDCA-NCA-CODING-STANDARD-001 + 编号机制补丁（GSEQ-0544/0551：B+C+max+1）+ 双库收口（GSEQ-0570）+ NCA-ECOACT 七字段 + OPC 准入 NCA（TDCA-ADMIT-TEMPLATE-001）
> 机读版本: `TDCA-NCA-SYSTEM-SCHEMA-001.yaml`（机器校验用，与本规范一一对应）
> 定位: **NCA 是智能体编程的认知资产，是人类读懂智能体编程行为的记录**——TDCA 核心制度之一，新会话框初始化必备制度对齐项目；修订走本规范 §八 备档验证。

---

## 一、总则

1. NCA = 嵌套认知资产：每次操作/调用/缔约生成不可篡改微型存证（哈希链），"操作即确权"
2. 本规范为 NCA 体系**单一权威文本**；既有 LIFECYCLE/CODING 规范作为子规范引用，冲突以本规范为准
3. 三库层次（防撞车关键）：
   - **Reasonix 双库**：工作区 `.tdca-nca/` ↔ 桌面归档 `.tdca-nca/`（REGISTRY 双库一致，MD5 校验）
   - **WorkBuddy A 库**（运行权威）：`开发会话文件/.tdca-nca/`——唯一权威 NCA_DIR（TC.NCA_DIR 指向）
   - **WorkBuddy B 库**（历史归档）：`TDCA-MEMO-006/.tdca-nca/`——冻结只读，历史存证（含 155-159）不删
   - 引用标注：跨库引用须标来源（A=运行/B=归档），审计先确认库来源

## 二、生命周期五环节（沿用 LIFECYCLE）

```
登记 Registration → 存证 Evidence → 归档 Archival → 检索 Retrieval → 审查 Review
```

| 环节 | 核心动作 | 载体 | 纪律 |
|------|---------|------|------|
| 登记 | NCA-ID + GSEQ，写入索引 | `NCA-REGISTRY.yaml` | 生成即登记 |
| 存证 | 11 字段 + 前后哈希 + 人类签批 | NCA 文件（.yaml）| 完整可验 |
| 归档 | 写权威库 → 镜像 | A 库 + Reasonix 双库 | A 权威 / B 冻结 / REGISTRY 一致 |
| 检索 | 项目目录 / 全局索引 | 双键（GSEQ + NCA-ID）| 标库来源 |
| 审查 | 哈希核对 + GSEQ 连续 + 签批完整 | dir_checksum + 索引 | 不可删改（KB-INST-010:33）|

## 三、编号机制（补丁 B+C 固化，GSEQ-0544/0551）

1. **统一生成**：编号仅由 `generate_nca` 生成，**人工禁止手动预分配**（`explicit_seq` 非 None → ValueError）
2. **max+1 保留缺口**：候选 = `max(existing)+1`——编号=事实存证时间序，缺口（历史事故/并发痕迹）**不可回填**（不可篡改精神）；per-date 序号（只扫当天）
3. **并发安全**：`os.open(O_CREAT|O_EXCL)` 原子预约，被抢顺延；跨挂载点/网络盘需分布式锁（单机场景 O_EXCL 足够）
4. **溯源标记**：生成物必含 `Generated-By: nca_generator.generate_nca`
5. **lint 校验**：`verify_numbering_discipline`——重复 id / 文件名格式 / 文件内 NCA-ID 不符 / 缺 Generated-By（疑似手动预分配）均检出（legacy 祖父条款仅报告不删）
6. **NCA-ID 编码**：`NCA-TDCA-REASONIX-{YYYYMMDD}-{SEQ:03d}`；GSEQ 全局单调（`GSEQ-{NNNN}`）

## 四、对外动作存证（NCA-ECOACT 七字段，强制 fail-closed）

对外动作（邀请/挂载/化合/治理协作）**先存证后动作，无存证不动作**，七字段必填：

```
repo_full / mode / license_spdx / invite_nca_ref / response_status / profit_sharing / compliance
```

纪律：分润模拟态（ID92，不承诺打款）｜算力零提及｜不点名｜只赋能不改码｜先于发送生成

## 五、准入 NCA（OPC 模板）

- 缔约者准入：`TDCA-ADMIT-{YYYYMMDD}-{SEQ}`（Operation-Type=AdmissionNCA），缔约者**自签署**（Signed-By=GitHub ID）
- 基协议接受 4 项（CONST/NSFL/WORKING-SPEC/OPC）+ 红线 5 条 + ID92 Simulated
- 生态准入（运行态）：enforce_entry v2（PENDING_LOAD 零权利态 → 机读证据 → EcosystemAdmit）

## 六、机读规范（详见 SCHEMA-001）

- 字段 schema：11 字段必填 + 七字段对外 + 编号规则表达式 + 库规则
- 校验入口：`verify_numbering_discipline` / REGISTRY 双库 MD5 / dir_checksum

## 七、数据性质标注

- 所有模拟/自报数据强制标注（mixed / [UNVERIFIED] / simulated-ID92）——不可冒充 real

## 八、修订备档（版本链）

| 版本 | 日期 | 修订 | 存证 |
|---|---|---|---|
| V1.0 | 2026-08-28 | 系统化整合（五环节+编号补丁+双库收口+ECOACT+准入）| GSEQ-0571 |

- 修订流程：提案（DCD/REV）→ 人类签批 → 更新本规范 + SCHEMA + 版本链 + GSEQ 锚
- **备档验证**：每次修订保留上一版本完整文本 + 修订差异 + 存证锚（哈希/版本文件）

---

> 关联: [[tdca-session-20260827]] ｜ LIFECYCLE-STANDARD-001（子规范）｜ GSEQ-0544/0551/0570（整合来源）
