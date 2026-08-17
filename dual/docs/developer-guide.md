# 开发者指南（developer-guide.md）

> TDCA-DUAL-PROTOCOL-001 | 面向引擎扩展开发者 | ID92 模拟态标注

## 架构总览

```
tdca-public/  ──►  DualProtocolCompiler  ──►  tdca-dual/（化合产物）
tdca-scenario/ ──►  (加载 → 同构校验 ID35 → 最小化合判定 ID90 → 化合)
                       │
                       ├── SceneValidator（场景制度实时校验）
                       ├── DualNcaGenerator（化合 NCA 存证）
                       └── MRCRManager（多角色兼容性）
```

## 核心流程（DualProtocolCompiler）

1. `load_tdca()` —— 加载 TDCA 公共制度（引用指针）
2. `load_scene()` —— 加载场景制度（3 必须 + 3 可选）
3. `validate_isomorphism()` —— 同构校验（ID35）：服从声明 + NSFL 覆盖 + strict 冲突扫描
4. `check_minimal_compound()` —— 最小化合判定（ID90 三条件）
5. `compile()` + `export()` —— 化合 + 导出 dual-* 产物 + dual-nca.json

## 扩展指南

### 新增行业示例
1. 复制 `examples/finance/` 为 `examples/{industry}/`
2. 修改 4 文件（宪法/约束/负空间/审查），使用 `{INDUSTRY}-NSFL-*` 规则前缀
3. 运行 `python engine/scene_validator.py tdca-public/constitution/TERMS-v3.0.md examples/{industry}`
4. 运行化合引擎验证

### 新增引擎能力
- **新校验规则**：扩展 `SceneValidator`（同构/覆盖/六要素/术语四类方法）
- **新化合输出**：扩展 `DualProtocolCompiler.export()`（dual-* 文件生成）
- **新角色**：扩展 `MRCRManager.ROLE_PERMISSIONS` + `SCENE_PROHIBITION_KEYS`

## 测试

```bash
cd tdca-dual-protocol-package
python -m pytest tests/ -v
```

| 测试文件 | 覆盖 |
|---------|------|
| test_validation.py | 场景校验（宪法/负空间/六要素/缺失检测） |
| test_compilation.py | 化合（加载/同构/最小化合/导出/冲突检测） |
| test_mrcr.py | 角色（注册/隔离/权限/禁止/审计） |

## 制度约束

- 所有公开函数须含六要素 docstring（本协议包代码遵循）
- 引擎不生成可绕过人类签批的执行路径（慢系统不可绕过 ID71）
- 化合产物必须 NCA 存证（制度同构跃进 ID82 硬约束之一：接口熵=0 的产物侧表达）
