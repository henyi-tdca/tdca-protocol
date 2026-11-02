# TDCA-HANDOFF-WORKBUDDY-NEUTRALITY-001 · WorkBuddy 整改指令：思维协议立场分离三律整改（全部产物）

> 文档编号: TDCA-HANDOFF-WORKBUDDY-NEUTRALITY-001 ｜ 编制: 2026-08-28（Reasonix 制度层）｜ 状态: ✅ **已下令**（创始人指令）
> 依据: 创始人 2026-08-28「编译器和全部思维协议产物都在 WorkBuddy 侧，要求重新全部整改；TDCA 协议和场景协议不用改；改完交 Kimi 推新版上仓库」
> 制度: TDCA-STANCE-SEPARATION-001（立场分离三律）｜ TDCA-COP-NEUTRALITY-CHECK-001（18 文件查验）
> 存证: GSEQ-0601

---

## 一、整改范围

**编译器 + 全部思维协议产物**（cop-library 下除 tdca_core/scenario 外的全部：stratagems / games / hundred_schools / compositions / simulations / mechanism_design）

**排除（不改）**：`tdca_core/`（TDCA 协议）✅ ｜ `scenario/`（场景协议）✅

## 二、三律整改要求（按 TDCA-STANCE-SEPARATION-001）

**律一 · 原语层去场景·去立场**
- `soul.core` / `decision.if` / `precond` 去除主体立场（敌我/阵营/意识形态/化合目标声明）
- `verse/origin`（典故素材）保留——是素材不是立场
- 机制核（stratum/steps/primitives/negative_space）结构保留

**律二 · 立场运行时注入**
- 编译期不得写死立场；立场移入场景绑定（scenario）与制度挂载（TDCA-CORE）
- **同核多编重构**：如「打草惊蛇」——1 个机制核（探测行为↔暴露度耦合，去立场）+ N 个场景绑定（侦查→主动试探 / 行动安全→暴露警示），不再多立场分编

**律三 · 原语永不单独生效**
- 组合/挂载依赖声明保留（scene/kg/skill/contract 四类）

## 三、编译器改造（schema 硬约束）

`cognitive_compiler.py`（及 admission_checklist / enforce_entry）新增**立场分离校验**（fail-closed）：
1. 原语层禁立场字段——soul.core/decision 含主体立场词（敌我/阵营/意识形态黑名单）→ 拒编译
2. 立场仅允许经 scene_binding / composition 注入
3. 四类依赖挂载强制声明（组合时）
4. 测试 ≥10 用例（立场词拦截/同核多编检测/挂载缺失拒绝/中性原语放行）

## 四、manifest/README 中性化（18 文件，TDCA-COP-NEUTRALITY-CHECK-001）

- `compound_target: 中国文化 ⊕ 马克思主义 = 毛泽东思想思维协议` → 中性化（如 `中国古典智慧 ⊕ 现代系统思维 = 跨范式化合思维协议` 或删字段）
- `../marxism/` 私有路径引用 → 删除/中性表述
- 待编译「毛泽东思想」→「中西化合思维范式」；MACM-14 旗舰示例 → 中性示例
- 私有 `marxism/` 目录**不入仓**（保持本地自用）

## 五、验收

1. 重扫 0 命中（意识形态词/立场字段，全量 cop-library 非 tdca_core/scenario）
2. 编译器立场校验生效（测试全绿）
3. 产物重编译全部通过（原有用例回归）
4. 原语机制核零语义损失（只去立场，不改结构）

## 六、交接

改完 → **交 Kimi 推新版上仓库**（PR 流：分支→PR→merge，更新 GitHub 主仓 docs/cop-library/）→ Gitee 同步后 451 文件如实观察。

## 纪律（红线不变）

无敏感词 ｜ 私有 marxism 不入仓 ｜ 不规避平台审核（修改=内容口径） ｜ NSFL 先于一切 ｜ 凭证零落盘

## 回报

整改完成后回报：① 编译器校验实现 + 测试结果 ② 整改文件数（原语/manifest/README）③ 重扫 0 命中证明 ④ 交接 Kimi 状态。

---

> 本指令为思维协议立场分离整改唯一执行依据；TDCA 协议（tdca_core）与场景协议（scenario）明确不改。
> 关联: [[tdca-session-20260828]] ｜ TDCA-STANCE-SEPARATION-001 ｜ TDCA-COP-NEUTRALITY-CHECK-001 ｜ 存证: GSEQ-0601
