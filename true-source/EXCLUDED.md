# 自纳管集剔除件（S0-1／S0-2，2026-09-29）

# 备查＝归档 zip（deploy/archive/tdca-web-deploy-FROZEN.zip）原样保有，逐件 sha256 见该包 MANIFEST（本文件不重复抄值）。

## S0-1 运行产物 28 件（⛔ 不入源码树）

- gateway/tdca.db（容器内 SQLite，db 非卷挂载）
- tdca-cross-scene/.coverage
- tdca-cscp/.coverage
- tdca-d2-union/.coverage
- tdca-eios/.coverage
- tdca-microtax/.coverage
- tdca-ns-runtime/.coverage
- tdca-nsfl-compiler/.coverage
- tdca-toolchain/.coverage
- tdca-translator-market/.coverage
- tdca-utility-genie/.coverage
- tdca-workbuddy/.coverage
- tdca-notification-machine/simulator/out/.tdca/identity.tdca
- tdca-notification-machine/simulator/out/.tdca/state.json
- tdca-notification-machine/simulator/out/.tdca/config/call-rules.json
- tdca-notification-machine/simulator/out/.tdca/config/scene-binding.json
- tdca-notification-machine/simulator/out/.tdca/fact-chain/block-0000.json
- tdca-notification-machine/simulator/out/.tdca/fact-chain/block-0001.json
- tdca-notification-machine/simulator/out/.tdca/fact-chain/block-0002.json
- tdca-notification-machine/simulator/out/.tdca/fact-chain/block-0003.json
- tdca-notification-machine/simulator/out/.tdca/fact-chain/block-0004.json
- tdca-notification-machine/simulator/out/.tdca/nca-lite/auth/TDCA-NCA-LITE-C582D1D5-0003.json
- tdca-notification-machine/simulator/out/.tdca/nca-lite/fact/TDCA-NCA-LITE-C582D1D5-0002.json
- tdca-notification-machine/simulator/out/.tdca/nca-lite/fact/TDCA-NCA-LITE-C582D1D5-0004.json
- tdca-notification-machine/simulator/out/.tdca/nca-lite/fact/TDCA-NCA-LITE-C582D1D5-0005.json
- tdca-notification-machine/simulator/out/.tdca/nca-lite/service/TDCA-NCA-LITE-C582D1D5-0001.json
- tdca-notification-machine/simulator/out/.tdca/session-index/L0-state.nca
- tdca-notification-machine/simulator/out/.tdca/session-index/L1-active.json

## S0-2 force-add 撤销 6 件（⛔ 不符忽略规则不入仓）

- tdca-cscp/.tdca-nca/NCA-TDCA-REASONIX-20260811-001.yaml（存证件）
- tdca-d2-union/.tdca-nca/NCA-TDCA-REASONIX-20260811-001.yaml（存证件）
- tdca-frontend/dist/** 四件（构建产物；按裁定⑤由 frontend src 改正后重建，走独立 PR）

## 说明

- S0-2 之 dist 四件为 Dockerfile.web 所需——#307 已改为镜像内多阶段 npm ci＋build 由 src 直构（见该 PR），不依赖入库 dist。
- 剔除后跟踪集 432 件（466−28−6），sha256 见 MANIFEST.sha256。
