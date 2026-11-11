# TDCA 通知机（tdca-notification-machine）

计量映射引擎（CALL-RULES V1.2 复用）＋ MRCR 管理器 ＋ SIL 模拟器。规格见 `tdca-firmware-spec.md` 与 `tdca-firmware-spec-V1.1-REV.md`，修复记录见 `REV-NM-001.md`。

## 测试通过率两口径（L1SI211-EXTERNAL-FIX-001 A，2026-11-12）

本套件测试依赖全部在公开树在册内容（`true-source/tdca-web/tdca-call-rules/engine` 之 `call_rules_engine`、`dual/engine` 之 `mrcr_manager`/`dual_protocol_compiler`，`conftest.py` 已按工作区相对位自携 path），公开面可运行。唯二例外：

| 口径 | 范围 | 例外 |
|------|------|------|
| **公开面通过率** | 全部 42 条用例 | 唯 `test_nm_mrcr.py` 之 `test_dual_isomorphism`／`test_dual_minimal_compound` 依赖运行态符号链接 `tdca-dual-protocol-package/tdca-public`（内部运行态件，非公开树跟踪内容）——链接未建时该 2 条 skip 并注原因（如实标待触发 ⛔ 假绿），其余 40 条照常 |
| **内部门禁通过率** | 全部 42 条用例含上述 2 条 | 内部全量环境（链接在架）42 条全跑 |

- 引用通过率数字时须注明口径；两口径 ⛔ 只写其一。
- CI 门禁：`gate-notification-machine.yml`（push／PR 触发）。
