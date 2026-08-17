# {场景名称} 双协议化合负空间（dual-nsfl.md）

> 自动生成（dual_protocol_compiler.py）| ID92 模拟态标注: 化合产物模板
> NSFL 层级: L2-Protocol-Only（技术转译，非法律替代——口径裁定 B）

## 化合负空间规则集

| 来源 | 规则数 | 说明 |
|------|--------|------|
| TDCA 公共 | 核心规则集（指针） | 三不可/三可/两层边界/三档熔断（引用 TDCA-NSFL-v0.2，无硬编码计数） |
| 场景特定 | {N} 条 | SCENE-NSFL-*（法律/伦理/业务扩展） |
| **合计** | 核心规则集 + {N} 条 | 公共规则不可删减，场景规则追加 |

## 触发动作语义

- BLOCK（CRITICAL）: 绝对负空间，无替代路径，立即停止
- HUMAN_OVERRIDE（BLOCKING）: 暂停执行，人类介入（慢系统不可绕过 ID71）
- ALT_PATH（WARNING）: 提供替代路径

## 触发记录

所有触发必须登记 scene_nsfl_trigger 并关联 NCA（TDCA-NCA-{date}-{seq}-SCENE-NSFL）
