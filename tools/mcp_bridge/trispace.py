# FC-ID: DCD-MCP-BRIDGE-001 | 模块 7 三空间流水线（TRISPACE-001 · NS→SBX→PCM · ⛔部署前不生效）
"""非原生通道三空间接入：匿名只读 / 写须 agent_card / 四判出 NSFL-CERT / SBX 分卷 / 熔断回退。

依据与纪律
-----------
* 施工令：TDCA-HANDOFF-EXEC-L1SI194-TRISPACE-001（A1~A10，⛔不部署）。
* 四判来源：TDCA-PRINCIPLE-DSA-001 §3.1（仓内 docs/sbx-ops/，逐字照抄于判据名）：
    J1 NS-Type 声明完整性（绝对禁止/场景限制/需审批）
    J2 ⊗禁止操作符覆盖度（是否遗漏法律负空间）
    J3 法律负空间绝对化检查（刑事/行政禁止领域）
    J4 最小化合原则验证（是否过度设计）
* agent_card 口径：TDCA-REGISTER-CONTRACT-001 §2.2（披露三要素 + 数据性质标注 +
  identity_type: native/external）；GUEST 路同款底线（JSON 对象 ≤4KB，
  见 agent_channel_ops.py，⛔不改该文件）。
* 四判的**机读化**是施工侧确定性判据（每条可测、可复算）；制度原文为上位口径，
  机读化实现逐条在回报 R-4 给读数。α 门槛只读配置（⛔写死、⛔自拟场景映射）。
* 硬界 N1~N6：不改 GUEST 路 / compose / nginx / 部署；不写主账（NCA-REGISTRY）；
  不动既有 MCP 链数据（append-only）；不改制度件；不对外表述。
* 链口径（A8）：取**分链登记**——本链为 TDCA-MCP-CHAIN-001，独立于主账
  NCA-REGISTRY（写主账触 N4，衔接选项在令面即被排除），跨段引用走 chain_ref。

SBX 分卷取法（A5）：**逻辑前缀**——SBX 件 Post-State.Path 前缀 `sbx:`，
与 PCM 面（`pcm:`，本批尚无条件产生）同卷不同前缀。⛔取物理卷（触 N2 改 compose）。
未过验证（SBX）件一律 data_provenance=simulated，⛔计入正式存证语义。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------- 配置（全部参数化：环境变量覆盖，⛔写死业务取值） ----------------
# 命名：TDCA_TRISPACE_* ；默认值集中于 CONFIG_DEFAULTS，回报 R-6 逐项列出。


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, ""))
    except ValueError:
        return default


def load_config() -> dict:
    """读配置（环境变量为唯一配置载体；未置则用默认值并在回报列明）。"""
    return {
        # 限流（A5）：每指纹每分钟写上限 + 全局每分钟写上限
        "rate_per_minute": _env_int("TDCA_TRISPACE_RATE_PER_MIN", 30),
        "rate_global_per_minute": _env_int("TDCA_TRISPACE_RATE_GLOBAL_PER_MIN", 120),
        # NSFL-CERT 有效期（小时，A3）
        "cert_ttl_hours": _env_int("TDCA_TRISPACE_CERT_TTL_HOURS", 24),
        # 越界降级限期重整（小时，A7）
        "suspend_hours": _env_int("TDCA_TRISPACE_SUSPEND_HOURS", 24),
        # SBX→PCM 验证周期（天，A6，制度占位——采值待创始人）
        "verify_days": _env_int("TDCA_TRISPACE_VERIFY_DAYS", 7),
        # α 门槛（A6）：阈值照 DSA-001 §3.2 原定 α>1.2（内外一致，⛔另设）；
        # α 现值只读 TDCA_TRISPACE_ALPHA，未置=未定（占位），⛔机算场景映射
        "alpha_threshold": float(os.environ.get("TDCA_TRISPACE_ALPHA_THRESHOLD", "1.2")),
        "alpha": os.environ.get("TDCA_TRISPACE_ALPHA", ""),
        # 最小化合：参数 JSON 最大深度（J4）
        "max_arg_depth": _env_int("TDCA_TRISPACE_MAX_ARG_DEPTH", 6),
    }


# ---------------- 状态位（A4） ----------------
SPACE_NS = "NS"
SPACE_SBX = "SBX"
SPACE_PCM = "PCM"
ST_NS_PENDING = "NS-PENDING"
ST_SBX_ACTIVE = "SBX-ACTIVE"
ST_PCM_LIVE = "PCM-LIVE"
ST_SBX_SUSPENDED = "SBX-SUSPENDED"
ST_SBX_BANNED = "SBX-BANNED"

# 本链标识（A8 分链登记，写进每件存证 chain_ref）
CHAIN_REF = "TDCA-MCP-CHAIN-001"

# 拒绝码（A1/A2：码与文案稳定可测）
# TODO(批4)：拒绝码形（-32001 等数字码）与规范闭集（E-*）统一，批4一并处理（TRISPACE-002 附条1，本批⛔改行为）
CODE_NO_CARD = -32001           # 写无 agent_card（fail-closed 零消耗）
CODE_BANNED = -32002            # 指纹已 SBX-BANNED
CODE_SUSPENDED = -32003         # 指纹 SBX-SUSPENDED（限期重整中）
CODE_RATE_LIMITED = -32004      # 限流
CODE_JUDGMENT_FAIL = -32005     # 四判未过（不升 SBX）

MSG_NO_CARD = ("AGENT_CARD_REQUIRED: 写工具须随调用提交 agent_card"
               "（双轨身份§三：智能体以机器可读身份卡声明身份）；"
               "本次拒绝为零消耗（不落存证、不写状态）")
MSG_BANNED = "SBX-BANNED: 该 agent_card 已触法律负空间封禁，写路永久关闭（读路不受影响）"
MSG_SUSPENDED = "SBX-SUSPENDED: 该 agent_card 越界已降级，限期重整至 {until}（读路不受影响）"
MSG_RATE_LIMITED = "RATE_LIMITED: 写路限流（每指纹 {per}/min，全局 {glob}/min），本次零消耗"
MSG_JUDGMENT_FAIL = "NSFL 四判未过（DSA-001 §3.1），不出 NSFL-CERT，不升 SBX：{detail}"

# J3 豁免语（对绝对禁止项出现即判「未绝对化」，fail-closed）
_EXEMPTION_RE = re.compile(r"豁免|例外|可放宽|白名单|可审批|可解禁|酌情")

# agent_card 底线（照 GUEST 路口径：JSON 对象 ≤4KB）
CARD_MAX_BYTES = 4096
_NS_TYPE_KEYS = ("absolute", "scene_limited", "approval_required")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json_dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def card_fingerprint(card: dict) -> str:
    """卡指纹 = 卡规范化 JSON 的 sha256 前 16 位（归责锚点，⛔强制采集真实身份）。"""
    return hashlib.sha256(_json_dumps(card).encode()).hexdigest()[:16]


def validate_card_shape(card) -> str | None:
    """卡底线校验：须为 JSON 对象且 ≤4KB（照双轨身份§三 + GUEST 路同口径）。

    返回 None=可受理；否则返回人话缺项（fail-closed：形状不合即不受理）。
    字段深度（披露三要素/identity_type）由 J1 四判承接，不在底线层展开。
    """
    if not isinstance(card, dict):
        return "agent_card 须为 JSON 对象"
    if len(_json_dumps(card).encode()) > CARD_MAX_BYTES:
        return "agent_card 超过 4KB"
    return None


# ---------------- 四判（A3 · DSA-001 §3.1 机读化，逐判可测） ----------------

def _depth(obj, level: int = 1) -> int:
    if isinstance(obj, dict) and obj:
        return max(_depth(v, level + 1) for v in obj.values())
    if isinstance(obj, list) and obj:
        return max(_depth(v, level + 1) for v in obj)
    return level


def judge_ns_type_completeness(card: dict) -> tuple[bool, str]:
    """J1 NS-Type 声明完整性：absolute / scene_limited / approval_required 三档齐全，
    各为列表；absolute 档非空（主体须声明其绝对不做的事，⛔空声明=无法证明）。"""
    ns = card.get("ns_types")
    if not isinstance(ns, dict):
        return False, "ns_types 缺失或非对象（三档声明是 §3.1 触发条件）"
    missing = [k for k in _NS_TYPE_KEYS if k not in ns]
    if missing:
        return False, "ns_types 缺档: " + ",".join(missing)
    for k in _NS_TYPE_KEYS:
        if not isinstance(ns[k], list):
            return False, f"ns_types.{k} 须为列表"
    if not ns["absolute"]:
        return False, "ns_types.absolute 为空（须声明绝对禁止项）"
    return True, "三档齐全，absolute 非空"


def judge_operator_coverage(card: dict) -> tuple[bool, str]:
    """J2 ⊗禁止操作符覆盖度：卡声明的每个 ⊗ 禁止操作符（forbidden_operators）
    必须被三档之一覆盖（归入 absolute / scene_limited / approval_required），
    ⛔有声明无归类=遗漏法律负空间（fail-closed）。"""
    ops = card.get("forbidden_operators", [])
    if not isinstance(ops, list):
        return False, "forbidden_operators 须为列表"
    ns = card.get("ns_types", {})
    if not isinstance(ns, dict):
        ns = {}  # MCPDIAG-001 批1：非对象视同空对象（fail-closed 语义不变）
    covered = set()
    for k in _NS_TYPE_KEYS:
        covered |= {str(x) for x in ns.get(k, [])}
    orphan = [str(o) for o in ops if str(o) not in covered]
    if orphan:
        return False, "⊗操作符未被三档覆盖: " + ",".join(orphan)
    return True, f"{len(ops)} 个 ⊗操作符全部被三档覆盖"


def judge_absolute_negative_space(card: dict, arg_text: str,
                                  fuse_hits: list) -> tuple[bool, str]:
    """J3 法律负空间绝对化：刑事/行政禁止领域不得被相对化。
    两条机读判据（任一命中即 fail）：
      a) 卡内对 absolute 档条目附加豁免语（豁免/例外/白名单…）→ 未绝对化；
      b) 调用实参命中 NSFL 扫描（fuse_hits 非空，单一事实源 enforce_entry）
         → 触碰绝对负空间（运行时侧，由调用方转 SBX-BANNED）。
    """
    ns = card.get("ns_types", {})
    if not isinstance(ns, dict):
        ns = {}  # MCPDIAG-001 批1：非对象视同空对象（fail-closed 语义不变）
    bad = [str(x) for x in ns.get("absolute", [])
           if _EXEMPTION_RE.search(str(x))]
    if bad:
        return False, "absolute 档含豁免语（负空间被相对化）: " + ",".join(bad)
    if fuse_hits:
        return False, "实参触碰法律负空间: " + ",".join(fuse_hits)
    return True, "absolute 档无豁免语，实参未触碰负空间"


def judge_minimal_composition(card: dict, arguments: dict,
                              max_depth: int) -> tuple[bool, str]:
    """J4 最小化合：是否过度设计。
    【机读化收窄版】（TRISPACE-002 附条2 标注）：制度上位口径为 DSA-001 §3.1
    「最小化合原则验证」，此处为其施工侧确定性收窄实现（字段集 + 深度边界），
    不等同制度原文全量语义。
    机读判据：实参键 ⊆ 卡声明的 declared_fields（未声明则默认只收 text），
    且实参 JSON 深度 ≤ 配置上限；超限即过度设计（fail-closed）。"""
    allowed = card.get("declared_fields", ["text"])
    if not isinstance(allowed, list):
        return False, "declared_fields 须为列表"
    extra = [k for k in arguments if k not in allowed]
    if extra:
        return False, "实参含未声明字段（过度设计）: " + ",".join(map(str, extra))
    if _depth(arguments) > max_depth:
        return False, f"实参嵌套深度 {_depth(arguments)} > {max_depth}"
    return True, "实参字段与深度均在声明边界内"


def run_four_judgments(card: dict, arguments: dict, fuse_hits: list,
                       config: dict) -> dict:
    """四判合一，逐判给读数（R-4）。任一 fail ⟹ 不出 NSFL-CERT（fail-closed）。"""
    j1 = judge_ns_type_completeness(card)
    j2 = judge_operator_coverage(card)
    j3 = judge_absolute_negative_space(card, _json_dumps(arguments), fuse_hits)
    j4 = judge_minimal_composition(card, arguments, config["max_arg_depth"])
    results = {"J1_NS-Type完整性": j1, "J2_⊗覆盖度": j2,
               "J3_法律负空间绝对化": j3, "J4_最小化合": j4}
    passed = all(ok for ok, _ in results.values())
    detail = "; ".join(f"{k}={'PASS' if v[0] else 'FAIL:' + v[1]}"
                       for k, v in results.items())
    return {"passed": passed, "judgments": {k: {"pass": v[0], "detail": v[1]}
                                            for k, v in results.items()},
            "detail": detail}


def issue_cert(fp: str, judgments: dict, config: dict) -> dict:
    """出 NSFL-CERT（含有效期，A3）。证书落状态文件（随存证卷走）。"""
    now = _now()
    return {
        "cert_id": f"NSFL-CERT-{now.strftime('%Y%m%d')}-{fp[:8].upper()}",
        "subject": f"agent_card:{fp}",
        "basis": "TDCA-PRINCIPLE-DSA-001 §3.1（四判全 PASS）",
        "judgments": {k: v["pass"] for k, v in judgments["judgments"].items()},
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=config["cert_ttl_hours"])).isoformat(),
        "space_id": SPACE_SBX,
        "status_on_issue": ST_SBX_ACTIVE,
    }


# ---------------- 三空间状态机（A4/A5/A7） ----------------

class TriSpaceState:
    """状态载体：trispace-state.json（随 /evidence 卷，逻辑前缀分卷的状态侧）。

    agents: fp -> {space_id, status, sbx_since, suspended_until, cert, writes}
    读写一律原子替换；⛔由件名/目录推断空间——状态只以本文件为准。
    """

    def __init__(self, evidence_dir: Path):
        self.path = Path(evidence_dir) / "trispace-state.json"
        self.data = {"chain_ref": CHAIN_REF, "agents": {}}
        if self.path.is_file():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.data = {"chain_ref": CHAIN_REF, "agents": {}}
        self.data.setdefault("agents", {})

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(_json_dumps(self.data), encoding="utf-8")
        tmp.replace(self.path)

    def agent(self, fp: str) -> dict:
        return self.data["agents"].get(fp)

    def ensure(self, fp: str) -> dict:
        a = self.data["agents"].get(fp)
        if a is None:
            a = {"space_id": SPACE_NS, "status": ST_NS_PENDING,
                 "sbx_since": None, "suspended_until": None,
                 "cert": None, "writes": 0}
            self.data["agents"][fp] = a
        return a

    # ---- 状态迁移 ----
    def admit_sbx(self, fp: str, cert: dict) -> dict:
        """NS-PENDING → SBX-ACTIVE（四判全过，出 CERT）。"""
        a = self.ensure(fp)
        a.update({"space_id": SPACE_SBX, "status": ST_SBX_ACTIVE,
                  "sbx_since": _now().isoformat(), "cert": cert})
        self.save()
        return a

    def suspend(self, fp: str, hours: int) -> dict:
        """越界 → SBX-SUSPENDED + 限期重整（A7）。"""
        a = self.ensure(fp)
        a["status"] = ST_SBX_SUSPENDED
        a["suspended_until"] = (_now() + timedelta(hours=hours)).isoformat()
        self.save()
        return a

    def ban(self, fp: str) -> dict:
        """触法律负空间 → SBX-BANNED（A7，熔断 NCA 由调用方落）。"""
        a = self.ensure(fp)
        a["status"] = ST_SBX_BANNED
        self.save()
        return a

    def check_writable(self, fp: str) -> tuple[bool, str, str]:
        """写前闸门：返回 (可写?, 状态, 说明)。BANNED/SUSPENDED 均 fail-closed。"""
        a = self.agent(fp)
        if a is None:
            return True, ST_NS_PENDING, "新指纹（未入册，走四判）"
        if a["status"] == ST_SBX_BANNED:
            return False, ST_SBX_BANNED, MSG_BANNED
        if a["status"] == ST_SBX_SUSPENDED:
            until = a.get("suspended_until") or ""
            if until and until > _now().isoformat():
                return False, ST_SBX_SUSPENDED, MSG_SUSPENDED.format(until=until)
            # 限期已过：重整回 SBX-ACTIVE（回退是状态机内迁移，⛔改链数据）
            a["status"] = ST_SBX_ACTIVE
            a["suspended_until"] = None
            self.save()
            return True, ST_SBX_ACTIVE, "限期重整届满，恢复 SBX-ACTIVE"
        return True, a["status"], "在册"

    # ---- SBX→PCM 出盒门槛（A6，参数化占位 + 读配置，⛔写死/⛔自拟映射） ----
    def promote_gate(self, fp: str, config: dict) -> dict:
        """出盒闸（本批不自动触发，仅供验证）：须过验证周期 + α 门槛（DSA-001 §3.2）。

        三读数：verified（周期）、alpha（现值是否达阈）、gate（总判定）。
        α 现值只读 TDCA_TRISPACE_ALPHA；未置=采值未定 ⇒ gate=HELD（占位，不判 FAIL）。
        """
        a = self.ensure(fp)
        if a["status"] != ST_SBX_ACTIVE:
            return {"gate": "DENIED", "reason": f"status={a['status']} 非 SBX-ACTIVE"}
        since = a.get("sbx_since")
        verified = bool(since) and (
            _now() - datetime.fromisoformat(since) >= timedelta(days=config["verify_days"]))
        alpha_raw = config["alpha"]
        if alpha_raw == "":
            alpha = None            # 采值未定（制度占位），⛔机算
        else:
            try:
                alpha = float(alpha_raw)
            except ValueError:
                alpha = None
        alpha_ok = None if alpha is None else alpha > config["alpha_threshold"]
        gate = ("PASS" if verified and alpha_ok is True else
                "HELD" if alpha is None else "DENIED")
        return {"gate": gate, "verified_period": verified,
                "verify_days": config["verify_days"],
                "alpha": alpha, "alpha_threshold": config["alpha_threshold"],
                "human_signature_required": False,
                "note": "PCM 段 Human-Signature 一律 Not-Required，保留人类熔断位"}


# ---------------- 限流（A5，参数可配） ----------------

class RateLimiter:
    """滑动窗口：每指纹 per/min + 全局 glob/min；超限零消耗拒绝。"""

    def __init__(self, config: dict):
        self.per = config["rate_per_minute"]
        self.glob = config["rate_global_per_minute"]
        self._hits: dict[str, list] = {}
        self._global: list = []

    def _sweep(self, lst: list, window_sec: int = 60) -> list:
        cut = _now().timestamp() - window_sec
        return [t for t in lst if t > cut]

    def allow(self, fp: str) -> tuple[bool, str]:
        now = _now().timestamp()
        self._global = self._sweep(self._global)
        mine = self._sweep(self._hits.get(fp, []))
        self._hits[fp] = mine
        if len(self._global) >= self.glob or len(mine) >= self.per:
            return False, MSG_RATE_LIMITED.format(per=self.per, glob=self.glob)
        self._global.append(now)
        self._hits[fp].append(now)
        return True, ""


# ---------------- 链声明件（A8 分链登记） ----------------

def ensure_chain_declaration(evidence_dir: Path) -> Path:
    """分链登记件：CHAIN-DECLARATION.yaml（每次启动确保在册，内容不变则不重写）。"""
    p = Path(evidence_dir) / "CHAIN-DECLARATION.yaml"
    body = (
        "# TDCA-MCP-CHAIN-001 分链登记（TRISPACE-001 A8）\n"
        f"chain_ref: {CHAIN_REF}\n"
        "relation: 分链登记（独立于主账 NCA-REGISTRY；写主账触令面 N4，衔接选项被排除）\n"
        "continuity: 本链内 prev_nca 逐件连续（Post-State.Hash 链式引用）\n"
        "cross_ref: 跨段引用一律走 chain_ref 字段（每件存证携带）\n"
        "append_only: true（⛔删改既有 MCP 链数据）\n"
        "data_provenance: simulated（制度演示态，ID92）\n"
    )
    if not p.is_file() or p.read_text(encoding="utf-8") != body:
        p.write_text(body, encoding="utf-8")
    return p
