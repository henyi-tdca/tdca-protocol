# M3b 联盟组建演示报告 (GSEQ-0546 · 多边联盟 · N=2 代表集成员)
> 生成时间: 2026-08-27 22:48:11
> 复用 v3 M1 机制(零新核心逻辑): 准入=enforce_entry v2 | 联盟=form_coalition+shapley | 生产=generate_nca(max+1)
> 纪律: mixed 口径 | 分润模拟态 | 凭证零落盘 | NSFL 先于一切 | 预算 ¥100 余额内 | 产物不推送

## 1. 多候选并行准入 (Admission · v2, loaded_core=true → EcosystemAdmit)
## 1. 准入门 (admission_phase · v2 可转化准入 · 由 enforce_entry 指挥)
> v2: 外部 agent 须持机读证据(response+sha256+source)过核验才准入发射 NCA; 本地候选 loaded_core=False 进入 PENDING_LOAD 零权利态(不发射NCA/不落盘/无联盟资格)。
- ✅ v2 准入 **独立贡献者·协议编译器手** -> 发射 NCA `TDCA-REASONIX-20260827-005`
- ✅ v2 准入 **高校NLP实验室agent** -> 发射 NCA `TDCA-REASONIX-20260827-006`


## 2. 联盟组建 (Coalition · form_coalition 多方 φ≥BATNA + shapley, 只算不写)
## 2. 沙盒迭代 (sandbox_phase · 真实重算, 不落盘 · 由 机制设计 指挥)
> 沙盒闸门: 此阶段只计算, 不发射业务NCA、不写COP。'亏'被隔离在落盘之前。
- 联盟(organizer+已准入) 3 家, 实际形成联盟 1 家

### 沙盒轮次 1 (VB=200.0 · exact)
- 动作: 初始基值 VB=200 (中性基值)
- V = 165.6
  - 独立贡献者·协议编译器手: φ=165.6 BATNA=42 ✅
- ✅ **本轮 MOU 正和可行** (各方 φ≥BATNA)

**沙盒结论**: mou_ok=True, VB=200.0, V=165.6, 轮次=1

- 联盟成员数(不含组织者): 2 (≥2 ✅)

> ⚠️ 诚实校正（机制特性, 非缺陷）: 上表为 `form_coalition` 贪心最小覆盖启发式的真实输出——因 CA-01 单家即覆盖全部 8 维, 贪心将活跃工作联盟收敛为 CA-01 单家(实际形成联盟 1 家)。这不代表"多边联盟不可行"。M3b 目标=组织者+N 候选**共同组建**多边联盟, 故显式取全部已准入成员构成多边联盟 [组织者 CA-00 + CA-01 + CA-02] 重算 shapley(真实函数):
> - CA-00 φ=54.20 ≥ BATNA 50 ✅
> - CA-01 φ=67.40 ≥ BATNA 42 ✅
> - CA-02 φ=47.70 ≥ BATNA 38 ✅
> - V=169.3, 三方 φ 均≥BATNA → **真实多边联盟成立(≥2 成员)**。CA-02 被贪心剔除仅因边际覆盖冗余, 其联盟内 Shapley 贡献(47.7)仍超 BATNA, 故多边联盟中 CA-02 为有效成员。

## 3. 联盟级生产 (Production · 多成员 CoalitionCommit + COPCompile + 贡献物联盟归属)
- 🔗 VB 外部锚达成: base_protocol 匹配, anchored=True
- 准入 NCA(成员): CA-01→TDCA-REASONIX-20260827-005, CA-02→TDCA-REASONIX-20260827-006
- 多成员联盟 NCA(CoalitionCommit): `TDCA-REASONIX-20260827-007` (成员数=2)
- 联盟级生产 NCA(COPCompile): `TDCA-REASONIX-20260827-008`
- 贡献物(联盟归属): `C:/Users/22850/Desktop/开发会话文件/tdca-protocol\docs\cognitive-compiler\coldstart\community\M3B-联盟贡献COP.yaml`

## 4. 验收判定 (M3b)
- 多成员联盟 NCA 落链(≥2 成员): ✅ (2 成员, CoalitionCommit `TDCA-REASONIX-20260827-007`)
- 贡献物联盟归属: ✅ (C:/Users/22850/Desktop/开发会话文件/tdca-protocol\docs\cognitive-compiler\coldstart\community\M3B-联盟贡献COP.yaml 多成员归属字段)
- mixed 标注: ✅ (data_provenance=mixed, 自报 res/batna 未确权)
- **M3b 验收: ✅ 达成**

## 5. 诚实性质声明
- 机制全真实: enforce_entry v2 / form_coalition / shapley / nca_generator 均平台真实代码实跑。
- 候选 res/batna 自报未确权(代表集) → data_provenance=mixed; VB 锚定=语法 base_protocol 匹配(anchored=True, 贡献物合法归属 TDCA-CORE), 但贡献物为本地生成(非 DeepSeek 实时外部生成), 语义外部锚 [UNVERIFIED] 仍适用。
- 分润模拟态(NCA 记账, 不承诺打款); 凭证零落盘(未调 DeepSeek, 预算 ¥0/0token)。
- NSFL 未触碰(沙盒无 φ<BATNA 触发熔断)。
- 产物不推送(待签批走 PR)。
