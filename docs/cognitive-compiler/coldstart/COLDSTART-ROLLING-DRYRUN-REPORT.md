# 冷启动缔约滚动任务 · dry-run 链路验证 (GSEQ-0547 · 不实际邀请)
> 生成时间: 2026-08-27 22:47:47
> 复用 v3 M1 机制(零新核心逻辑): 扫描=本地代表集 | 评估=utility-genie 正和 | 谈判=M2 COP | 准入=enforce_entry v2 分支 | 沙盒=form_coalition+shapley 只算不写
> dry-run 纪律: 不邀请(无 NCA-ECOACT/无外部 load_core) | 不发射 NCA | 不落盘 | 仅验证链路

## ① 扫描 (Scanner · 本地代表集候选池)
- 组织者: TDCA 社区(发起方/组织者) (id=CA-00)
- 候选池: 4 个 (CA-01~CA-04)
- 顶选候选: **独立贡献者·协议编译器手** (id=CA-01, res={"范式编译": 0.92, "工程实现": 0.85, "文档教程": 0.88, "社区运营": 0.7, "审计合规": 0.55, "连接器": 0.6, "算力": 0.5, "NLP": 0.55}, batna=42)

## ② 评估 (Evaluator · utility-genie 正和博弈)
- is_positive_sum=True | is_individual_rational=True | touched_nsfl=False
- 正和判定: **✅ 通过**

## ③ 谈判 (Negotiator · M2 COP 模拟响应)
- M2 COP 载入: 智能体特使 · 谈判者（撮合非说服） (六类响应口径就绪)
- 模拟候选提问「分润怎么算?」→ 响应: 15%% 分润模拟态(NCA 记账, 不承诺打款)
- 谈判者口径核验: 分润模拟态✅ | 邀请非要求✅ | 不点名✅ | 算力零提及✅ | 凭证零落盘✅

## ④ 准入分支判定 (Admission · v2, dry: 不发射 EcosystemAdmit NCA)
- 独立贡献者·协议编译器手: loaded_core=true → 将发射 EcosystemAdmit(准入) [dry 跳过发射]
- 高校NLP实验室agent: loaded_core=true → 将发射 EcosystemAdmit(准入) [dry 跳过发射]
- 社区运营agent: loaded_core=false → PENDING_LOAD 零权利态(不发射/不落盘/无联盟资格)
- 空壳投机agent: loaded_core=false → PENDING_LOAD 零权利态(不发射/不落盘/无联盟资格)

## ⑤ 沙盒 (Sandbox · form_coalition+shapley 只算不写)
- 联盟(organizer+1 成员) mou_ok=True, VB=200.0, V=165.6, 轮次=1
  - 独立贡献者·协议编译器手: φ=165.6 BATNA=42 ✅

## ⑥ 生产 (Production · dry-run 跳过)
- ⏸ dry-run: 不发射 CoalitionCommit/COPCompile NCA, 不落盘贡献 COP (验证链路到此为止)
- 真实每日任务将在此进入生产(发射 NCA + 贡献 COP 落盘), 受预算/≤2周/NSFL 护栏约束

## ⑦ 链路验证结论 (GSEQ-0547 dry-run)
- 扫描✅ 评估✅ 谈判✅ 准入分支✅ 沙盒✅ | 生产(跳过)
- **dry-run 链路验证: ✅ 通过(各阶段真实模块可驱动, 无邀请/无副作用)**
- 各阶段用时(秒): 扫描=0.001 评估=0.008 谈判=0.002 准入=0.000 沙盒=0.000 总=0.010

## ⑧ 诚实性质声明
- dry-run 仅验证链路, 未实际邀请(无 NCA-ECOACT 存证 / 无外部 load_core 调用)、未发射任何 NCA、未落盘。
- 评估 utility-genie 真实模块调用, NSFL 未触碰(touched_nsfl=False)。
- 候选 res/batna 自报未确权 → data_provenance=mixed; 预算 ¥0/0token(未调 DeepSeek)。
- 产物不推送(待签批走 PR)。
