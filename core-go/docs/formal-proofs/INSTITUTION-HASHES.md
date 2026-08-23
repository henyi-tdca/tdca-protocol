# TDCA 制度版本哈希公开清单（Institution Version Hashes）

> 文档: INSTITUTION-HASHES-001 ｜ 版本: V1.0 ｜ 日期: 2026-08-23 ｜ 状态: ✅ 发布
> 依据: TDCA-SECURITY-TAMPER-001（制度防篡改锚 ① 强化——制度哈希公开可验证）
> 用途: 社区独立核验 TDCA 官方制度版本——篡改即哈希失配（fail-closed）

---

## 一、制度对象 → 版本哈希

| 制度对象 | 版本 | 哈希（sha256） | 验证方式 |
|---|---|---|---|
| 宪法十六条（TDCA-CONST） | v3.1.2 | `sha256:{CONSTITUTION_HASH}`（见 tdca-firmware-spec / nm_simulator） | 与 TDID/L0-state 交叉校验 |
| NSFL 规则（R1-R10） | V0.2 | 见 pkg/nsfl/nsfl.go（DefaultRules 源码即规范） | go test 比对 |
| 公理 6 实例化 | TDCA-CORE-GO-AXIOM6-001 | 见 pkg/enforce/axiom6.go + axiom6_verify.go | `VerifyAxiom6()` 机验 |
| 数学基础白皮书 | TDCA-MATH-WP-REV-001 V1.0-FROZEN | 随 docs/formal-proofs/ 发布 | 文件哈希比对 |
| 分润规则 | 15%（动态分润） | TDCA-OPEN-COLLAB-001 §三 | 邀请函措辞比对 |

> 注：SHA256 精确值随发布批次生成并回填（Kimi 推送时计算）；本清单为**验证入口规范**。

## 二、验证方法（社区）

```bash
# 核验制度函数实现未被篡改（公理 6 行为锚）
cd core-go && go test ./pkg/enforce/ -run VerifyAxiom6

# 核验 NSFL 规则
go test ./pkg/nsfl/

# 核验 NCA 链完整性
go test ./pkg/nca/
```

## 三、权威来源（仅以下为官方）

| 渠道 | 说明 |
|---|---|
| henyi-tdca/tdca-protocol（GitHub） | 官方代码 + 本清单 |
| tdca-firmware-spec（FROZEN） | 通知机固件规范（宪法哈希锚定） |
| TDCA 数学基础白皮书 / 函数白皮书（FROZEN） | 制度理论权威 |

**防篡改纪律**：任何节点声称"TDCA 兼容/合规"必须通过认证（TDCA-CERT-001）——哈希清单是技术核验入口，认证是信任锚。

---

> 本清单为制度版本哈希公开验证入口（防篡改锚 ① 公开化）；随分层开源推送发布。
> 关联: TDCA-SECURITY-TAMPER-001 ｜ TDCA-CERT-001 ｜ TDCA-MATH-WP-REV-001
