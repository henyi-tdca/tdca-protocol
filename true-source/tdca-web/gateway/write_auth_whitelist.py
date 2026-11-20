# -*- coding: utf-8 -*-
"""
AUTHFOUR-001（D-2/D-3/D-4）＋ GATEEXPAND-002 写鉴权白名单——逐端点登记，
⛔禁整族通配。比对键（GATEEXPAND-002 三列化）：文件前缀＋method＋全路径
——五文件重名实证：agent_channel_ops／authorization_ops／ownership_ops／
toolshelf_ops 各持 "/register"，api_v1 持 "/auth/register"，无文件前缀
无法区分。

语义：清单内端点维持既有手写鉴权现状、零行为变更（UNIFYAUTH-001 步三；
闸门见 tools/ci_write_auth_gate.py，未挂 require_write_privilege 之写端点
必须命中本清单，否则阻断）。登记列：文件前缀／端点全路径／用途／加入理由。

档别（依 -441 映射表，2026-11-18 在册；GATEEXPAND-002 于 2026-11-20 增补
api_v1.py 十件，逐件定档见回报 -481）：
  E 组 S-UA2 反例①（3）：本人或 founder 双闸／含 founder-例 external，四档无一可挂；
  F 组 S-UA2 反例②（14）：仅本人、⛔任何角色例外，须单立 W_OWNER 档（待裁，现维持手写）；
  D-3（G-68）1 件：join_ops /review 双凭证 reviewer_gate（TDCA-SES∈{founder,operator}
      或 TDCA-CRT 令牌＋x-tdca-reviewer 人类标识头）；
  D-4（G-69）1 件：fuse_bcast_ops /trigger/sync 机间 HMAC 签名触发。
  勘误增补（2，-469 报备，⛔令面外自加，系 -441 登记与现码不符之维持现状归口）：
      classify（引擎写口无鉴权，四档化即加鉴权＝行为变更）、
      register_agent（条件会话：注册开关＋ANCHOR/GUEST 分流，GUEST 匿名路挂 login
      档即破既有行为）。
  api_v1 十件（GATEEXPAND-002）：六件四档可挂者已挂统一依赖（genie/compute、
      me/sessions/revoke、me/sessions/revoke-all、me/password 挂 login 档；
      auth/identity-annotation 挂 founder 档；me/anchor/verify 挂 operator 档）；
      余十件四档无一可挂（或挂即行为变更未授），逐条理由见下。
SPDX-License-Identifier: TDCA-Internal
"""

# (文件前缀, method, path, 用途, 加入理由) —— path 为全路径（含前缀）
WHITELIST = [
    # ── E 组·S-UA2 反例①「本人或 founder」（3）──
    ("agent_channel_deposit_ops", "POST", "/api/v1/agent-channel/{reg_no}/deposit-actions",
     "保证金冻结/退还（本人或 founder）与没收（founder 独有）双动作双闸",
     "E 组 S-UA2：函数内双分支双闸含 founder-例 external，四档无一可挂（-441 #51）"),
    ("workbuddy_ops", "POST", "/api/v1/workbuddy/workflow/create",
     "工作流创建（幂等重建语义，创建人或其 founder 可建）",
     "E 组 S-UA2：owner-or-founder 且含幂等重建语义，四档无一可挂（-441 #52）"),
    ("workbuddy_ops", "POST", "/api/v1/workbuddy/workflow/execute",
     "工作流执行（仅创建人或 founder 可执行）",
     "E 组 S-UA2：owner-or-operator 语义，四档无一可挂（-441 #53）"),

    # ── F 组·S-UA2 反例②「仅本人、⛔任何角色例外」（14，待立 W_OWNER 档，现维持手写）──
    ("agent_channel_deposit_ops", "POST", "/api/v1/agent-channel/{reg_no}/deposits",
     "保证金缴纳（通道主体本人）",
     "F 组 S-UA2：仅本人无角色例外，四档无 W_OWNER 档（-441 #54）"),
    ("agent_channel_insurance_ops", "POST", "/api/v1/agent-channel/{reg_no}/insurance-policies",
     "保险单登记（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #55）"),
    ("agent_channel_insurance_ops", "POST", "/api/v1/agent-channel/{reg_no}/promotion",
     "保险晋级（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #56）"),
    ("agent_channel_insurance_ops", "POST", "/api/v1/agent-channel/{reg_no}/claims",
     "理赔申请（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #57）"),
    ("agent_channel_promo_ops", "POST", "/api/v1/agent-channel/{reg_no}/promotion-token",
     "晋级令牌签发（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #58）"),
    ("agent_channel_promo_ops", "POST", "/api/v1/agent-channel/{reg_no}/promotion-token/{token_no}/revoke",
     "晋级令牌吊销（通道主体本人）",
     "F 组 S-UA2：仅本人（-441 #59）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/{reg_no}/credentials",
     "凭证签发（主体本人＋前置步骤核验 _require_prior_steps）",
     "F 组 S-UA2：仅本人（-441 #60）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/protocol-load",
     "协议装载（_subject_gate：会话→总闸→主体本人）",
     "F 组 S-UA2：主体本人（-441 #61）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/token",
     "令牌管理（_subject_gate 同上＋前置步骤）",
     "F 组 S-UA2：主体本人（-441 #62）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/ns-review",
     "命名空间复核（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #63）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/sandbox",
     "沙盒验证（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #64）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/{reg_no}/grants",
     "授权签发（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #65）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/{reg_no}/grants/{grant_no}/revoke",
     "授权吊销（_subject_gate 同上）",
     "F 组 S-UA2：仅本人（-441 #66）"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/execute",
     "通道执行（_subject_gate 同上）",
     "F 组 S-UA2：主体本人（-441 #67）"),

    # ── D-3（G-68）双凭证复核门 ──
    ("join_ops", "POST", "/api/site/join/review",
     "加入申请复核（reviewer_gate：TDCA-SES∈{founder,operator} 或 TDCA-CRT 令牌"
     "＋x-tdca-reviewer 人类标识头）",
     "D-3：双凭证体系挂四档任一档即丢 CRT 分支＝降级，维持手写（-441 #68）"),

    # ── D-4（G-69）机间 HMAC 签名触发 ──
    ("fuse_bcast_ops", "POST", "/trigger/sync",
     "机间广播触发（authenticate_trigger：source_id＋nonce＋signature HMAC 签名）",
     "D-4：机间签名鉴权非人类会话写路径，维持手写（-441 #69）"),

    # ── 勘误增补（2，-469 报备：-441 登记与现码不符，维持现状归口）──
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/classifications",
     "判级事件写入（引擎判级档输入面，系统内写口，无会话鉴权）",
     "勘误：-441 #14 误登记为 W_FOUNDER；现码为引擎写口零鉴权，四档化即加鉴权＝行为变更"),
    ("agent_channel_ops", "POST", "/api/v1/agent-channel/register",
     "智能体自助登记（注册开关 TDCA_AGENT_REG_OPEN＋ANCHOR 须会话／GUEST 匿名分流）",
     "勘误：-441 #20 登记 W_LOGIN；现码条件会话，GUEST 匿名路挂 login 档即破行为"),

    # ── GATEEXPAND-002 增补：api_v1.py 十件（四档无一可挂或挂即行为变更未授，维持手写）──
    ("api_v1", "POST", "/api/v1/config-right/call",
     "配置权调用（模拟态经济计算＋税收/MOU 落库）",
     "GATEEXPAND-002：现码零鉴权（连登录都不查，函数体逐行实读）；挂任一档＝新增拦截"
     "＝改鉴权语义未授（令边界⛔）；S-UA1 型独立缺陷随回报 -481 另报智库，不在本件顺带加鉴权"),
    ("api_v1", "POST", "/api/v1/audit/nca-verify",
     "NCA 哈希校验＋在链核验",
     "GATEEXPAND-002：公开只读核验面（哈希比对＋链上查询，零状态写入），无鉴权属服务"
     "设计；挂任一档＝公开核验面破环"),
    ("api_v1", "POST", "/api/v1/sandbox/apply",
     "入盒申请（沙盒编译-核验闭环，申请落库）",
     "GATEEXPAND-002：现码登录可选（_session_username 匿名回退 sponsor_did 落申请人），"
     "挂 W_LOGIN＝收紧未授（令边界⛔改鉴权语义）"),
    ("api_v1", "POST", "/api/v1/attestation/meta",
     "元函数初始确权提交（出盒终裁，落库）",
     "GATEEXPAND-002：现码零强制鉴权（_session_username 仅作归属注入，匿名可写），"
     "挂档＝新增拦截未授"),
    ("api_v1", "POST", "/api/v1/attestation/dynamic",
     "动态确权审批（OTA 四操作，落库）",
     "GATEEXPAND-002：同上——零强制鉴权、_session_username 仅归属注入，挂档＝新增拦截未授"),
    ("api_v1", "POST", "/api/v1/auth/login",
     "登录（PBKDF2 校验→签发 TDCA-SES；失败滑动窗限流）",
     "GATEEXPAND-002：豁免面——鉴权签发口本身不能要求已鉴权（UNIFYAUTH-001 闸规#4"
     "明举之例），挂任一档＝死循环"),
    ("api_v1", "POST", "/api/v1/auth/logout",
     "登出（吊销当前会话，未命中幂等返回）",
     "GATEEXPAND-002：凭证自证型——凭 TDCA-SES 吊销自身；挂登录档会把过期/无效令牌的"
     "幂等 200 改 401＝语义变更未授"),
    ("api_v1", "POST", "/api/v1/auth/register",
     "注册即缔约（限流＋同意 fail-closed→PBKDF2 落库→存证→签发会话）",
     "GATEEXPAND-002：豁免面——注册缔约口须匿名可达（成功才签发会话），挂登录档＝死循环"),
    ("api_v1", "POST", "/api/v1/governance/huf-sign",
     "HUF 人类签批登记（落 governance_events＋nca_chain）",
     "GATEEXPAND-002：_gov_gate 含 GOVGATE-001 NCA 留痕语义（成功与拒皆落 NCA 五元），"
     "统一依赖无留痕，替换＝丢审计留痕＝行为变更未授，维持手写"),
    ("api_v1", "POST", "/api/v1/governance/emergency-fuse",
     "紧急熔断（NSFL fail-closed，事件落库）",
     "GATEEXPAND-002：同上——_gov_gate 之 GOVGATE-001 留痕语义不可由统一依赖复刻，"
     "维持手写"),
]
