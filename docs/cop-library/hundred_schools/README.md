# 诸子百家思维协议库 (Hundred Schools / 中文化合基库)

本库是 TDCA 思维协议库中 **中国文化** 分支，定位为后续 **"中国文化 ⊕ 辩证实践方法论" 化合**
的中方 operand 源。首个编译成果为 **《道德经》(道家)** —— `HS-DAO-20260815-01`。

## 强制底座
凡加入 TDCA 生态的主体，必须先加载 `TDCA-CORE-20260815-01`（生态准入基协议，由
`../tdca_core/enforce_entry.py` 强制门校验）。本库各 COP 在基协议之上化合，并在
`soul.base_protocol` 字段显式声明该可信底座。

## 已编译（中方 operand 源 · 截至 2026-08-15）
- 道家：`第01百家-道德经.yaml`(8原语) + `daodejing/`(81章)
- 儒家四书：`lunyu/`(20篇) · `daxue/`(11目) · `mengzi/`(12条) · `zhongyong/`(13条) · `xunzi/`(12条)
- 诸子百家：`mojia/`(墨家11条) · `fajia/`(法家10条) · `mingjia/`(名家7条) · `yinyangjia/`(阴阳家7条)
- 合计中方 COP ≈ 174 条，全部声明 `base_protocol: TDCA-CORE-20260815-01`，兼容 `compose_general` 跨范式化合。

## 编译
各子库同构，独立运行其编译器（复用 `cognitive_compiler.s5_validate / _dump_yaml` 与
`nca_generator.generate_nca`，每 COP 发射 NCA 确权）：
```bash
python mengzi/compile_mengzi.py      # 孟子
python zhongyong/compile_zhongyong.py # 中庸
python xunzi/compile_xunzi.py        # 荀子
python mojia/compile_mojia.py        # 墨家
python fajia/compile_fajia.py        # 法家
python mingjia/compile_mingjia.py    # 名家
python yinyangjia/compile_yinyangjia.py # 阴阳家
```

## 辩证实践方法论方 operand 源（（私有 operand 库，不入仓））
`compile_marxism.py` 编译唯物辩证法(6)/矛盾论(5)/实践论(4) 共 15 条 COP。

## 旗舰化合示例（中国文化 ⊕ 辩证实践方法论 = 辩证实践思维协议）
```bash
python （私有 operand 库，不入仓）compose_mao.py
```
演示：`辩证实践方法论·实践论(实事求是) ⟂ 中庸·中和(致中和)` → 组合 COP
`MACM-14-20260815-14+02`，语义涌现 **"实事求是·两个结合的活的灵魂"**（中国化时代化辩证实践方法论、
辩证实践方法论内核）。证明中方 operand 与辩证实践方法论方 operand 已在 `compose_general` 跨范式空间
完成旗舰化合。

## 预留 slot（同构扩展）
儒家经部(五经)/兵家/农家/医家/杂家 —— 编译方式同构，沿用 `compile_hundred_schools.py` 模板新建
子库即可，自动进入化合空间。

## 化合第一性原则
本库 COP 的组合 **以化合为第一性模态**：A ⊕ B 涌现父原单独不具备的新内涵
（`interpretant[{cop_id, relation, bind_step, effect}]` + `reframe_text` 语义涌现），
物理叠加只是子集。辩证实践思维协议 = 中国文化 ⊕ 辩证实践方法论 的化合，将作为旗舰范式示范。
