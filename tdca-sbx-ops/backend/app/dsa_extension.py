# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，DSA 扩展组）
# 目标函数:     M3-6 DSA 状态机扩展适配层——SBX-SUSPENDED/SBX-BANNED 扩展字段先行 + 熔断落地
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-8 + SV-9 + 接口熵=0（ID82）
#               + TDCA-PRINCIPLE-DSA-001（SBX-SUSPENDED 0x22 / SBX-BANNED 0x2F + 回退三档）
#               + 待 DCD 边界（完整状态机替换须 DCD 批准，本子任务扩展字段先行）
# 先验分布:     TDCA-PRINCIPLE-DSA-001 + S0-M3 交接（SV-9/M3-6）+ M3-1 nsops_adapter（NS-IF-002）
#               + M3-3 phase_adapter（PM-IF-001）
# 配置权边界:   L2 层；DSA-001 只读参考（待 DCD）
# 预期分配:     DSA 状态扩展（suspend/ban/resume + 熔断落地）；失败=契约破坏显式失败
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-6 DSA 状态机扩展适配层（SBX-SUSPENDED/SBX-BANNED 扩展字段先行）。

制度锚定: FC-SBX-OPS-001 / SV-9 | SPDX-License-Identifier: TDCA-Internal

DSA 状态扩展（TDCA-PRINCIPLE-DSA-001，待 DCD 冻结）:
  - SBX-SUSPENDED（0x22）: 沙盒内暂停（熔断回退，等待整改/人类裁决）
  - SBX-BANNED（0x2F）: 永久休眠（法律负空间，配置权价格强制归零）

熔断回退三档（DSA-001 §3.4）:
  - 轻微越界 → 限期重整（可 resume 返回）
  - 中度越界 → 深度整改需人类裁决
  - 严重越界（法律负空间）→ SBX-BANNED 永久休眠（不可逆）

待 DCD 边界: 完整状态机替换（Phase 枚举扩展）须 DCD 批准；本子任务实现
dsa_status 扩展字段 + 熔断标记先行（SV-9 语义），DCD 批准后完整落地。
"""

from __future__ import annotations

import time
from typing import Any, Dict

from . import nca_logger
from .models import Phase

DSA_SUSPENDED = "SBX-SUSPENDED"  # 0x22
DSA_BANNED = "SBX-BANNED"  # 0x2F
DSA_ACTIVE = "SBX-ACTIVE"  # 0x21（正常态）

# 接口契约编号（I-7 修复：DSA-001 为待 DCD 制度参考稿，非接口契约；独立登记 DSA-EXT-001）
DSA_EXT_CONTRACT = "DSA-EXT-001"

# 人类签批身份格式（#9：统一 did:tdca: 前缀，对齐 M1/M2 签批）
HUMAN_SIGNATORY_PREFIX = "did:tdca:"

SV8_LATENCY_MS = 1000  # SV-8: 联动延迟 < 1s
SV9_LATENCY_MS = 100  # SV-9: NS-OPS 熔断触发后 100ms 内进入 SUSPENDED

# 熔断回退档位（DSA-001 §3.4 三档）
BREAK_LEVEL_MINOR = "MINOR"  # 轻微 → 限期重整
BREAK_LEVEL_MODERATE = "MODERATE"  # 中度 → 深度整改需人类裁决
BREAK_LEVEL_SEVERE = "SEVERE"  # 严重（法律负空间）→ SBX-BANNED


class DsaLinkError(ConnectionError):
    """DSA 状态扩展联动接口错误（fail-closed 统一异常）。

    非法状态迁移/契约破坏时抛出，禁止静默降级。
    """


class DsaExtension:
    """SBX-OPS → DSA 状态机扩展适配层（SBX-SUSPENDED/SBX-BANNED 扩展字段先行）。

    六要素声明:
    目标函数: DSA 状态扩展——熔断落地（SV-9）+ 回退路径（DSA-001 三档）
    约束矩阵: 输入——sandbox_id/触发原因/break_level；输出——dsa_status 扩展字段；
              禁止——终态（Closed/Exit）再迁移、SBX-BANNED 恢复（永久休眠不可逆）、
              非法 break_level
    先验分布: TDCA-PRINCIPLE-DSA-001（回退三档）+ SV-9（100ms 熔断落地）
    配置权边界: L2；DSA-001 只读参考（待 DCD）
    预期分配: 返回 {contract, dsa_status, break_level, latency_ms, nca_refs}
              失败=DsaLinkError/ValueError
    审计轨迹: 每契约调用生成 SBX-OPS 侧 NCA（SV-10）+ 回写沙盒扩展字段
    """

    # ---------------- 内部 ----------------#

    @staticmethod
    def _fail_nca(contract: str, error: Exception, nsfl: bool = False) -> None:
        """fail-closed 异常路径 NCA 存证（#8：区分负空间 FUSE 与技术/参数失败 FAIL）。"""
        try:
            nca = nca_logger.build_nca(
                operation=f"DSA_FAIL_CLOSED_{contract.replace('-', '_')}",
                operator="system",
                pre_state="LINK",
                post_state="ERROR",
                audit_trail=f"{contract} fail-closed: {type(error).__name__}: {error}",
                negative_space_check="FUSE" if nsfl else "FAIL",
            )
            nca_logger.save_nca(nca)
        except Exception:  # noqa: BLE001 - 存证失败不掩盖原始异常
            pass

    def _nca(self, operation: str, pre: str, post: str, audit: str) -> str:
        """SBX 侧 NCA 存证（SV-7，返回 nca_id）。"""
        nca = nca_logger.build_nca(
            operation=operation, operator="system",
            pre_state=pre, post_state=post, audit_trail=audit,
        )
        return nca_logger.save_nca(nca)

    @staticmethod
    def _apply_dsa_status(sbx: Any, status: str, break_level: str,
                          reason: str, ts: str) -> None:
        """回写沙盒 dsa_status 扩展字段 + 熔断标记（SV-9 语义，不动 Phase 枚举）。

        #1/#2（tdca-pricer/M4-3）：BANNED/SUSPENDED 时配置权价格强制归零 + S-Right 失效
        （DSA-001 §3.4，对齐接口规范 REV-1 _clearActiveConfigRights 防御语义）。
        """
        from . import store as _store
        sbx.dsa_status = status
        sbx.dsa_break_level = break_level
        sbx.dsa_reason = reason
        sbx.dsa_updated_at = ts
        if status in (DSA_BANNED, DSA_SUSPENDED):
            # 配置权价格强制归零（M4-3：DSA-001 §3.4 强制归零义务落地）
            sbx.config_right_price = 0.0
            # S-Right 失效（释放配置权调用资格）
            for sr in getattr(sbx, "s_rights", []) or []:
                if isinstance(sr, dict):
                    sr["frozen"] = True
                    sr["price"] = 0.0
            # 当前持价重置
            sbx.pucr = dict(getattr(sbx, "pucr", None) or {}) | {"price_cleared": True}
        if status == DSA_BANNED:
            sbx.dsa_banned_at = ts
        _store.save_sandbox(sbx)

    # ---------------- 熔断落地（SV-9） ----------------

    def suspend(self, sandbox_id: str, reason: str,
                break_level: str = BREAK_LEVEL_MINOR) -> Dict[str, Any]:
        """DSA 熔断落地：沙盒进入 SBX-SUSPENDED（SV-9，100ms 内）。

        六要素声明:
        目标函数: 熔断触发后沙盒 100ms 内进入 SUSPENDED（SV-9 扩展字段先行）
        约束矩阵: 输入——sandbox_id/reason/break_level；输出——dsa_status；
                  禁止——终态沙盒迁移、非法 break_level
        先验分布: DSA-001 §3.4（回退路径）+ SV-9（100ms 实时性）
        配置权边界: L2；DSA-001 只读参考
        预期分配: 返回 {contract, dsa_status, break_level, latency_ms, nca_refs}
                  失败=ValueError（非法参数）/DsaLinkError
        审计轨迹: DSA_SUSPEND NCA（SV-7）+ 回写沙盒扩展字段
        """
        t0 = time.monotonic()
        from . import store as _store
        sbx = _store.load_sandbox(sandbox_id)
        if sbx is None:
            e = ValueError(f"[DSA] 沙盒不存在: {sandbox_id}")
            self._fail_nca("DSA-SUSPEND", e)
            raise e
        if sbx.phase in (Phase.EXIT, Phase.CLOSED):
            e = ValueError(f"[DSA] 终态沙盒（{sbx.phase.value}）不可迁移 SUSPENDED")
            self._fail_nca("DSA-SUSPEND", e)
            raise e
        # I-1 修复：BANNED 不可被 suspend 覆盖（ID86 法律负空间绝对熔断，永久休眠不可逆）
        if getattr(sbx, "dsa_status", None) == DSA_BANNED:
            e = ValueError(f"[DSA] BANNED 永久休眠不可覆盖为 SUSPENDED（ID86）: {sandbox_id}")
            self._fail_nca("DSA-SUSPEND", e)
            raise e
        if break_level not in (BREAK_LEVEL_MINOR, BREAK_LEVEL_MODERATE, BREAK_LEVEL_SEVERE):
            e = ValueError(f"[DSA] break_level 非法: {break_level}")
            self._fail_nca("DSA-SUSPEND", e)
            raise e
        # I-2 修复：SEVERE（法律负空间）必须走 ban 端点（suspend 拒绝 SEVERE，防绕过 BANNED）
        if break_level == BREAK_LEVEL_SEVERE:
            e = ValueError(
                "[DSA] SEVERE（法律负空间）必须经 ban 端点 → SBX-BANNED 永久休眠（DSA-001 §3.4/ID86）")
            self._fail_nca("DSA-SUSPEND", e)
            raise e
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            self._apply_dsa_status(sbx, DSA_SUSPENDED, break_level, reason, ts)
            latency_ms = int((time.monotonic() - t0) * 1000)
        except Exception as e:  # noqa: BLE001
            self._fail_nca("DSA-SUSPEND", e)
            raise DsaLinkError(f"[DSA] SUSPENDED 落地失败: {e}") from e
        if latency_ms > SV9_LATENCY_MS:
            # SV-9: 100ms 实时性——超限记录（NCA 可观测），不阻断（扩展字段先行语义）
            audit = f"SV-9 超时警告 {latency_ms}ms > {SV9_LATENCY_MS}ms"
        else:
            audit = f"SV-9 达标 {latency_ms}ms <= {SV9_LATENCY_MS}ms"
        nca_id = self._nca("DSA_SUSPEND", sbx.phase.value, DSA_SUSPENDED,
                           f"{audit}; {sandbox_id} break_level={break_level} reason={reason}")
        return {
            "contract": DSA_EXT_CONTRACT,  # I-7 修复：独立接口契约编号
            "operation": "suspend",
            "sandbox_id": sandbox_id,
            "dsa_status": DSA_SUSPENDED,
            "break_level": break_level,
            "latency_ms": latency_ms,
            "sv9_compliant": latency_ms <= SV9_LATENCY_MS,
            "nca_refs": {"sbx": nca_id},
        }

    # ---------------- 永久休眠（严重越界） ----------------

    def ban(self, sandbox_id: str, reason: str, human_signatory: str = "") -> Dict[str, Any]:
        """DSA 永久休眠：沙盒进入 SBX-BANNED（法律负空间，ID86 不可逆）。

        六要素声明:
        目标函数: 严重越界（法律负空间）→ SBX-BANNED 永久休眠（DSA-001 §3.4）
        约束矩阵: 输入——sandbox_id/reason/human_signatory（I-5：L0 最重裁决须人类签批）；
                  输出——dsa_status=BANNED；
                  禁止——BANNED 恢复（永久休眠不可逆）、终态沙盒迁移、无人类签批执行（I-5）
        先验分布: DSA-001 §3.4（严重越界→永久休眠）+ ID86（法律负空间绝对熔断）
        配置权边界: L2；DSA-001 只读参考
        预期分配: 返回 {contract, dsa_status, nca_refs}；失败=ValueError/DsaLinkError
        审计轨迹: DSA_BAN NCA（含 human_signature，SV-7）+ 回写沙盒扩展字段（不可逆）
        """
        t0 = time.monotonic()
        if not human_signatory:
            e = ValueError("[DSA] 永久休眠（L0 法律负空间）须人类裁决签批（I-5）")
            self._fail_nca("DSA-BAN", e)
            raise e
        # #9：签批身份格式统一（did:tdca: 前缀，对齐 M1/M2 签批）
        if not human_signatory.startswith(HUMAN_SIGNATORY_PREFIX):
            e = ValueError(f"[DSA] human_signatory 须 {HUMAN_SIGNATORY_PREFIX} 前缀: {human_signatory}")
            self._fail_nca("DSA-BAN", e)
            raise e
        from . import store as _store
        sbx = _store.load_sandbox(sandbox_id)
        if sbx is None:
            e = ValueError(f"[DSA] 沙盒不存在: {sandbox_id}")
            self._fail_nca("DSA-BAN", e)
            raise e
        if sbx.phase in (Phase.EXIT, Phase.CLOSED):
            e = ValueError(f"[DSA] 终态沙盒（{sbx.phase.value}）不可迁移 BANNED")
            self._fail_nca("DSA-BAN", e)
            raise e
        if getattr(sbx, "dsa_status", None) == DSA_BANNED:
            e = ValueError(f"[DSA] 沙盒已 BANNED（永久休眠不可逆）: {sandbox_id}")
            self._fail_nca("DSA-BAN", e)
            raise e
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            self._apply_dsa_status(sbx, DSA_BANNED, BREAK_LEVEL_SEVERE, reason, ts)
            latency_ms = int((time.monotonic() - t0) * 1000)
        except Exception as e:  # noqa: BLE001
            self._fail_nca("DSA-BAN", e)
            raise DsaLinkError(f"[DSA] BANNED 落地失败: {e}") from e
        # I-5 修复：human_signatory 写入 NCA（审计链人类签批留痕）
        nca = nca_logger.build_nca(
            operation="DSA_BAN", operator="system",
            pre_state=sbx.phase.value, post_state=DSA_BANNED,
            audit_trail=f"{sandbox_id} reason={reason}（法律负空间永久休眠，ID86）",
            human_signature=human_signatory,
        )
        nca_id = nca_logger.save_nca(nca)
        # I-6/#10 修复：nca_id 回写沙盒链（SV-7 审计链闭合；失败生成 ERROR NCA）
        try:
            sbx.nca_ids = list(getattr(sbx, "nca_ids", []) or []) + [nca_id]
            _store.save_sandbox(sbx)
        except Exception as e:  # noqa: BLE001 - 回写失败显式存证（#10）
            self._fail_nca("DSA-BAN", e)
        return {
            "contract": DSA_EXT_CONTRACT,  # I-7
            "operation": "ban",
            "sandbox_id": sandbox_id,
            "dsa_status": DSA_BANNED,
            "break_level": BREAK_LEVEL_SEVERE,
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id},
        }

    # ---------------- 恢复（轻微越界限期重整） ----------------

    def resume(self, sandbox_id: str, human_approval: str = "") -> Dict[str, Any]:
        """DSA 恢复：SBX-SUSPENDED → SBX-ACTIVE（轻微越界限期重整后；中度需人类裁决）。

        六要素声明:
        目标函数: 轻微越界限期重整后恢复（DSA-001 §3.4；中度需人类裁决）
        约束矩阵: 输入——sandbox_id/human_approval；输出——dsa_status=ACTIVE；
                  禁止——BANNED 恢复（永久休眠不可逆）、中度越界无人类裁决恢复、
                  终态沙盒迁移
        先验分布: DSA-001 §3.4（轻微→限期重整可返回）
        配置权边界: L2；DSA-001 只读参考
        预期分配: 返回 {contract, dsa_status, nca_refs}；失败=ValueError/DsaLinkError
        审计轨迹: DSA_RESUME NCA（SV-7）+ 回写沙盒扩展字段
        """
        t0 = time.monotonic()
        from . import store as _store
        sbx = _store.load_sandbox(sandbox_id)
        if sbx is None:
            e = ValueError(f"[DSA] 沙盒不存在: {sandbox_id}")
            self._fail_nca("DSA-RESUME", e)
            raise e
        if getattr(sbx, "dsa_status", None) == DSA_BANNED:
            e = ValueError(f"[DSA] BANNED 永久休眠不可恢复: {sandbox_id}")
            self._fail_nca("DSA-RESUME", e)
            raise e
        # T-2 修复：仅 SUSPENDED 可 resume（契约破坏显式失败）
        if getattr(sbx, "dsa_status", None) != DSA_SUSPENDED:
            e = ValueError(f"[DSA] 仅 SBX-SUSPENDED 可恢复，当前 {getattr(sbx, 'dsa_status', None)}")
            self._fail_nca("DSA-RESUME", e)
            raise e
        level = getattr(sbx, "dsa_break_level", BREAK_LEVEL_MINOR)
        if level == BREAK_LEVEL_MODERATE and not human_approval:
            e = ValueError("[DSA] 中度越界恢复须人类裁决（DSA-001 §3.4）")
            self._fail_nca("DSA-RESUME", e)
            raise e
        if sbx.phase in (Phase.EXIT, Phase.CLOSED):
            e = ValueError(f"[DSA] 终态沙盒（{sbx.phase.value}）不可恢复")
            self._fail_nca("DSA-RESUME", e)
            raise e
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            sbx.dsa_status = DSA_ACTIVE
            sbx.dsa_break_level = ""
            sbx.dsa_reason = ""
            sbx.dsa_updated_at = ts
            _store.save_sandbox(sbx)
            latency_ms = int((time.monotonic() - t0) * 1000)
        except Exception as e:  # noqa: BLE001
            self._fail_nca("DSA-RESUME", e)
            raise DsaLinkError(f"[DSA] RESUME 落地失败: {e}") from e
        nca_id = self._nca("DSA_RESUME", DSA_SUSPENDED, DSA_ACTIVE,
                           f"{sandbox_id} level={level} human_approval={human_approval or '-'}")
        return {
            "contract": DSA_EXT_CONTRACT,  # I-7
            "operation": "resume",
            "sandbox_id": sandbox_id,
            "dsa_status": DSA_ACTIVE,
            "break_level": level,
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id},
        }

    # ---------------- 状态查询 ----------------

    def status(self, sandbox_id: str) -> Dict[str, Any]:
        """DSA 状态查询（扩展字段 dsa_status）。

        六要素声明:
        目标函数: DSA 状态扩展查询（审计/前端参考）
        约束矩阵: 输入——sandbox_id；输出——dsa_status；禁止——无
        先验分布: 沙盒扩展字段
        配置权边界: L2；只读
        预期分配: 返回 {contract, sandbox_id, dsa_status, break_level, phase}；失败=ValueError
        审计轨迹: 只读，不生成 NCA
        """
        from . import store as _store
        sbx = _store.load_sandbox(sandbox_id)
        if sbx is None:
            e = ValueError(f"[DSA] 沙盒不存在: {sandbox_id}")
            self._fail_nca("DSA-STATUS", e)
            raise e
        return {
            "contract": DSA_EXT_CONTRACT,  # I-7
            "operation": "status",
            "sandbox_id": sandbox_id,
            "dsa_status": getattr(sbx, "dsa_status", None),
            "break_level": getattr(sbx, "dsa_break_level", ""),
            "phase": sbx.phase.value,
        }


# 全局适配器实例（路由层消费；测试可注入）
ADAPTER = DsaExtension()
