MAIL｜id=TDCA-HANDOFF-EXEC-L1SI168-X1GUARD-001｜令=TDCA-DESIGN-L1SI168-ASSERT-X1-001｜sha256_16=PENDING-SIDECAR｜态=SENT｜依据=n/a｜时=2026-10-23T19:17+08:00

# 交办令 · **`X-1` `A` 级六条守卫包**（可挂 `CI`）

> 件号: **`TDCA-HANDOFF-EXEC-L1SI168-X1GUARD-001`** ｜ 版本: **`V1.0`** ｜ 日期: **`2026-10-23`**（+08）
> 会话框: **`L1-SI-168`** ｜ 编制: **`Reasonix`** ｜ 操作类型: **`Handoff`**
> 性质: ⚠️ **内部件 · ⛔ 非对外** ｜ 受令方: ⭐ **`KIMI`（执行侧）** ｜ 状态: ⭐ **已投信箱**
> 依据: ⭐ `GSEQ-5846`（`E-01`~`E-12` 验证断言件）／ ⭐ `GSEQ-5855`（`E-13`~`E-15`）

---

## 〇、⭐ 一句话

⭐ **脚本已写好在主仓**：⭐ `tools/tdca_x1_guard_v1.py`（**`4,150`**B · `A31DC08D85D294CD`）；⭐ **挂进 `CI` 即成**：⭐ 本侧已自测 **`PASS 6/6` · `X1-GUARD=GREEN`**；⭐ 缺样本 **`SKIP`**、⛔ **假绿**。

---

## 一、⭐ 交了哪两样

| # | 物 | 路径 | 大小 ／ 哈希 |
|---|---|---|---|
| `1` | ⭐ **守卫脚本** | `tools/tdca_x1_guard_v1.py` | **`4,150`**B · **`A31DC08D85D294CD`** |
| `2` | ⭐ **合成夹具**（`6` 件 · `SIMULATED-TEST`） | `tools/fixtures/x1-samples/E-0x.json` | ⭐ 见 §三 |

⭐ **验哪六条**：⭐ `E-01` 净额结算 ／ `E-02` 微交付税额 ／ `E-08` 身份映射互逆 ／ `E-09` `S-Right` 十四步 ／ `E-11` 出题评分 ／ `E-12` 标注分歧。

---

## 二、⭐ 挂法（⭐ 三种，任选其一）

1. ⭐ **`pytest` 包一层**（⭐ 推荐，⭐ 与既有 `gateway/tests/` 同构）：
   ```python
   # gateway/tests/test_x1_guard.py
   import subprocess, sys, pathlib
   ROOT = pathlib.Path(__file__).resolve().parents[2]
   def test_x1_guard():
       r = subprocess.run([sys.executable, str(ROOT / "tools/tdca_x1_guard_v1.py"),
                           str(ROOT / "tools/fixtures/x1-samples")],
                          capture_output=True, text=True)
       print(r.stdout)
       assert r.returncode == 0, "X1-GUARD=RED"
   ```
2. ⭐ **`CI` 直跑**：⭐ 在既有跑测脚本里加一行 `python tools/tdca_x1_guard_v1.py tools/fixtures/x1-samples`（⭐ 退出码即判据）。
3. ⭐ **前置守卫**：⭐ 仅当改动触及判定路径时跑（⭐ 与 `model_invariant_diff_gate.py` 同法）。

---

## 三、⭐ 退出码语义（⭐ ⛔ 改）

| 码 | 含义 | ⭐ 说明 |
|---|---|---|
| `0` | ⭐ **`GREEN`**：已有样本**全过** | ⭐ 缺样本**不算红**（⭐ 但**逐条打 `SKIP`**） |
| `1` | ⭐ **`RED`**：⭐ 有 `FAIL`；⭐ 或 `--strict` 下有 `SKIP` | ⭐ 样本应齐的场合用 `--strict` |
| `2` | ⭐ 样本目录不存在 | ⭐ 配置错 |

⭐ **⛔ 三条禁令**：⭐ ① ⛔ 把 `SKIP` 改 `PASS`（⭐ 假绿）；⭐ ② ⛔ 为凑绿删样本；⭐ ③ ⛔ 改判定式迁就样本（⭐ 判定式在 `GSEQ-5846`／`5855` 在案，⭐ 改须出 `AMEND`）。

---

## 四、⭐ 样本从哪来（⭐ 与 `B` 级联动）

⭐ 本守卫吃的是**产品产出样本**：⭐ 现给了 `6` 件**合成夹具**（⭐ 仅证脚本可跑，⭐ 标 `SIMULATED-TEST`）。
⭐ **真样本到位即替换**（⭐ 文件名不变：`E-01.json` 等）⟹ ⭐ **同一条守卫自动升为真验**，⭐ 无改脚本。
⭐ `B` 级 `9` 条（`E-03`…`E-15`）样本到了以后，⭐ 本侧按同法扩守卫（⭐ 另批）。

---

## 五、⭐ 停手（`S-1`~`S-3`）

`S-1` ⭐ 若挂入后 `CI` **红且非环境病** ⟹ 停手报原文；`S-2` ⭐ 若判定式与既有断言冲突 ⟹ 停手报本侧；`S-3` ⭐ 若需改判定式本身 ⟹ 停手（⭐ 须 `AMEND`）。

---

## 六、⭐ 回报（`4` 项）

1. ⭐ 挂法（⭐ 三选一）与**落点文件**；2. ⭐ 首次跑**原文**（⭐ 含 `PASS/FAIL/SKIP` 计数与 `X1-GUARD=` 行）；3. ⭐ 真样本替换后**再跑一次**原文；4. ⭐ 未办与原因。

---

## 七、边界

- 本件 ⭐ 只出令与交付物：⛔ 本侧不入仓远端 ／ ⛔ 不推送 ／ ⛔ 不挂 `CI`（⭐ 挂载在于你侧）；
- 件名 ≤ `110`；`UTF-8` 无 `BOM`；`LF`。

---

*Reasonix · L1-SI-168 · Handoff · 2026-10-23（+08）*
