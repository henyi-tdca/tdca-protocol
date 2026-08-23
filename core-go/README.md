# TDCA Core Go — 制度逻辑的 Go 强类型生产级实现

> **TDCA 制度逻辑的 Go 强类型生产级实现**（双引擎：Python 指挥台 + Go 核反应堆）
> 版本: 1.0.0 ｜ 许可: **Apache-2.0**（独立子目录，随 tdca-protocol 仓库）
> 立项: DCD-CORE-GO-001（ACCEPT）｜ 融入: TDCA-CORE-GO-INTEGRATION-001（I-1~I-4）

## 定位

Python 版（tools/）承担制度/编排/沙盒——灵活；**本 Go 引擎承担核心执行层——强类型/高并发/零篡改**，是"制度与技术同构（ID35）"的工程硬核。**全绿不是唯一验证标准——须经受破坏性测试**（伪造 NCA/绕过 NSFL/篡改税收/并发压测/提示注入）。

## 模块

| 包 | 功能 | 破坏性测试 |
|---|---|---|
| `pkg/enforce` | 强类型准入门禁（AgentCard 校验 + 公理 6 反函数 + 注入检测） | 注入/越权 fail-closed；未知字段；超长；无 NSFL 边界 BLOCK |
| `pkg/nca` | 不可变哈希链（append-only + 并发安全 + SM2 验签接口） | 伪造 prev_hash 拒绝；篡改检测；签名缺失；万级并发 |
| `pkg/nsfl` | 负空间熔断器（WARN→BLOCK→HUMAN→FUSED 分级 + 物理/制度） | 绕过 FUSED 不可逆；FUSED 后不可 HumanOverride；并发判定 |
| `cmd/tdcad` | 守护进程 CLI（enforce/nca/nsfl 子命令） | — |
| `bridge/` | Python↔Go 桥接（接口熵=0） | — |

## 快速开始

```bash
# 构建
go build -o tdcad ./cmd/tdcad

# 准入校验
./tdcad enforce check card.json

# NCA 链
./tdcad nca append record.json
./tdcad nca verify records.json

# 熔断判定
./tdcad nsfl eval t1 suspicious-pattern

# 测试（含破坏性 + -race）
go test -race ./...
```

## Python 桥接（tools/ 侧）

```python
from tdca_core_go import TdcadBridge
b = TdcadBridge()                    # 自动探测 tdcad
assert b.enforce_check(card)["status"] == "PASS"
b.nca_append(record)                 # NCA 链追加
b.nsfl_eval("t1", "key-export")      # 熔断判定
```

## 制度纪律

- **接口熵=0**：JSON 输出与 Python 版（NCA 模板/NCA-Lite）100% 同构
- **Apache-2.0 开源 + 服务层收费**（创始人裁定，不闭源；ID77/CALL-001 一致）
- **SE 密钥永不落盘**（SM2 私钥注入即锁死）；人类签名权归 TCN 慢系统（ID71）
- 破坏性测试：伪造 NCA / 绕过 NSFL / 篡改税收锚定 / 十万级并发 / 提示注入——全绿非唯一标准

## 关联

DCD-CORE-GO-001 ｜ TDCA-CORE-GO-INTEGRATION-001 ｜ TDCA-OPEN-COLLAB-001 ｜ 通知机（NCA-Lite/NSFL 对接）
