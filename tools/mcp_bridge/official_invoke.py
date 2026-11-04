# FC-ID: DCD-MCP-BRIDGE-001 | 模块 8 官方能力调用 API 面（INTERFACE-001 批4 · ⛔不部署不生效）
"""POST /api/v1/official/invoke —— 批2之门（agent_card 校验／四判／SBX 分卷／space_id／熔断）
之上只加一个端点：复用 tools/mcp_bridge/trispace.py 全部校验与判据函数（OC-19 单一判据源，
⛔复制一份），证与账皆由本面完成；MCP 侧仅薄封装转发（official:invoke）。

依据与纪律
-----------
* 施工令：TDCA-HANDOFF-EXEC-L1SI194-INTERFACE-001（B1~B9，⛔不部署）。
* 请求七字段（OC-17）：caller_id／callee_id／operation／arguments／authz_ref（用资产必填）
  ／space_id／request_id；两 Header：X-TDCA-Agent-Card（机机必填）／X-TDCA-Contract。
* 响应五字段（OC-18）：result 或 error_code／nca_id／space_id／ledger（GOV/TOOL/ASSET）／billing。
* billing 一律 {"status":"pending-declaration"}（计费条款未生效：⛔金额、⛔计费收费）。
* 拒绝码闭集八（OC-34/35），全部 fail-closed 零消耗（⛔计量⛔落计费）：
  E-NO-CARD／E-NO-AUTHZ／E-NS-FAIL／E-SPACE／E-VERSION／E-FIELD／E-LIMIT／E-DEGRADED。
  唯一例外（与批2 A7 熔断纪律一致）：触碰法律负空间/越界时落 FuseReject 熔断件并降级，
  属「绝不静默通过」之留痕，非正式调用存证，回报 R-3 逐码注明。
* 幂等（OC-20）：同 request_id 重投=重试，一条存证（缓存响应原样复放）。
* 写只落 SBX（批2 A5/A6 门槛未过前 PCM 不可写）；NS/PCM 一律 E-SPACE。
* Operator 中性值 anonymous；Source 三项：user-agent＋来源标识或加盐摘要＋request_id。
* 版本：X-TDCA-Contract 须等于 CONTRACT_VERSION，不兼容回 E-VERSION，⛔静默降级。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import trispace
from .fuse import precheck
from .watermark import Watermark

CONTRACT_VERSION = "TDCA-OFFICIAL-INVOKE-V1.0"
WRITE_SPACE = trispace.SPACE_SBX
LEDGERS = ("GOV", "TOOL", "ASSET")
REQUEST_CACHE_CAP = 5000  # 幂等缓存上限（FIFO 淘汰，防状态文件无界增长）

# 拒绝码闭集（八，OC-34/35；S-6：实测见未列入情形须停手回报，⛔自行增码）
E_NO_CARD = "E-NO-CARD"
E_NO_AUTHZ = "E-NO-AUTHZ"
E_NS_FAIL = "E-NS-FAIL"
E_SPACE = "E-SPACE"
E_VERSION = "E-VERSION"
E_FIELD = "E-FIELD"
E_LIMIT = "E-LIMIT"
E_DEGRADED = "E-DEGRADED"

# HTTP 状态映射（R-3 逐码给读数用）
HTTP_STATUS = {E_VERSION: 400, E_FIELD: 400, E_NO_CARD: 401, E_NO_AUTHZ: 403,
               E_SPACE: 403, E_NS_FAIL: 403, E_LIMIT: 429, E_DEGRADED: 503}

_REQUIRED_STR = ("caller_id", "callee_id", "operation", "space_id", "request_id")


def derive_ledger(operation: str) -> str:
    """ledger 由 operation 名空间前缀导出：gov:/tool:/asset:，缺省 TOOL（确定性，回报注明）。"""
    head = str(operation).split(":", 1)[0].upper()
    return head if head in LEDGERS else "TOOL"


def _salted_source(fp: str, request_id: str) -> str:
    """来源标识或加盐摘要：无 X-TDCA-Source 头时取 指纹:请求号 的加盐摘要（sha256 前 16 位）。"""
    raw = f"tdca-src::{fp}::{request_id}".encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()[:16]


class OfficialInvokeService:
    """API 面服务载体（与 FastAPI 解耦，可单测；shim.py 仅做薄接线）。"""

    def __init__(self, evidence_dir: Path):
        self.ev = Path(evidence_dir)
        self.config = trispace.load_config()
        self.state = trispace.TriSpaceState(self.ev)
        self.limiter = trispace.RateLimiter(self.config)
        self.wm = Watermark(self.ev)
        self.fuse_log = self.ev / ".nsfl-fuse.log"
        trispace.ensure_chain_declaration(self.ev)

    # ---- 拒绝构造（统一零消耗口径：不落 ToolCall 存证、不计费、不写状态）----
    def _reject(self, code: str, detail: str) -> tuple[int, dict]:
        return HTTP_STATUS[code], {"error_code": code, "detail": detail,
                                   "billing": {"status": "pending-declaration"}}

    def handle(self, body, card_header: str | None, contract: str | None,
               user_agent: str | None, source_header: str | None) -> tuple[int, dict]:
        # ① 版本闸（E-VERSION，⛔静默降级）
        if contract != CONTRACT_VERSION:
            return self._reject(E_VERSION,
                                f"契约版本须为 {CONTRACT_VERSION}（收到: {contract!r}），不兼容拒绝")

        # ② 字段闸（E-FIELD）
        if not isinstance(body, dict):
            return self._reject(E_FIELD, "请求体须为 JSON 对象")
        missing = [f for f in _REQUIRED_STR if not isinstance(body.get(f), str) or not body.get(f)]
        if not isinstance(body.get("arguments"), dict):
            missing.append("arguments（须为对象）")
        if missing:
            return self._reject(E_FIELD, "缺/类型不合字段: " + ",".join(missing))
        operation = body["operation"]
        request_id = body["request_id"]
        ledger = derive_ledger(operation)

        # ③ 空间闸（E-SPACE）：写只落 SBX；缺 space_id 已在②拒
        if body["space_id"] not in (trispace.SPACE_NS, trispace.SPACE_SBX, trispace.SPACE_PCM):
            return self._reject(E_SPACE, f"space_id={body['space_id']!r} 非法（闭集 NS/SBX/PCM）")
        if body["space_id"] != WRITE_SPACE:
            return self._reject(E_SPACE,
                                f"写只落 SBX（批2 A5/A6 门槛未过，{body['space_id']} 不可写）")

        # ④ 幂等闸（OC-20）：同 request_id 重投=重试，缓存原样复放（零消耗）
        cached = self.state.data.setdefault("requests", {}).get(request_id)
        if cached is not None:
            return 200, dict(cached["response"])

        # ⑤ 卡闸（E-NO-CARD，照双轨身份§三 + GUEST 路 ≤4KB 同口径）
        if not card_header:
            return self._reject(E_NO_CARD, "缺 X-TDCA-Agent-Card 头（机机调用必填）")
        try:
            card = json.loads(card_header)
        except json.JSONDecodeError:
            return self._reject(E_NO_CARD, "X-TDCA-Agent-Card 非法 JSON")
        shape_err = trispace.validate_card_shape(card)
        if shape_err:
            return self._reject(E_NO_CARD, f"agent_card 不受理：{shape_err}")

        # ⑥ 资产授权闸（E-NO-AUTHZ：ledger=ASSET 时 authz_ref 必填）
        authz_ref = body.get("authz_ref")
        if ledger == "ASSET" and not isinstance(authz_ref, str) or ledger == "ASSET" and not authz_ref:
            return self._reject(E_NO_AUTHZ, "用资产调用（ledger=ASSET）须携 authz_ref")

        # ⑦ 退化闸（E-DEGRADED：存证卷不可写即退化，fail-closed）
        if not os.access(self.ev, os.W_OK):
            return self._reject(E_DEGRADED, "存证卷不可写，服务退化拒绝")

        fp = trispace.card_fingerprint(card)

        # ⑧ 状态闸：BANNED/SUSPENDED 映射 E-NS-FAIL（闭集内，无新码）
        ok, st, why = self.state.check_writable(fp)
        if not ok:
            return self._reject(E_NS_FAIL, why)

        # ⑨ 限流闸（E-LIMIT，参数可配）
        ok, why = self.limiter.allow(fp)
        if not ok:
            return self._reject(E_LIMIT, why)

        args = body["arguments"]

        # ⑩ 轻量前置（批2保留项）：触碰法律负空间 ⟹ SBX-BANNED + 熔断件（留痕，非正式存证）
        ok, hits = precheck(args, self.fuse_log)
        if not ok:
            self.state.ban(fp)
            self.wm.stamp("anonymous", "official:invoke", args,
                          f"REJECTED-BANNED {hits}", rejected=True,
                          space_id=trispace.SPACE_SBX, status=trispace.ST_SBX_BANNED)
            return self._reject(E_NS_FAIL, f"触碰法律负空间 {hits}，已 SBX-BANNED（熔断 NCA 已落）")

        # ⑪ 越界：触及声明边界 ⟹ SBX-SUSPENDED + 熔断件（限期重整）
        ns = card.get("ns_types", {})
        text = json.dumps(args, ensure_ascii=False)
        crossed = [str(x) for k in ("scene_limited", "approval_required")
                   for x in ns.get(k, []) if str(x) and str(x) in text]
        if crossed:
            a = self.state.suspend(fp, self.config["suspend_hours"])
            self.wm.stamp("anonymous", "official:invoke", args,
                          f"REJECTED-SUSPENDED crossed={crossed}", rejected=True,
                          space_id=trispace.SPACE_SBX, status=trispace.ST_SBX_SUSPENDED)
            return self._reject(E_NS_FAIL,
                                f"越界 {crossed}，已 SBX-SUSPENDED（限期重整至 {a['suspended_until']}）")

        # ⑫ 四判（A3 复用）：全过才出 CERT 升 SBX；未过零消耗（无 CERT 不升 SBX）
        j = trispace.run_four_judgments(card, args, [], self.config)
        if not j["passed"]:
            return self._reject(E_NS_FAIL, f"NSFL 四判未过：{j['detail']}")

        # ⑬ 成功：一调一证（OC-30/31/32），Source 三项，prev_nca 连续（Watermark 链式）
        cert = trispace.issue_cert(fp, j, self.config)
        self.state.admit_sbx(fp, cert)
        source = {"user_agent": user_agent or "(未携)",
                  "source": (source_header or "").strip() or _salted_source(fp, request_id),
                  "request_id": request_id}
        extra = {"ledger": ledger, "authz_ref": authz_ref if isinstance(authz_ref, str) else None,
                 "Source": source, "operation": operation,
                 "caller_id": body["caller_id"], "callee_id": body["callee_id"],
                 "cert_id": cert["cert_id"], "contract": CONTRACT_VERSION,
                 "billing": {"status": "pending-declaration"}}
        out = json.dumps({"operation": operation, "echo": args}, ensure_ascii=False)
        nca = self.wm.stamp("anonymous", "official:invoke", args, out,
                            space_id=trispace.SPACE_SBX, status=trispace.ST_SBX_ACTIVE,
                            extra=extra)
        resp = {"result": {"ack": operation, "echo": args},
                "nca_id": nca["NCA-ID"], "space_id": trispace.SPACE_SBX,
                "ledger": ledger, "billing": {"status": "pending-declaration"}}
        cache = self.state.data["requests"]
        cache[request_id] = {"nca_id": nca["NCA-ID"], "response": resp,
                             "ts": datetime.now(timezone.utc).isoformat()}
        while len(cache) > REQUEST_CACHE_CAP:   # FIFO 淘汰
            cache.pop(next(iter(cache)))
        self.state.save()
        return 200, resp
