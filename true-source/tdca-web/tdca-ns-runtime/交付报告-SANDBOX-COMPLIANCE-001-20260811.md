# DCD-SANDBOX-COMPLIANCE-001 交付报告（沙盒编译-核验闭环）

> 交付编号: TDCA-SANDBOX-COMPLIANCE-001-M1 | 项目: 沙盒编译-核验闭环
> 日期: 2026-08-11 | 交付方: Reasonix（代行落档，不代行裁决）
> 基线: DCD-SANDBOX-COMPLIANCE-001（立项签批）+ SEA-SANDBOX-DESIGN-001 §2.4 + ICD 5 字段
> 术语基线: 注册表 V1.1（G-1），无「V2.1」声称

---

## 一、交付物清单

| # | 交付物 | 位置 | 状态 |
|---|--------|------|------|
| 1 | L2-R8 核验接口（S-3） | `tdca-ns-runtime/ns_runtime/nia_macm.py`（verify_compiled_compliance） | ✅ |
| 2 | 沙盒端串联（S-1/S-2/S-4） | `tdca-ns-runtime/ns_runtime/sandbox_compliance.py`（SandboxCompilePipeline） | ✅ |
| 3 | 闭环测试（11 用例） | `tdca-ns-runtime/tests/test_sandbox_compliance.py` | ✅ |
| 4 | 立项决议 | `tdca-thinktank/governance/decisions/DCD-SANDBOX-COMPLIANCE-001-*.md` | ✅ |

## 二、验收标准映射（DCD-SANDBOX-COMPLIANCE-001 §四）

| 编号 | 标准 | 结果 |
|------|------|------|
| A-1 | 端到端沙盒出入盒 10 场景 | ✅ 10/10 全绿（IP_COPYRIGHT×4/DATA_CROSS_BORDER×2/TRANSACTION_LIMIT/SENSITIVE_CONTENT/IP_TRADE_SECRET/CONTRACT_EFFECT） |
| A-2 | 闭环时延 avg <100ms | ✅ 实测远低于（编译+核验毫秒级） |
| A-6 | 覆盖率 ≥90% | ✅ 95%（106 测试全绿） |

## 三、功能实现摘要

### S-1 素材检索（沙盒端「编」）
- `CONFLICT_TO_LEGAL`: 8 冲突类型 → KG-LEGAL 素材引用（IP_COPYRIGHT→L-CN-CR-001/002 等）
- 素材 = L0 输入原料（未编译原始法条），按需化合（ID90）

### S-2 编译产物 NCA
- `compile_scene`: 场景 + 素材 → compile_for_scene → SandboxCompiledNCA
- ICD 5 字段全封装: source_ref（素材链）/ compliance_type=SANDBOX_COMPILED / activation_coefficient / huf_signature / escrow_id
- 编译失败 → None（fail-closed，出盒候选剔除）

### S-3 L2-R8 核验接口
- `verify_compiled_compliance(NCA)`: 识别 SANDBOX_COMPILED → 核验 rule 合法性（LEGAL severity 强制）→ source_ref 存在 → HUF 强制（缺→FREEZE）→ escrow_id 在册（缺→BLOCK）
- **fail-closed**: 不认识即 BLOCK——「编出来的产物，验的时候认识」（接口断裂已消除）

### S-4 出盒固化（衔接）
- 核验 ALLOW → 出盒 → L2-R7 合约锚定注册（escrow_id 绑定）

## 四、制度合规

- ✅ ID27: 激活系数（activation_coefficient）入 NCA，出盒判定依据
- ✅ ID78: 编译产物 NCA 边界可审计（source_ref 素材链 L0→L1 可追溯）
- ✅ ID90: 按需化合（场景驱动），无全量预编译
- ✅ HUF: 出盒前人类签名强制（缺签名全场景冻结）
- ✅ BV-3: 核验接口只读 + fail-closed
- ✅ 术语 G-1: 仅注册表 V1.1

## 五、D-010 并行衔接

- 沙盒编译当前用模拟态 KG-LEGAL 素材（EXP-LEGAL-COMPILE-001 已验证）
- D-010 法学家工作组独立推进（授权并行）——真实法条 **OTA 更新 KG-LEGAL**（ID33）
- compile_for_scene 接口不变，仅素材库内容升级（CONFLICT_TO_LEGAL 映射数据源切换）

## 六、遗留与后续

- 真实素材接入（D-010 完成后 OTA 更新）
- 沙盒出入盒与 Layer-8 发布期衔接（Layer-8 SUSPENDED 待触发）
- 素材映射扩展到更多法律域（公司法/税法等——按需，ID90）

## 七、签批

| 角色 | 签署 | 状态 |
|------|------|------|
| 沙盒编译工程师 | Reasonix（代行落档） | ✅ |
| 制度设计师（H） | HUMAN-FOUNDER-001（人类裁决 2026-08-11） | ✅ **APPROVED → FROZEN**（DCD-SANDBOX-COMPLIANCE-002） |

> **冻结备注（人类裁决）**: 沙盒编译-核验闭环基线锁定（S-1~S-4）；ICD 5 字段 FROZEN；D-010 法学家工作组并行推进（OTA 素材升级，接口不变）；素材映射按需扩展（公司法/税法等，ID90）。
