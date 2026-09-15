# REV-NM-001 制度合规审查报告（通知机实现阶段轨道 1+2 交付物）

> 审查官: tdca-compliance-auditor（隔离执行）| 审查日期: 2026-08-11
> 审查基准: KB-INST-020（宪法十六条 V3.0 STABLE）/ KB-INST-010（TERMS-001）/ KB-ECON-001 / AGENT-EXEC-001 / FC-NSFL-001
> 审查模式: 模拟态（MOU 锚定 D-011，不构成真实配置权执行路径；通知机硬件未投产部署）
> 状态: ❌ FAILED（1 CRITICAL + 2 BLOCKING + 7 WARNING）| 修复后复审预期: PASSED_WITH_FINDINGS

---

## 一、审查对象

| # | 对象 | 类型 | 位置 |
|---|------|------|------|
| 1 | .tdca 固件元数据格式规范 V0.2-REV（DRAFT） | 文档 | tdca-notification-machine/tdca-firmware-spec.md |
| 2 | 8 个 JSON 模板 | 模板 | tdca-notification-machine/templates/.tdca/ |
| 3 | 计量映射引擎 V0.1 | 代码 | tdca-notification-machine/engine/notification_machine_engine.py |
| 4 | 8 用例测试 | 测试 | tdca-notification-machine/tests/test_nm_engine.py |
| 5 | NCA-Lite 8 字段裁剪映射 | 文档 | tdca-notification-machine/nca-lite-mapping.md |
| 6 | FC-SPEC V1.2（五层架构基线） | 文档 | docs/notification-machine/TDCA-FC-20260811-004-NOTIFICATION-MACHINE-FC-SPEC.md |

## 二、违规清单

| # | 严重度 | 位置 | 制度依据 | 问题描述 | 修复建议 |
|---|--------|------|---------|---------|---------|
| 1 | 🔴 **CRITICAL** | engine/notification_machine_engine.py L268-286（服务调用分支） | KB-ECON-001 §5 MOU 归零：`T(y_t)>0` 才有效，≤0 强制归零；FC-SPEC 4.2 | 服务调用（NODE_AUTH）分支不校验 tax_receipt：tax_receipt=0 仍 APPROVED 收服务费，未走 MOU 归零；测试无 tax=0 负例 | 服务分支调用 validate_mou；或由人类显式裁决"L2 年度合同服务费豁免 MOU 归零"并记录豁免依据——**禁止静默绕过** |
| 2 | 🟠 **BLOCKING** | tdca-firmware-spec.md §七 模板清单 L314-315 | 制度裁决 SE-SIGN-5（2026-08-11） | **文档内部矛盾**：正文 §1.6/§2.2 已按裁决将 config/* 升 SE 签名，但 §七 模板清单仍写"固件 HMAC" | §七 模板清单 config 两行改为"SE SM2（SE-SIGN-5）" |
| 3 | 🟠 **BLOCKING** | engine L234-255/322-323（fuse_info 恒 None） | 规范 §1.4/§6.2；宪法 C09 | 实现层未落实物理/制度负空间区分：FUSED 转换不记录 fuse_info.type，审计无法区分不可逆物理熔断与可逆制度熔断 | FUSED/SUSPENDED 转换填充 fuse_info{type, sc_phy_id, irreversible} |
| 4 | 🟡 WARNING | engine L168（NODE_AUTH→mou）；test L86 | 规范 §1.3；TERMS-001 接口熵=0 | 认证事件映射为 mou 类型——语义漂移，TCN 解析器可能误判 | 独立 type（service/cert）或显式裁决借用 mou |
| 5 | 🟡 WARNING | test L87 / engine L280-281 | FC-SPEC §七 状态机 | 认证调用 UNREGISTERED→CERTIFIED 跳过 REGISTERED | 补中间态或注明原型简化豁免 |
| 6 | 🟡 WARNING | templates L0-state.nca.json L10（sm3_full）vs 规范 §1.2 | TERMS-001 接口熵=0 | 模板含 sm3_full 字段但规范未同步 | 规范 §1.2 补 sm3_full（SM3 国密 + SHA-256 双哈希） |
| 7 | 🟡 WARNING | 规范 §6 / FC-SPEC 澄清 C | 三档熔断 | 场景级 BLOCK/FUSED 两级未声明与生态三档（Level-1/2/3）的映射关系 | 文档补映射说明 |
| 8 | 🟡 WARNING | test L135（`or True` 弱断言）；docstring | AGENT-EXEC-001 模拟态 | 恒真断言失效；测试头未显式模拟态标注 | 删 or True；docstring 加模拟态标注 |
| 9 | 🟡 WARNING | engine _sign L147-154 | 规范 §2.2/§2.3 | mock 只签 payload 非记录整体，签名对象语义需明确 | 注释/规范明确正式签名对象=记录整体载荷 |
| 10 | 🟡 WARNING | engine _advance_state/_snapshot | 规范 §1.4；宪法 C01 | transition_nca_ref 恒 None，状态转换审计断点 | 标注"TCN 慢系统回填"，预留回写接口 |
| 11 | 🟡 WARNING | nca-lite-mapping.md / 规范 §三 | TERMS-001 接口熵=0 | 映射表未覆盖 PACK-001 模板 Scope/MOU-Anchor 扩展字段去向 | 补"扩展字段裁剪说明"行 |
| 12 | 🟡 WARNING | nca-lite-mapping.md L21 | 快慢系统 | "裁剪 → 硬件签名替代"措辞易误读为硬件签名取代人类签批 | 改为"硬件签名采集证据（快系统）；人类签批由 TCN 全量 NCA 承载（慢系统）" |

## 三、审查要点逐项结论

| 要点 | 结论 |
|------|------|
| A. NSFL 负空间区分 | 文档层 ✅ 正确（物理 001/003 不可逆 vs 制度 002 NSFL）；实现层 ❌ fuse_info 未区分（违规 3） |
| B. 人类签名权不可绕过（快慢系统） | ✅ 合规：SE 硬件签名=快系统采集证据，人类签批归 TCN 慢系统 |
| C. PUF 密钥材料不落盘/外传 | ✅ 合规：仅存 puf_hash、SE 私钥不导出、引擎无密钥处理。**无违规** |
| D. Config-Right-Token 裁剪至 TCN | ✅ 合规：映射表裁剪至 TCN、L1-active 仅存引用摘要、引擎无配置权调度。**无违规** |
| E. MOU 归零 | ⚠️ 部分：计量分支 ✅；服务分支 ❌ 绕过（违规 1，CRITICAL） |
| F. 可观测性/自证 | ⚠️ 大部分：每次 execute 生成 NCA-Lite + fact block ✅；状态转换 transition_nca_ref 缺失（违规 10） |
| G. 字段同构（制度同构跃进） | ⚠️ 8↔11 映射无漂移 ✅（人类裁决落地正确，附录 A 已降概念对照）；扩展字段去向未声明 + L0-state 模板字段未同步（违规 6/11） |

## 四、总体结论

- **合规状态: ❌ FAILED**（1 CRITICAL + 2 BLOCKING + 7 WARNING）
- **修复优先级**：
  1. **P0-CRITICAL**：违规 1（MOU 归零绕过）——经济硬约束绕过，先修（**待人类裁决豁免或强制**）
  2. **P0-BLOCKING**：违规 2（SE-SIGN-5 §七 同步，改两行）、违规 3（fuse_info 落实）
  3. **P1-WARNING**：违规 4-7（type 语义/状态机/字段同步/三档熔断映射）
  4. **P2-WARNING**：违规 8-12（测试/标注/表述）
- **制度裁决提请**：服务调用（L2 年度合同）是否豁免 MOU 归零——经济公理解释分歧，须由人类裁决；裁决前按"待确认"处理，禁止静默绕过

---
> 审查链: 轨道 1+2 交付物 → REV-NM-001（tdca-compliance-auditor）→ 人类裁决 → 修复 → 复审

---

## 五、复审结论（PASSED_WITH_FINDINGS → 全闭环）

> 复审官: tdca-compliance-auditor（sa_20260811_102607，静态核对）| 复审日期: 2026-08-11

**复审结果：✅ PASSED_WITH_FINDINGS**（原 12 项违规：11 项完全闭环 + 违规 4 部分闭环残留 R1；CRITICAL/BLOCKING 全清零）

### 复审残留项处置记录

| 残留 | 严重度 | 内容 | 处置 |
|------|--------|------|------|
| R1 | 🟡 必改 | 规范 §三 type 枚举未补 service（正文与映射文档矛盾） | ✅ 已修复（§三 Operation-Type 枚举 + 完整字段示例补 service） |
| R2 | 🟡 建议 | validate_mou 传 HardwareCall 与基座类型标注不符 | ✅ 已修复（服务分支改 CallRequest 包装） |
| R3 | 🟡 待裁决 | 服务调用 MOU 归零后状态机是否推进 CERTIFIED | ✅ 人类裁决（2026-08-11）：**归零时不推进状态**——引擎条件化状态推进 + 测试断言 UNREGISTERED 保持 |
| R4 | 🟢 可选 | 附录 A type 枚举补 service | ✅ 已同步（附录 A lite.call_type 行） |

### 修复验证

- 引擎 10/10 测试全绿（新增 test_service_mou_zeroed 含 R3 断言、test_physical_vs_institutional_fuse 物理/制度区分）
- 引擎、测试、规范、映射、模板五侧 service type 枚举全同步（接口熵=0）
- fuse_info（type/sc_phy_id/irreversible）在 FUSED 转换落实，物理（001/003）不可逆 vs 制度（002）可逆区分可审计

**REV-NM-001 状态：✅ CLOSED → 已签批归档**（2026-08-11：经人类签批后归档，通知机协议包 V1.0 生效）
