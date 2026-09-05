# cop-compiler · COP 编译器（生产化打包库 · 源码发布版）

> 版本: V1.0.0 ｜ 来源: TDCA-COP-COMPILER-001（M1-M4 FROZEN，DCD-COPCOMPILER-M1/M2/M3/M4-FROZEN-001）
> 许可: Apache-2.0（本目录独立 LICENSE，与仓库根双许可口径一致——见 core-go/ 先例）
> 落位: docs/cognitive-compiler/cop-compiler/（门户「COP 编译器」解锁入口）

## 结构

```
cop-compiler/
├── LICENSE                  # Apache-2.0 全文
├── cop_compiler/__init__.py # 生产化入口（51 符号导出 + 便捷 API compile_cop/batch_compile）
├── compiler_src/            # 编译引擎源模块（语义层/批产/schema 对齐/接线 + 传递依赖）
│   ├── semantic_layer.py    #   U0 定值/负空间继承/U_CDE 联合/E 定标
│   ├── batch_pipeline.py    #   7 域一键编译/72 文件/强制门（LIB → cop-library 数据）
│   ├── schema_alignment.py  #   FORM-001 PART A-F 对齐
│   ├── compiler_wiring.py   #   NCA/NSFL/强制门接线
│   ├── cognitive_compiler.py / compile_thirty_six_stratagems.py
│   ├── nca_generator.py / nsfl_runtime.py / tdca_config.py
│   └── e_calibration_sim.py / e_calibration_review.py / 麦肯锡思维协议.yaml
└── tests/                   # 引擎 5 模块测试 + 包测试（pytest，101 用例全绿）
```

## 运行前置（数据依赖）

- 批产与语义实证需 **cop-library 数据**（7 域 COP yaml）——本仓库 `docs/cop-library/` 已在架；
- 本地运行时将 `cop-library/` 置于本包上级目录（`batch_pipeline.LIB` 默认 = `本包上级/cop-library`，单行常量可配），或 symlink 指向 `docs/cop-library`；
- `compiler_wiring` 的强制门复用 `cop-library/tdca_core/enforce_entry.py`（同源只读引用）。

## 使用

```python
import sys
sys.path.insert(0, "<本目录>")          # 例 docs/cognitive-compiler/cop-compiler
import cop_compiler as CC

cop = yaml.safe_load(open(CC.LIB + "/stratagems/第36计-走为上.yaml", encoding="utf-8"))
CC.compile_cop(cop)                     # 语义增强（U0）
CC.batch_compile("mechanism_design")    # 单域批产
CC.get_calibration()                    # E-1=0.15 / E-2=0.2 / E-3=0.5-0.3-0.2
```

## 测试

```bash
cd tests && python -m pytest -q
```

## 纪律

- 引擎源 = M1-M3 FROZEN 基线副本（Apache 头增补；逻辑未改写）；cop-library 数据只读引用不改写；
- E 定标 V1.0-TENTATIVE 沿用（修订走 T-068）；生产化修订走 DCD 变更。

---
*U1b 源码发布版（方案 B：包 + compiler_src 自包含）｜ Apache-2.0 ｜ 数据依赖 docs/cop-library 在架*
