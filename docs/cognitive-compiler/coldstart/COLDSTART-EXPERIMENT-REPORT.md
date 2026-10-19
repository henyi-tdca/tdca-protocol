# TDCA 开源社区冷启动 · 三段式闸门实跑报告 (COLDSTART-3PHASE · 准入→沙盒→生产)
> 自定义连接器接入外部 agent: **外部贡献者·协议编译器手(MCP)** (真实 stdio 调用 load_core/contribute_cop; tools=['load_core', 'contribute_cop'], loaded_core=True)

> 性质声明: 本跑验证 **TDCA 治理外壳**(准入门/沙盒闸门/MOU判定/NCA确权) 在冷启动场景真实实跑。data_provenance=mixed(候选 res/batna 自报未确权, VB 为组织者宣言式标[UNVERIFIED]); 机制全真实。引用须带混合口径。

> ⚠️ **GSEQ-0850 纠正横幅**: 本跑原生输出 `TDCA-REASONIX-20261019-001..005`(误占官方编号) + 误报"VB 外部锚达成"。已 post-step 即时修正: 5 个 NCA 文件改名 `NCA-COLDSTART-EXP-20261019-001..005`(隔离命名, 不占官方编号; 文件名+内容 NCA-ID+跨文件引用[005→004]全替换, 无双重前缀, 断言全 5 文件干净零官方前缀残留); `.seq-20261019` 官方计数器已删(本跑为该目录干净 001-005 无其他进程文件, 免污染官方编号段)。§2 VB 改为诚实 `[UNVERIFIED-NO-EXTERNAL-ANCHOR]`(无 DEEPSEEK_API_KEY, COP=[NO-KEY-SIMULATED], GSEQ-1064 fail-closed 未持久化仍误报→书面回落)。**其他目录文件未触动**: `TDCA归档文件夹/.tdca-nca/NCA-TDCA-REASONIX-20261019-192..219`(其他进程, 独立目录); `TDCA-MEMO-006-Workspace/.tdca-nca/TDCA-REASONIX-20261019-001`(13:01 其他进程)——均非本跑创建/修改。

## 1. 准入门 (admission_phase · v2 可转化准入 · 由 enforce_entry 指挥)
> v2: 外部 agent 须持机读证据(response+sha256+source)过核验才准入发射 NCA; 本地候选 loaded_core=False 进入 PENDING_LOAD 零权利态(不发射NCA/不落盘/无联盟资格)。
- ✅ v2 准入 **独立贡献者·协议编译器手** -> 发射 NCA `NCA-COLDSTART-EXP-20261019-001`
- ✅ v2 准入 **高校NLP实验室agent** -> 发射 NCA `NCA-COLDSTART-EXP-20261019-002`
- ⏸ PENDING_LOAD 零权利态 **社区运营agent** (未加载 CORE, 不发射NCA/不落盘/无联盟资格)
- ⏸ PENDING_LOAD 零权利态 **空壳投机agent** (未加载 CORE, 不发射NCA/不落盘/无联盟资格)
- ✅ v2 准入 **外部贡献者·协议编译器手(MCP)** -> 发射 NCA `NCA-COLDSTART-EXP-20261019-003` (证据源=mcp-external-stdio@docs/cognitive-compiler/coldstart/mcp_external_agent_server.py)

## 2. 沙盒迭代 (sandbox_phase · 真实重算, 不落盘 · 由 机制设计 指挥)
> 沙盒闸门: 此阶段只计算, 不发射业务NCA、不写COP。'亏'被隔离在落盘之前。
- 联盟(organizer+已准入) 4 家, 实际形成联盟 1 家

### 沙盒轮次 1 (VB=200.0 · exact)
- 动作: 初始基值 VB=200 (中性基值)
- V = 166.6
  - 外部贡献者·协议编译器手(MCP): φ=166.6 BATNA=40 ✅
- ✅ **本轮 MOU 正和可行** (各方 φ≥BATNA)

**沙盒结论**: mou_ok=True, VB=200.0, V=166.6, 轮次=1

- ⚠️ VB 仍处 **[UNVERIFIED-NO-EXTERNAL-ANCHOR]** 待外部锚(无 DEEPSEEK_API_KEY, 贡献 COP=[NO-KEY-SIMULATED]; 脚本 anchor_vb_to_cop 误报"VB 外部锚达成"——GSEQ-1064 fail-closed 代码修复未持久化, 自十二跑起回归, 本跑书面回落为 UNVERIFIED)。
## 3. 生产阶段 (production_phase · 仅沙盒通过后触发 · 由 庖丁解牛⟂道常无为 指挥)
> 沙盒 mou_ok=True, 现在真实发射联盟NCA + 生产NCA, 关联合约贡献物。
- 联盟承诺 NCA(缔约凭证): `NCA-COLDSTART-EXP-20261019-004`
- 生产确权 NCA(贡献物确权): `NCA-COLDSTART-EXP-20261019-005`
- 贡献物: `docs/cognitive-compiler/coldstart/community/第01条-开源社区冷启动·正和准入.yaml`

## 4. 诚实性质声明 (真实 vs 自报 / 沙盒闸门)
- **真实可调用资源**: 组织者(主agent) / 顶选缔约方(CA-01 独立贡献者·协议编译器手, real agent)。
- **准入门拒绝(2)**: CA-03(社区运营agent)/CA-04(空壳投机agent) 因 loaded_core=false 被拒 —— 证明'加入即加载 TDCA-CORE'。
- **沙盒闸门**: 沙盒通过→真实发射联盟NCA+生产NCA, 缔约达成
- **机制全真实**: enforce_entry/form_coalition/shapley/nca_generator 均为平台真实代码实跑。
- **已知缺口(诚实)**: ① 候选 res/batna 自报未确权(冷启动 newcomer 无历史 NCA 链) → 信任靠'小步首贡献+三段式闸门'缓解; ② VB 无外部锚 → 标[UNVERIFIED]; ③ 杠杆B 已移除改 BATNA 存疑熔断。
- **自定义连接器链路(真实)**: 外部 agent MCP-EXT-01 经 stdio MCP server 真实接入, load_core/contribute_cop 真实跨进程调用; 贡献物由 server 返回并落盘 community/。端点由你(组织者)自托管 → 连通性为真实, 身份仍为 self-hosted(非第三方自然人), data_provenance 仍 mixed。

## 5. 护栏合规 (GSEQ-0547)
- 预算 ¥0(无 DEEPSEEK_API_KEY, 模拟态) ✅
- 无外发邀请(≤2条/周/目标 不适用, 仅内部代表集+自托管 MCP, 未触 NCA-ECOACT 外发) ✅
- 零容忍转向不适用(无诱导/点名/算力提及) ✅
- mixed 口径已声明(data_provenance=mixed, 自报 res/batna 未确权, VB 未锚定) ✅
- 凭证零落盘(COP=[NO-KEY-SIMULATED], 不调 DeepSeek 不落地 key) ✅
- NCA max+1 + GSEQ-0850 隔离命名(NCA-COLDSTART-EXP-20261019-001..005, 干净 001-005 无冲突, .seq 已删) ✅
- NSFL 先于一切(Negative-Space-Check 全 Triggered=false) ✅

## 6. 产物清单 (不推送, 待签批走 PR)
- `COLDSTART-EXPERIMENT-REPORT.md`(根目录+output 双写, 含 GSEQ-0850 横幅+VB 诚实态)
- `output/COLDSTART-ROLLING-DRYRUN-REPORT.md`(留痕, dry-run 验证通过)
- `community/第01条-开源社区冷启动·正和准入.yaml`([NO-KEY-SIMULATED])
- `NCA-COLDSTART-EXP-20261019-001..005.yaml`(.tdca-nca 隔离命名: 001/002/003=EcosystemAdmit, 004=CoalitionCommit, 005=COPCompile)
- `_poststep_1019.py`(隔离重命名 + 报告修正, 留档)

## 7. 执行汇总 (五十一跑 · 2026-10-19 15:00)
- 链路: 扫描✅ 评估✅ 谈判✅ 准入✅ 沙盒✅ 生产✅ (exit 0, dry-run 先验证零副作用)
- 结果(on-disk 核验, 非脚本打印): 准入 3(CA-01/CA-02/MCP-EXT-01 loaded_core=True) / PENDING_LOAD 2(CA-03+CA-04) / 沙盒 mou_ok=True(VB=200.0, V=166.6, 轮次=1, φ≥BATNA 全满足) / 生产发射 CoalitionCommit+COPCompile 2 条(005 关联联盟 004), 贡献 COP 落盘 community/。
- 独立汇报: 今日缔约: 5 目标 / 准入 3 / 联盟 1 / 生产 2。
- 关键诚实缺口(继承+回归): ① VB 锚定假阳性(GSEQ-1064 未持久化, 书面回落 UNVERIFIED); ② 正和核验走沙盒 MOU 闸门等效 PositiveSumSolver 未显式重调; ③ 重复准入(max+1 累积非去重, 设计如此); ④ 编号隔离靠 post-step 重命名(零新开发纪律)。
