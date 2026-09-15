# tdca-eios — EIOS 生态智能操作系统

> **Function-Call-ID：** TDCA-PHASE-E-INT-1
> **签批：** TDCA 创始人（已签批 2026-08-04：确认 E-INT-1 启动，E-HW-2 硬件制造搁置后续补）
> **制度依据：** 快慢系统战略 / 制度基座第一性 / TDCA-PRINCIPLE-ENG-003 最小化合 / 破例识别
> **硬约束：** 不修改 FC-001~012 / UI-001~007 / TIMA 已归档代码（封装调用）
> **原型态：** 本包为原型实现（mock 先行）；通知机硬件未投产部署，相关驱动为模拟（SIL），不构成真实部署。

## 目录结构

```
tdca-eios/
├── README.md                  # 本文件
├── docs/
│   └── EIOS-ARCH-001.md       # M1: EIOS 三层架构设计（模块划分 + 接口契约 + 调用关系）
├── src/
│   ├── __init__.py
│   └── nm_device_driver.py    # M4: NMDeviceDriver 抽象接口 + mock 实现（E-HW-1 兼容）
└── (后续里程碑)
    ├── asp_protocol.py        # M2: ASP 智能体调度协议（与 FC-012 9 Phase 同构）
    ├── cks_deployment.py      # M3: CKS 同步协议部署（与 TIMA VersionVector 兼容）
    └── dashboard/             # M5: 全周期管理看板原型（复用 UI-001~007）
```

## 里程碑

| 里程碑 | 日期 | 交付 | 状态 |
|--------|------|------|------|
| M1 | 08-10 | EIOS 三层架构文档 | **进行中** |
| M2 | 08-20 | ASP 智能体调度协议 V0.1 | 待启动 |
| M3 | 08-25 | CKS 同步协议部署规范 | 待启动 |
| M4 | 08-20 | NMDeviceDriver 接口草案 + mock | 进行中（与 M1 同步） |
| M5 | 08-30 | 全周期管理看板原型 | 待启动 |
| M6 | 09-01 | E-INT-1 归档 + 集成测试报告 | 待启动 |

## NSFL 禁止操作（任务书配置权边界）

- 禁止修改 FC-001~012 / UI-001~007 / TIMA 已归档代码
- 禁止绕过 FC-012 9 Phase 流程直接调度智能体
- 禁止在 EIOS 中重新实现 TIMA 或 FC-012 的功能
- 禁止 NMDeviceDriver 接口偏离 E-HW-1 硬件规格书
