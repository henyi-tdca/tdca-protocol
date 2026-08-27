# v3 M1 五特使接线实跑报告 (FIVE-EMISSARY · 1 候选全链自动缔约)
> 生成时间: 2026-08-27 16:50:54
> 纪律: mixed 口径(self-hosted/代表集 UNVERIFIED 直至实跑 COP 落链) | 分润模拟态 | 凭证零落盘(DeepSeek key 延续方案B, 本次不激活) | 产物不推送 | 算力零提及 | 无 NCA-ECOACT 存证不动作 | NSFL 先于一切 | 预算 ¥100 余额内
> 资产复用(零新开发): 扫描者/信使=tdca-external-agent(MCP-EXT-01) | 评估者=utility-genie.PositiveSumSolver | 谈判者=emissary/谈判者-特使-001.yaml(M2) | 落地者=enforce_entry.ecosystem_admit_v2 + 沙盒 MOU + 生产 NCA

## ① 扫描者 (Scanner · ecoscan 候选池 / mcp 连接器可达候选)
- 输入: tdca-external-agent 自定义连接器(stdio MCP server) 呈现可达候选
- 输出: 选定 **1 候选** = **外部贡献者·协议编译器手(MCP)** (id=MCP-EXT-01, loaded_core=True, 端点=self-hosted stdio)
- 能力画像 res={"范式编译": 0.9, "工程实现": 0.82, "文档教程": 0.85, "社区运营": 0.68, "审计合规": 0.55, "连接器": 0.62, "算力": 0.5, "NLP": 0.58}
- BATNA=40 | intent=经自定义连接器接入, 把'社区冷启动/正和准入'编译为 COP 贡献给 TDCA

## ② 评估者 (Evaluator · utility-genie 正和博弈验证)
- 输入: 候选 res/batna → utility-genie.PositiveSumSolver
- 输出: is_positive_sum=True | is_individual_rational=True | total_utility=100.0 | independent_sum=90.0 | delta=10.0
- NSFL 触碰: touched_nsfl=False
- 正和判定: **✅ 通过** (通过=进入缔约; 拒绝=全链终止)

## ③ 信使 (Messenger · mcp 连接器 load_core 邀请)
- 输入: 向候选 MCP-EXT-01 发邀请 (load_core)
- 输出: 机读证据 response(len=288) + sha256=d0fd85ef32eaff9a + source=mcp-external-stdio@C:\Users\22850\Desktop\TDCA-MEMO-006-Workspace\.tdca-protocol\cognitive-compiler\coldstart\mcp_external_agent_server.py
- tools/list 暴露: ['load_core', 'contribute_cop']

## ④ 谈判者 (Negotiator · M2 COP 响应, 模拟态口径)
- 输入(模拟候选提问): 分润怎么算？
- 输出(M2 COP 响应): 15% 分润模拟态：NCA 记账，法币通道后凭账本转实际结算，不承诺打款
- 响应后提醒: 涉及对外动作须先 NCA-ECOACT 存证(无存证不动作) —— 本次仅模拟, 不落存证
- 谈判者口径核验: 分润模拟态(不承诺打款)✅ | 邀请非要求✅ | 不点名✅ | 算力零提及✅ | 凭证零落盘✅

## ⑤ 落地者 (Implementer · enforce_entry v2 准入→沙盒→生产)
## 1. 准入门 (admission_phase · v2 可转化准入 · 由 enforce_entry 指挥)
> v2: 外部 agent 须持机读证据(response+sha256+source)过核验才准入发射 NCA; 本地候选 loaded_core=False 进入 PENDING_LOAD 零权利态(不发射NCA/不落盘/无联盟资格)。
- ✅ v2 准入 **外部贡献者·协议编译器手(MCP)** -> 发射 NCA `TDCA-REASONIX-20260827-155` (证据源=mcp-external-stdio@C:\Users\22850\Desktop\TDCA-MEMO-006-Workspace\.tdca-protocol\cognitive-compiler\coldstart\mcp_external_agent_server.py)

## 2. 沙盒迭代 (sandbox_phase · 真实重算, 不落盘 · 由 机制设计 指挥)
> 沙盒闸门: 此阶段只计算, 不发射业务NCA、不写COP。'亏'被隔离在落盘之前。
- 联盟(organizer+已准入) 2 家, 实际形成联盟 1 家

### 沙盒轮次 1 (VB=200.0 · exact)
- 动作: 初始基值 VB=200 (中性基值)
- V = 166.6
  - 外部贡献者·协议编译器手(MCP): φ=166.6 BATNA=40 ✅
- ✅ **本轮 MOU 正和可行** (各方 φ≥BATNA)

**沙盒结论**: mou_ok=True, VB=200.0, V=166.6, 轮次=1

- 🔗 VB 外部锚(语法): base_protocol 匹配, anchor_vb_to_cop=True
## 3. 生产阶段 (production_phase · 仅沙盒通过后触发 · 由 庖丁解牛⟂道常无为 指挥)
> 沙盒 mou_ok=True, 现在真实发射联盟NCA + 生产NCA, 关联合约贡献物。
- 联盟承诺 NCA(缔约凭证): `TDCA-REASONIX-20260827-156`
- 生产确权 NCA(贡献物确权): `TDCA-REASONIX-20260827-157`
- 贡献物: `C:\Users\22850\Desktop\TDCA-MEMO-006-Workspace\.tdca-protocol\cognitive-compiler\coldstart\community\第01条-开源社区冷启动·正和准入.yaml`

## ⑥ 验收判定 (M1)
- 准入 NCA: TDCA-REASONIX-20260827-155
- 联盟 NCA: TDCA-REASONIX-20260827-156
- 生产 NCA: TDCA-REASONIX-20260827-157
- 全链自动完成(无人工干预): ✅ 是
- **M1 验收: ✅ 达成**

## ⑦ 各特使用时 (秒)
- 扫描者: 0.626 | 评估者: 0.000 | 信使: 0.000 | 谈判者: 0.002 | 落地者: 0.032
- 端到端总用时: 0.660

## ⑧ 诚实性质声明 (mixed 口径, 随引用携带)
- 端点 self-hosted(非第三方自然人) → data_provenance=mixed; MCP-EXT-01 为 self-hosted stdio server, 连通性真实, 身份未第三方确权。
- 候选 res/batna 自报未确权(代表集) → 信任靠三段式闸门缓解。
- 贡献物 = `community/第01条-开源社区冷启动·正和准入.yaml` (既有冻结 COP, 前次受控真实试验 DeepSeek 生成, 本次复用为冻结资产; 非本跑新生成) → VB 外部锚语义未达成(仍 [UNVERIFIED]), 语法 base_protocol 匹配。
- 谈判者为模拟态响应(分润 15% NCA 记账, 不承诺打款); 不点名/不诱导/算力零提及。
- 评估者 utility-genie 真实模块调用, NSFL 未触碰(touched_nsfl=False)。
- DeepSeek key 未注入(凭证零落盘, 方案B 延续但未激活) → 本跑零外部 LLM 调用, 预算 ¥0 / 0 token。
- 产物不推送(待签批走 PR)。
- **编号事故与修复(诚实披露)**: 本跑 `nca_generator.generate_nca` 自动编号未扫盘, 复用 155 覆盖上一轮手动创建的 M2 编译 NCA-155(写入 M1 准入 EcosystemAdmit), 致 M2 原 provenance 文件内容丢失。已修复: **M1 链保留 155/156/157**(现场自洽), **M2 编译 NCA 顺延至空闲号 158** 恢复 provenance(见 `emissary/谈判者-特使-001.yaml` provenance 行; M2 报告因被其他进程锁定本次未能同步, 其 line 21 仍暂显 155, 释锁后可一键改为 158)。根因=手动预分配编号与自动编号机制冲突; 后续应禁止手动创建 NCA 与 generate_nca 同号。

