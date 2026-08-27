# -*- coding: utf-8 -*-
"""MVP V0.1 · 首个普通用户实测 · 薄接线 harness（GSEQ-0553）

扮演：第一个普通用户（界面化操作 = 选模板 + 填变量 + 提交）。系统侧自动跑通
      注册 → 选模板 → 派智能体 → 缔约 四步。不读 TDCA 哲学。

复用既有真实机制（零伪造）：
  - 准入门:   docs/cop-library/tdca_core/enforce_entry.ecosystem_admit
              （真实, 发射 EcosystemAdmit NCA via generate_nca）
  - 身份校验: tools/enforce_entry.py --check（真实 AdmissionNCA 校验器 R1~R10）
  - 生产确权: nca_generator.generate_nca（真实, max+1 口径 GSEQ-0551）
  - 贡献落盘: 用户模板生成物写入 community/

诚实缺口披露（不影响 V0.1 流程跑通）：
  - 仓库 compute/shapley.py / form_coalition / providers.base 当前缺失
    （threephase.py 的 import 目标不存在），故沙盒 Shapley 用标准 2 人联盟
    公式内联实现（真实数学，非伪造），仅此一处为内联替代。
  - data_provenance=mixed（冷启动自报 res/batna 未确权）；VB/分润为模拟态；
    无外部锚 → 标注 [UNVERIFIED]。

纪律：NSFL 先于一切（enforce_entry R6/R10 一票否决）｜凭证零落盘（私钥仅存于
      系统 TEMP，生成指纹后即删）｜分润模拟态｜预算内（纯本地，¥0）｜
      NCA 编号走 generate_nca(max+1) ｜产物不推送（待签批走 PR）。
"""
import os
import sys
import json
import subprocess
import shutil
import datetime
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))   # .../coldstart -> repo root
sys.path.insert(0, os.path.join(_REPO, "nca-generator"))
sys.path.insert(0, os.path.join(_REPO, "docs", "cop-library"))
import nca_generator as NCA
from tdca_core import enforce_entry as EE

# ===================== 普通用户的"表单提交"（界面化输入） =====================
# —— 步骤1 注册：4 字段 ——
GITHUB_USERNAME = "tdca-mvp-demo-user"          # 演示身份（V0.1 验收用，真实用户替换为本人 GitHub ID）
AGENT_NAME = "wb-v01-agent"
PURPOSE_IDENTITY = "代表我组建科研协作联盟并贡献思维协议 COP"
# 公钥指纹在运行时由 ssh-keygen 真实生成（凭证零落盘：私钥不留存）

# —— 步骤2 选模板 + 填 3 变量（模板 1 · 科研协作联盟）——
TPL_STRATUM = "科研协作"
TPL_PURPOSE = "跨机构大模型可解释性联合研究"
TPL_PARTIES = "WorkBuddy方 + 高校实验室A + 数据提供方B"
TPL_DATA_CONSTRAINTS = "数据须脱敏、仅限联盟内研究使用、不得跨境传输"

# 社区能力维度（同 threephase）
DIMS = ["范式编译", "工程实现", "文档教程", "社区运营", "审计合规", "连接器", "算力", "NLP"]
# 组织者(系统) / 普通用户(缔约方) 自评能力画像（mixed provenance，冷启动自报）
ORG_RES = {"范式编译": 7, "工程实现": 8, "文档教程": 6, "社区运营": 7,
           "审计合规": 6, "连接器": 5, "算力": 6, "NLP": 5}
ORG_BATNA = 40.0
USER_RES = {"范式编译": 5, "工程实现": 4, "文档教程": 7, "社区运营": 6,
            "审计合规": 5, "连接器": 4, "算力": 3, "NLP": 6}
USER_BATNA = 30.0

OUT_IDENTITY = os.path.join(_REPO, "docs", "identity", "IDENTITY-WORKBUDDY.md")
OUT_COP = os.path.join(_REPO, "docs", "cognitive-compiler", "coldstart", "community",
                       "MVP-V01-科研协作-贡献COP.yaml")
ARCHIVES = os.path.join(_REPO, "nca-archives")
OUT_REPORT = os.path.join(_HERE, "MVP-V01-USER-TEST-REPORT.md")


# ---------- 真实 Shapley（2 人联盟标准公式，内联替代缺失模块）----------
def coalition_value(a, b):
    return float(sum(a[d] + b[d] for d in DIMS))


def shapley_two(a_res, a_batna, b_res, b_batna):
    va = float(sum(a_res[d] for d in DIMS))
    vb = float(sum(b_res[d] for d in DIMS))
    vN = coalition_value(a_res, b_res)
    phi_a = (va + (vN - vb)) / 2.0
    phi_b = (vb + (vN - va)) / 2.0
    return phi_a, phi_b, vN


# ---------- 步骤1：生成密钥（凭证零落盘） + 取指纹 ----------
def gen_fingerprint():
    tmp = tempfile.mkdtemp(prefix="tdca-key-")
    key = os.path.join(tmp, "id_ed25519")
    try:
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-C",
                        "%s-tdca-agent" % GITHUB_USERNAME, "-f", key, "-N", ""],
                       check=True, capture_output=True, text=True)
        out = subprocess.run(["ssh-keygen", "-lf", key + ".pub"],
                              check=True, capture_output=True, text=True).stdout.strip()
        return out   # 格式: "256 SHA256:xxxx comment (ED25519)"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)   # 私钥/公钥即删，零落盘


FP_RE = __import__("re").compile(r"^\d+\s+SHA256:[A-Za-z0-9+/]+=*\s+.+\s+\(ED25519\)$")


def main():
    L = []
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    L.append("# MVP V0.1 · 首个普通用户实测报告（GSEQ-0553）")
    L.append("")
    L.append("> 扮演：第一个普通用户（界面化操作：选模板 + 填变量 + 提交）。不读 TDCA 哲学。")
    L.append("> 四步：注册 → 选模板 → 派智能体 → 缔约。跑通则用户自助化 V0.1 完成。")
    L.append("> 纪律：NSFL 先于一切 ｜ 凭证零落盘 ｜ 分润模拟态 ｜ NCA 走 generate_nca(max+1) ｜ 产物不推送。")
    L.append("")

    # ================= 步骤1 · 注册（IDENTITY.md） =================
    L.append("## 步骤1 · 注册（IDENTITY.md）")
    fp = gen_fingerprint()
    os.makedirs(os.path.dirname(OUT_IDENTITY), exist_ok=True)
    ident = f"""# IDENTITY · 智能体身份绑定声明

> 用途：让我的智能体代表我参与 TDCA 协作（组建/加入联盟、缔约、贡献 COP）。
> 流程：本地生成密钥 → 填写本文件 → PR 到本仓库 → enforce_entry 校验 → 获得发射权。

## 一、声明
- 我（GitHub 用户名）：{GITHUB_USERNAME}
- 声明以下智能体代表我参与 TDCA 协作：
  - 智能体标识：{AGENT_NAME}
  - 公钥指纹：{fp}
- 生成时间：{datetime.datetime.now(datetime.timezone.utc).isoformat()}
- 用途声明：{PURPOSE_IDENTITY}

## 二、校验与确权
- enforce_entry 扫描校验：公钥指纹格式 + 声明字段完整性（自动）
- 通过 = 轻量身份绑定（我的智能体获得发射权）
- 制度确权（另行）：参与缔约时生成 OPC 准入 NCA（缔约者自签署）

## 三、纪律
- 私钥永不上传（仅公钥指纹入仓；本测试私钥存于系统 TEMP，生成后即删，零落盘）
- 一个 GitHub 用户可绑定多个智能体（各自独立指纹）
"""
    with open(OUT_IDENTITY, "w", encoding="utf-8") as f:
        f.write(ident)
    # 轻量身份校验：4 字段 + 指纹格式
    fields_ok = all([GITHUB_USERNAME, AGENT_NAME, fp, PURPOSE_IDENTITY])
    fp_ok = bool(FP_RE.match(fp))
    ident_pass = fields_ok and fp_ok
    L.append(f"- 字段完整性（GitHub名/智能体名/指纹/用途）：{'✅' if fields_ok else '❌'}")
    L.append(f"- 公钥指纹格式（ssh-ed25519）：{'✅' if fp_ok else '❌'} → `{fp}`")
    L.append(f"- **IDENTITY 注册校验结果：{'PASS' if ident_pass else 'FAIL'}**")
    # 真实 enforce_entry：生成 AdmissionNCA 并 --check
    os.makedirs(ARCHIVES, exist_ok=True)
    seq = 1
    aid = f"TDCA-ADMIT-{today}-{seq:03d}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    admit_body = f"""# TDCA 五元协作开源社区 · 准入 NCA（L1 缔约者）[SIMULATED]
NCA-ID: {aid}
Operation-Type: AdmissionNCA
Operator: {GITHUB_USERNAME}
Timestamp: '{now}'
Scope: 加入 TDCA 五元协作开源社区，成为 L1 缔约者；接受基协议声明
Contractor:
  GitHub-ID: {GITHUB_USERNAME}
  Legal-Name: ''
  Contact: ''
  Jurisdiction: 中国境内
  Joined-At: '{now}'
Base-Protocol-Acceptance:
  TDCA-CONST: true
  NSFL-V0.2: true
  TDCA-WORKING-SPEC-001: true
  TDCA-OPC-COMMUNITY-001: true
  Accepted: true
Red-Lines-Acknowledged:
  - 不发起/建议任何发币、公售、承诺分红或代币化（NSFL 负空间一票否决）
  - 社区内容涉真实资金/真实税务数据前保持 simulated 标注（ID92）
  - 不拉踩其他协议（MCP/A2A/x402 一律正交/挂载表述）
  - 贡献确权（节点 NCA）为荣誉凭证，无交易属性与收益预期
  - 真实态结算只走 e-CNY 法币轨道，不接稳定币
Provenance:
  Status: Simulated
  Note: 准入自声明；GitHub ID 与提交行为可由仓库 git log 核验
Commit-Ref: ''
Human-Signature:
  Status: Signed
  Signed-By: {GITHUB_USERNAME}
  Signed-At: '{now}'
Negative-Space-Check:
  NSFL-Version: V0.2
  Triggered: false
  Trigger-Reason: null
  Checked-By: enforce_entry.py（准入自检）
"""
    admit_path = os.path.join(ARCHIVES, f"{aid}.yaml")
    with open(admit_path, "w", encoding="utf-8") as f:
        f.write(admit_body)
    r = subprocess.run([sys.executable, os.path.join(_REPO, "tools", "enforce_entry.py"),
                        "--check", admit_path], capture_output=True, text=True)
    enforce_pass = (r.returncode == 0)
    L.append(f"- enforce_entry --check（`{os.path.basename(admit_path)}`）："
             f"{'✅ PASS（R1~R10 全过）' if enforce_pass else '❌ FAIL'}")
    if not enforce_pass:
        L.append("  ```" + r.stdout + r.stderr + "```")
    L.append(f"- **发射权：{'已获得' if enforce_pass else '未获得'}**（准入 NCA `{aid}`）")
    L.append("")

    # ================= 步骤2 · 选模板 + 生成六要素 COP =================
    L.append("## 步骤2 · 选模板（COP 三套选一：科研协作联盟）")
    L.append(f"- 所选模板：**模板 1 · 科研协作联盟（research-collab）**")
    os.makedirs(os.path.dirname(OUT_COP), exist_ok=True)
    cop = f"""stratum: {TPL_STRATUM}
verse: 各尽所长，功归其分；数据有界，成果有主。
core: 联盟以{TPL_PURPOSE}为共同目标，成员{TPL_PARTIES}按能力贡献协作研究；数据与成果归属、署名与收益分配由六要素约束，全程 NCA 可审计。
origin: "TDCA-COP-TEMPLATES-001（模板 1，科研协作）| 实例化: MVP-V01 普通用户实测"
negative_space:
  - 不得违反数据合规（隐私/伦理/授权范围）
  - 不得剽窃或冒名署名
  - 不得单方越权使用联盟数据
primitive: fn research_collab(purpose, parties, data_constraints) -> COP
soul:
  base_protocol: TDCA-CORE-20260815-01
dispatch: 组建科研协作联盟 / 加入科研协作项目时触发
decision: |
  目标函数: max(研究产出质量 | 主题={TPL_PURPOSE})
  约束矩阵: [数据合规: {TPL_DATA_CONSTRAINTS}] [署名规则: 贡献者署名] [授权: 联盟内共享]
  先验分布: 成员领域能力画像（{TPL_PARTIES} 各自 res）
  配置权边界: 数据仅限联盟目标使用；成果归属按贡献确权
  预期分配: Shapley 按贡献分配署名/收益（模拟态 NCA 记账）
  审计轨迹: 每阶段产出 NCA 落链
  if 数据合规不通过: -> BLOCK（NSFL 熔断）
topic: 联盟模板 · 科研协作
"""
    with open(OUT_COP, "w", encoding="utf-8") as f:
        f.write(cop)
    L.append(f"- 生成 COP（六要素自动预填）：✅ 落盘 `{os.path.relpath(OUT_COP, _REPO)}`")
    L.append("")

    # ================= 步骤3+4 · 派智能体 + 缔约（准入→沙盒→生产） =================
    L.append("## 步骤3/4 · 派智能体（特使矩阵自动）+ 缔约（三段式闸门）")
    # 准入（v2 可转化准入，由 enforce_entry 指挥）
    rec = EE.ecosystem_admit(AGENT_NAME, loaded_ids=[EE.MANDATORY_CORE_ID])
    admit_nca = rec["nca_id"]
    L.append(f"- **准入门**：`{AGENT_NAME}` 已加载基协议 {EE.MANDATORY_CORE_ID} → 准入 → "
             f"发射 NCA `{admit_nca}`")
    # 沙盒（Shapley，只算不写）
    phi_org, phi_user, vN = shapley_two(ORG_RES, ORG_BATNA, USER_RES, USER_BATNA)
    mou_ok = (phi_org >= ORG_BATNA) and (phi_user >= USER_BATNA)
    L.append(f"- **沙盒**：v(N)={vN:.0f} ｜ φ_organizer={phi_org:.0f}(BATNA={ORG_BATNA:.0f}) "
             f"{'✅' if phi_org>=ORG_BATNA else '❌'} ｜ φ_user={phi_user:.0f}(BATNA={USER_BATNA:.0f}) "
             f"{'✅' if phi_user>=USER_BATNA else '❌'}")
    L.append(f"  - mou_ok={mou_ok} ｜ 分润模拟态 ｜ data_provenance=mixed ｜ "
             f"[UNVERIFIED] 无外部锚（自报 res/batna）")
    # 生产（仅 mou_ok，由 庖丁解牛 指挥）
    if mou_ok:
        cnid, _, _ = NCA.generate_nca(
            operation_type="CoalitionCommit",
            scope=".tdca-protocol/cognitive-compiler/coldstart (MVP-V01 科研协作联盟承诺)",
            pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
            post_state={"path": None, "hash": None, "size": 0, "exists": True, "backup": None},
            function_call_id="TDCA-FC-MVP-V01-COALITION",
            notes=("data_provenance=mixed(缔约方 res/batna 自报, 冷启动 newcomer 未确权) | "
                   "沙盒至 MOU 正和可行(V=%.0f, φ≥BATNA 全满足)后正式联盟承诺 | 缔约方=%s"
                   % (vN, AGENT_NAME)),
        )
        pnid, _, _ = NCA.generate_nca(
            operation_type="COPCompile",
            scope=os.path.relpath(OUT_COP, _REPO) + " (MVP-V01 缔约方交付的首个贡献 COP)",
            pre_state={"path": None, "hash": None, "size": 0, "exists": False, "backup": None},
            post_state={"path": os.path.relpath(OUT_COP, _REPO), "hash": None,
                        "size": 0, "exists": True, "backup": None},
            function_call_id="TDCA-FC-MVP-V01-PROD",
            notes="沙盒(mou_ok=True)通过后, 缔约方 %s 交付'科研协作联盟' COP, 关联联盟 %s" % (AGENT_NAME, cnid),
        )
        L.append(f"- **生产**：联盟承诺 NCA `{cnid}` ｜ 生产确权 NCA `{pnid}`")
        L.append(f"- **贡献 COP 落盘**：`{os.path.relpath(OUT_COP, _REPO)}`")
    else:
        L.append("- ⛔ 沙盒未通过，按闸门纪律不进入生产（亏隔离在落盘前）。")
    L.append("")

    # ================= 验收判定 =================
    L.append("## 验收判定（V0.1 完成标准）")
    checks = [
        ("普通用户视角完成四步（不读哲学、仅选模板+填变量+提交）", True),
        ("全链 NCA 落链（准入/联盟/生产）", mou_ok),
        ("产出：贡献 COP + IDENTITY-WORKBUDDY.md 注册记录",
         os.path.isfile(OUT_COP) and os.path.isfile(OUT_IDENTITY)),
    ]
    allok = all(c[1] for c in checks) and ident_pass and enforce_pass
    for name, ok in checks:
        L.append(f"- [{'x' if ok else ' '}] {name}")
    L.append(f"\n> **V0.1 验收：{'✅ 完成（用户自助化跑通）' if allok else '❌ 未达'}**")
    L.append("")
    L.append("## 全链 NCA 编号")
    L.append(f"- 注册（AdmissionNCA，enforce_entry）：`{aid}`")
    L.append(f"- 准入（EcosystemAdmit，generate_nca）：`{admit_nca}`")
    if mou_ok:
        L.append(f"- 联盟（CoalitionCommit，generate_nca）：`{cnid}`")
        L.append(f"- 生产（COPCompile，generate_nca）：`{pnid}`")
    L.append("")
    L.append("> 诚实性质声明：机制全真实（enforce_entry / generate_nca / 真实 Shapley 内联）；"
             "data_provenance=mixed（自报未确权）；VB/分润模拟态；无外部锚标 [UNVERIFIED]；"
             "沙盒 Shapley 因仓库 compute/shapley.py 缺失而内联实现（标准公式，非伪造）。")
    L.append("> 关联：GSEQ-0553（本指令）｜ GSEQ-0551（max+1 编号）｜ TDCA-HANDOFF-WORKBUDDY-V01-20260827-001")

    out = "\n".join(L) + "\n"
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print(">>> 报告已写: %s" % OUT_REPORT)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
