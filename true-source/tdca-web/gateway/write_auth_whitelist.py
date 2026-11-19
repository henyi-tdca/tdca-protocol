# -*- coding: utf-8 -*-
"""
AUTHFOUR-001（D-2/D-3/D-4）写鉴权白名单——逐端点三列登记，⛔禁整族通配。

语义：清单内端点维持既有手写鉴权现状、零行为变更（UNIFYAUTH-001 步三；
闸门见 tools/ci_write_auth_gate.py，未挂 require_write_privilege 之写端点
必须命中本清单，否则阻断）。登记前三列：端点全路径／用途／加入理由。

档别（依 -441 映射表，2026-11-18 在册）：
  E 组 S-UA2 反例①（3）：本人或 founder 双闸／含 founder-例 external，四档无一可挂；
  F 组 S-UA2 反例②（14）：仅本人、⛔任何角色例外，须单立 W_OWNER 档（待裁，现维持手写）；
  D-3（G-68）1 件：join_ops /review 双凭证 reviewer_gate（TDCA-SES∈{founder,operator}
      或 TDCA-CRT 令牌＋x-tdca-reviewer 人类标识头）；
  D-4（G-69）1 件：fuse_bcast_ops /trigger/sync 机间 HMAC 签名触发。
  勘误增补（2，-469 报备，⛔令面外自加，系 -441 登记与现码不符之维持现状归口）：
      classify（引擎写口无鉴权，四档化即加鉴权＝行为变更）、
      register_agent（条件会话：注册开关＋ANCHOR/GUEST 分流，GUEST 匿名路挂 login
      档即破既有行为）。
SPDX-License-Identifier: TDCA-Internal
"""

# (method, path, 用途, 加入理由) —— path 为全路径（含前缀）
WHITELIST = [
    # ── E 组·S-UA2 反例①「本人或 founder」（3）──
    ("POST", "/api/v1/agent-channel/{reg_no}/deposit-actions",
     "保证金冻结/退还（本人或 founder）与没收（founder 独有）双动作双闸",
     "E 组 S-UA2：函数内双分支双闸含 founder-例 external，四档无一可挂（-441 #51）"),
    ("POST", "/api/v1/workbuddy/workflow/create",
     "工作流创建（幂等重建语义，创建人或其 founder 可建）",
     "E 组 S-UA2：owner-or-founder 且含幂等重建语义，四档无一可挂（-441 #52）"),
    ("POST", "/api/v1/workbuddy/workflow/execute",
     "工作流执行（仅创建人或 founder 可执行）",
     "E 组 S-UA2：owner-or-founder 语义，四档无一可挂（-441 #53）"),

    # ── F 组·S-UA2 反例②「仅本人、⛔任何角色例外」（14，待立 W_OWNER 档，现维持手写）──
    ("POST", "/api/v1/agent-channel/{reg_no}/deposits",
     "保证金缴纳（通道主体本人）",
     "F 组 S-UA2：仅本人无角色例外，四档无 W_OWNER 档（-441 #54）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/insurance-policies",
     "保险单登记（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #55）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/promotion",
     "保险晋级（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #56）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/claims",
     "理赔申请（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #57）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/promotion-token",
     "晋级令牌签发（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #58）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/promotion-token/{token_no}/revoke",
     "晋级令牌吊销（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #59）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/credentials",
     "凭证签发（主体本人＋前置步骤核验 _require_prior_steps）",
     "F 组 S-UA2：仅本人（-441 #60）"),
    ("POST", "/api/v1/agent-channel/protocol-load",
     "协议装载（_subject_gate：会话→总闸→主体本人）",
     "F 组 S-UA2：主体本人（-441 #61）"),
    ("POST", "/api/v1/agent-channel/token",
     "令牌管理（_subject_gate 同上＋前置步骤）",
     "F 组 S-UA2：主体本人（-441 #62）"),
    ("POST", "/api/v1/agent-channel/ns-review",
     "命名空间复核（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #63）"),
    ("POST", "/api/v1/agent-channel/sandbox",
     "沙盒验证（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #64）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/grants",
     "授权签发（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #65）"),
    ("POST", "/api/v1/agent-channel/{reg_no}/grants/{grant_no}/revoke",
     "授权吊销（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #66）"),
    ("POST", "/api/v1/agent-channel/execute",
     "通道执行（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #67）"),

    # ── D-3（G-68）双凭证复核门 ──
    ("POST", "/api/site/join/review",
     "加入申请复核（reviewer_gate：TDCA-SES∈{founder,operator} 或 TDCA-CRT 令牌"
     "＋x-tdca-reviewer 人类标识头）",
     "D-3：双凭证体系挂四档任一档即丢 CRT 分支＝降级，维持手写（-441 #68）"),

    # ── D-4（G-69）机间 HMAC 签名触发 ──
    ("POST", "/trigger/sync",
     "机间广播触发（authenticate_trigger：source_id＋nonce＋signature HMAC 签名）",
     "D-4：机间签名鉴权非人类会话写路径，维持手写（-441 #69）"),

    # ── 勘误增补（2，-469 报备：-441 登记与现码不符，维持现状归口）──
    ("POST", "/api/v1/agent-channel/classifications",
     "判级事件写入（引擎判级档输入面，系统内写口，无会话鉴权）",
     "勘误：-441 #14 误登记为 W_FOUNDER；现码为引擎写口零鉴权，四档化即加鉴权＝行为变更"),
    ("POST", "/api/v1/agent-channel/register",
     "智能体自助登记（注册开关 TDCA_AGENT_REG_OPEN＋ANCHOR 须会话／GUEST 匿名分流）",
     "勘误：-441 #20 登记 W_LOGIN；现码条件会话，GUEST 匿名路挂 login 档即破行为"),
]
