# 入仓来源说明 · DEPS4 四工程（ARTIFACT-DEPS4-001 及修正案 -001-001）

> 本文件为入仓 provenance 说明（TDCA-HANDOFF-EXEC-ARTIFACT-DEPS4-001 / TDCA-AMEND-...-001-001），非制度件。覆盖四个工程：`tdca-flow-orchestrator/`、`tdca-fos/`、`tdca-toolchain/`、`tdca-utility-genie/`。

## 一、来源账

- 来源包：`TDCA-ARTIFACT-PAYLOAD-deps4-20261010.tar.gz`（277,464 B）
- 包 sha256：`7ce9aaf30f5fae8dfb8ca38f54703aeafe56509e68a8ab6628a085aea2b582e3`（取件时核验一致）
- 权威逐件账：`TDCA-ARTIFACT-PAYLOAD-deps4-20261010-MANIFEST.sha256`，**216 行**
- 入仓 **215 件**，逐件已对清单复核（哈希＋字节）一致；**排除 1 件**（见下）

## 二、排除声明（1 件，创始人裁定）

| 件 | 处置 | 理由 |
|---|---|---|
| `tdca-fos/deploy/docker-compose.yml` | **不入仓** | 源件含明文弱口令（`NEO4J_AUTH=neo4j/tdca2026` L25／`POSTGRES_PASSWORD=tdca2026` L45／`PG_URI=postgresql://tdca:tdca2026@…` L99）；主仓系公开库，「凭据不入库」系主仓既有口径（既有 `deploy/docker-compose.yml` 无明文口令、`deploy/.env` 归创始人自管不入库） |

- 包不重打、不退回；其余 215 件照原样入仓（搬不造，内容与清单哈希一致）。
- 该排除件如后续需要，由创始人自管或待脱敏后另案。

## 三、运行时依赖互指（T-2 注记）

**四工程系 `tdca-sbx-ops`／`tdca-ns-ops` 之运行时依赖**，落仓根即为此定位：

- `tdca-sbx-ops/backend/app/flow_adapter.py`、`phase_adapter.py` 以 `Path(__file__).resolve().parents[4] / "tdca-flow-orchestrator" / "src"` 硬路径加载编排器；缺该工程时 flow／phase 路由与对应测试不可用。
- `tdca-ns-ops/backend/app/integration/flow_adapter.py`、`sandbox_real.py` 同构加载；缺该工程时整个 ns 测试套件在 conftest 导入期被阻断。
- `tdca-utility-genie`：sbx 侧 `utility_genie_adapter.py`（ERI/CCI 评分语义源）。
- `tdca-toolchain`：配置权令牌（TDCA-CRT-*）生成／验证链工具（sbx/ns NCA 与多签流程配套）。
- `tdca-fos`：NCA 体系制度件与部署参考（其中 `deploy/docker-compose.yml` 已按 §二 排除，其余 deploy 参考件 Dockerfile×2、PRODUCTION.md 入仓）。

## 四、敏感面（入仓前复扫）与脱敏更正（DEPS4-MERGE-001 追加）

- **已脱敏（2026-10-10，创始人令 TDCA-HANDOFF-EXEC-ARTIFACT-DEPS4-MERGE-001）**：
  - `tdca-fos/TDCA-NCA-SYSTEM-SCHEMA-001-NCA体系制度机读规范.yaml` 4 处路径值改占位符（`%APPDATA%…`→`<APPDATA>…`、`Desktop/TDCA归档文件夹…`→`<Desktop>/TDCA归档文件夹…`、两处含用户名之本机绝对路径→`<工作区>/.tdca-nca/` 与 `<Desktop>/TDCA-MEMO-006-Workspace/.tdca-nca/`）。**该件因此偏离包清单哈希**，理由：脱敏（去用户名与用户目录前缀），偏离仅此 4 处路径值，其余一字未动。
  - `tdca-fos/TDCA-NCA-LIFECYCLE-STANDARD-001_NCA登记存证归档检索审查规范.md` 逐行自查：所指行已是占位/相对形态（`<Desktop>…`、`global-workspace…`），无用户名残留，**未改、不偏离清单**。
  - 自查另发现 `tdca-fos/TDCA-NCA-SYSTEM-STANDARD-001-NCA体系制度规范.md` L17 含工作区相对路径片段（`开发会话文件/.tdca-nca/`，无用户名与用户目录前缀）；因脱敏令限定两件，**未代改**，报创始人备裁。
- 本机路径串（脱敏前原状，既有内容、非本次引入）：
  - `tdca-fos/TDCA-NCA-SYSTEM-SCHEMA-001-NCA体系制度机读规范.yaml` L36/L40：`C:/Users/22850/Desktop/…`（含用户名 22850）
  - `tdca-fos/TDCA-NCA-SYSTEM-STANDARD-001-NCA体系制度规范.md` L17：`开发会话文件/.tdca-nca/`
- tdca-toolchain 的 TOKEN 命中均为配置权令牌示例／测试样例／环境变量读取／子命令误报，非凭据。
- 排除件之外的凭据形态：0；外部 IP：0；人名：0。

## 五、硬约束确认

不改任何被搬运工程内容；不改 `tdca-sbx-ops`／`tdca-ns-ops` 既有代码（本轮零改码）；不改在册件正文；不动 host 白名单件（`deploy/.env`、`freeze-pair-1009.yml`、`docker-compose.yml`＋bak、nginx、`web.conf`、`portal/index.html`、`install.sh`——本交付之四工程均落仓根新目录，与上述路径零重叠）；不部署·不上云·不合并不推送。
