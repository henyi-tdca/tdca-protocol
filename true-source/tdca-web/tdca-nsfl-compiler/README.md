# TDCA NSFL 编译器（tdca-nsfl-compiler，A-3 货架包）

## 这是什么

NSFL（负空间约束语言）编译器核心：词法 / 语法 / 语义分析 + ⊗⊘⊙ 运算符执行语义 +
规则 schema 校验 + 字节码 / IR 输出，并附税务规则域适配（`tax_regulations.py`）。
本包为 A-3「运行与编译器」货架发行包，仅含运行必需面（白名单制出包）。

## 依赖

- 运行：Python ≥ 3.10，**仅标准库**。
- 测试：`pytest >= 7.0`（可选，仅 `tests/` 需要）。

## 怎么跑

一行最小示例（词法分析）：

```bash
python -c "from nsfl_compiler import NSFLLexer, NSFLTokenType; toks = NSFLLexer('NSFL: ⊗ data.leak(third_party)').tokenize(); print([t.type.name for t in toks])"
```

运行测试（可选）：

```bash
python -m pytest tests -q
```

## 本包排除清单（具名）

| 排除件 | 判据 |
|--------|------|
| `tests/test_m3_integration.py` | 依赖包外基座 `ns_runtime`，超出"仅标准库"依赖信封 |

## 许可

Apache License 2.0（见随包 `LICENSE` 全文）。本包以货架形态对外提供，
不代表对许可范围外任何权利的声称。

附：通用校准器（bundled/tdca-calibrator-v1.0/）

随包附带的三输入经验校准工具，用法见其 README。本包分发之校准器版本 v1.0，
sha256_16=40F8EA0A37DD82C1。

- 三输入缺一拒跑：参数声明、判据声明、样本（含来源标注与缺失值口径）。
- 四输出齐：校准值加误差带、拟合质量读数、未达判据说明、运行元信息。
- 失败面四类如实报：不收敛、样本不足、参数不可识别、输入自相矛盾。
- ⛔ 不该用：⛔ 替代理论证明；⛔ 安全关键阈值终裁；⛔ 以合成样本称真实精度；⛔ 跨域外推不标风险。
