#!/bin/bash
# TDCA 测试云一键部署（GSEQ-0642）
# 用法：git clone 仓库后，在仓库根目录执行  bash deploy/install.sh <待发dist包路径>
#       （dist 包须先过 CI 门禁产出 deploy-receipt.json 凭证，详见 deploy/deploy_gate.py）
# 纪律：DeepSeek/Moonshot key 只在运行前以环境变量注入（不落盘、不写文件）；
#       未备案测试实例，不对外正式宣称。
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== [0/4] 部署门禁（CI-GATE-001 站点机校验）=="
TDCA_DIST_TGZ="${1:-}"
if [ -z "$TDCA_DIST_TGZ" ]; then
  echo "usage: bash deploy/install.sh <待发dist包路径>（须先过 CI 门禁产出 deploy-receipt.json 凭证）"
  exit 2
fi
python3 deploy/deploy_gate.py "$TDCA_DIST_TGZ" || { echo "部署门禁拒：deploy_gate.py exit=$?，中止部署"; exit 1; }

echo "== [1/4] 环境自检 =="
docker --version
docker compose version

echo "== [2/4] 会话令牌（仅本次 shell，不落盘） =="
export TDCA_GATEWAY_TOKEN="${TDCA_GATEWAY_TOKEN:-$(openssl rand -hex 16)}"
echo "TDCA_GATEWAY_TOKEN 已生成（session-only）"

echo "== [3/4] 编排构建上线（nginx:8080 仅本机回环冒烟口 / gateway / mcp-bridge） =="
docker compose -f deploy/docker-compose.yml up -d --build
sleep 12
docker compose -f deploy/docker-compose.yml ps

echo "== [4/4] 冒烟自检 =="
curl -s -o /dev/null -w "portal(8080): %{http_code}\n" http://localhost:8080/
curl -s -o /dev/null -w "gateway(/api/v1/system/overview): %{http_code}\n" http://localhost:8080/api/v1/system/overview
curl -s http://localhost:8080/mcp/health; echo
curl -s -X POST http://localhost:8080/mcp/call -H 'Content-Type: application/json' \
  -d '{"name":"tdca:echo","arguments":{"text":"install smoke (GSEQ-0642)"}}'; echo

echo "== DONE → https://tdca.com.cn/ （公网正式面；内网调试口 8080 已收口，仅本机冒烟用 localhost:8080）=="
