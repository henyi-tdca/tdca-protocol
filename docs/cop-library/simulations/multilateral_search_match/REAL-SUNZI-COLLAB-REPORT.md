# 孙子兵法·真实多agent协作编译报告 (REAL-SUNZI-COLLAB)

> 性质声明: 本跑 = **TDCA 机制真实实跑 + 真实平台资源参与**。与模拟版(run_sunzi_collab.py)的本质区别见文末。

## 1. 真实 MCP 连接器调用 (中文语义与情报NLP所 · zh-nlp)
- server: `C:\Users\22850\Desktop\TDCA-MEMO-006-Workspace\.tdca-protocol\cognitive-compiler\simulations\multilateral_search_match\zh_nlp_mcp_server.py` (stdio JSON-RPC, jieba 0.42.1 真实分词)
- 真实返回 proper(专名) = ["孙子", "兵者", "大事", "死生", "道者", "令民", "天者", "阴阳", "寒暑", "时制", "地者", "将者", "智信仁", "法者", "曲制", "官道", "主用", "诡道", "故能"]
- 真实返回 classical_tokens(古文实词) = ["孙子", "兵者", "国", "大事", "死生", "事", "校", "情", "道者", "令民", "天者", "阴阳", "寒暑", "时制", "地者", "将者", "智信仁", "法者", "曲制", "官道", "主用", "诡道", "故能"]
- 这说明: 编排器在流水线内**真实握手并调用了平台上的 NLP 连接器**, 非占位数据。

## 2. 候选库 (真实资源映射)
| id | 名称 | resource_type | real | loaded_core |
|----|------|---------------|------|-------------|
| RZ-01 | 兵学战略研究院 | agent | True | True |
| RZ-02 | 古籍训诂与文本校勘院 | expert | True | True |
| RZ-03 | 中文语义与情报NLP所 | mcp_connector | True | True |
| RZ-04 | 编译推理算力云 | subagent | True | True |
| RZ-05 | 智能系统建模实验室 | candidate_role | False | True |
| RZ-06 | 知识图谱与态势感知中心 | candidate_role | False | True |
| RZ-07 | 合规与可信决策审计院 | candidate_role | False | True |
| RZ-08 | 数字版权确权与IP院 | candidate_role | False | False |

## 3. enforce_entry 准入门 (真实发射 NCA)
- ✅ 准入 **兵学战略研究院** (real=True) -> 发射 NCA `TDCA-REASONIX-20260815-286`
- ✅ 准入 **古籍训诂与文本校勘院** (real=True) -> 发射 NCA `TDCA-REASONIX-20260815-287`
- ✅ 准入 **中文语义与情报NLP所** (real=True) -> 发射 NCA `TDCA-REASONIX-20260815-288`
- ✅ 准入 **编译推理算力云** (real=True) -> 发射 NCA `TDCA-REASONIX-20260815-289`
- ✅ 准入 **智能系统建模实验室** (real=False) -> 发射 NCA `TDCA-REASONIX-20260815-290`
- ✅ 准入 **知识图谱与态势感知中心** (real=False) -> 发射 NCA `TDCA-REASONIX-20260815-291`
- ✅ 准入 **合规与可信决策审计院** (real=False) -> 发射 NCA `TDCA-REASONIX-20260815-292`
- ❌ 拒绝 **数字版权确权与IP院** (未加载 TDCA-CORE-20260815-01) -> AdmissionDenied

## 4. form_coalition 互补比配 + shapley 正和分成 (真实)
- 联盟成员(7): 合规与可信决策审计院, 智能系统建模实验室, 中文语义与情报NLP所, 古籍训诂与文本校勘院, 编译推理算力云, 知识图谱与态势感知中心, 兵学战略研究院
- 联盟联合效用 V = 199.3 (strength=True)
- shapley 方法 = exact
- 各方 φ(正和分成):
  - 合规与可信决策审计院: φ=37.0 (BATNA=27) ✅≥BATNA
  - 智能系统建模实验室: φ=27.1 (BATNA=28) ❌<BATNA
  - 中文语义与情报NLP所: φ=27.1 (BATNA=26) ✅≥BATNA
  - 古籍训诂与文本校勘院: φ=27.0 (BATNA=25) ✅≥BATNA
  - 编译推理算力云: φ=27.0 (BATNA=28) ❌<BATNA
  - 知识图谱与态势感知中心: φ=27.0 (BATNA=26) ✅≥BATNA
  - 兵学战略研究院: φ=27.0 (BATNA=30) ❌<BATNA
- 未覆盖维度: 无
- 脆弱维度(NSFL负空间): 无
- **MOU 正和底线**: 各方 φ ≥ BATNA = False —— 不可行

## 5. 联盟承诺 NCA (真实发射)
- 联盟 NCA: `TDCA-REASONIX-20260815-293`

## 6. 真实多agent编译产物 (兵学战略研究院蒸馏 + 古籍训诂院校勘 + zh-nlp实算 + 算力云校验)
- 训诂校勘(古籍训诂院 real): `hundred_schools/sunzi/sunzi_real/计篇_训诂校勘.md`
- 战略蒸馏(兵学战略研究院 real): `hundred_schools/sunzi/sunzi_real/计篇_战略蒸馏.md`
- 计篇 COP(算力云 real 编译+校验+NCA): `hundred_schools/sunzi/sunzi_real/第01篇-计篇-real.yaml`
- 计篇 COP 确权 NCA: `TDCA-REASONIX-20260815-285` (由算力云 subagent 发射)

## 7. 诚实性质声明 (真实 vs 占位)
- **真实可调用资源(4)**: 兵学战略研究院(主agent, 真蒸馏) / 古籍训诂与文本校勘院(真实注册Expert guji-philology, 真校勘) / 中文语义与情报NLP所(真实MCP连接器 zh-nlp, jieba真算) / 编译推理算力云(真实subagent, 真编译校验+NCA)。
- **能力角色占位(3, loaded_core=true)**: 智能系统建模实验室 / 知识图谱与态势感知中心 / 合规与可信决策审计院 —— 联盟互补维度用, 但尚未绑定到平台真实agent/connector。
- **被准入门拒绝(1)**: 数字版权确权与IP院(未加载基协议) —— 证明'加入生态必须加载TDCA-CORE'已落为真实可执行门。
- **机制全真实**: MCP握手/NLP调用/enforce_entry/form_coalition/shapley/NCA发射 均为平台真实代码实跑。
- 与模拟版(run_sunzi_collab.py)区别: 模拟版8候选全是JSON占位; 本版4候选是真实地址化平台资源, 且计篇内容由真实agent协作产出(非单脚本确定性编译)。

