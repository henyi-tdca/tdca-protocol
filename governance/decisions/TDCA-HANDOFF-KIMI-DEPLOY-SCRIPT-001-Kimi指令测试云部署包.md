# TDCA-HANDOFF-KIMI-DEPLOY-SCRIPT-001 · Kimi 指令：测试云部署包（deploy/install.sh + docker-compose）

> 文档编号: TDCA-HANDOFF-KIMI-DEPLOY-SCRIPT-001 ｜ 编制: 2026-08-28（Reasonix 制度层）｜ 状态: ✅ **已下令**
> 依据: TDCA-CLOUD-DEPLOY-FIX-001（git clone 部署路径，GSEQ-0641）｜ TDCA-CLOUD-TEST-ARCH-001（架构）
> 存证: GSEQ-0642

---

## 目标

生成测试云部署包并推入仓库 `deploy/` 子目录——实例 `git clone` 后 `bash deploy/install.sh` 一键部署（**绕开 SSH/长命令传输**）。

## 交付物（deploy/ 子目录，PR 推入 tdca-protocol）

| 文件 | 内容 |
|---|---|
| `deploy/install.sh` | 一键部署：环境检查（docker/docker-compose）→ 生成 .env（DeepSeek key 从环境变量/交互输入注入，**不落盘到仓库**）→ `docker compose up -d` → 健康检查 → 输出访问 URL |
| `deploy/docker-compose.yml` | 单机编排：**nginx**（反代 80→前端、8080→API）→ **tdca-gateway**（DID/HUF 鉴权）→ **backend**（W0-W5 端点）→ **NL 全周期服务**（DeepSeek 接入）→ **data_feed**（模拟+真实流）→ **MCP bridge** → **SQLite/Postgres** |
| `deploy/Dockerfile.*` | gateway/backend/NL/data_feed/MCP 各服务构建（从现有代码打包；依赖纳入构建上下文，无需宿主机额外安装） |
| `deploy/README.md` | 部署说明（3 条命令 + 访问 URL + simulated 标注 + 安全加固提示） |

## 关键要求

1. **三栏门户接真实后端**：人类栏 NL 全周期（DeepSeek real）/ 大模型栏 MCP 实测 / 哨兵视图实时刷新
2. **simulated→real 过渡标注**（页面显示「测试体验环境」）
3. **DeepSeek key**：`install.sh` 从 `$DEEPSEEK_KEY` 环境变量或交互输入注入 `.env`（**不入仓库、不落盘 git**）；冷启动 key 保留至 v3 结束
4. **NSFL 全程 fail-closed**（测试环境同样熔断）｜ 算力熔断日 ¥2/月 ¥8 口径
5. **无敏感词** ｜ 凭证零落盘 ｜ 不备案不对外正式宣称（IP:port 测试访问）

## 回报

① deploy/ PR 链接 + merge SHA ② install.sh 用法摘要 ③ 三栏/后端接线说明 ④ NCA 存证号。

---

> 本指令为测试云部署包生成唯一执行依据；实例端仅需 3 条短命令（apt git / git clone / bash install.sh）。
> 关联: [[tdca-session-20260828]] ｜ TDCA-CLOUD-DEPLOY-FIX-001 ｜ TDCA-CLOUD-TEST-ARCH-001 ｜ 存证: GSEQ-0642
