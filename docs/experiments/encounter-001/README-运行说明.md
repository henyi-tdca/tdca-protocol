# ENC-REPO-001 · 相遇专章检查器 · 运行说明

> 件依据：《场景线 · 相遇专章》TDCA-STD-SCENE-ENCOUNTER-001 V1.0（人读版＋机读版，签批记录见 docs/regulations/ 同名签批件）
> 闸门：`.github/workflows/encounter-assert-gate.yml` 于每次改动相关路径之 PR 自动跑**三脚本**（硬闸），不过不许合。
> 纪律：四脚本只读、零出网；⛔ 不改任何在册件；交付件内本机绝对路径串零命中（仓内相对锚定／环境变量占位）。

## 一、四脚本与期望输出

| 脚本 | 作用 | 期望输出 |
|---|---|---|
| `enc_gaps_sandbox_v1.py` | 沙盒仿真（有限模型穷举：合法路径／非法迁移／存证二分／配置权／门禁面） | 7/7 通过 ｜ EXIT 0 |
| `enc_identity_interface_assert_v1.py` | 相遇线↔身份线接口断言（合规 7 断言＋对抗 7 条＋换序＋可重复） | 7/7 全过 · 对抗 7/7 · 0 漏检 · EXIT 0 |
| `enc_gaps_assert_v2_formal.py` | 复跑版（对正式条文：人读版＋机读版，结构面硬校验；仓内相对锚定） | 12/12 通过 ｜ EXIT 0 |
| `enc_gaps_assert_v1.py` | 相遇三缝隙断言（对研究草案＋双向奔赴口径件两件智库件） | 12/12 通过 ｜ EXIT 0；**被引件不在位 ⟹ 如实 SKIP（EXIT 0）** |

## 二、怎么跑

```bash
# 三脚本（CI 同口径·任意工作目录均可，路径自锚定于脚本位）
python docs/experiments/encounter-001/enc_gaps_sandbox_v1.py
python docs/experiments/encounter-001/enc_identity_interface_assert_v1.py
python docs/experiments/encounter-001/enc_gaps_assert_v2_formal.py

# v1（本地复跑件·不进 CI 硬闸）：先设环境变量指向智库工作区根
set TDCA_ENC_ASSERT_WS=<智库工作区根>          # Windows
export TDCA_ENC_ASSERT_WS=<智库工作区根>        # Linux/macOS
python docs/experiments/encounter-001/enc_gaps_assert_v1.py
```

## 三、依赖说明（如实登记）

- `enc_gaps_sandbox_v1.py`、`enc_identity_interface_assert_v1.py`：零外部依赖（仅标准库）；沙盒位取脚本旁相对目录（`.tmp-enc-identity-interface`），跑完自删复原。
- `enc_gaps_assert_v2_formal.py`：需 PyYAML（标准外唯一依赖）；条文路径仓内相对锚定（`../../regulations/` 两件），云端 runner 直接可跑。
- `enc_gaps_assert_v1.py`：被引两件智库 `governance/decisions` 件不在仓——云端 runner 不进此步（改造令·丙）；本地复跑经环境变量 `TDCA_ENC_ASSERT_WS` 占位锚定，缺件如实 SKIP，⛔ 不伪报通过。
