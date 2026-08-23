# TDCA ECOSCAN · 生态雷达 + 邀请自动化（M2 全链流水线）

> 许可：Apache-2.0（独立许可，与仓库根 MIT 双轨并存）｜ 制度纪律：BIDIR-001 只赋能不改码 ｜ ID92 数据性质逐文件标注

ECOSCAN 是 TDCA 的生态扫描与受邀实测流水线：扫描目标开源项目 → 生成诊断 → 发出邀请 → 回收实测报告 → NCA 台账存证，全链自动化（`tdca_ecoscan/pipeline.py`，40 用例全绿）。

## 结构

| 路径 | 内容 |
|---|---|
| `tdca_ecoscan/` | 引擎：scanner（生态雷达）/ diagnoser（诊断）/ inviter（邀请）/ ledger（NCA 台账）/ pipeline（全链编排） |
| `tests/` | 40 用例（引擎 + 流水线） |
| `scripts/round1_dsh_codex.py` | 首轮双目标（DSH / Codex）受邀实测 |
| `scripts/retry_codex2.py` | Codex 504 重试轮 |
| `reports/` | 实测数据：`dsh-codex-round1.json` / `codex-retry-round2.json`（**real**，受邀实测回收）+ `.ledger/` NCA 台账（14 份存证） |

## 快速开始

```bash
cd ecoscan && python -m pytest tests -q   # 40 用例
```

## 纪律

- 邀请发送节流：≤ 2 条/周/目标（真实发送走人类签批闸门，ID71）
- 数据性质：tests/scripts 演示数据 = simulated（ID92）；reports/ = real（受邀实测，台账可溯）
- 生态协作：分润 15% + 开源方优先（双向赋能口径）
- 只赋能不改码（BIDIR-001）：不对目标项目提修改要求
