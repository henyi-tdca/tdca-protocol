# TDCA 测试云部署包（deploy/）

> 指令：GSEQ-0642 / TDCA-HANDOFF-KIMI-DEPLOY-SCRIPT-001 ｜ 定位：未备案测试实例一键部署，不对外正式宣称。

## 一键部署（3 条命令）

```bash
apt update && apt install -y git
git clone --depth 1 https://gitee.com/siweihanshuzhineng_0/tdca-protocol.git /root/tdca \
  || git clone --depth 1 https://github.com/henyi-tdca/tdca-protocol.git /root/tdca
cd /root/tdca && bash deploy/install.sh
```

## 架构（单机 Compose 编排）

| 服务 | 镜像 | 职责 |
|---|---|---|
| `nginx` | nginx:alpine | 8080 → 门户静态 + `/api/` 反代 gateway + `/mcp/` 反代 bridge |
| `gateway` | Dockerfile.gateway | FROZEN 封板包（tdca-web-deploy，审查四层 PASS）原样入镜像：FastAPI 全周期 API（W0-W5 流程脚本 / NL 意图 `/api/v1/intent` / 存证账本 / 鉴权 / db sqlite 内置种子） |
| `mcp-bridge` | Dockerfile.mcp | 仓内 `tools/mcp_bridge`（stdio JSON-RPC）+ HTTP shim（`deploy/mcp/shim.py`），门户 MCP 实测用，存证落 docker 卷 |

## 三栏门户（deploy/portal/）接真实后端

- 人类栏：NL 意图导航 → `/api/v1/intent`（规则表引擎，real 水印，零模型调用）
- 大模型栏：agent.json 规格 + MCP 实测按钮 → `/mcp/call`（真实桥调用，自动落 NCA + NSFL 预检）
- 哨兵视图：`/api/v1/tax/nca-history` 30s 实时轮询

## 纪律

- LLM key（DeepSeek/Moonshot）仅在运行前以环境变量注入：`DEEPSEEK_API_KEY=... bash deploy/install.sh`，不落盘、不写文件、可选（NL 意图/哨兵/MCP 三条真实链路不依赖 LLM key）
- 数据性质标注：real / simulated 双标在位（ID92）
- NSFL 熔断全程（MCP 调用预检 + 网关负空间）
- 未备案测试实例：IP 直连，不绑域名，不对外正式宣称

## 安全基线（部署后恢复）

```bash
rm -f /etc/ssh/sshd_config.d/00-tdca.conf; usermod -p '*' root; systemctl restart ssh; echo HARDENED
```
