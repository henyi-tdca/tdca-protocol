# TDCA 开源社区冷启动方案 + 决策思维 + 方案形成说明
> 真实实验：3 天内由一个外部智能体加入 TDCA 并完成缔约（多智能体协作 · 思维协议指挥 skill）
> 实验时间：2026-08-27 ｜ 性质：机制全真实 / 候选代表集模拟 / 守 GitHub 为主纪律未推送开源

---

## 〇、一句话结论
用 TDCA 既有治理原语（准入门 + 三段式闸门 + 搜索比配 + NCA 确权）把"如何加入社区"本身编译为一个可被程序审计的协议，由**三个智能体**分别受不同思维协议（COP）指挥、调用对应 skill，在 workspace 内真实跑通：顶选候选 CA-01 通过准入→沙盒 MOU 正和判定→落盘首个贡献物并获得联盟 NCA(096)+生产 NCA(097)。**3 天冷启动目标达成判定：四项全满足。**

---

## 一、决策思维（我们为什么这么设计）

### 1.1 冷启动的本质难点是"信任"，不是"流量"
新开源社区最大的风险是：**不可信的主体先拿到了落盘/缔约权**。所以方案的第一性原则是——
> 把"亏隔离在落盘之前"（继承 `run_sunzi_threephase` 的闸门纪律）。

任何外部 agent 在通过可信判定之前，不发射业务 NCA、不写贡献 COP。这与框架"NSFL 熔断 / 生产后置"一致。

### 1.2 为什么用"多智能体 + 思维协议指挥 skill"
框架的元定位（MEMORY 战略层）：
- **COP = 大脑**（L3 认知基础设施，自主决策源泉层）；**Skill = 肌肉**（程序性能力）。
- 超人比配推论：信任模型从"人类理解"转向"**程序可审计**"——NCA 链查来源 / NSFL 卡底线 / MOU 验正和。

因此每个 agent 的角色**不由自由发挥定义，而由一个可被审计的思维协议 COP 定义**；COP 的 `dispatch` 字段就是"指挥哪个 skill"的硬接线。好处：
- 可解释（每个动作能追到 COP 与 NCA）；
- 可复用（这套"招募 COP→准入 COP→生产 COP"是可插拔配方，下一个 newcomer 直接套）；
- 可审计（不阉割可解释性换涌现）。

### 1.3 为什么用三段式闸门（准入→沙盒→生产）
直接复用已验证的 `run_sunzi_threephase.py` 结构，不为冷启动另造轮子：
- **准入**只验"是否加载 TDCA-CORE"（加入即加载基协议），不验"本联盟能否正和"——后者是沙盒的事；
- **沙盒**真实重算 `form_coalition` + `shapley`，判各方 φ≥BATNA（MOU 正和），只算不写；
- **生产**仅当 `mou_ok=True` 才发射联盟 NCA + 生产 NCA + 落盘贡献。

### 1.4 为什么招募用"搜索比配引擎"而非拍脑袋
《孙子兵法·谋攻篇》"知己知彼者，百战不殆" → 先知己（社区能力缺口）、再知彼（候选互补度），用真实 `compute` 层（`form_coalition`/`coalition_value`/`shapley`/`grade_dims`/`fragile_dims`）做互补比配，而不是主观排序。

---

## 二、方案形成说明（方案是怎么长出来的）

本方案 = **组织者协作机制 L0–L3 坐标系** 在子目标"3 天引入 1 个外部 agent 并缔约"上的实例化：

| 坐标系层 | 本方案对应 | 来源原语 |
|---|---|---|
| L0 发起（Why，不可审计） | "冷启动需要首个外部贡献者" | 用户目标 |
| L1 协议（What，目标函数+ConstraintProfile+负空间→意图 NCA） | 把"如何加入"编译为 `COLDSTART-01` COP（正和准入协议） | cognitive_compiler schema + TDCA-CORE |
| L2 执行（Who，准入→比配→Shapley） | 三段式闸门编排器 | enforce_entry / compute / shapley |
| L3 审计（Proof，NCA链/NSFL/MOU） | 准入 NCA + 联盟 NCA + 生产 NCA | nca_generator |

**化合视角**：本方案本身是一次"框架原语 ⊕ 具体子目标"的化合——
- 孙子·谋攻篇 ⊕ 搜索比配引擎 = 招募比配智能体
- 机制设计 ⊕ 一诺千金⟂论语·学而(信用) = 准入缔约智能体
- 庖丁解牛 ⊕ 道常无为(顺其理) = 生产交付智能体
- TDCA-CORE-03(正和协作涌现) = 组织者编排的总指挥

方案不是"写出来的"，是"用已有原语组合出来的"——这也是框架"编译即摊薄制度增量"的实证。

---

## 三、多智能体角色与"思维协议 → skill"指挥映射

| 角色 | 指挥它的思维协议（COP） | 调用的 skill / 引擎（真实代码） | 交付产物 |
|---|---|---|---|
| **R0 组织者 / 编排** | `TDCA-CORE-03`(正和协作涌现) + `孙子·谋攻篇`(知己知彼) | `run_coldstart_threephase.py` → `enforce_entry`/`form_coalition`/`shapley`/`nca_generator` | 三段式闸门实跑报告 + 缔约 NCA |
| **R1 招募比配** | `孙子·谋攻篇`("知己知彼") | `coldstart_match.py`(compute 层: 缺口覆盖增益 / 互补度 / Shapley 预演) | 候选排名 + 邀约简报 |
| **R2 准入缔约** | `机制设计`(激励相容) + `一诺千金⟂论语·学而`(信用) | `enforce_entry.ecosystem_admit` + `nca_generator.CoalitionCommit` | 准入 NCA(094/095) + 联盟 NCA(096) |
| **R3 生产交付（即加入方本身）** | `庖丁解牛⟂道常无为`("依天理，因其固然"=顺其理、不强为) | `cognitive_compiler` schema（写 COP，复用模板） | 贡献物 COP(`COLDSTART-01`) + `ONBOARDING.md` |

> 注：R3 就是"加入并完成缔约的那个智能体"——它受《庖丁解牛》指挥，严格复用既有 COP schema 落盘首个贡献，体现"顺其理、不为不可为"。

---

## 四、3 天里程碑（部署时间线；本次实验在 workspace 内加速实跑）

| 天 | 阶段 | 负责智能体 | 动作 | 判定 |
|---|---|---|---|---|
| **Day 1** | 发起 + 招募 | R0 + R1 | 立协议(起草 `COLDSTART-01` COP)；R1 跑比配出排名；向顶选发邀约(附 TDCA-CORE 加载指引) | 顶选可准入候选锁定 = CA-01 |
| **Day 2** | 准入 + 缔约谈判 | R2 | 对顶选跑准入门(发射准入 NCA) + 沙盒(VB/φ/BATNA MOU 判定) | `mou_ok=True` → 发联盟 NCA(096) |
| **Day 3** | 生产 + 交付 | R3 + R0 | R3 落盘首个贡献 COP + ONBOARDING；R0 发生产 NCA(097)；社区公告 | 缔约闭环完成 |

---

## 五、成功判定（"3 天内由一个智能体加入并完成缔约"的四条硬指标）

| # | 指标 | 本实验实测 | 结果 |
|---|---|---|---|
| 1 | 顶选通过准入门（loaded_core=true） | CA-01 准入 NCA `TDCA-REASONIX-20260827-094` | ✅ |
| 2 | 沙盒 MOU 正和（各方 φ≥BATNA） | V=165.6，CA-01 φ=165.6 ≫ BATNA 42 | ✅ |
| 3 | 发射联盟 NCA（缔约凭证）+ 生产 NCA（贡献确权） | `096`(CoalitionCommit) + `097`(COPCompile) | ✅ |
| 4 | 贡献物落盘且 `base_protocol=TDCA-CORE-20260815-01` | `community/第01条-开源社区冷启动·正和准入.yaml` | ✅ |

**判定：3 天冷启动目标达成。**

---

## 六、诚实口径（mixed，引用须带）

1. **机制全真实**：`enforce_entry` / `form_coalition` / `shapley` / `nca_generator` 均为平台真实代码实跑；三段式闸门"生产后置"纪律生效（CA-03/CA-04 因未加载 CORE 被准入门拒，证明"加入即加载基协议"）。
2. **候选为"代表集模拟"**：CA-01~CA-04 是代表性外部 agent 画像，非真实外部自然人/法人；res/batna 为**自报**——冷启动 newcomer 无历史 NCA 链，**未确权**（框架已知缺口②）。
3. **VB 无外部锚**：组织者任务重定价基值 VB=200 为**主权宣言**，无可比任务定价锚 → 标 `[UNVERIFIED-NO-EXTERNAL-ANCHOR]`；mou_ok 在算术上由基值托底，非独立价值发现。
4. **门禁"非黑即白"误伤风险（R1 诚实发现）**：互补度最高的 CA-03(社区运营agent, 缺口增益 2.688) 仅因 `loaded_core=false` 被永久拒——它恰好最补社区缺口。建议将"未加载 CORE"改为"引导加载后再准入"的**可转化状态**，而非直接丢弃。
5. **实验在 workspace 内实跑，未推送开源**（守 GitHub 为主纪律）；部署到真实社区时须经用户签批再发 Issue/PR。

---

## 七、可复用配方（沉淀为 coldstart/ 资产）
- `coldstart_candidates.json` — 候选池（可替换为真实外部 agent 注册表）
- `coldstart_match.py` — R1 招募比配器（真实 compute 层）
- `run_coldstart_threephase.py` — 三段式闸门编排器（准入→沙盒→生产）
- `community/第01条-开源社区冷启动·正和准入.yaml` — 把"如何加入"本身编译为 COP（自举）
- `COLDSTART-EXPERIMENT-REPORT.md` — 实跑报告
- `coldstart_recruit_brief.md` — R1 邀约简报
