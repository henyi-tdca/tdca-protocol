# Security Policy（TDCA 安全策略与漏洞披露）

> 文档: SECURITY.md ｜ 版本: V1.0 ｜ 日期: 2026-08-23 ｜ 状态: ✅ 发布
> 依据: TDCA-SECURITY-OPEN-001（四道防线）｜ TDCA-SECURITY-TAMPER-001（制度防篡改）

## 一、支持的版本（Supported Versions）

| 组件 | 支持策略 |
|---|---|
| core-go（enforce/nca/nsfl/mcp） | 当前 main + 最近 1 个发布版 |
| ecoscan（扫描/诊断/邀请/台账） | 当前 main |
| 通知机（协议包/固件规范） | FROZEN 版本（变更走 DCD） |

## 二、报告漏洞（Responsible Disclosure）

**请勿公开披露未修复漏洞。** 报告方式：

1. **私密渠道**：GitHub Security Advisory（仓库 → Security → Report a vulnerability）
2. **备选**：项目维护者私信（先确认身份）

**报告内容**：
- 受影响组件 + 版本
- 漏洞类型（注入/越权/链伪造/熔断绕过等）
- 复现步骤（PoC 优先）
- 影响评估

**响应承诺**：
- 48h 内确认收到
- 90 天内修复（按严重度：Critical < 14 天）
- 修复后公开致谢（报告者署名，如同意）

## 三、安全立场（Security Posture）

- **fail-closed 底线**：任何不确定 → BLOCK/熔断（不默认放行）
- **破坏性测试**：伪造 NCA / 绕过 NSFL / 篡改 / 注入 / 并发（-race）——全绿非唯一标准
- **公理 6 机验**：`VerifyAxiom6()` 自动检测制度函数行为偏离（制度防篡改锚 ④）
- **密钥纪律**：SE 密钥永不落盘；SM2 注入即锁死
- **制度防篡改**：宪法哈希锚定（TDID）+ 硬宪法不可 OTA + 四方联签（详见 TDCA-SECURITY-TAMPER-001）

## 四、威胁模型（简版）

开源协作交易攻击面分两类：
- **技术攻击**（漏洞/注入/越权）→ 技术防线（本策略 + 测试 + CI）
- **经济-博弈攻击**（分润欺诈/Sybil/冒名/审计规避）→ 制度防线（NCA 链/认证/准入/熔断——详见 TDCA-SECURITY-INSTITUTIONAL-001）

## 五、供应链

- core-go：零第三方依赖（Go 标准库）
- ecoscan：stdlib + pyyaml（依赖清单 + checksum 维护中）
- 构建可复现（CI 门禁 vet/race/build/smoke）

## 六、联系

安全相关（非漏洞）：[GitHub Issues] → 标签 `security`

---

> 本策略为 TDCA 开源安全运营入口（漏洞披露 + 安全立场 + 威胁模型）；修复走 DCD 紧急流程。
> 关联: TDCA-SECURITY-OPEN-001 ｜ TDCA-SECURITY-INSTITUTIONAL-001 ｜ TDCA-SECURITY-TAMPER-001
