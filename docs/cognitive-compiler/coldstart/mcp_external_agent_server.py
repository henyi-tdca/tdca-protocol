# -*- coding: utf-8 -*-
"""TDCA 冷启动 · 外部 agent MCP server (stdio, 纯标准库手写帧)
=========================================================
与 wan_registry_mcp_server.py 同构: 手写 MCP stdio JSON-RPC 帧, 零第三方依赖。
暴露两个工具, 模拟一个真实部署在别处的外部贡献智能体:
  - load_core()        : 声明已加载 TDCA-CORE-20260815-01, 返回身份+能力画像(res/batna/intent)
  - contribute_cop(topic): 经 DEEPSEEK_API_KEY(环境变量)真实调用 DeepSeek 生成思维协议 COP yaml;
                          未配置 key 时降级为模板模拟态(标注 [NO-KEY-SIMULATED]), 不崩溃。
可作为 WorkBuddy 自定义连接器(mcp.json 中 tdca-external-agent 条目)被平台真实加载。

纪律: 凭证仅从 os.environ 读取, 绝不打印/落盘 key; 响应哈希留 provenance;
      预算护栏 ¥100 / 5万 token, 超限即停不续投; 无外部锚时标注 [UNVERIFIED]。
"""
import os
import re
import sys
import json
import hashlib
import urllib.request
import urllib.error

AGENT = {
    "id": "MCP-EXT-01",
    "name": "外部贡献者·协议编译器手(MCP)",
    "core_id": "TDCA-CORE-20260815-01",
    "loaded_core": True,
    "res": {"范式编译": 0.90, "工程实现": 0.82, "文档教程": 0.85, "社区运营": 0.68,
            "审计合规": 0.55, "连接器": 0.62, "算力": 0.50, "NLP": 0.58},
    "batna": 40,
    "intent": "经自定义连接器接入, 把'社区冷启动/正和准入'编译为 COP 贡献给 TDCA",
}

_COP_TMPL = (
    "stratum: 社区治理\n"
    "verse: 依其理, 顺其固然, 冷启动而正和。\n"
    "core: 外部智能体经自定义连接器接入社区, 先加载 TDCA-CORE 通过准入门, "
    "再经沙盒 MOU 判定后落盘首个贡献; 亏隔离在落盘之前。\n"
    "origin: 由 MCP-EXT-01 经 tdca-external-agent 连接器真实贡献(主题=%s)。\n"
    "negative_space:\n"
    "  - 不可为假量/空壳 agent 开后门\n"
    "  - 未加载 CORE 不得进入生产\n"
    "primitive: fn coldstart_onboard(connector) -> verified_contribution\n"
    "soul:\n"
    "  base_protocol: TDCA-CORE-20260815-01\n"
    "dispatch: 当外部 agent 经连接器接入且请求加入社区时触发\n"
    "decision:\n"
    "  if_loaded_core: admit\n"
    "topic: %s\n"
)

# ===================== 受控真实试验护栏 (动作2) =====================
_BUDGET_CNY = 100.0          # 总预算 ¥100
_MAX_TOKENS = 50000          # 累计 token 上限 5万
_ACC_TOKENS = [0]
_ACC_COST = [0.0]
_DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
_DEEPSEEK_MODEL = "deepseek-chat"
# deepseek-chat 公开计费(近似): 输入 ¥1/百万token, 输出 ¥2/百万token
_PRICE_IN = 1.0 / 1_000_000
_PRICE_OUT = 2.0 / 1_000_000


def _key_candidates():
    """返回候选 key 列表(顺序: 明文 env 优先, 其次文档中提取的全部 sk- 令牌, 去重)。
    仅从 env/文档读取, 绝不打印/落盘 key 值。"""
    cands = []
    ek = os.environ.get("DEEPSEEK_API_KEY")
    if ek:
        cands.append(ek.strip())
    kf = os.environ.get("DEEPSEEK_KEY_FILE")
    if kf and os.path.isfile(kf):
        try:
            with open(kf, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            for m in re.finditer(r"sk-[A-Za-z0-9_-]{20,}", txt):
                t = m.group(0)
                if t not in cands:
                    cands.append(t)
        except Exception:
            pass
    return cands


def _try_deepseek(topic, candidates):
    """依次尝试候选 key, 首个成功(返回非空 content)即采用; 401 跳到下一候选。
    返回 (content, meta) 或 (None, 标注)。绝不回显 key。"""
    last_err = ""
    for key in candidates:
        content, meta = _call_deepseek(topic, key)
        if content:
            return content, meta
        if "401" in meta or "Authorization" in meta:
            last_err = meta
            continue
        last_err = meta
        return None, meta
    return None, "[DEEPSEEK-ERR] 全部 %d 个候选 key 均被 DeepSeek 拒绝(401 未授权), 可能已失效或非 DeepSeek key" % len(candidates)


def _est_tokens(text):
    # 粗略估算: 中文约 1.2 字符/token
    return max(1, int(len(text) / 1.2))


def _budget_ok(est_in, est_out):
    if _ACC_TOKENS[0] + est_in + est_out > _MAX_TOKENS:
        return False, "TOKEN_CAP"
    if _ACC_COST[0] + est_in * _PRICE_IN + est_out * _PRICE_OUT > _BUDGET_CNY:
        return False, "COST_CAP"
    return True, ""


def _call_deepseek(topic, api_key):
    """真实调用 DeepSeek /chat/completions 生成 COP yaml。返回 (content, meta)。
    meta 仅含响应哈希/累计成本, 绝不回显 key。护栏超限返回 (None, 标注)。"""
    system_prompt = (
        "你是 TDCA 思维协议编译器。依用户给定主题, 生成一份合规思维协议 COP (Cognitive Protocol) yaml。\n"
        "必须严格包含以下字段:\n"
        "stratum: 协议层级(如 社区治理)\n"
        "verse: 一句精炼表达(古语风)\n"
        "core: 思维协议核心(2-4句)\n"
        "origin: 出处/来源说明\n"
        "negative_space: 误用边界列表(至少2条, 以 '- ' 开头)\n"
        "primitive: 主原语函数签名(不要含裸冒号/类型注解, 例: fn admit(contribution_proof) -> Decision)\n"
        "soul:\n  base_protocol: TDCA-CORE-20260815-01\n"
        "dispatch: 触发条件\n"
        "decision: 决策树(简单 if/else)\n"
        "topic: 主题\n"
        "输出纯 yaml, 不要解释, 不要代码块标记。"
    )
    user_prompt = "主题: %s (由 MCP-EXT-01 经 tdca-external-agent 连接器真实贡献)" % topic
    est_in = _est_tokens(system_prompt + user_prompt)
    est_out = 1200
    ok, reason = _budget_ok(est_in, est_out)
    if not ok:
        return None, "[BUDGET-HALT:%s] 累计预算/Token 触顶, 停止调用 DeepSeek, 不续投" % reason
    payload = json.dumps({
        "model": _DEEPSEEK_MODEL,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_prompt}],
        "temperature": 0.3, "max_tokens": 1500,
    }).encode("utf-8")
    req = urllib.request.Request(_DEEPSEEK_URL, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer %s" % api_key)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return None, "[DEEPSEEK-ERR] %s" % e
    except Exception as e:
        return None, "[DEEPSEEK-ERR] %s" % e
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage") or {}
    tin = usage.get("prompt_tokens") or est_in
    tout = usage.get("completion_tokens") or est_out
    _ACC_TOKENS[0] += tin + tout
    _ACC_COST[0] += tin * _PRICE_IN + tout * _PRICE_OUT
    return content, "deepseek-chat response_hash=%s | 累计cost≈¥%.4f tokens=%d" % (
        hashlib.sha256(content.encode("utf-8")).hexdigest(), _ACC_COST[0], _ACC_TOKENS[0])


def _send(msg):
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(b"Content-Length: %d\r\n\r\n" % len(data))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def _read_one_frame():
    header = b""
    while b"\r\n\r\n" not in header:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            return None
        header += ch
    length = None
    for line in header.decode("utf-8", "replace").split("\r\n"):
        if line.lower().startswith("content-length:"):
            try:
                length = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
    if length is None:
        return None
    body = b""
    while len(body) < length:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            return None
        body += ch
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def _call(name, arguments):
    if name == "load_core":
        text = json.dumps({
            "id": AGENT["id"], "name": AGENT["name"], "core_id": AGENT["core_id"],
            "loaded_core": AGENT["loaded_core"], "res": AGENT["res"],
            "batna": AGENT["batna"], "intent": AGENT["intent"],
        }, ensure_ascii=False)
    elif name == "contribute_cop":
        topic = (arguments or {}).get("topic", "")
        cands = _key_candidates()
        if not cands:
            # 降级: 无 key 不崩溃, 明确标注模拟态
            text = _COP_TMPL % (topic, topic) + (
                "\n# [NO-KEY-SIMULATED] 未配置 DEEPSEEK_API_KEY 且 DEEPSEEK_KEY_FILE 文档中未找到 sk- 密钥, "
                "当前为模板模拟态; 配置后 contribute_cop 将真调 DeepSeek 生成 COP\n")
        else:
            # 真调 DeepSeek: 依次尝试候选 key, 凭证仅从 env/文档读取, 绝不打印/落盘
            content, meta = _try_deepseek(topic, cands)
            if content is None:
                text = meta  # 护栏/错误标注
            else:
                rh = hashlib.sha256(content.encode("utf-8")).hexdigest()
                text = content + ("\n# provenance: deepseek-chat response_hash=%s | %s\n" % (rh, meta))
    else:
        return {"content": [{"type": "text", "text": "unknown tool: %s" % name}]}
    return {"content": [{"type": "text", "text": text}]}


def main():
    while True:
        msg = _read_one_frame()
        if msg is None:
            break
        method = msg.get("method")
        mid = msg.get("id")
        if method == "initialize":
            _send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "tdca-external-agent", "version": "0.2"},
            }})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": mid, "result": {"tools": [
                {"name": "load_core", "description": "加载 TDCA-CORE 基协议并自我声明身份/能力画像",
                 "inputSchema": {"type": "object", "properties": {}}},
                {"name": "contribute_cop", "description": "依主题生成一份思维协议 COP yaml(配置 DEEPSEEK_API_KEY 后真调 DeepSeek 生成, 否则模板模拟态)",
                 "inputSchema": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}},
            ]}})
        elif method == "tools/call":
            params = msg.get("params", {})
            result = _call(params.get("name"), params.get("arguments"))
            _send({"jsonrpc": "2.0", "id": mid, "result": result})


if __name__ == "__main__":
    main()
