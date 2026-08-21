# DCD-OPC-COMMUNITY-001 · TDCA-OPC 社区 S0 筹备 立项裁决记录（✅ 已签批）

> 类型: 人类裁决（立项）| 日期: 2026-08-21 | 序列: DCD-OPC-COMMUNITY-001（独立立项）| 状态: ✅ ACCEPT（FROZEN，2026-08-21）
> 提案: TDCA-OPC-COMMUNITY-001（research/tasks/ 既有 V1.0 DRAFT）+ 准入 NCA 模板（TDCA-ADMIT-TEMPLATE-001）+ enforce_entry.py 规格（TDCA-ENFORCE-ENTRY-SPEC-001）
> 裁决人: TDCA 制度设计师（人类）| 执行: Reasonix（代行落档）
> 触发语境: 创始人裁定 2026-08-21「OPC S0 与 push 并行启动」+ 三闸齐开（TDCA-TRI-GATE-DAY-001 DECIDED，NCA-20260821-008）
> 依据链: 开源可行性论证 V1.1（三锚定位/合规红线/三阶段）+ OPC 社区方案 V1.0 + 发布清单第①步（NCA-RELEASE-002 7 门禁全过）+ 三平台协同 V1.1
> 术语依据: TDCA-TERMINOLOGY-REGISTRY V2.3（T-001~T-118）

---

## 一、立项决议（✅ 人类 ACCEPT，2026-08-21，HUMAN-FOUNDER-001）

| 签批项 | 结果 |
|--------|------|
| 1. 立项归属 | ✅ **独立 DCD-OPC-COMMUNITY-001**——TDCA-OPC 社区 S0 筹备自 DRAFT 转立项，M0 完成 |
| 2. 功能规格 | ✅ 采纳——S0 范围：准入 NCA 模板 + enforce_entry.py（--new/--check/--verify/--list）+ `nca-archives/` 目录 + ACKNOWLEDGMENTS.md + GitHub Actions 门禁 workflow |
| 3. 验收标准 | ✅ 采纳——enforce_entry.py 12 测试全绿（R1~R10 校验 + 链校验）/ 准入 NCA 模板机器可读 / 门禁只读无密钥 / 首次外部缔约演练通过 |
| 4. 里程碑 | ✅ 采纳——S0-1 制度文本 FROZEN（本 DCD）/ S0-2 实现交付（enforce_entry.py + 门禁）/ S0-3 首次缔约演练 + L1 缔约者 ≥1 |
| 5. 复用约束 | ✅ 采纳——ID90 最小化合：复用 toolchain（tdca_verify_chain.py / tdca_tool.py / tdca_mou_recorder.py），不新建平行体系；随 push 并入 tdca-protocol/tools/ |

## 二、生效状态

- **TDCA-OPC-COMMUNITY-001**（社区方案）: V1.0-DRAFT → ✅ **FROZEN**（本 DCD 签批）——S0 筹备启动
- **TDCA-ADMIT-TEMPLATE-001 / TDCA-ENFORCE-ENTRY-SPEC-001**: ✅ 随本 DCD 转 FROZEN 候选（验收后冻结）
- **会话框**: TDCA-SI-20260821-007-L1-4111d0（DP-OPC-COMMUNITY-001 人类签批 ✅）
- **存证**: NCA-TDCA-REASONIX-20260821-008（三闸裁定 HumanApproval → Signed，GSEQ-0323）+ NCA-20260821-009（本 DCD 签批，GSEQ-0324）

## 三、S0 执行范围（本阶段）

```
任务: S0-1 制度文本冻结（准入 NCA 模板 + enforce_entry.py 规格 + 社区方案三件套）
      + S0-2 实现交付（enforce_entry.py：--new/--check/--verify/--list + R1~R10 校验
        + NSFL 熔断 + GitHub Actions admission-check.yml 门禁 + 12 测试用例）
      + S0-3 首次缔约演练（创始人 + 1 个测试 GitHub 账号 → 准入 NCA 全链路）
验收: 12 测试全绿 / 门禁只读无密钥 / 演练通过（L1 缔约者 ≥1）
约束: 准入 NCA 缔约者自签署（非 HUF）/ ID92 Simulated / 红线 5 条不可绕过
      / NSFL 熔断不静默通过 / 合规红线（不发币不代币化）随 push 公开
基座: tdca-toolchain/（tdca_verify_chain.py 链校验 / tdca_tool.py CLI / tdca_mou_recorder.py 记账）
      + tdca-protocol-pack/templates/nca-template.yaml（字段风格对齐）
```

## 四、后续联动

- S0 完成 → 人类签批 → FROZEN → 与开源推送（NCA-RELEASE-003）同批发布
- 与三闸齐开并行：闸 3 push 即携带 S0 制度文本与 enforce_entry.py
- 遗留核验: 首个外部第三方 CTS-L1 一致性声明（北极星，S3）→ 以 S0 缔约机制为入口
- 资金: 赞助通道（FUNDING.yml）被动接收，支出逐笔 NCA——S0 阶段 0 成本

> 本 DCD 已由 HUMAN-FOUNDER-001 签批（2026-08-21，NCA-20260821-009，GSEQ-0324）；验收以 S0-2 测试全绿 + S0-3 演练通过为准，禁止绕过红线（NSFL 一票否决）。S0-2 实现移交 Kimi Work 施工。
