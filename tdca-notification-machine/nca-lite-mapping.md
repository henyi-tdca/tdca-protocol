# NCA-Lite 字段裁剪映射表（nca-lite-mapping）

> 依据: 制度合伙人待澄清项 A | 交付: 通知机规范包
> 模拟态: 通知机硬件未投产部署，本文件为模拟（SIL）语境之概念对照，不构成真实部署。
> 目的: 显式声明芯片端轻量 NCA（8 字段）与全量 NCA（MEMO-006 附录 C 11 字段）的裁剪逻辑

---

## 一、映射总表

| 全量 NCA 11 字段（PACK-001 nca-template） | Lite 8 字段 | 处理方式 | 承载侧 |
|------|------------|---------|--------|
| NCA-ID | `nca_id` | 保留（TDCA-NCA-LITE-{HWID}-{seq}） | 芯片端 |
| FC-ID | `type` + nca_id 前缀 | **合并**（调用类型由 type 承载，FC 归属由 TCN 全量 NCA 关联） | 芯片端/TCN |
| Operation-Type | `type` | 保留（fact/auth/mou/state） | 芯片端 |
| Operator | `signer` | **合并**（芯片端 Operator=硬件签名者，SE SM2） | 芯片端 |
| Timestamp | `ts` | 保留（芯片 RTC + 网络校时） | 芯片端 |
| Pre-State | `prev_hash` | **合并**（前块哈希 = 前状态链式隐含） | 芯片端 |
| Post-State | `hash` | 保留（载荷 SHA-256） | 芯片端 |
| Config-Right-Token | — | **裁剪 → TCN 侧**（芯片端不承载配置权调度，L2 配置权市场在 TCN 层） | TCN |
| Audit-Trail | `payload_ref` | **裁剪 → 链式引用**（内嵌轨迹改为 FactHash_n 引用，全量轨迹由 TCN 回溯补全） | TCN |
| Human-Signature | `signer` | **裁剪 → 硬件签名采集证据（快系统）；人类签批由 TCN 全量 NCA 承载（慢系统，不可绕过）** | TCN |
| Negative-Space-Check | `nsfl` | 保留（NSFL-V0.2 触发标记） | 芯片端 |

## 二、裁剪原则

1. **配置权字段（Config-Right-Token）不上芯片**：配置权调度属 L2 配置权市场层，芯片端只做采集与签名，不做调度（权限边界下沉禁止）
2. **审计轨迹用链式引用替代内嵌**：`payload_ref` 指向事实哈希链（FactHash_n），全量轨迹由 TCN 侧按引用回溯补全——受限存储下不丢失制度效力
3. **人类签批归慢系统**：芯片端 SE 硬件签名 = 快系统采集证据；人类签批由 TCN 全量 NCA 承载（慢系统裁决不可绕过）

**扩展字段裁剪**（PACK-001 nca-template.yaml 的 Scope + MOU-Anchor）：
- `Scope`（操作范围）→ TCN 全量 NCA 承载（芯片端无独立操作范围主张，从属原则）
- `MOU-Anchor` → config/call-rules.json 快照承载（mou_mode/mou_anchor，模拟态 D-011）

**type 枚举扩展**：`fact`/`auth`/`mou`/`state` + `service`（认证/服务事件，人类裁决 2026-08-11 独立 type）。

## 三、版本控制

- Lite 协议版本号：`nca_lite.version = "1.0"`（写入 .tdca/nca-lite/ 元数据头，TCN 解析器按版本识别，防版本漂移——制度合伙人建议）
- 升级路径：版本不兼容变更须经 TCN 解析器灰度 + 制度审查（REV-NM-001 链）
