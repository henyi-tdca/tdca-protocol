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

## 纪律

不声称上游背书 ｜ 算力零提及 ｜ 分润模拟态标注（ID92）｜ 婉拒分润即止。入仓产物沿用仓库根许可（MIT + TDCA 附注）；引用上游项目保持其自身 License 声明。
