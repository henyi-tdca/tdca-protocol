# 孙子兵法·真实多agent协作治理流程实跑报告 (REAL-SUNZI-3PHASE · 准入→沙盒→生产)

> 性质声明: 本跑验证的是 **TDCA 治理外壳**(准入门/沙盒闸门/MOU判定/NCA确权) 在真实平台真实实跑, **非编译内容本身**。data_provenance=mixed(4真实/3占位), VB为组织者宣言式(无外部锚, 标[UNVERIFIED]), 生产产出薄。引用须带混合口径。

## 1. enforce_entry 准入门 (admission_phase · 真实发射准入NCA)
> 准入只验证'是否接受正和博弈原则'(加载 TDCA-CORE-20260815-01), 不验证'本联盟能否正和'——后者是沙盒的事。
- ✅ 准入 **兵学战略研究院** (real=True) -> 发射 NCA `TDCA-REASONIX-20260816-001`
- ✅ 准入 **古籍训诂与文本校勘院** (real=True) -> 发射 NCA `TDCA-REASONIX-20260816-002`
- ✅ 准入 **中文语义与情报NLP所** (real=True) -> 发射 NCA `TDCA-REASONIX-20260816-003`
- ✅ 准入 **编译推理算力云** (real=True) -> 发射 NCA `TDCA-REASONIX-20260816-004`
- ✅ 准入 **智能系统建模实验室** (real=False) -> 发射 NCA `TDCA-REASONIX-20260816-005`
- ✅ 准入 **知识图谱与态势感知中心** (real=False) -> 发射 NCA `TDCA-REASONIX-20260816-006`
- ✅ 准入 **合规与可信决策审计院** (real=False) -> 发射 NCA `TDCA-REASONIX-20260816-007`
- ❌ 拒绝 **数字版权确权与IP院** (未加载 TDCA-CORE-20260815-01) -> AdmissionDenied

## 2. 沙盒迭代 (sandbox_phase · 真实重算, 不落盘)
> 沙盒闸门: 此阶段无论如何只计算, 不发射业务NCA、不写COP。'亏'被隔离在落盘之前。
- 初始候选(已准入) 7 家, 联盟互补维度: 训诂/战略/建模/图谱/NLP/合规/算力/版权

### 沙盒轮次 1 (VB=200.0 · exact)
- 动作: 初始基值 VB=200 (中性基值)
- V = 199.3
- 各方 φ vs BATNA:
  - 兵学战略研究院: φ=27.0 BATNA=30 ❌
  - 古籍训诂与文本校勘院: φ=27.0 BATNA=25 ✅
  - 中文语义与情报NLP所: φ=27.1 BATNA=26 ✅
  - 编译推理算力云: φ=27.0 BATNA=28 ❌
  - 智能系统建模实验室: φ=27.1 BATNA=28 ❌
  - 知识图谱与态势感知中心: φ=27.0 BATNA=26 ✅
  - 合规与可信决策审计院: φ=37.0 BATNA=27 ✅
- ❌ 本轮不可行, 亏方(φ<BATNA): 智能系统建模实验室(φ=27.1<BATNA=28); 编译推理算力云(φ=27.0<BATNA=28); 兵学战略研究院(φ=27.0<BATNA=30)

### 沙盒轮次 2 (VB=220.0 · exact)
- 动作: 杠杆A: 组织者任务重定价 VB→220.0 [UNVERIFIED-NO-EXTERNAL-ANCHOR] (编译《孙子兵法》为制度压力测试样本, 战略价值高于中性基值)
- V = 219.2
- 各方 φ vs BATNA:
  - 兵学战略研究院: φ=29.7 BATNA=30 ❌
  - 古籍训诂与文本校勘院: φ=29.7 BATNA=25 ✅
  - 中文语义与情报NLP所: φ=29.8 BATNA=26 ✅
  - 编译推理算力云: φ=29.7 BATNA=28 ✅
  - 智能系统建模实验室: φ=29.8 BATNA=28 ✅
  - 知识图谱与态势感知中心: φ=29.7 BATNA=26 ✅
  - 合规与可信决策审计院: φ=40.7 BATNA=27 ✅
- ❌ 本轮不可行, 亏方(φ<BATNA): 兵学战略研究院(φ=29.7<BATNA=30)

### 沙盒轮次 3 (VB=242.0 · exact)
- 动作: 杠杆A: 组织者任务重定价 VB→242.0 [UNVERIFIED-NO-EXTERNAL-ANCHOR] (编译《孙子兵法》为制度压力测试样本, 战略价值高于中性基值)
- V = 241.1
- 各方 φ vs BATNA:
  - 兵学战略研究院: φ=32.7 BATNA=30 ✅
  - 古籍训诂与文本校勘院: φ=32.7 BATNA=25 ✅
  - 中文语义与情报NLP所: φ=32.7 BATNA=26 ✅
  - 编译推理算力云: φ=32.7 BATNA=28 ✅
  - 智能系统建模实验室: φ=32.8 BATNA=28 ✅
  - 知识图谱与态势感知中心: φ=32.7 BATNA=26 ✅
  - 合规与可信决策审计院: φ=44.8 BATNA=27 ✅
- ✅ **本轮 MOU 正和可行** (各方 φ≥BATNA)

**沙盒结论**: mou_ok=True, 最终 VB=242.0, V=241.1, 迭代轮次=3 (注: VB 无外部锚上限, mou_ok=True 在算术上由重定价驱动, 见 §5 ①)

## 3. 生产阶段 (production_phase · 仅沙盒通过后触发)
> 沙盒 mou_ok=True, 现在才真实调NLP + 真实发射NCA + 真实落盘COP。
- 真实调 zh-nlp MCP: proper=["孙子", "兵者", "大事", "死生", "道者", "令民", "天者", "阴阳", "寒暑", "时制", "地者", "将者", "智信仁", "法者", "曲制", "官道", "主用", "诡道", "故能"]
- 真实调 zh-nlp MCP: classical_tokens=["孙子", "兵者", "国", "大事", "死生", "事", "校", "情", "道者", "令民", "天者", "阴阳", "寒暑", "时制", "地者", "将者", "智信仁", "法者", "曲制", "官道", "主用", "诡道", "故能"]
- 真实落盘: 回填 `C:\Users\22850\Desktop\TDCA-MEMO-006-Workspace\.tdca-protocol\cognitive-compiler\hundred_schools\sunzi\sunzi_real\第01篇-计篇-real.yaml` 的 coalition_nca=TDCA-REASONIX-20260816-008 + mou_ok + 沙盒元信息
- 联盟承诺 NCA: `TDCA-REASONIX-20260816-008` (notes 已标 data_provenance=mixed)
- 计篇生产 NCA: `TDCA-REASONIX-20260816-009`

## 4. 诚实性质声明 (真实 vs 占位 / 沙盒闸门)
- **真实可调用资源(4)**: 兵学战略研究院(主agent) / 古籍训诂院(真实Expert guji-philology) / 中文语义NLP所(真实MCP zh-nlp, jieba真算) / 编译推理算力云(真实subagent)。
- **能力角色占位(3)**: 建模/图谱/合规 —— loaded_core=true, 联盟互补维度用, 待绑定真实资源。
- **被准入门拒绝(1)**: 数字版权院(未加载基协议) —— 证明'加入生态必须加载TDCA-CORE'。
- **沙盒闸门已生效**: 沙盒通过→已真实生产落盘(发联盟NCA+生产NCA+回填COP)
- **机制全真实**: MCP握手/NLP调用/enforce_entry/form_coalition/shapley/NCA发射 均为平台真实代码实跑。
- 与旧版(run_sunzi_real.py)区别: 旧版生产落盘在沙盒判定之前(错误); 本版沙盒不过不落盘。
- **data_provenance=mixed**: 联盟承诺 NCA 标注 mixed——建模/图谱/合规 3 家无真实资源绑定却进入 form_coalition 维度覆盖与 Shapley 分配, 联盟 V 含幻影产能, 其作为签署方无法实际执行。引用须带此口径。

## 5. 已知局限与诚实评估 (实验主评审 · 2026-08-16)
- **① 杠杆A正和是定价宣言制造, 非价值发现**: VB 200→242 使所有 φ 机械抬升越BATNA, mou_ok=True 在算术上必然(无VB外部锚上限)。已加 EXTERNAL_ANCHOR+provenance 标注 [UNVERIFIED-NO-EXTERNAL-ANCHOR]; 真实化须接可比任务定价/第三方评估。
- **② 杠杆B 已移除**: 原'校准BATNA到φ'使 mou_ok=φ≥φ 重言式化; 改 BATNA存疑熔断(要求举证)。未根治自报BATNA未确权, 但不再制造假正和。
- **③ 3/7 占位方参与分配**: 建模/图谱/合规 loaded_core=true 但无真实资源, 却进 form_coalition 维度覆盖与 Shapley 分配, 联盟V含幻影产能; 联盟承诺签署方有3家无法实际执行。data_provenance=mixed。下版: 绑真实资源 或 移出分配。
- **④ 生产产出薄**: 生产=2次NLP调用+回填yaml元数据; 制度化编译内容不在本次跑。本报告验证治理外壳, 非编译本身。
- **可直接引用性**: '亏隔离在落盘之前'是治理层最强30秒演示, 可用于开源; 但须带混合口径标注(mixed: 机制真实/资源4真3占位/VB宣言式/生产薄)。

> 说明: 原 `REAL-SUNZI-3PHASE-REPORT.md` 因被实时预览面板独占锁定无法原地覆盖, 本文件为其诚实修正版(标题已降为"治理流程实跑", 性质声明改治理外壳验证)。编排器 `run_sunzi_threephase.py` 的报告生成字符串已同步修正, 关闭预览后重跑将自动再生本诚实版。
