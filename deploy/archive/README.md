# FROZEN 封板包归档（GSEQ-3180 第②段）

`tdca-web-deploy-FROZEN.zip`＝原 gateway/web 镜像之构建源（GSEQ-0642/0659 封板）。

**状态：归档物——⛔ 不再作运行源、⛔ 不再随改重建、⛔ 解封/重建须创始人明示。**

## 处置（2026-09-29）

- 部署改源：`Dockerfile.gateway`／`Dockerfile.web` 改由仓内正源 `true-source/tdca-web/` 构建（随正源纳管 PR 入仓）。
- 本包仅移动位置（`deploy/` → `deploy/archive/`），**字节未动**。指纹（2026-09-29 实测）：**md5 `47a9fd58475e33e0e160c7108a405686`**；sha256 前 16 `6054aa91fb294c99`（此前回报误将 sha256_16 标注为 md5，特此更正）。

## 与仓内两版之差异（详见 FROZEN-vs-repo-tdca-web-diff.txt）

| 对照 | 同 | 异 | zip 有而仓版无 |
|---|---|---|---|
| zip ⟷ `tdca-web/`（#301 856 行版） | 19 | 21 | 426 |

要点：

- `gateway/api_v1.py`：zip 版 **1235 行**（md5 `ee964146…`，线上实跑）vs 仓 856 行版——两版并存期间以 `true-source/` 为正源。
- 其余 20 件「异」：d2-union 各模块、app.py/auth.py/models.py/seed.py 等存在变体差异（856 行线源自 `deploy-pkg`，与 zip 非同一快照）。
- zip 内含**运行时产物**（`gateway/tdca.db`、多处 `.coverage`、`simulator/out/*`）——真源纳管（`true-source/`）按字节原样保留备查，⛔ 不代表其应入常规源控面。
