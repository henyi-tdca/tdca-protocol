# tdca-scenario/ —— 场景制度编写指南

> 层级: L2 配置权市场层（可配置）| 依据: TDCA-DUAL-PROTOCOL-001-V1.0 设计稿
> **ID92 模拟态标注**: 本目录模板为可复制产物，不构成真实配置权执行路径

## 场景制度的本质

用户场景制度是 **TDCA 公共制度的局部坐标卡**（ID81）：
- 必须服从 TDCA 宪法十六条，不得与任何条款冲突（ID35 同构）
- 必须完整包含 TDCA-NSFL 全部规则，可扩展不可删减
- 必须通过最小化合判定三条件（ID90）才启动双协议化合

## 文件清单（3 必须 + 3 可选）

| 文件 | 必须/可选 | 内容 |
|------|----------|------|
| `scene-constitution.md` | 必须 | 场景宪法（场景声明/核心原则/约束矩阵扩展/负空间扩展/审查标准/术语表） |
| `scene-constraints.md` | 必须 | 场景约束矩阵（目标扩展/约束扩展/配置权边界扩展/审查标准扩展） |
| `scene-nsfl.md` | 必须 | 场景负空间（TDCA 规则自动引用 + 场景特定规则扩展） |
| `scene-terms.md` | 可选 | 场景术语表（映射至 TDCA 术语） |
| `scene-review.md` | 建议必填（场景制度委员会审批前置） | 场景审查标准（行业合规审查项）；引擎运行时仅强制 3 必须文件，审查标准为合规审批前置 |
| `scene-pricing.md` | 可选 | 场景定价规则（必须兼容 UPDA 基础框架） |

## 编写流程

1. 复制本目录为 `./my-scenario`
2. 填写 3 个必须文件（场景名称、核心原则、场景特定负空间、审查项）
3. 运行校验器：`python engine/scene_validator.py tdca-public/constitution/TERMS-v3.0.md ./my-scenario`
4. 运行化合引擎：`python engine/dual_protocol_compiler.py --tdca-path tdca-public/ --scene-path ./my-scenario --scene-name my-scenario --output ./dual-protocol --mode strict`
5. 场景制度委员会签批 → 发布化合产物

## 合规红线

- 场景制度**不得触碰** L0 法律底层（宪法条文仅引用指针）
- 场景负空间**不得删除** TDCA 公共负空间任何规则
- 场景术语**必须映射**至 TDCA 术语（100% 映射）
- 场景 OTA 升级必须经过同构校验 + 最小化合判定 + 委员会签批
