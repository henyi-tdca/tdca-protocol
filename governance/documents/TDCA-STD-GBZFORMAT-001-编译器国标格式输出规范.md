# TDCA-STD-GBZFORMAT-001 · 编译器国标格式输出规范（185.4 / 185.7）**V1.1**

> 文档编号: TDCA-STD-GBZFORMAT-001 ｜ 版本: **V1.3**（V1.0 → V1.1 纠偏 → V1.2 批量导出 → V1.3 入向解析）｜ 日期: 2026-09-11（+08）
> 会话框: **L1-SI-028-BE481C** ｜ 编制: Reasonix ｜ 存证: **GSEQ-1252**（M1）+ **GSEQ-1253**（M2）+ **GSEQ-1254**（M3）｜ 缺陷依据: **GSEQ-1250**（D1/D2 等九项）
> 依据: 内化白皮书 §2.2 ｜ **GB/Z 185 全文**（`_docx_text/gbz185-fulltext.txt`）｜ 冲突识别机制 C-1 处置（**前缀隔离**）｜ M3 深化（创始人点单，GSEQ-1250）
> 实现: `tdca-adapters/national_format/`（**V1.1，20 用例全绿 + 原文逐字段审计全 MATCH**）｜ 性质: 制度规范（内部基线）

---

## 〇、V1.1 纠偏说明（重要）

V1.0 的实现存在 **2 处字段名与国标原文不符**（2026-09-11 对读国标全文发现，登记 GSEQ-1250 D1/D2）：

| 级 | 缺陷 | V1.0（错） | **V1.1（正）** | 原文依据 |
|---|---|---|---|---|
| 🔴 | 185.7 参数名 | `inputParams` / `outputParams` | **`toolInputParam` / `toolOutputParam`** | 表 1（6.1）；附录 A.3.1 JSON 示例同为正名 |
| 🔴 | 185.4 名称/版本/描述 | `agentName` / `agentVersion` / `agentDescription` | **`name` / `version` / `description`** | 表 1（第 5 章） |

**结论**：V1.0 的"10 用例全绿"系**基于自造字段名的自洽测试**，不构成国标兼容证明；V1.1 起以**原文逐字段审计**（`_m1_gbz_field_audit.py`）为兼容性凭证。旧名仅作**入向别名**兼容读入（`normalize_gbz`），**输出一律国标正名**。

## 一、目的（M3 = 原 D+21 项）

使 TDCA 侧编译/构造的函数语料与工具描述，能输出**国标兼容格式**（GB/Z 185.7 工具属性描述 / 185.4 智能体描述），供跨体系互操作与对外报送——同时**不损失 TDCA 制度语义**。

## 二、185.7 工具属性描述（表 1，六字段 · 正名）

| 属性名 | 变量名（**原文正名**） | 必需 | 内容来源（TDCA） |
|---|---|---|---|
| 工具标识符 | **`toolId`** | **是** | 工具/函数唯一标识 |
| 工具名称 | `toolName` | 否 | 名称 |
| 工具描述 | `toolDescription` | 否 | 语义描述（+ 目标函数摘要） |
| 工具版本 | `toolVersion` | 否 | 版本 |
| 工具输入参数 | **`toolInputParam`**（对象） | 否 | **约束矩阵**（布尔化 → JSON Schema） |
| 工具输出参数 | **`toolOutputParam`**（对象） | 否 | 预期输出（+ 效用计量/税收/分配字段位） |

**制度层扩展（`x-tdca-*` 前缀隔离）**：`objective` / `constraints` / `priorDistribution` / `configRightBoundary` / `expectedAllocation` / `auditTrail` / `sixElementsMapping`（自描述对照表）/ `simulated`（ID92）/ `compileStatus` + `compileWarnings`（IR 编译态）

## 三、185.4 智能体描述（表 1 **全 15 字段** · 正名）

| 属性名 | 变量名 | 必需 | 内容来源（TDCA） |
|---|---|---|---|
| 身份码 | `agentId` | **是** | 智能体身份码（可携国标身份链接） |
| 名称 | **`name`** | **是** | 智能体名称 |
| 别名 | `alias` | 否 | 别名 |
| 智能体版本 | **`version`** | 否 | 版本 |
| 描述 | **`description`** | 否 | 功能自然语言描述 |
| 图标地址 | `iconAddress` | 否 | 图标 |
| 提供方 | `provider` | 否 | 提供方（字符串或自定义） |
| 访问地址 | `accessAddress` | 否 | URL / IP / FQDN |
| 访问方法 | `accessMethod` | 否 | 支持/当前使用的访问方法 |
| 智能体服务区域 | `servingArea` | 否 | 地理区域范围 |
| 认证方式 | `authentication` | 否 | 与访问方法配套的认证 |
| 辅助功能描述 | `capabilities` | 否 | **对辅助功能的支持程度**（原义；能力画像另落 `x-tdca-capabilityProfile`） |
| 默认输入类型 | `defaultInputTypes` | 否 | 字符串数组 |
| 默认输出类型 | `defaultOutputTypes` | 否 | 字符串数组 |
| 技能 | `skills` | 否 | **表 2 结构数组**（见下） |

**表 2 技能属性（`skills[]`）**：`skillId`（**必需**）/ `skillName`（**必需**）/ `skillDescription` / `tags` / `examples` / `inputTypes` / `outputTypes` / `dependencies`

**制度层扩展**：`x-tdca-nationalAgentId`（国标身份链接，可空）/ `x-tdca-configRightBoundary` / `x-tdca-capabilityProfile`（能力画像）/ `x-tdca-simulated`

## 四、校验纪律（fail-closed，双 profile）

| profile | 语义 | 185.7 必需 | 185.4 必需 |
|---|---|---|---|
| `national` | 严格按国标原文 | 仅 `toolId` | `agentId` + `name` |
| `tdca`（默认） | TDCA 更严 | 六字段齐备 + 六要素扩展在位 | `agentId` + `name` + 边界扩展 |

1. 参数类字段须为 JSON Schema `object` 形态
2. **前缀纪律**：非国标字段不得出现（仅允许 `x-tdca-*`）
3. JSON 可序列化（对外报送前提）
4. 数据性质模拟态标注（ID92）

## 五、接入

| 上游 | 路径 | 状态 |
|---|---|---|
| **函数编译器 IR** | `from_ir(ir, tool_id=..., name=...)` —— `IntermediateRepresentation`（`target_function_formalized` / `constraints_sat` / `prior_distribution_params`）→ 185.7 全字段自动填充 | ✅ **V1.1 已实现（#6）** |
| S-Right ToolDescriptor | `to_gbz_from_tool_descriptor(desc, outcome)`（含边界/审计引用） | ✅ 保留 |
| 身份桥接 | 185.4 的 `x-tdca-nationalAgentId` 取自身份桥接在册映射 | ✅ |
| 入向解析 | `gbz_intake.intake(data)`（统一入口：自动判别 tool/agent/message）+ `parse_tool_document` / `parse_agent_document` / `parse_message`（§6.2~6.4 五类报文）+ `import_bundle(dir)`（报送包读回） | ✅ **V1.3 已实现（#9）** |

## 六、验收（V1.1 实测）

- **用例**：**44 用例全绿**（自检驱动 `_gbz_selfcheck.py`：`test_gbz_format.py` **20** + `test_gbz_bundle.py` **10** + `test_gbz_intake.py` **14** → 44 passed / 0 failed）——覆盖六字段正名（D1 回归）、参数 object 形态、前缀隔离、六要素对照表/直传/反向、fail-closed、前缀纪律拒键、JSON 可序列化、**185.4 全 15 字段（#7）**、字段名正名（D2 回归）、national profile 必需性、**表 2 skills 结构**、capabilities 语义归位、旧名入向兼容与正名优先、**IR → 185.7 全字段（#6）**、IR 缺核心三要素即拒、国标 → 内部模型视图、S-Right 桥接。
- **原文兼容凭证**：`_m1_gbz_field_audit.py` —— 三段字段集与 GB/Z 185 原文**逐字段审计全 MATCH**（185.7 表 1 = 6/6；185.4 表 1 = 15/15；表 2 = 8/8）。
- **模块级合计（含既往）**：`identity_bridge`(10) + `tool_call_right`(20) + `national_format`(**20**) 。

## 七、发布批次衔接（含 D1/D2 更正口径）

- **V1.0 公开副本**（`tdca-adapters-public/national_format/gbz_format.py`）含 D1/D2 错误；创始人裁定 **口径 A**：**随下次正常发布批次版本化重推**（不单独开紧急通道；符合"FROZEN 不因修缮被破"纪律）。
- **发布前纪律**：对外件零内部编号 / 算力零提及 / 披露口径（1089）——对外格式说明文档需另行脱敏。
- **重推时同步**：本规范 V1.1 + 模块 V1.1 + 终扫（披露口径）+ Witness。

## 八、待细化（余项跟踪）

1. ~~函数编译器 IR 直接对接~~ ✅ **V1.1 完成（#6）**
2. ~~185.4 能力画像的完整字段集~~ ✅ **V1.1 完成（#7，全 15 字段 + 表 2）**
3. ~~批量导出~~ ✅ **V1.2 完成（#8）**：`gbz_bundle.make_bundle`（逐件校验 + manifest + `bundleSha256` + fail-closed）/ `verify_bundle`（回验：哈希/计数/清单自洽）/ `to_tool_sync_list` / `to_tool_request`（185.7 §6.2 报文形态）
4. ~~国标格式入向解析~~ ✅ **V1.3 完成（#9）**：`gbz_intake.py` —— 单件（185.4/185.7）解析 + §6.2~6.4 五类报文（`tool_request`/`tool_sync`/`tool_update`/`tool_invoke`/`tool_result`）+ 统一入口 `intake()` + 报送包读回 `import_bundle()`；外部件按国标必需项**宽松校验**（允许无 `x-tdca-*`）、**缺失即如实标注不推测填补**、未知键记 warnings

---

*编译器国标格式输出规范 V1.1：**字段名按原文正名（D1/D2 纠偏）** + 185.4 全 15 字段 + 表 2 skills + IR 对接（#6）+ 入向兼容；20 用例全绿 + 原文逐字段审计全 MATCH ｜ 存证: GSEQ-1252*
