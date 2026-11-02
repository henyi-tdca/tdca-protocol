# TDCA-HANDOFF-WORKBUDDY-ENG-GOV-B1-002 · WorkBuddy 补充施工指令：D-1~D-3 处置（批次 1 补全）

> 文档编号: TDCA-HANDOFF-WORKBUDDY-ENG-GOV-B1-002 ｜ 编制: 2026-09-02（Reasonix）｜ 状态: ✅ 已下令（GSEQ-0884）｜ 存证: GSEQ-0884
> 依据: Reasonix 核证批次 1 回报 + D-1~D-5 裁定（GSEQ-0883）

---

## 一、裁定结论（D-1~D-5）

| 编号 | 裁定 | 责任 |
|---|---|---|
| **D-1** | **既有 P0 实现存在**（Reasonix 工作区 `tdca-thinktank/governance/sandbox_coalition_validator.py` 7234B + `sandbox_drill.py` 7115B，实核含 form_coalition 严格小于拦截/COALITION_NOT_FEASIBLE/nca_emitted=False）——「不可核」= 同步缺口 | WorkBuddy 补核验 |
| **D-2** | `compute/coalition.py::form_coalition` 同名不同义（贪心撮合）→ **重命名为 `form_coalition_greedy`**（避免误认已硬化） | WorkBuddy（其侧文件） |
| **D-3** | `fuse.py::precheck` 缺 form_coalition + `emit_nca` 无强制网关 = **生产链真实硬化缺口** → 补字段映射 + 强制网关 | WorkBuddy 施工 |
| **D-4** | daily-obs 口径统一为实际编排 **09:00**（OPS-DISPOSAL-001 已修正） | Reasonix ✅ 已完成 |
| **D-5** | 接受 **M3B 真实数据**为标准回归基线（本次已采用）；酒店数据补存挂账 | 已定 |

## 二、WorkBuddy 补充执行项

1. **D-1 补核验**：既有实现核验（非规范复刻）——对 `sandbox_coalition_validator.py` + `sandbox_drill.py` 执行 1a 三子项（边界语义/网关强制/回归 M3B）+ 拦截率实测（负例 600 级，seed=42 可复现）——文件由 Reasonix 工作区同步提供（归档镜像 `工作区归档/tdca-thinktank/governance/` 已含，可检索）；
2. **D-2 重命名**：`compute/coalition.py::form_coalition` → `form_coalition_greedy`（含调用点同步更新）；不改变其撮合语义，仅消除「误认已硬化」风险；
3. **D-3 硬化施工**：`tools/mcp_bridge/fuse.py::precheck` 补 `form_coalition` 字段（复用既有/复刻校验语义）+ `emit_nca` 前强制网关（不可行联盟 → SandboxEntryDenied）——**生产链硬化，本项为批次 1 真正缺口**；
4. 交付物 NCA 存证（批次 1 补全后统一登记）。

## 三、纪律

- D-2/D-3 属核心代码施工：WorkBuddy 侧可执行（其文件），但改动须可回溯（diff + 测试）+ NCA 存证；
- 先搜不重复：D-3 网关复用 `coalition_precheck_ref.py` 已验证语义，不另起炉灶；
- 数据性质标注：real（既有实现实测）/constructed（构造用例）如实。

## 四、回报格式

D-1 补核验报告（既有实现拦截率）+ D-2 重命名 commit + D-3 硬化测试 → Reasonix 核证（批次 1 收口 → 触发批次 2）。

---

*批次 1 补全指令（D-1~D-3 处置）｜ 存证：GSEQ-0884*
