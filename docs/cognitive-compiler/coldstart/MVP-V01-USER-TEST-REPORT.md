# MVP V0.1 · 首个普通用户实测报告（GSEQ-0553）

> 扮演：第一个普通用户（界面化操作：选模板 + 填变量 + 提交）。不读 TDCA 哲学。
> 四步：注册 → 选模板 → 派智能体 → 缔约。跑通则用户自助化 V0.1 完成。
> 纪律：NSFL 先于一切 ｜ 凭证零落盘 ｜ 分润模拟态 ｜ NCA 走 generate_nca(max+1) ｜ 产物不推送。

## 步骤1 · 注册（IDENTITY.md）
- 字段完整性（GitHub名/智能体名/指纹/用途）：✅
- 公钥指纹格式（ssh-ed25519）：✅ → `256 SHA256:+GHiqFTYse+QsnxBnKsNECNzP4QwmAgf/D57C9wPJvk tdca-mvp-demo-user-tdca-agent (ED25519)`
- **IDENTITY 注册校验结果：PASS**
- enforce_entry --check（`TDCA-ADMIT-20260827-001.yaml`）：✅ PASS（R1~R10 全过）
- **发射权：已获得**（准入 NCA `TDCA-ADMIT-20260827-001`）

## 步骤2 · 选模板（COP 三套选一：科研协作联盟）
- 所选模板：**模板 1 · 科研协作联盟（research-collab）**
- 生成 COP（六要素自动预填）：✅ 落盘 `docs\cognitive-compiler\coldstart\community\MVP-V01-科研协作-贡献COP.yaml`

## 步骤3/4 · 派智能体（特使矩阵自动）+ 缔约（三段式闸门）
- **准入门**：`wb-v01-agent` 已加载基协议 TDCA-CORE-20260815-01 → 准入 → 发射 NCA `TDCA-REASONIX-20260827-001`
- **沙盒**：v(N)=90 ｜ φ_organizer=50(BATNA=40) ✅ ｜ φ_user=40(BATNA=30) ✅
  - mou_ok=True ｜ 分润模拟态 ｜ data_provenance=mixed ｜ [UNVERIFIED] 无外部锚（自报 res/batna）
- **生产**：联盟承诺 NCA `TDCA-REASONIX-20260827-002` ｜ 生产确权 NCA `TDCA-REASONIX-20260827-003`
- **贡献 COP 落盘**：`docs\cognitive-compiler\coldstart\community\MVP-V01-科研协作-贡献COP.yaml`

## 验收判定（V0.1 完成标准）
- [x] 普通用户视角完成四步（不读哲学、仅选模板+填变量+提交）
- [x] 全链 NCA 落链（准入/联盟/生产）
- [x] 产出：贡献 COP + IDENTITY-WORKBUDDY.md 注册记录

> **V0.1 验收：✅ 完成（用户自助化跑通）**

## 全链 NCA 编号
- 注册（AdmissionNCA，enforce_entry）：`TDCA-ADMIT-20260827-001`
- 准入（EcosystemAdmit，generate_nca）：`TDCA-REASONIX-20260827-001`
- 联盟（CoalitionCommit，generate_nca）：`TDCA-REASONIX-20260827-002`
- 生产（COPCompile，generate_nca）：`TDCA-REASONIX-20260827-003`

> 诚实性质声明：机制全真实（enforce_entry / generate_nca / 真实 Shapley 内联）；data_provenance=mixed（自报未确权）；VB/分润模拟态；无外部锚标 [UNVERIFIED]；沙盒 Shapley 因仓库 compute/shapley.py 缺失而内联实现（标准公式，非伪造）。
> 关联：GSEQ-0553（本指令）｜ GSEQ-0551（max+1 编号）｜ TDCA-HANDOFF-WORKBUDDY-V01-20260827-001
