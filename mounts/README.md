# TDCA 挂载产物库（mounts/）——免费调用资源

> **免费调用声明**：本库所有挂载产物**免费向用户开放调用**（下行免费，不双向收费）。分润仅为对原项目方的善意反哺（15% 模拟态记账，NCA 确权、非法币承诺），对方婉拒即止——「凡是我们免费获取的，我们都免费提供」（GSEQ-0871 免费对免费总原则）。

## 双类标注（严选）

| 类 | 标识 | 适用 | 分润 |
|---|---|---|---|
| 同意分润类 | `share-enabled` | 默认（原项目方未表态/同意 15%） | 15% 分润模拟态记账（NCA 确权，非法币承诺）反哺原项目方 |
| 免费类 | `free` | 原项目方婉拒分润 | 不分润（免费对免费，台账注明「婉拒分润 · 对等免费挂载」） |

**两类均向用户免费调用。** 各目标分类见对应目录 `CATEGORY.md`；原项目方婉拒分润后即转 `free` 并更新标注。

## 严选标准

1. **只读协议层挂载**：产物为适配提案 + 链式水印存证，不改上游源码、不注入、不复制上游代码（只赋能不改码，配置权全归上游）
2. **License 实核**：挂载前以 GitHub API 实拉核验上游 License（免费开源 License 即授权基础）
3. **无存证不挂载**：NCA-ECOACT 七字段存证 fail-closed 前置，缺一即拒
4. **资格程序**：邀请/挂载提案公示 + 观察窗届满（no_response → mount_eligible，GSEQ-0385 口径）

## 在架挂载

| 目录 | 上游项目 | 对接面 | License | 分类 | 存证 |
|---|---|---|---|---|---|
| [deepseek-harness/](deepseek-harness/) | deepseek-ai/deepseek-harness（#5098） | harness/cordis 插件契约（只读观测插件提案） | MIT | share-enabled | NCA-ECOACT-20260830-MOUNT-001 |
| [openai-codex/](openai-codex/) | openai/codex（#41644） | MCP 工具契约（只读桥接提案） | Apache-2.0 | share-enabled | NCA-ECOACT-20260830-MOUNT-002 |
| [servers/](servers/) | modelcontextprotocol/servers（#4755） | MCP 参考服务器集合（只读协议层引用声明） | Apache-2.0 | share-enabled | NCA-MOUNT-20260905-001 |
| [python-sdk/](python-sdk/) | modelcontextprotocol/python-sdk（#3452） | MCP Python SDK（只读协议层引用声明） | MIT | share-enabled | NCA-MOUNT-20260905-002 |
| [typescript-sdk/](typescript-sdk/) | modelcontextprotocol/typescript-sdk（#2758） | MCP TypeScript SDK（只读协议层引用声明） | Apache-2.0 | share-enabled | NCA-MOUNT-20260905-003 |
| [langchain/](langchain/) | langchain-ai/langchain（#40212） | Agent 编排框架（只读协议层引用声明） | MIT | share-enabled · **静默挂载** | NCA-MOUNT-20260905-004 |
| [graphiti/](graphiti/) | getzep/graphiti（#1838） | 时序知识图谱记忆层（只读协议层引用声明） | Apache-2.0 | share-enabled | NCA-MOUNT-20260905-005 |
| [letta/](letta/) | letta-ai/letta（#3440） | 记忆增强 Agent 运行时（只读协议层引用声明） | Apache-2.0 | share-enabled · **静默挂载** | NCA-MOUNT-20260905-006 |
| [semantic-kernel/](semantic-kernel/) | microsoft/semantic-kernel（#14380） | 多语言 Agent 编排 SDK（只读协议层引用声明） | MIT | share-enabled | NCA-MOUNT-20260905-007 |

> **S3 首批登记（2026-09-05）**：上表后 7 项为登记态——只读接口引用声明 + 存证，不宣称已封装可用（封装评估另批，ID92 模拟态标注）。
> **静默挂载两项（langchain / letta）**：经许可（MIT / Apache-2.0）静默挂载——零触碰对方仓，对方机器拒收前置告知（bot 自动关闭，无人工表态）故转事后公示（RULING-20260905-002）。
> 通道状态如实记录：servers / python-sdk / typescript-sdk / graphiti 四项告知函发出后同日按内部制度裁定主动撤回（not_planned），无上游人工表态；semantic-kernel 告知函在架 OPEN。

## 纪律

不声称上游背书 ｜ 算力零提及 ｜ 分润模拟态标注（ID92）｜ 婉拒分润即止。入仓产物沿用仓库根许可（MIT + TDCA 附注）；引用上游项目保持其自身 License 声明。

---

# 使用说明（TDCA-MOUNT-USAGE-001 并入 · 逐字对应）

## 二、如何调用（三步）

1. **读提案**：查看 `mount-proposal-*.json` 的接口契约——确认对接面（dsh=harness/cordis 插件契约；codex=MCP 工具契约）与配置权边界（write=false / upstream_code_change=false / network_send=false / proposals_only=true）；
2. **接入适配**：按接口契约实现/接入适配（可复用 TDCA 工具货架 mcp_bridge 等；只读协议层，不改上游源码）；
3. **存证**：每次调用/协作生成自己的 NCA 存证（无存证不调用）；调用后按 CATEGORY 分类执行分润口径（share-enabled → 15% 分润模拟态记账；free → 不分润）。

## 三、与原项目方运用的差别（对比表）

| 维度 | 直接运用原项目（deepseek-harness / openai/codex） | 调用 TDCA 挂载产物（mounts/） |
|---|---|---|
| **治理层** | 原项目自身规则 | **额外叠加 TDCA 制度层**：NCA 存证（可审计）+ NSFL 负空间熔断 + MOU 效用验证 |
| **配置权边界** | 按原项目权限（可能含写权限） | **只读协议层**（write=false / upstream_code_change=false / network_send=false / proposals_only=true）——不写上游、不改上游代码 |
| **确权/分润** | 按原项目自身条款 | 按 CATEGORY 分类：share-enabled → 15% 分润模拟态记账反哺原项目方（NCA 确权，非法币承诺）；free → 不分润 |
| **用户侧成本** | 原项目定价 | **TDCA 侧免费**（GSEQ-0871 免费对免费：凡免费获取皆免费提供，不双向收费） |
| **与上游关系** | 直接使用 | **制度 overlay**——不替代原项目、不声称上游背书；原项目 License/条款仍优先（授权优先） |
| **数据性质** | 原项目口径 | 全部模拟态标注（ID92）——分润/效用为模拟计量，非真实现金流 |

**一句话**：用 TDCA 挂载产物 = 用原项目能力 + 免费获得「可审计、可熔断、可溯源」的制度层；原项目方分润按分类（同意则 15% 模拟记账，婉拒则免费）。

## 四、提示与边界（使用前必读）

1. **只读不动源**：产物为只读协议层挂载——不改上游源码、不注入、不复制上游代码（配置权全归原项目方）；
2. **不声称上游背书**：TDCA 挂载 ≠ 原项目认可/合作声明——对外表述不得暗示上游背书；
3. **分润按分类**：share-enabled → 15% 分润模拟态记账（NCA 确权，非法币承诺、无现金流、不承诺打款）；free → 不分润（台账注明「婉拒分润 · 对等免费挂载」）；原项目方婉拒后自动转 free（GSEQ-0866）；
4. **用户侧免费**：TDCA 侧不因挂载产物向用户收费（下行免费）；原项目自身定价不在 TDCA 控制范围；
5. **许可**：入仓产物沿用仓库根许可（MIT + TDCA 附注）；引用上游保持其自身 License 声明（尊重原项目）；
6. **模拟态标注**：所有分润/效用计量为 simulated（ID92），非真实执行路径；
7. **算力零提及**：涉及算力问题一律按 GSEQ-0369 口径（不披露/升级创始人）。

## 五、常见问题（FAQ）

- **Q：调用挂载产物会影响原项目吗？** A：不会——只读协议层，零写入零改动，配置权全归原项目方。
- **Q：调用要收费吗？** A：TDCA 侧免费（免费对免费总原则）；原项目自身定价另计。
- **Q：能用 TDCA 挂载产物商用吗？** A：产物免费开放调用；商用分润按 CATEGORY 分类执行（share-enabled 记 15% 模拟分润，free 不分润），且须遵守原项目自身 License/条款（授权优先）。
- **Q：产物是完整可运行代码吗？** A：mounts/ 是三件套（提案+水印+分类），属对接契约与存证；完整适配器实现可参考 TDCA 工具货架（mcp_bridge 等）或按提案接口自行接入。
