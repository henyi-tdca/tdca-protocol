# API 参考（api-reference.md）

> TDCA-DUAL-PROTOCOL-001 | ID92 模拟态标注

## DualProtocolCompiler（engine/dual_protocol_compiler.py）

| 方法 | 签名 | 说明 |
|------|------|------|
| load_tdca | `load_tdca() -> dict` | 加载 TDCA 公共制度引用指针 |
| load_scene | `load_scene() -> dict` | 加载场景制度（缺必须文件报错） |
| validate_isomorphism | `validate_isomorphism() -> bool` | 同构校验（ID35），错误入 validation_errors |
| check_minimal_compound | `check_minimal_compound() -> tuple[bool, str]` | 最小化合判定（ID90 三条件） |
| compile | `compile() -> dict` | 化合产物结构（metadata/constitution/constraints/nsfl/six_elements/review） |
| export | `export(output_dir: str) -> str` | 导出 dual-* 文件 + dual-nca.json |

**CLI**: `python engine/dual_protocol_compiler.py --tdca-path <p> --scene-path <p> --scene-name <n> --output <dir> --mode strict|lenient`

## SceneValidator（engine/scene_validator.py）

| 方法 | 签名 | 说明 |
|------|------|------|
| validate_scene_constitution | `(path: str) -> bool` | 校验服从声明（TDCA-CONST/不得冲突） |
| validate_scene_nsfl | `(path: str) -> bool` | 校验 TDCA-NSFL 引用 + 场景规则 |
| validate_scene_constraints | `(path: str) -> bool` | 校验六要素覆盖（6/6） |
| print_report | `() -> None` | 打印 errors/warnings 报告 |

**CLI**: `python engine/scene_validator.py <tdca_terms_path> <scene_dir>`（退出码 0=通过）

## DualNcaGenerator（engine/nca_generator.py）

| 方法 | 签名 | 说明 |
|------|------|------|
| generate | `generate(product: dict | None) -> dict` | 化合 NCA（MEMO-006 11 字段 + Scope + MOU-Anchor） |
| save | `save(nca: dict, output_dir: str | None) -> str` | 保存 dual-nca-{scene}.json |

**CLI**: `python engine/nca_generator.py --scene-name <n> --scene-version <v> --output <dir>`

## MRCRManager（engine/mrcr_manager.py）

| 方法 | 签名 | 说明 |
|------|------|------|
| register_role | `(user_id, role, scene) -> None` | 注册场景角色（隔离） |
| check_permission | `(user_id, scene, action) -> bool` | 权限检查（含禁止项） |
| audit_action | `(user_id, scene, action, result) -> dict` | 审计记录 |
| get_audit_trail | `(user_id, scene) -> list` | 场景独立审计轨迹 |
| get_role | `(user_id, scene) -> str | None` | 角色查询 |
| scene_users | `(scene) -> list` | 场景用户视图 |
| set_scene_prohibitions | `(scene, prohibitions: dict) -> None` | 注入场景负空间（测试/接入） |

## 数据契约

### 化合产物（dual_protocol）
```yaml
dual_protocol:
  metadata: { tdca_version, scene_name, scene_version, compilation_mode, compilation_time, compiler }
  constitution: { hierarchy, conflict_resolution }
  constraints: { tdca_base, scene_extension, merged }
  nsfl: { tdca_rules, scene_rules, total_rules, merged_rules }
  six_elements: { template }
  review: { base_review, scene_review, merged_review }
```

### 化合 NCA（dual-nca.json）
MEMO-006 附录 C 11 字段 + `Scene`（name/version/tdca_version/compiler）+ `MOU-Anchor`（模拟态）。
