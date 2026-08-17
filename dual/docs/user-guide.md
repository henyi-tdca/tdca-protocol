# 用户操作指南（user-guide.md）

> TDCA-DUAL-PROTOCOL-001 | 面向场景开发者 | ID92 模拟态标注

## 从零开始：创建你的第一个场景制度协议（6 步）

### Step 1: 获取协议包
```bash
# 获取协议包（git clone 或复制 tdca-dual-protocol-package/）
cd tdca-dual-protocol-package
pip install pyyaml   # 唯一依赖
```

### Step 2: 复制场景模板
```bash
cp -r tdca-scenario/ ./my-scenario
# 目录结构
my-scenario/
├── scene-constitution.md       # 场景宪法（必须）
├── scene-constraints.md        # 场景约束矩阵（必须）
├── scene-nsfl.md               # 场景负空间（必须）
├── scene-terms.md              # 场景术语表（可选）
├── scene-review.md             # 场景审查标准（建议必填：委员会审批前置）
└── scene-pricing.md            # 场景定价规则（可选）
```

### Step 3: 填写场景宪法
打开 `scene-constitution.md`，填写：场景名称、核心原则（场景第一性/合规优先/风险可控）、约束矩阵扩展（六要素）、场景特定负空间（SCENE-NSFL-*）、审查标准。

### Step 4: 运行场景制度校验器
```bash
python engine/scene_validator.py tdca-public/constitution/TERMS-v3.0.md ./my-scenario
# 期望输出: ✅ 场景制度校验通过
```

### Step 5: 运行双协议化合引擎
```bash
python engine/dual_protocol_compiler.py \
  --tdca-path tdca-public/ \
  --scene-path ./my-scenario \
  --scene-name "my-scenario" \
  --output ./dual-protocol/ \
  --mode strict
# 期望输出: ✅ 双协议化合完成 + NCA 生成 + 产物导出
```

### Step 6: 使用双协议产物进行开发
化合产物输出到 `dual-protocol/dual-protocol/`：
- `dual-constitution.md` / `dual-constraints.md` / `dual-nsfl.md`：化合制度
- `dual-six-elements.md`：化合六要素模板（每个 FC 强制声明）
- `dual-review.md`：化合审查模板
- `dual-nca.json`：化合 NCA 存证

开发时：所有代码生成遵循 dual-six-elements.md，所有审查遵循 dual-review.md，所有产出生成 Scene-NCA 关联到 dual-nca.json。

## 场景制度 OTA 升级

```
[场景制度委员会提案] → 变更影响分析 → 同构校验 → 最小化合判定
→ 重新化合 → 差异测试 → 人类签批 → 发布 Δ 修正案 → 自动更新
```

| 版本类型 | 触发 | 审批 | 影响 |
|---------|------|------|------|
| major | 场景核心原则变更 | 委员会全票通过 | 所有项目重新化合 |
| minor | 场景约束矩阵扩展 | 委员会多数通过 | 可选升级 |
| patch | 场景负空间规则修正 | 快速通道 | 自动推送 |

## 合规红线

- 场景制度不得触碰 L0 法律底层（宪法仅引用指针）
- 场景负空间必须完整包含 TDCA-NSFL 全部规则
- 双协议启动必须通过最小化合判定三条件（ID90）
- 化合产物必须生成 NCA 存证并关联 TDCA-NCA 主链
