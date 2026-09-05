# TDCA-NM-L7-001 · 通知机接入恢复（L-7）交付报告

> 交付编号: TDCA-NM-L7-001 | 日期: 2026-08-12
> 任务: ECOCOG 遗留 L-7 —— 通知机接入 TDCA 系统恢复执行（TDCA-FC-20260811-004）
> 承接: 生态认知项目遗留 L-7 任务（内部交接，2026-08）
> 基座: 通知机协议包 V1.0（FC-SPEC V1.2 FROZEN + 引擎 V1.0.0 + SIL 模拟器 V1.0.0）
> 状态: ✅ 层 3 场景化合补齐完成，验收 6 项全绿，**人类签批（HUMAN-FOUNDER-001，2026-09-05）**
> 发布注记（2026-09-05 公开版）：SIL 过渡态——实物生产部署前以软件在环（SIL）承载流程验证，流程不废（ID92 SIMULATED）——不宣称实物可用

---

## 一、执行摘要

ECOCOG 体系冻结后（613 测试绿），L-7 通知机接入恢复。前置核验确认通知机协议包 V1.0
在位（FC-SPEC V1.2 FROZEN / 引擎 10 测试 / SIL 模拟器 6 测试），唯一缺口为
**FC-SPEC §九 验收项 3（层 3 场景化合）**——`scene-phy-notification` 场景制度缺失 +
NM-* 四角色 MRCR 注册缺失 + 引擎未接入 MRCR 权限校验。

本次补齐该缺口并完成验收闭环。

## 二、交付物清单

| # | 交付物 | 位置 | 说明 |
|---|--------|------|------|
| 1 | 场景宪法 | `scenes/scene-phy-notification/scene-constitution.md` | 物理锚点场景宪法（服从 TDCA-CONST v3.1.2，ID29 信任锚） |
| 2 | 场景约束矩阵 | `scenes/scene-phy-notification/scene-constraints.md` | 六要素扩展 + CON-001~004 + MRCR 四角色配置权边界 |
| 3 | 场景负空间 | `scenes/scene-phy-notification/scene-nsfl.md` | SCENE-PHY-001/002/003（物理/制度负空间区分，澄清 C） |
| 4 | 场景术语 | `scenes/scene-phy-notification/scene-terms.md` | 术语表（TDID/PUF/NCA-Lite/MRCR 等） |
| 5 | 场景审查 | `scenes/scene-phy-notification/scene-review.md` | REV-PHY-001~003 |
| 6 | 场景定价 | `scenes/scene-phy-notification/scene-pricing.md` | CALL-RULES 计量映射 + MOU 归零 + 定价快照 |
| 7 | MRCR 扩展 | `engine/nm_mrcr.py` | NmMrcrManager（NM-* 四角色，子类扩展不改 DUAL 基座，BV-3） |
| 8 | 引擎 MRCR 接入 | `engine/notification_machine_engine.py` | execute 前置权限检查（fail-closed） |
| 9 | 测试套件 | `tests/test_nm_mrcr.py` | 13 项新测试（场景化合 + MRCR + 引擎接入） |

## 三、验收映射（FC-SPEC §九 六项核验）

| # | 验收项 | 标准 | 核验结果 |
|---|--------|------|---------|
| 1 | .tdca 固件元数据格式 | 与 PACK-001 SI/NCA 模板同构，SE 签名完整性可验证 | ✅ 模板 ×8 在位 + firmware-spec V1.0 |
| 2 | 芯片端轻量 NCA | 8 字段精简版 + 与 TCN 全量 NCA 链式关联 | ✅ NCA-Lite 8 字段（nca_lite.version="1.0"）+ payload_ref 链式 |
| 3 | 场景化合 | 物理锚点场景模板 + MRCR 角色注册（复用 DUAL 引擎测试） | ✅ **本次补齐**：scene-phy-notification 六文件 + NM-* 四角色 MRCR |
| 4 | 商业计量 | 调用类型映射 + MOU 归零 + L3 税收（复用 CALL-RULES 引擎测试全绿） | ✅ 日抛/化合/服务映射 + ID79 归零 + 调度税/版税 |
| 5 | 制度存证 | NCA-010+ 序列 + 审查闭环 + 人类签批 | ✅ NCA-010/011/012 Signed（2026-08-11）+ REV-NM-001 CLOSED |
| 6 | 负空间 | SCENE-PHY-001~003 熔断路径验证 | ✅ 物理（001/003 不可逆）vs 制度（002 可逆）fuse_info 区分 |

## 四、验证结果

- **DUAL 编译器**: 同构校验 PASS + 最小化合三条件（不可拆分/涌现价值/非线性）全 PASS
- **通知机全量测试**: **29 passed**（原引擎 10 + 新增 13 + SIL 模拟器 6）
  - 新增覆盖：场景六文件齐全 / DUAL 同构 / 最小化合三条件 / NM 四角色注册 /
    权限授予 / 未注册 fail-closed / 禁止项阻断 / HW_ACTION_MAP 完整 /
    引擎 MRCR APPROVED / 引擎 MRCR REJECTED（拒绝留痕 + 状态不推进）/
    NODE_AUTH 登记豁免 / 角色隔离 / 引擎真实 DUAL 场景化合端到端
- **ECOCOG 全量回归**: 613 全绿未受影响（microtax 183 + utility-genie 78 + toolchain 109
  + nsfl-compiler 121 + ns-runtime 111 + call-rules 11）+ DUAL 18 绿

## 五、纪律核验

- **BV-3**: FROZEN 基座只读——MRCR 扩展采用子类继承（NmMrcrManager），未改动 DUAL 基座文件
- **F-4/HUF**: 升级权人类；本交付待人类签批后生效
- **MOU 不可降（ID79）**: 计量分支归零语义保持；MRCR 拒绝独立 REJECTED verdict（不混入 ZEROED）
- **ID92 模拟态**: 全链路 simulated 标注（MOU 锚定 D-011）；真实 DCEP 后转硬数据
- **负空间区分（澄清 C）**: SCENE-PHY-001/003 物理不可逆 vs 002 制度可逆
- **术语（G-1）**: 仅注册表 V1.1

## 六、遗留与后续

- 层 4 商业计量已在协议包 V1.0 实现；真实税率待 D-010 校准（L-1）
- 层 1 硬件身份为 mock（E-HW-2 未到位），硬件到位后仅需替换 NMDeviceDriver
- 数字人民币硬件钱包（M3 里程碑）待 DCEP 接入（L-2）

## 七、签批

| 角色 | 签署 | 状态 |
|------|------|------|
| 协议工程师（M） | TDCA 制度层 | ✅ 层 3 场景化合补齐 + 验收闭环 |
| 制度设计师（H） | TDCA-FOUNDER-001 | ✅ **人类签批通过（2026-08-12，H ACCEPT）** |

> 本交付为 ECOCOG 遗留 L-7 通知机接入恢复；**L-7 已关闭（人类签批 2026-08-12）**，
> 体系确认书遗留项 7 → 6。
