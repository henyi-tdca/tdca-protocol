# 通知机物理锚点场景审查（scene-phy-notification）
# 版本: SCENE-REVIEW-v1.0.0
# 关联: TDCA-REVIEW 通用审查标准 + FC-SPEC §3.1 scene_review
# 交付: 通知机规范包（层 3 场景化合）
# 模拟态标注: 本场景为模拟态示范；通知机硬件未投产部署，本场景为 SIL 模拟

## 一、通用审查（TDCA 标准）

- 六要素完整性 / 正和博弈验证 / NCA 存证合规

## 二、通知机特定审查（FC-SPEC §3.1）

| 审查 ID | 名称 | 标准 | 阈值 |
|---------|------|------|------|
| REV-PHY-001 | 品类认证有效 | TDCA-REG-NAMING-001 命名授权 | 100% |
| REV-PHY-002 | 国密合规 | SM2 签名 / SM4 加密不落盘 | 100% |
| REV-PHY-003 | 场景合规前置 | 政务/金融/医疗 → 等保（复用行业模板） | 100% |

## 三、接入审查链

- tdca-compliance-auditor（复用 PACK-001 审查链）+ 制度合伙人确认 + 人类签批
- 审查记录: REV-NM-001（CLOSED）+ REV-PHY-001~003 场景审查
