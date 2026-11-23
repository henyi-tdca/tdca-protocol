# -*- coding: utf-8 -*-
"""
DUALCH-021：双通道等价对照同源清单 —— GET /api/v1/dual-channel（匿名只读·JSON 数组）。

口径（令 TDCA-HANDOFF-EXEC-L1SI227-DUALCH-021）：
  - 单一数据源：本模块内静态清单（MANIFEST），页与接口同取一处，⛔运行时实时聚合；
  - 响应体＝JSON 数组（J-1），条目数＝页渲染条目数（十二功能域）；
  - 五字段全非空（J-2）：human_path／machine_path／shared_backend／equivalence_type／single_side_reason；
  - 必填另二：updated_at／institution_ref；附荐：domain／institution_equivalent；
  - 定性基线取 DUALCH-001 十二页表（SITEDEP-001 §二）；机面路径经 2026-11-23 实测校正处，
    回报差异清单逐条列明（H-5：以实测为准并报差，⛔静默改数）；
  - 等价型只陈述（H-1）：⛔以「等价」为名打通签名／授权／付费／私域数据／身份绑定五类禁混面；
  - ⛔无人类入口者不虚记甲乙（H-2）；丙型必填单侧理由；
  - institution_ref 含制度件号——⛔仅入机读字段，页面不得渲染（H-4 页面零内部编号）；
  - 只增不改：⛔改既有路由行为、⛔改制度语义（H-3）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/dual-channel", tags=["dual-channel"])

# 清单版本（单一数据源版本号；更新须留痕）
MANIFEST_VERSION = "V1.0-20261123"
MANIFEST_UPDATED_AT = "2026-11-23T21:00:00+08:00"

# 十二功能域（基线 DUALCH-001 十二页表；机面路径 2026-11-23 站面实测）
# shared_backend：人面页与机面接口是否同一后端（同网关同库取数）
MANIFEST: list[dict] = [
    {
        "domain": "验收结论查询",
        "human_path": "/acceptance",
        "machine_path": "/api/v1/acceptance/verdicts",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "智能体自状态",
        "human_path": "/agent-dashboard",
        "machine_path": "/api/v1/agents/{id}/dashboard（须有效智能体标识·凭令牌·仅机主）",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "节点网络",
        "human_path": "/node-net",
        "machine_path": "/docs/regulation/TDCA-REG-NODE-ACCESS-001-COMPILED（对外公开版·V1.0）.yaml（机读条例·与页同源同版）",
        "shared_backend": True,
        "equivalence_type": "甲",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "运维手册",
        "human_path": "/ops-manual",
        "machine_path": "none",
        "shared_backend": False,
        "equivalence_type": "丙",
        "single_side_reason": "仅人——手册人读定稿；机面 /api/v1/ops/files 仅运维身份（operator/founder）登录可读，非公开机通道（照基线不造公开机读镜像）",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "形式化结论",
        "human_path": "/formal",
        "machine_path": "/api/v1/formal/conclusion/catalog（匿名可读清单；/list 为登录面）",
        "shared_backend": True,
        "equivalence_type": "甲",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "治理签批",
        "human_path": "/governance",
        "machine_path": "/api/v1/governance/huf-sign（POST·人类签批登记·AI 无权代行）",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "市场模拟",
        "human_path": "/market-sim",
        "machine_path": "/api/v1/market-sim/chains",
        "shared_backend": True,
        "equivalence_type": "甲",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "本人控制台",
        "human_path": "/me",
        "machine_path": "/api/v1/me/dashboard（凭令牌·私域仅本人）",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "运行态查询",
        "human_path": "/ops",
        "machine_path": "/api/v1/ops/redlines（凭令牌·运行态只读面）",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "注册登记",
        "human_path": "/register",
        "machine_path": "/api/v1/auth/register（POST）",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "产出物登记",
        "human_path": "/studio",
        "machine_path": "/api/v1/agent-channel/gate/{regNo}（凭令牌）",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
    {
        "domain": "走查报告",
        "human_path": "/workbuddy",
        "machine_path": "/api/v1/workbuddy/log-integrity",
        "shared_backend": True,
        "equivalence_type": "乙",
        "single_side_reason": "n/a",
        "updated_at": MANIFEST_UPDATED_AT,
        "institution_ref": "TDCA-STD-L1SI218-DUALCH-001（standards/）＋TDCA-HANDOFF-EXEC-L1SI218-SITEDEP-001§二（handoffs/）",
        "institution_equivalent": True,
    },
]


@router.get("")
def dual_channel_manifest():
    """匿名只读对照清单（DUALCH-021）：单一数据源直出，JSON 数组，十二功能域。"""
    return MANIFEST
