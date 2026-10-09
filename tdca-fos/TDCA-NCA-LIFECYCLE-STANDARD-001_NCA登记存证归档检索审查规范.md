# TDCA NCA 登记·存证·归档·检索·审查规范

> 文档标识: TDCA-NCA-LIFECYCLE-STANDARD-001 | 版本: V1.0 | 状态: ACTIVE
> 制度锚定: TDCA-WORKING-SPEC-001 §二制度基线（第 8 项）+ §六 NCA 生成与归档 + TDCA-MEMO-006 附录 C
> 关联规范: TDCA-NCA-CODING-STANDARD-001（统一编码与归档纪律）
> 定位: **NCA 是智能体编程的认知资产，是人类读懂智能体编程行为的记录。** 本规范覆盖 NCA 全生命周期五环节，并作为任意新会话框初始化的必备「制度对齐项目」。

---

## 一、总纲：NCA 全生命周期五环节

```
登记 Registration → 存证 Evidence → 归档 Archival → 检索 Retrieval → 审查 Review
```

| 环节 | 核心动作 | 权威工具/载体 | 纪律 |
|------|---------|--------------|------|
| 登记 | 分配 NCA-ID + GSEQ，写入统一索引 | `NCA-REGISTRY.yaml` | 每生成一个 NCA 立即登记 |
| 存证 | 11 字段 + 前后状态哈希 + 人类签批 | NCA 文件本体（.yaml） | 内容完整、哈希可验 |
| 归档 | 写归档库 → 镜像运行库 → 归并 | 双库 `.tdca-nca/` | 归档库权威、禁止单库滞留 |
| 检索 | 单一项目走项目目录 / 全局走索引 | 项目目录 + NCA-REGISTRY.yaml | 双键（GSEQ + NCA-ID）定位 |
| 审查 | 哈希基线核对 + GSEQ 连续性 + 签批完整性 | dir_checksum + 索引比对 | 不可删除/篡改（KB-INST-010:33） |

---

## 二、登记（Registration）

1. **NCA-ID 编码**：`NCA-TDCA-REASONIX-{YYYYMMDD}-{SEQ:04d}`，SEQ 由归档库当日现有最大 SEQ+1 统一分配，**禁止双库独立编号**。
2. **GSEQ 时间序列号**：全局单调递增（`GSEQ-{NNNN}`），按 `Timestamp` 升序编制，只登记在索引、不写入文件不改命名。
3. **索引登记**：每个 NCA 生成后立即在 `NCA-REGISTRY.yaml` 登记 `gseq / nca_id / files / timestamp / fc_id / operation_type / operator / source / status`。
4. **项目内 NCA**：项目目录内的 NCA（运行时/测试/研究）原地保留，按分组登记到 `project_sections`（含 `dir_checksum` 目录哈希基线）。

---

## 三、存证（Evidence）

1. **11 字段必含**（MEMO-006 附录 C）：NCA-ID / Function-Call-ID / Operation-Type / Operator / Timestamp / Pre-State / Post-State / Config-Right-Token / Audit-Trail / Human-Signature / Negative-Space-Check。
2. **哈希可验**：Pre-State / Post-State 记录 SHA-256；文件整体哈希与索引一致性可复核。
3. **人类签批**：制度决策点（立项/交付冻结/审查）必须有 `human_signatory`；签批缺失即完整性违规。
4. **负空间检查**：`Negative-Space-Check` 必须显式标注 `Triggered: true/false`，真触发走熔断路径。

---

## 四、归档（Archival）

1. **双库架构**：
   - 归档库（权威）：`<Desktop>\TDCA归档文件夹\.tdca-nca\`，人类审读。
   - 运行库（镜像）：`global-workspace\.tdca-nca\`，智能体开发时实时调用。
2. **归档纪律**：生成 → 写归档库 → 复制镜像到运行库 → 会话结束前归并 → 更新索引。**禁止只在单库落盘后长期不归并。**
3. **撞车/镜像/异常处置**：跨库同名 NCA-ID 内容不同 = 撞车（以 `-D`/`-W` 后缀区分双版本）；跨库同 MD5 = 镜像（各保留副本）；非标准格式/草稿 = legacy/draft（索引标注）。

---

## 五、检索（Retrieval）

1. **单一项目检索**：处理单一项目时，直接在该项目目录内检索（项目内 NCA 原地保留）。
2. **全局检索**：跨项目/全链检索走 `NCA-REGISTRY.yaml`，双键定位——GSEQ（时间序列）+ NCA-ID（引用键）。
3. **时间序列定位**：GSEQ 单调递增，可按时间窗快速切片；撞车同名 NCA 以 GSEQ 区分。

---

## 六、审查（Review / Audit）

1. **目录哈希基线核对**：审查某项目 NCA 时，重算 `dir_checksum`（目录内 NCA 文件名+MD5 排序哈希）与索引基线比对，一致即未篡改/缺失。
2. **GSEQ 连续性校验**：索引 GSEQ 应连续无断号；断号须定位缺失 NCA。
3. **签批完整性**：抽查决策点 NCA 的 `Human-Signature.Status`，Pending 未闭合须追责。
4. **撞车/镜像核查**：核对 `status` 标注与物理文件一致（collision 双版本、mirror 双副本）。

---

## 七、会话初始化制度对齐（新增·必备）

本规范是**任意新会话框初始化时必备完成的制度对齐项目**（并入开发规范制度基线第 8 项）。会话初始化须逐项确认：

1. [ ] `NCA-REGISTRY.yaml` 双库（归档库 + 运行库）存在且可读、内容一致
2. [ ] 末条 GSEQ 已知（下一个 GSEQ 起点明确）
3. [ ] 本会话 NCA 登记起点 = 归档库当日 SEQ 最大值 +1（或新日期 0001）
4. [ ] 项目内 NCA 分组（project_sections）的 dir_checksum 基线在位
5. [ ] 制度基线 8 项（含本规范）全部就绪

> 会话初始化存证（ProtocolInit NCA）须在 Scope 中声明「NCA 制度对齐已通过」。

---

## 八、违规与熔断

| 违规 | 后果 |
|------|------|
| 双库独立编号（撞车） | 制度完整性违规，触发负空间熔断审查 |
| 单库滞留不归并 | 索引失真，禁止继续新任务 |
| 删除/篡改 NCA | 违反 KB-INST-010:33，最高等级违规 |
| 签批缺失 | 决策点无效，回退并补签 |

> 本规范自 V1.0 起生效；存量 NCA 按 TDCA-NCA-CODING-STANDARD-001 §五归并登记。
