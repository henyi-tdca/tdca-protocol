# TDCA 原生协议库（tdca-native）

> 单一事实源（Single Source of Truth）：TDCA 原生思维协议的权威库。
> 数据性质（ID92）：本库内容为**制度编译产物**——原生协议 455 + 化合协议 60 = 515（审查闭环口径），经全库七原则审查 PASS（化合 60/60 + 原生 454/454 复审全合规，GSEQ-0755 复核通过）。
> 许可：Apache-2.0（随本仓库统一）。

## 一、七原则声明（P1~P7，2026-08-30 创始人颁布）

1. **P1 组合性强制**：思维协议不是独立发挥作用的——化合 COP `composition_policy.standalone=false`。
2. **P2 TDCA 强制遵守**：TDCA 体系内 `base_protocol=TDCA-CORE` 强制绑定，不可配置关闭。
3. **P3 原生可剥离独立性**：剥离 TDCA 治理层后协议语义保持独立自洽（`detachable` 声明，设计目标而非副作用）。
4. **P4 换绑自由**：解释项绑定关系为运用层配置，运行期允许换绑（`bind_policy` 声明，dispatch.graph 可扩展）。
5. **P5 化合判据**：化合=改变属性、产生新思维；叠加不改变属性、只是两个独立思维的合作。化合 COP 须携带 `fusion_spec`（attribute_changes 属性改变表 + emergence 涌现物判据）。
6. **P6 F1.5 NSFL 否决权**：NSFL 预检未过即整体拒绝（Fail-Closed），优先级恒高于其他一切判据——负空间是安全宪法的宪法，不可推翻、不可配置关闭。
7. **P7 F1.5b 四态动态处置**：否决权的不可推翻性仅指即时门控裁决，不指永恒身份；触犯负空间按四态处置——休眠/禁止/重塑/出清，裁定存证，禁悬置；负空间版本更新时休眠/重塑态强制重评。

## 二、结构（13 家族 + 核心基协议）

```
protocols/tdca-native/
├── README.md / VERSION.md / MANIFEST.json
├── tdca_core/          # TDCA 核心基协议 ×3（可信底座，不计入原生审计口径）
├── chengyu/            # 中国成语（150）
├── hundred_schools/    # 诸子百家（200 原生 + 4 化合）
├── stratagems/         # 三十六计（37）
├── games/              # 经典博弈（4）
├── scenario/           # 场景（7）
├── mechanism_design/   # 机制设计（1）
├── microeconomics/     # 微观经济学（12）
├── marxism/            # 马克思主义（15 原生 + 1 旗舰化合）
├── engineering-three/  # 工程三协议（25 原生 + 16 化合）
├── emissary/           # 特使（1，标准 COP 版）
├── compositions/       # 跨库化合（39 化合）
└── 麦肯锡思维协议.yaml  # 西方/通用范式（1，根目录）
```

## 三、与 cop-library 的关系

- **本库（protocols/tdca-native）= 原生协议权威库 / 单一事实源**：CTS-L1 认证、外部挂载、引用均以本库为准。
- **docs/cop-library = 思维协议策略库（运用/展示层）**：内容与本库同步，面向社区展示与运用示例；两库内容差异时以本库为准。

## 四、引用方式

- 协议引用：按 家族/路径 + 文件名（如 `protocols/tdca-native/chengyu/…yaml`），并在引用方注明版本锚（见 VERSION.md 正典锚）。
- 合规要点：化合协议不得脱离 `composition_policy` 单独使用（P1）；TDCA 体系内使用须保持 `base_protocol=TDCA-CORE` 绑定（P2）；NSFL 否决权不可配置关闭（P6）。

## 五、暂不纳入（如实标注）

- **simulations 家族**：口径待裁定（模拟件归属），暂不纳入本库；社区 cop-library 旧版保留并同标注。
- **coldstart 围栏件**（1 件，YAML 解析失败）：归口修复后补入。
- **emissary 旧版**（谈判者-特使-001.yaml，结构异常）：已由标准 COP 版（谈判者-特使-001-COP.yaml）替代，旧版不收录。

*审查链：TDCA-REVIEW-OPINION-001/002/003 ｜ 修订批次 NCA-TDCA-REASONIX-20260830-007~012 ｜ 建库批次 GSEQ-0759*
