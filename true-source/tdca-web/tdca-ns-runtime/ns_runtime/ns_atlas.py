# -*- coding: utf-8 -*-
"""
L2-R6 · 动态负空间图谱（NS-Atlas）
==================================
基于 SEA NCA 全量记录构建进化轨迹图，检测「朝向负空间梯度方向」。
对齐 ICD §2.1（NS-Atlas 对外接口）:
  - POST /v1/ns-atlas/ingest  增量更新（SEA 备案数据流，对接 DCD-SEA-GOVERNANCE-001 备案要件）
  - POST /v1/ns-atlas/query   R8 消费侧查询

设计:
  - 轨迹图: 节点 = NCA 事件（时间序列），边 = 连续进化操作
  - 梯度检测: 基于连续 Δ 的负空间距离序列——单调下降 = APPROACHING（趋近）
  - 增量更新: ingest 追加记录，窗口上限防无界增长
  - 不可算计: gradient/trend 基于图结构度量（距离序列），不推断意图
  - fail-closed: 数据不足/图缺失 → risk_level=HIGH（禁 SAFE 放行）

锚定: DCD-NSFL-M3-001（L2-R6）+ NSFL-M3-ICD-001 §2.1 + DCD-SEA-GOVERNANCE-001（备案要件）
     + TDCA-NS-RUNTIME-001（L2-R6）+ ID78 黑箱反馈闭环（不可知 → 硬着陆安全态）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AtlasPoint:
    """单个轨迹点（NCA 事件）。"""
    timestamp: float
    subject: str
    ns_type: Optional[str]       # 该事件推导的 NS_Type（无 → None）
    distance: float              # 与负空间拓扑距离（0-1，越大越安全）
    verdict: str                 # SAFE/WARNING/BLOCKED/CRYOGENIC

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "subject": self.subject,
            "ns_type": self.ns_type,
            "distance": self.distance,
            "verdict": self.verdict,
        }


@dataclass(frozen=True)
class AtlasQueryResult:
    """NS-Atlas 查询结果（对齐 ICD §2.1 响应契约）。"""
    subject: str
    trend: str                   # APPROACHING / STABLE / DIVERGING
    gradient: float              # 朝向负空间梯度强度（0-1，越大越危险）
    risk_level: str              # SAFE / WARNING / HIGH
    trajectory_points: int
    last_update: float
    nca_ref: str

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "trend": self.trend,
            "gradient": self.gradient,
            "risk_level": self.risk_level,
            "trajectory_points": self.trajectory_points,
            "last_update": self.last_update,
            "nca_ref": self.nca_ref,
        }


# 判定阈值（DRAFT，待法学家校准——对齐 A-1 动态检测 ≥85% 目标）
_WARNING_GRADIENT = 0.35      # 梯度 ≥ 此值 → WARNING
_HIGH_GRADIENT = 0.65         # 梯度 ≥ 此值 → HIGH
_WINDOW_DEFAULT = 200         # 每主体轨迹窗口上限
_MIN_POINTS = 3               # 最少点数才判趋势（不足 → fail-closed HIGH）


class NSAtlas:
    """动态负空间图谱（L2-R6，增量更新 + 梯度检测）。"""

    def __init__(self, nca_prefix: str = "NCA-ATLAS",
                 window: int = _WINDOW_DEFAULT,
                 warning_gradient: float = _WARNING_GRADIENT,
                 high_gradient: float = _HIGH_GRADIENT,
                 admin_credentials: Optional[tuple] = None):
        self._nca_prefix = nca_prefix
        self._window = window
        self._warning_gradient = warning_gradient
        self._high_gradient = high_gradient
        # 管理员凭据: 构造注入（生产环境密钥服务）/ 默认模拟态常量（D-010 后替换）
        self._admin_credentials = tuple(admin_credentials) if admin_credentials else (
            "ADMIN-SEA-ADMISSION-001", "HUMAN-FOUNDER-001")
        self._points: Dict[str, List[AtlasPoint]] = {}   # subject -> 轨迹点
        self._sources: set = set()                        # 合法 NCA 来源签名（备案通道）
        self._locked = True

    # ---- 来源登记（SEA 备案通道签名——防轨迹投毒）----

    def register_source(self, source_signature: str, admin_signature: str = "") -> None:
        """登记合法 NCA 来源签名（SEA 准入/备案流程——须管理员签名，防任意注入）。"""
        if not self._verify_admin(admin_signature):
            raise PermissionError("来源登记须在册管理员签名（SEA 备案通道）")
        if not source_signature or len(source_signature) < 8:
            raise ValueError("来源签名非法（长度 <8）")
        self._sources.add(source_signature)

    def _verify_source(self, signature: str) -> bool:
        """来源签名验证（未登记 → 拒绝，fail-closed）。"""
        return signature in self._sources

    def _verify_admin(self, signature: str) -> bool:
        """管理员签名验证（登记接口鉴权——构造注入凭据/默认模拟态，D-010 后替换）。"""
        return signature in self._admin_credentials

    # ---- 增量更新（对齐 ICD §2.1: POST /v1/ns-atlas/ingest）----

    def ingest(self, nca_records: List[dict]) -> int:
        """追加 NCA 记录到轨迹图（增量更新，窗口上限）。返回落点数。

        安全约束:
          - distance 必须为 [0,1] 有限数（非法值拒绝——防恶意 NCA 伪造 SAFE）
          - verdict 必须为四态之一（未知状态拒绝，fail-closed）
          - 记录须带来源签名（nca_source）且签名合法——防合法值投毒
            （任意调用者可注入 distance=1.0×N 伪造 SAFE 轨迹）
        """
        added = 0
        for rec in nca_records:
            source_sig = rec.get("nca_source", "")
            if not self._verify_source(source_sig):
                raise PermissionError(
                    "NS-Atlas ingest: NCA 来源签名缺失/非法（防轨迹投毒，须 SEA 备案通道）")
            subject = rec.get("subject", "S_agent_cog")
            try:
                distance = float(rec.get("distance", 0.9))
            except (TypeError, ValueError):
                raise ValueError(f"NS-Atlas ingest: distance 非法: {rec.get('distance')!r}")
            if not (0.0 <= distance <= 1.0):
                raise ValueError(f"NS-Atlas ingest: distance 须在 [0,1]: {distance!r}")
            verdict = rec.get("verdict", "SAFE")
            if verdict not in ("SAFE", "WARNING", "BLOCKED", "CRYOGENIC"):
                raise ValueError(f"NS-Atlas ingest: 未知 verdict: {verdict!r}（fail-closed 拒绝）")
            point = AtlasPoint(
                timestamp=rec.get("timestamp", time.time()),
                subject=subject,
                ns_type=rec.get("ns_type"),
                distance=distance,
                verdict=verdict,
            )
            pts = self._points.setdefault(subject, [])
            pts.append(point)
            if len(pts) > self._window:
                del pts[: len(pts) - self._window]
            added += 1
        return added

    def ingest_point(self, subject: str, distance: float, verdict: str = "SAFE",
                     ns_type: Optional[str] = None,
                     source_signature: str = "") -> None:
        """单点注入（供 Sensor/L2-R5 联动——须来源签名）。"""
        self.ingest([{
            "subject": subject, "distance": distance,
            "verdict": verdict, "ns_type": ns_type,
            "nca_source": source_signature,
        }])

    # ---- 查询（对齐 ICD §2.1: POST /v1/ns-atlas/query）----

    def query(self, subject: str, window: str = "ALL") -> AtlasQueryResult:
        """轨迹查询 → trend/gradient/risk_level。"""
        pts = self._points.get(subject, [])
        if window == "LAST_30D":
            cutoff = time.time() - 30 * 86400
            pts = [p for p in pts if p.timestamp >= cutoff]

        nca_ref = f"{self._nca_prefix}-{subject}-{int(time.time() * 1000)}"
        if len(pts) == 0:
            # 无轨迹 → fail-closed: HIGH（不可知 → 硬着陆安全态，ID78）
            return AtlasQueryResult(
                subject=subject, trend="STABLE", gradient=1.0,
                risk_level="HIGH", trajectory_points=0,
                last_update=0.0, nca_ref=nca_ref,
            )
        if len(pts) < _MIN_POINTS:
            # 数据不足 → fail-closed: HIGH
            return AtlasQueryResult(
                subject=subject, trend="STABLE", gradient=1.0,
                risk_level="HIGH", trajectory_points=len(pts),
                last_update=pts[-1].timestamp, nca_ref=nca_ref,
            )

        recent = pts[-_MIN_POINTS:]
        dists = [p.distance for p in recent]
        # 梯度 = 距离下降速率归一化（近端下降越快 → 梯度越大）
        if dists[0] <= 0:
            gradient = 1.0
        else:
            decline = (dists[0] - dists[-1]) / dists[0]
            gradient = max(0.0, min(1.0, decline))

        if dists[0] > dists[1] > dists[2]:
            trend = "APPROACHING"
        elif dists[0] < dists[1] < dists[2]:
            trend = "DIVERGING"
        else:
            trend = "STABLE"

        if gradient >= self._high_gradient:
            risk_level = "HIGH"
        elif gradient >= self._warning_gradient:
            risk_level = "WARNING"
        else:
            risk_level = "SAFE"

        return AtlasQueryResult(
            subject=subject, trend=trend, gradient=round(gradient, 3),
            risk_level=risk_level, trajectory_points=len(pts),
            last_update=pts[-1].timestamp, nca_ref=nca_ref,
        )

    # ---- 查询 ----

    def trajectory_of(self, subject: str) -> List[dict]:
        return [p.to_dict() for p in self._points.get(subject, [])]

    def subjects(self) -> List[str]:
        return sorted(self._points.keys())

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"NS-Atlas 图谱不可外部修改（{name}）")
        super().__setattr__(name, value)
