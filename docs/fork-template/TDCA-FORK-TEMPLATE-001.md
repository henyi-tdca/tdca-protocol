# TDCA-FORK-TEMPLATE-001 · 主动 Fork 标准化模板（借船出海）

> 文档编号: TDCA-FORK-TEMPLATE-001 ｜ 编制: 2026-08-24（Reasonix 制度层）｜ 状态: ✅ 模板就绪（A-2 采纳）
> 依据: TDCA-STRATEGY-OPEN-20260824（观点 2 主动 Fork + 三根高压线）｜ TDCA-OPEN-COLLAB-001（挂载/分润）｜ BIDIR-001（只赋能不改码）｜ AUDIT-001（许可校验）
> 用途: 对热门开源项目主动 Fork + 协议挂载的标准模板——**不改上游源码，仅加协议层**；借船出海第一步基建

---

## 〇、模板使用纪律（Fork 前三查）

| # | 检查 | 工具 |
|---|---|---|
| 1 | **许可校验**：上游 LICENSE 允许二次分发/挂载（MIT/Apache/BSD 等宽松许可）| `enforce_entry.py`（AUDIT-001）|
| 2 | **活跃确认**：近 30 天有提交（非死仓）| ECOSCAN `is_recent` |
| 3 | **去重**：同仓库 7 天内不重复 Fork 建议 | 候选池/台账 |

**Fork 边界（红线）**：Fork 副本**加协议层文件**（不改上游任何源码文件）——属挂载模式合法落地；上游源码零改动（BIDIR-001）。

---

## 一、Fork 仓库结构（附加文件清单）

```
{repo}-tdca/                    # Fork 副本（自动跟随上游）
├── README.md                   # ★ 顶部附加声明（见 §二）
├── TDCA-Agreement.yaml         # ★ 准入声明（NCA 锚定）
├── tdca-mcp-bridge/            # ★ 轻量挂载配置（MCP 协议层）
│   └── README.md               #   挂载说明（零侵入）
└── .tdca/                      # 制度水印（可选，metadata）
    └── provenance.yaml         #   来源/许可/分润锚点
```

## 二、README 顶部附加声明（必须逐字使用）

```markdown
# {repo}（TDCA 协议层附加版本）

> ⚠️ **TDCA 协议层附加版本**：原始代码版权归原作者所有（{上游 owner}/{repo}），
> 本 Fork **未修改任何上游源码**，仅增加 TDCA 制度赋能配置（协议层）。
> 上游原始仓库：[{上游 owner}/{repo}](https://github.com/{上游 owner}/{repo})

## 为什么有这个 Fork
为 {repo} 提供 TDCA 可信结算与合规审计的**可选挂载层**：
- **NCA 确权**：每次协作调用可验证、可追溯
- **MOU 锚定**：收益产生自动计税（模拟态记账）
- **NSFL 熔断**：负空间操作自动拦截（fail-closed）

## 许可与分润
- 上游代码：遵循上游 License（{SPDX}）
- TDCA 协议层：Apache-2.0（独立许可，不覆盖上游）
- **分润**：当本 Fork 被调用/化合产生收益时，版权被权调用方（原作者）默认获得 **15% 版税**（模拟态：NCA 确权 + ERI 权重记账，e-CNY 接入前不产生真实现金流）
- 授权优先：以上游项目方授权规定为准，TDCA 不覆盖

## 无侵入声明
您可以选择使用或不用本协议层——这是您的配置权（TDCA 只赋能不改码）。
```

## 三、TDCA-Agreement.yaml（准入声明模板）

```yaml
tdca_agreement:
  version: "1.0"
  upstream:
    repo: "{上游 owner}/{repo}"
    license: "{SPDX}"
    source_url: "https://github.com/{上游 owner}/{repo}"
  mount_mode: "fork-append"          # 只追加协议层，不改上游源码
  attestation:
    nca_ref: "NCA-ECOSCAN-{date}-{seq}"   # 挂载存证编号
  profit_sharing:
    default_rate: 0.15                # 版权被权调用方 15%
    mode: "simulated"                 # 模拟态（NCA + ERI 记账，无真实现金流）
    priority: "upstream_license_first"
  nsfl:
    red_lines: ["no-source-modify", "no-license-violation", "no-misrepresentation"]
```

## 四、分润话术（对外统一，模拟态口径）

> "在 TDCA 生态中，您代码被化合/调用产生收益时，作为原创方将获得 15% 版税（**模拟态记账**：NCA 确权 + ERI 权重；真实态 e-CNY 接入后按合约执行）。我们不剥夺所有权，只帮您从'被白嫖'走向'被调用即增值'。"

⚠️ **禁止话术**：「真实打款」「数字人民币结算」等承诺——e-CNY 接入前一律模拟态口径（TDCA-PUBLIC-COMPUTE V1.2）。

## 五、Fork 后动作

| # | 动作 | 说明 |
|---|---|---|
| 1 | 上游 PR（可选）| 若上游维护者愿意，可提 PR 仅加协议层（不强制——尊重上游）|
| 2 | 台账登记 | 候选池 → Fork 记录（NCA 存证）|
| 3 | 反哺公示 | 每周 Weekly「反哺公示」板块记录本 Fork 的调用/分润记账 |

## 六、纪律

- 不动上游源码（红线 1）｜ 许可校验先行（红线 2）｜ 正和感话术 + 模拟态分润（红线 3 + 纠偏）
- 算力零提及（V1.2）｜ 匿名/不留痕（BIDIR-001）
- 礼貌 ≤2 条/周/目标（不轰炸上游）

## 七、关联

- 上游: TDCA-STRATEGY-OPEN-20260824 ｜ TDCA-OPEN-COLLAB-001 ｜ AUDIT-001
- 存证: GSEQ-0416 ｜ NCA-TDCA-REASONIX-20260824-054

---

> 本模板为主动 Fork 标准件（借船出海第一步基建）；使用前三查（许可/活跃/去重），三红线（不改源码/许可校验/正和话术）。
