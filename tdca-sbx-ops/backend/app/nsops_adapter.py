# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-1 沙盒-负空间实时联动适配层——NS-IF-001~003（映射 DSA IF-001~003）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-8（联动延迟<1s）+ SV-10（NCA 双向存证）
#               + 宪法十六条（可观测/正和）+ ID71（快系统）+ ID86（法律负空间绝对熔断）
#               + NS-OPS BV-1~7 + DSA-001（SBX-SUSPENDED/BANNED 待 DCD，扩展字段先行）
# 先验分布:     DSA 接口规范 V1.0-REVIEW（IF-001~003）+ NS-OPS M3 确认书 + flow_adapter HTTP 模式
# 配置权边界:   L2 层；NS-OPS 只读对接（HTTP 8123，不改写 NS-OPS 工程）
# 预期分配:     NS-IF-001 约束查询 / NS-IF-002 熔断触发 / NS-IF-003 合规证明；失败=契约破坏显式失败
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}（SBX-OPS 侧存证 + NS-OPS 侧 nca_ref 双向）
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-1 沙盒-负空间实时联动适配层（NS-IF-001~003）。

制度锚定: FC-SBX-OPS-001 F7 / SV-8 / SV-10 | SPDX-License-Identifier: TDCA-Internal

NS-IF 契约（S0-M3 §3.3，映射 DSA 接口规范 IF-001~003）:
  - NS-IF-001 约束查询: 沙盒创建/运行时查询负空间约束清单（NS-OPS F1 API）
  - NS-IF-002 熔断触发: 实验运行时实时校验负空间边界，触碰即 BV-1 熔断（NS-OPS F3 API）
  - NS-IF-003 合规证明: 出盒评估时获取负空间合规证明（NS-OPS NSFL 预检 + 熔断台账）

对接模式: HTTP（默认，调 NS-OPS 8123 /api/v1/*）；测试经 monkeypatch 模拟传输层（参照
NS-OPS test_m3_acceptance 模式），不依赖真实服务常驻——契约断言确定性。

SV-10 双向存证: 每次 NS-OPS 联动调用在 SBX-OPS 侧生成 NCA（nca_logger），并回引
NS-OPS 侧 nca_ref（judgments/预检响应），两链交叉可审计。
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from . import nca_logger

# NS-OPS 服务（8123，M3 验收冻结）——默认端点
NS_OPS_BASE_URL = "http://127.0.0.1:8123"
SV8_LATENCY_MS = 1000  # SV-8: 沙盒-负空间联动延迟 < 1s（ID71 快系统）
# HTTP 超时严格低于 SV-8 预算（E2 修复：1s 边界内快速失败，不等满超预算）
HTTP_TIMEOUT_SEC = 0.9

# NS-IF 契约编号（TERMS-GOVERNANCE-002 已登记 NC-20260810-001）
NS_IF_001 = "NS-IF-001"  # 约束查询（DSA IF-001 语义参考：负空间声明校验）
NS_IF_002 = "NS-IF-002"  # 熔断触发（DSA IF-003 语义参考：实时熔断）
NS_IF_003 = "NS-IF-003"  # 合规证明（语义参考：NSFL 预检 + 熔断台账，非 DSA IF-002 六要素审查等价）

# NS-IF 与 DSA IF 的映射关系声明（T3 修复）：
# NS-IF-001~003 为 SBX-OPS↔NS-OPS 联动独立命名空间（NC-20260810-001 已登记），
# DSA IF-001~003 仅作语义参考（负空间校验/实时熔断/审查证明），非接口等价——
# DSA IF-001 的 nonce 防重放/legal_baseline_hash/nsfl_cert 字段、IF-002 的六要素评分、
# IF-003 的 WebSocket 流在本工程阶段由 HTTP 同步端点承载，字段差异以 NS-OPS M3 工程契约为准。


class NSInterfaceError(ConnectionError):
    """NS-OPS 联动接口错误（T1 修复：fail-closed 统一异常）。

    NS-OPS 返回非 200 或契约破坏时抛出，禁止 fail-open 放行（ID86/NSFL 三不可）。
    继承 ConnectionError：路由层统一转 503（NS-OPS 依赖故障）。
    """


def _http_call(
    method: str,
    path: str,
    body: Optional[dict] = None,
    params: Optional[dict] = None,
    base_url: str = NS_OPS_BASE_URL,
) -> tuple[int, dict]:
    """调用 NS-OPS HTTP 服务（/api/v1/*，接口熵=0）。

    六要素声明:
    目标函数: NS-OPS 工程端点 HTTP 调用（NS-IF 联动传输层，SV-8 快路径）
    约束矩阵: 输入——method/path/body/params 契约；输出——(status, json)；
              禁止——非 JSON 响应静默通过（契约破坏显式失败）、绕过鉴权
    先验分布: flow_adapter._http_call 模式（NS-OPS M3）+ urllib 标准库
    配置权边界: L2；仅调用 NS-OPS 既有端点，不修改
    预期分配: 返回 (status, parsed_json)；失败=ConnectionError（服务不可达）/契约破坏
    审计轨迹: 调用结果由调用方 NCA 存证（SV-10）
    """
    url = f"{base_url}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=HTTP_TIMEOUT_SEC) as r:
            raw = r.read().decode("utf-8")
            try:
                return r.status, json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                # 契约破坏：非 JSON 响应显式失败（REV-N3 对齐，不静默降级）
                raise ConnectionError(
                    f"[NS-IF] NS-OPS 响应非 JSON（契约破坏）: HTTP {r.status} {raw[:200]}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            raise ConnectionError(
                f"[NS-IF] NS-OPS 错误响应非 JSON（契约破坏）: HTTP {e.code} {raw[:200]}")
    except OSError as e:
        raise ConnectionError(f"[NS-IF] NS-OPS 服务不可达（{base_url}）: {e}")


class NSOpsAdapter:
    """SBX-OPS → NS-OPS 实时联动适配层（NS-IF-001~003）。

    六要素声明:
    目标函数: 沙盒-负空间实时联动（F7）——约束查询/熔断触发/合规证明三契约
    约束矩阵: 输入——契约参数（subject_id/action/scene 等）；输出——NS-IF 响应；
              禁止——触碰法律负空间放行（ID86 绝对熔断）、延迟≥1s 静默通过（SV-8）
    先验分布: DSA 接口规范 IF-001~003 + NS-OPS M3 API（8123）
    配置权边界: L2；NS-OPS 只读对接
    预期分配: 返回 NS-IF 契约响应（含 nca_refs 双向存证）；失败=ConnectionError/ValueError
    审计轨迹: 每契约调用生成 SBX-OPS 侧 NCA（SV-10 双向存证）
    """

    def __init__(self, base_url: str = NS_OPS_BASE_URL) -> None:
        self.base_url = base_url

    # ---------------- fail-closed 存证辅助（#5: C01/SV-7 联动故障可观测） ----------------

    @staticmethod
    def _fail_nca(contract: str, operator: str, error: Exception) -> None:
        """fail-closed 异常路径 NCA 存证（联动故障亦须可观测，SV-7 全操作存证）。

        六要素声明:
        目标函数: 异常路径存证——NS-OPS 联动失败/契约破坏生成 ERROR 状态 NCA
        约束矩阵: 输入——contract/operator/error；输出——NCA 落盘；禁止——存证异常掩盖原始错误
        先验分布: C01 可观测（不可观测视为无效）+ SV-7 全操作 NCA
        配置权边界: L2；只追加存证
        预期分配: 落盘 ERROR NCA；失败=存证异常静默（不掩盖原始异常）
        审计轨迹: 本记录即审计轨迹
        """
        try:
            nca = nca_logger.build_nca(
                operation=f"NSOPS_FAIL_CLOSED_{contract.replace('-', '_')}",
                operator=operator or "system",
                pre_state="LINK",
                post_state="ERROR",
                audit_trail=f"{contract} fail-closed: {type(error).__name__}: {error}",
                negative_space_check="FUSE",
            )
            nca_logger.save_nca(nca)
        except Exception:  # noqa: BLE001 - 存证失败不掩盖原始异常（可观测优先但不可吞错）
            pass

    # ---------------- NS-IF-001 约束查询 ----------------

    def query_constraints(self, layer: Optional[str] = None) -> Dict[str, Any]:
        """NS-IF-001 约束查询：获取 NS-OPS 负空间约束清单（沙盒创建/运行时）。

        六要素声明:
        目标函数: 沙盒准入/运行时查询负空间约束清单（NS-OPS F1 API，约束查询契约）
        约束矩阵: 输入——layer（可选 subject/scene/institutional）；输出——约束清单；
                  禁止——NS-OPS 不可达/非 200 静默放行（fail-closed，沙盒准入必须过负空间审查）
        先验分布: NS-OPS GET /api/v1/constraints（8 条种子约束，含 institutional absolute）
        配置权边界: L2；只读查询
        预期分配: 返回 {contract, constraints, count, latency_ms, nca_refs}；
                  失败=NSInterfaceError（非 200/fail-open 禁止）/ConnectionError（不可达）
        审计轨迹: SBX-OPS NCA（NS-IF-001 查询）+ NS-OPS 响应指纹侧链（SV-10 双向存证）
        """
        t0 = time.monotonic()
        params = {"layer": layer} if layer else None
        try:
            status, resp = _http_call("GET", "/api/v1/constraints", params=params, base_url=self.base_url)
        except Exception as e:  # noqa: BLE001 - 统一 fail-closed 存证（#5）
            self._fail_nca(NS_IF_001, "system", e)
            raise
        if status != 200:  # T1 修复：fail-closed（ID86/NSFL 三不可）
            e = NSInterfaceError(f"[NS-IF-001] NS-OPS 非 200 响应（fail-closed）: HTTP {status} {resp}")
            self._fail_nca(NS_IF_001, "system", e)
            raise e
        constraints = resp if isinstance(resp, list) else resp.get("constraints", resp.get("items", []))
        latency_ms = int((time.monotonic() - t0) * 1000)
        if latency_ms >= SV8_LATENCY_MS:
            e = ConnectionError(f"[NS-IF-001] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
            self._fail_nca(NS_IF_001, "system", e)
            raise e
        # T2 修复：NS-OPS 侧只读查询无 nca_ref 字段——以响应内容 SHA-256 作侧链证据（SV-10）
        resp_fingerprint = hashlib.sha256(
            json.dumps(resp, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        nca = nca_logger.build_nca(
            operation="NSOPS_QUERY_CONSTRAINTS",
            operator="system",
            pre_state="NONE",
            post_state=f"NS-OPS:{status}",
            audit_trail=f"NS-IF-001 约束查询 layer={layer or 'ALL'} count={len(constraints)} "
                        f"resp_fingerprint={resp_fingerprint}",
        )
        nca_id = nca_logger.save_nca(nca)
        return {
            "contract": NS_IF_001,
            "status": status,
            "constraints": constraints,
            "count": len(constraints),
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id, "nsops_fingerprint": resp_fingerprint},
        }

    # ---------------- NS-IF-002 熔断触发 ----------------

    def check_and_fuse(self, actor: str, action: str, scene: str = "community",
                       sandbox_id: str = "") -> Dict[str, Any]:
        """NS-IF-002 熔断触发：实时校验负空间边界，触碰即 BV-1 熔断（NS-OPS F3 API）。

        六要素声明:
        目标函数: 实验运行时实时负空间边界校验（F3 声明-行为校验 + BV-1 熔断触发）
        约束矩阵: 输入——actor/action/scene/sandbox_id（M3-6 熔断落地预留，可为空）；
                  输出——decision + fuse_triggered；
                  禁止——BLOCK（法律负空间）放行执行（ID86 绝对熔断，无替代路径）
        先验分布: NS-OPS POST /api/v1/judgments
                  （decision ∈ allow / restrict / allow_with_conditions / block + fuse，NS-OPS Decision 枚举）
        配置权边界: L2；熔断指令来自 NS-OPS 判定，SBX-OPS 不代行
        预期分配: 返回 {contract, decision, fuse_triggered, matched, nca_refs, latency_ms}
                  失败=NSInterfaceError（非 200 fail-closed）/ConnectionError（不可达/超预算）
                  注（E1 边界声明）: 本契约完成判定层（fuse 结果 + NCA 存证）；沙盒侧熔断
                  落地（SUSPENDED 标记/关闭）由 M3-6 dsa_extension 承接（SV-9 扩展字段先行，
                  sandbox_id 已透传记录，M3-6 直接消费）
        审计轨迹: SBX-OPS NCA（NS-IF-002，negative_space_check=FUSE when blocked）+ NS-OPS nca_ref
        """
        t0 = time.monotonic()
        body = {"actor": actor, "action": action, "scene": scene}
        try:
            status, resp = _http_call("POST", "/api/v1/judgments", body=body, base_url=self.base_url)
        except Exception as e:  # noqa: BLE001 - 统一 fail-closed 存证（#5）
            self._fail_nca(NS_IF_002, actor, e)
            raise
        if status != 200:  # T1 修复：fail-closed——服务异常时禁止默认 allow 放行（ID86 绝对熔断）
            e = NSInterfaceError(
                f"[NS-IF-002] NS-OPS 非 200 响应（fail-closed，禁止放行）: HTTP {status} {resp}")
            self._fail_nca(NS_IF_002, actor, e)
            raise e
        latency_ms = int((time.monotonic() - t0) * 1000)
        if latency_ms >= SV8_LATENCY_MS:
            e = ConnectionError(f"[NS-IF-002] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
            self._fail_nca(NS_IF_002, actor, e)
            raise e
        decision = resp.get("decision")
        # #1（compliance-auditor P0）: decision 缺失/非法 → fail-closed（禁止默认 allow 放行，ID86）
        VALID_DECISIONS = {"allow", "restrict", "allow_with_conditions", "block"}
        if decision not in VALID_DECISIONS:
            e = NSInterfaceError(
                f"[NS-IF-002] NS-OPS decision 缺失/非法（fail-closed）: {decision!r}，"
                f"须 ∈ {sorted(VALID_DECISIONS)}")
            self._fail_nca(NS_IF_002, actor, e)
            raise e
        fuse = bool(resp.get("fuse_triggered", False))
        nca = nca_logger.build_nca(
            operation="NSOPS_BOUNDARY_CHECK",
            operator=actor,
            pre_state="IN-SBX",
            post_state=f"DECISION:{decision}",
            audit_trail=f"NS-IF-002 action={action} scene={scene} sandbox_id={sandbox_id or '-'} "
                        f"matched={resp.get('matched_constraints', [])}",
            negative_space_check="FUSE" if fuse else "PASS",
        )
        nca_id = nca_logger.save_nca(nca)
        return {
            "contract": NS_IF_002,
            "status": status,
            "decision": decision,
            "fuse_triggered": fuse,
            "reason": resp.get("reason", ""),
            "matched_constraints": resp.get("matched_constraints", []),
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id, "nsops": resp.get("nca_ref", "")},
            "sandbox_id": sandbox_id,
        }

    # ---------------- NS-IF-003 合规证明 ----------------

    def compliance_cert(self, actor: str, action: str) -> Dict[str, Any]:
        """NS-IF-003 合规证明：出盒评估时获取负空间合规证明（NSFL 预检 + 熔断台账）。

        六要素声明:
        目标函数: 出盒评估负空间合规证明（NS-OPS NSFL 预检 + 熔断台账交叉验证）
        约束矩阵: 输入——actor/action；输出——合规证明（compliant + 证据）；
                  禁止——活跃熔断/预检 blocked 判合规（ID86/NSFL 三不可）
        先验分布: NS-OPS GET /api/v1/integration/nsfl/declarations + /fuses + /history
        配置权边界: L2；只读审计查询
        预期分配: 返回 {contract, compliant, precheck, active_fuses, fuse_count, nca_refs, latency_ms}
                  失败=NSInterfaceError（非 200 fail-closed，禁止误判合规）/ConnectionError（不可达）
        审计轨迹: SBX-OPS NCA（NS-IF-003 合规证明）+ NS-OPS 响应指纹侧链（SV-10 双向存证）
        """
        t0 = time.monotonic()
        try:
            precheck_st, precheck = _http_call(
                "GET", "/api/v1/integration/nsfl/declarations",
                params={"text": action}, base_url=self.base_url,
            )
            fuses_st, fuses = _http_call("GET", "/api/v1/integration/nsfl/fuses", base_url=self.base_url)
            history_st, history = _http_call("GET", "/api/v1/integration/nsfl/history", base_url=self.base_url)
        except Exception as e:  # noqa: BLE001 - 统一 fail-closed 存证（#5）
            self._fail_nca(NS_IF_003, actor, e)
            raise
        # T1 修复：任一查询非 200 → fail-closed（禁止错误合规证明）
        for name, st in (("precheck", precheck_st), ("fuses", fuses_st), ("history", history_st)):
            if st != 200:
                e = NSInterfaceError(f"[NS-IF-003] NS-OPS {name} 非 200（fail-closed）: HTTP {st}")
                self._fail_nca(NS_IF_003, actor, e)
                raise e
        latency_ms = int((time.monotonic() - t0) * 1000)
        if latency_ms >= SV8_LATENCY_MS:
            e = ConnectionError(f"[NS-IF-003] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
            self._fail_nca(NS_IF_003, actor, e)
            raise e

        fuse_list = fuses
        # #2（compliance-auditor P0）: fuses 结构异常（非 list）→ fail-closed（禁止默认空台账判合规，ID86）
        if not isinstance(fuse_list, list):
            e = NSInterfaceError(
                f"[NS-IF-003] NS-OPS fuses 响应结构异常（fail-closed）: {type(fuse_list).__name__}，"
                f"非 list 禁止判合规")
            self._fail_nca(NS_IF_003, actor, e)
            raise e
        precheck_blocked = bool(precheck.get("blocked", False))
        active_fuses = [f for f in fuse_list if isinstance(f, dict) and f.get("state") != "RESOLVED"]
        # 合规判定：预检不 blocked ∧ 无活跃熔断
        compliant = (not precheck_blocked) and (len(active_fuses) == 0)

        # T2 修复：NS-OPS 侧台账无 nca_ref——以响应内容 SHA-256 作侧链证据（SV-10）
        resp_fingerprint = hashlib.sha256(
            json.dumps({"precheck": precheck, "fuses": fuses, "history": history},
                       sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        nca = nca_logger.build_nca(
            operation="NSOPS_COMPLIANCE_CERT",
            operator=actor,
            pre_state="OUT-SBX",
            post_state="COMPLIANT" if compliant else "NON-COMPLIANT",
            audit_trail=f"NS-IF-003 action={action} precheck_blocked={precheck_blocked} "
                        f"active_fuses={len(active_fuses)} history={len(history) if isinstance(history, list) else 0} "
                        f"resp_fingerprint={resp_fingerprint}",
            negative_space_check="PASS" if compliant else "FUSE",
        )
        nca_id = nca_logger.save_nca(nca)
        return {
            "contract": NS_IF_003,
            "compliant": compliant,
            "precheck": precheck,
            "active_fuses": active_fuses,
            "fuse_count": len(active_fuses),
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id, "nsops_fingerprint": resp_fingerprint},
        }


# 全局适配器实例（路由层消费；测试可注入 base_url）
ADAPTER = NSOpsAdapter()
