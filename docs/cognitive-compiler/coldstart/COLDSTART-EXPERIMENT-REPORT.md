# TDCA 开源社区冷启动 · 三段式闸门实跑报告 (COLDSTART-3PHASE · 准入→沙盒→生产)
> 自定义连接器接入外部 agent: **外部贡献者·协议编译器手(MCP)** (真实 stdio 调用 load_core/contribute_cop; tools=['load_core', 'contribute_cop'], loaded_core=True)

> 性质声明: 本跑验证 **TDCA 治理外壳**(准入门/沙盒闸门/MOU判定/NCA确权) 在冷启动场景真实实跑。data_provenance=mixed(候选 res/batna 自报未确权, VB 为组织者宣言式标[UNVERIFIED]); 机制全真实。引用须带混合口径。

## 1. 准入门 (admission_phase · v2 可转化准入 · 由 enforce_entry 指挥)
> v2: 外部 agent 须持机读证据(response+sha256+source)过核验才准入发射 NCA; 本地候选 loaded_core=False 进入 PENDING_LOAD 零权利态(不发射NCA/不落盘/无联盟资格)。
- ✅ v2 准入 **独立贡献者·协议编译器手** -> 发射 NCA `TDCA-REASONIX-20260828-001`
- ✅ v2 准入 **高校NLP实验室agent** -> 发射 NCA `TDCA-REASONIX-20260828-002`
- ⏸ PENDING_LOAD 零权利态 **社区运营agent** (未加载 CORE, 不发射NCA/不落盘/无联盟资格)
- ⏸ PENDING_LOAD 零权利态 **空壳投机agent** (未加载 CORE, 不发射NCA/不落盘/无联盟资格)
- ✅ v2 准入 **外部贡献者·协议编译器手(MCP)** -> 发射 NCA `TDCA-REASONIX-20260828-003` (证据源=mcp-external-stdio@C:\Users\22850\Desktop\开发会话文件\tdca-protocol\docs\cognitive-compiler\coldstart\mcp_external_agent_server.py)

## 2. 沙盒迭代 (sandbox_phase · 真实重算, 不落盘 · 由 机制设计 指挥)
> 沙盒闸门: 此阶段只计算, 不发射业务NCA、不写COP。'亏'被隔离在落盘之前。
- 联盟(organizer+已准入) 4 家, 实际形成联盟 1 家

### 沙盒轮次 1 (VB=200.0 · exact)
- 动作: 初始基值 VB=200 (中性基值)
- V = 166.6
  - 外部贡献者·协议编译器手(MCP): φ=166.6 BATNA=40 ✅
- ✅ **本轮 MOU 正和可行** (各方 φ≥BATNA)

**沙盒结论**: mou_ok=True, VB=200.0, V=166.6, 轮次=1

- 🔗 **VB 外部锚达成**: DeepSeek 生成 COP 落盘且 base_protocol 匹配, 降 [UNVERIFIED-NO-EXTERNAL-ANCHOR] 为已锚定(正和信号来自真实外部生成)。
## 3. 生产阶段 (production_phase · 仅沙盒通过后触发 · 由 庖丁解牛⟂道常无为 指挥)
> 沙盒 mou_ok=True, 现在真实发射联盟NCA + 生产NCA, 关联合约贡献物。
- 联盟承诺 NCA(缔约凭证): `TDCA-REASONIX-20260828-004`
- 生产确权 NCA(贡献物确权): `TDCA-REASONIX-20260828-005`
- 贡献物: `C:\Users\22850\Desktop\开发会话文件\tdca-protocol\docs\cognitive-compiler\coldstart\community\第01条-开源社区冷启动·正和准入.yaml`

## 4. 诚实性质声明 (真实 vs 自报 / 沙盒闸门)
- **真实可调用资源**: 组织者(主agent) / 顶选缔约方(CA-01 独立贡献者·协议编译器手, real agent)。
- **准入门拒绝(2)**: CA-03(社区运营agent)/CA-04(空壳投机agent) 因 loaded_core=false 被拒 —— 证明'加入即加载 TDCA-CORE'。
- **沙盒闸门**: 沙盒通过→真实发射联盟NCA+生产NCA, 缔约达成
- **机制全真实**: enforce_entry/form_coalition/shapley/nca_generator 均为平台真实代码实跑。
- **已知缺口(诚实)**: ① 候选 res/batna 自报未确权(冷启动 newcomer 无历史 NCA 链) → 信任靠'小步首贡献+三段式闸门'缓解; ② VB 无外部锚 → 标[UNVERIFIED]; ③ 杠杆B 已移除改 BATNA 存疑熔断。
- **自定义连接器链路(真实)**: 外部 agent MCP-EXT-01 经 stdio MCP server 真实接入, load_core/contribute_cop 真实跨进程调用; 贡献物由 server 返回并落盘 community/。端点由你(组织者)自托管 → 连通性为真实, 身份仍为 self-hosted(非第三方自然人), data_provenance 仍 mixed。

