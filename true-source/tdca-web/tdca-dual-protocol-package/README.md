# TDCA 双协议架构协议包（TDCA-DUAL-PROTOCOL-001）

> 版本: V1.0.0 | 发布日期: 2026-08-11 | 状态: 待人类签批
> 制度锚定: ID35（制度-技术同构）/ ID81（五元拓扑空间）/ ID90（最小化合原则）/ CHEM-001~002（化学热力学原理簇）/ MRCR（多角色兼容性规则）/ MEMO-022（会话分片协议）
> 依据设计文档: TDCA-DUAL-PROTOCOL-001-V1.0（双协议架构协议包设计稿）
> 生成者: Reasonix Protocolizer | 审查: REV-DUAL-PROTOCOL-001（待执行）

---

## 六要素声明（本协议包作为 FC 的制度约束）

| 六要素 | 声明 |
|--------|------|
| 目标函数 | 将双协议架构设计稿实现为**可运行的协议包**：TDCA 公共制度（全局坐标系）+ 用户场景制度（局部坐标卡）的双协议化合基础设施，含化合引擎、场景模板、行业示例、测试与文档 |
| 约束矩阵 | 宪法十六条 + UPDA-v2.0 + NSFL-V0.2 + ID35 同构 + ID81 五元拓扑 + ID90 最小化合 + CHEM-001/002 + MRCR + MEMO-022；宪法条文仅引用指针（口径裁定 B） |
| 先验分布 | TDCA-DUAL-PROTOCOL-001-V1.0 设计稿；TDCA-METHODOLOGY-001-V1.1；TDCA-PACK-001（协议包 V1.3 已签批）；10.37 亿 tokens / ¥37.26 实证 |
| 配置权边界 | L2 配置权市场层；场景制度不得触碰 L0 法律底层；化合产物必须生成 NCA 存证；所有模板标注 ID92 模拟态 |
| 预期分配 | 可运行协议包（骨架 + 公共制度 + 场景模板 + 引擎 + 示例 + 测试 + 文档）+ 测试全绿 + NCA 存证 + 审查通过记录 |
| 审计轨迹 | TDCA-NCA-20260811-006-DUAL-PROTOCOL + REV-DUAL-PROTOCOL-001 + 人类签批记录 |

---

## 一、双协议架构是什么

**双协议架构** = TDCA 公共制度协议（全局坐标系）+ 用户场景制度协议（局部坐标卡）

```
TDCA 公共制度（Public Protocol）         用户场景制度（Scenario Protocol）
├── 宪法十六条（不可修改）               ├── 场景约束矩阵（行业特定）
├── UPDA 通用定价算法                    ├── 场景流程规范（业务特定）
├── NSFL 负空间函数语言                  ├── 场景负空间清单（领域红线）
├── 核心公理（ID29~ID38）                ├── 场景术语表（术语映射）
└── 术语规范（TDCA-TERMS-v3.0）          └── 场景审查标准（合规特定）
        │ 化合（CHEM-001/002） ↓
        双协议化合产物（Dual-Protocol NCA）
        ├── 化合配置权边界 ├── 化合负空间规则
        └── 化合审查模板   └── 化合 NCA 存证链
```

## 二、协议包目录结构

```
tdca-dual-protocol-package/
├── README.md                       # 本文件：协议包说明 + 六要素声明
├── LICENSE                         # MIT（TDCA 公共部分）
├── tdca-public/                    # TDCA 公共制度（只读，不可修改）
│   ├── constitution/               # 宪法/UPDA/NSFL/TERMS 引用指针（L0 不内嵌全文）
│   ├── principles/                 # 核心公理 ID29~ID38 摘要
│   └── templates/                  # six-elements-template.md
├── tdca-scenario/                  # 用户场景制度（可配置）
│   ├── README.md                   # 场景制度编写指南
│   └── scene-*.md                  # 场景宪法/约束/负空间/术语/审查/定价 6 模板
├── tdca-dual/                      # 双协议化合产物（自动生成 + 示例）
│   └── dual-*.md                   # 化合宪法/约束/负空间/六要素/审查模板
├── engine/                         # 双协议化合引擎
│   ├── dual_protocol_compiler.py   # 化合编译器（同构校验 + 最小化合判定 + 化合）
│   ├── scene_validator.py          # 场景制度校验器
│   ├── nca_generator.py            # 双协议 NCA 生成器
│   └── mrcr_manager.py             # 多角色兼容性管理器
├── examples/                       # 行业示例（金融/医疗/政务/教育）
├── tests/                          # 测试套件
│   ├── test_compilation.py
│   ├── test_validation.py
│   └── test_mrcr.py
└── docs/                           # 文档
    ├── user-guide.md               # 用户操作指南
    ├── developer-guide.md          # 开发者指南
    └── api-reference.md            # API 参考
```

## 三、快速开始（3 步）

1. **复制场景模板**：`cp -r tdca-scenario/ ./my-scenario`，填写 `scene-constitution.md` / `scene-constraints.md` / `scene-nsfl.md`（3 个必须文件）
2. **校验**：`python engine/scene_validator.py tdca-public/constitution/TERMS-v3.0.md ./my-scenario`
3. **化合**：`python engine/dual_protocol_compiler.py --tdca-path tdca-public/ --scene-path ./my-scenario --scene-name my-scenario --output ./dual-protocol --mode strict`

## 四、关键原则

| 原则 | 内容 | 制度依据 |
|------|------|---------|
| 同构校验 | 场景制度必须与 TDCA 公共制度同构映射 | ID35 |
| 局部坐标卡 | 场景制度是全局坐标系的局部坐标卡，变换可逆、不破坏拓扑 | ID81 |
| 最小化合 | 不可拆分性 + 涌现价值 + 非线性 三条件通过才启动双协议 | ID90 |
| 化合模型 | 公共制度 + 场景制度 → 配置权调用（活化能）→ 化合产物（NCA） | CHEM-001/002 |
| 场景隔离 | 独立审计、独立演化（OTA）、场景自适应弹性膜 | MRCR |

## 五、合规红线

- 场景制度**不得触碰** L0 法律底层；宪法条文仅引用指针（口径裁定 B）
- 场景负空间**必须完整包含** TDCA-NSFL 全部规则，可扩展不可删减
- 化合产物**必须生成** NCA 存证并关联 TDCA-NCA 主链
- 双协议启动**必须通过**最小化合判定三条件（ID90）
- 所有模板保持模拟态/制度约束语义（ID92），不构成真实配置权执行路径

## 六、与 PACK-001 的联动策略（并行，人类已确认 2026-08-11）

**联动策略 = 并行独立发布**：本协议包不依赖 TDCA-PACK-001（单协议包 V1.3）的版本锁定，可独立发布、分轨迭代。

- 依赖关系：共享 TDCA 公共制度（宪法/UPDA/NSFL/TERMS 引用指针）+ 口径裁定 A/B，无代码级依赖
- 版本策略：PACK-001（基础包）与 DUAL-PROTOCOL-001（架构包）独立版本号，独立 OTA
- 产品矩阵：「单协议基础包 + 双协议架构包」并行覆盖入门到生产全谱系

## 七、版本与签批

| 版本 | 日期 | 变更 | 审查 | 签批 |
|------|------|------|------|------|
| V1.0 | 2026-08-11 | 由 TDCA-DUAL-PROTOCOL-001-V1.0 设计稿实现：骨架 + 公共制度 + 场景模板 + 引擎 + 示例 + 测试 + 文档。NCA 编号注：设计稿原归档 003-DUAL-PROTOCOL 与 PACK-001 已占 003-PACK 冲突，实现改序 **006-DUAL-PROTOCOL**（REV-DUAL #12） | REV-DUAL-PROTOCOL-001（修复后待复审） | [待签署] |
| V1.1 | 2026-08-11 | REV-DUAL-PROTOCOL-001 修复 12 项：宪法条文错引 C16（#1）/ID86 法律表重分类（#2）/术语权威（#3）/NSFL 25 无溯源（#4）/运行期 FC 独立（#5）/ID82 绑定（#6）/口径统一（#7）/YAML 契约重构（#8）/测试夹具（#9）/ID92 水印（#10）/字段表述（#11）/改序记录（#12） | tdca-compliance-auditor REV-DUAL-PROTOCOL-001（BLOCKING→修复后复审） | [待签署] |

---

> 本协议包为 TDCA 生态基础设施，遵循 ID77：协议层永久免费。
> NCA 存证: TDCA-NCA-20260811-006-DUAL-PROTOCOL
