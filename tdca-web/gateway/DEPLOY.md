# KIMI-WEB-DB-TASK-001 · M4 部署上线说明（DEPLOY）

> 编制：2026-08-21 ｜ 状态：后端生产就绪已实证；整站公开发布**有阻塞，如实披露**

---

## 一、已实证（本机活体验证 `scripts/m4_live_check.py`，ALL PASS）

| 验收 | 实测 |
|---|---|
| 服务器生产拉起 | uvicorn 0.52.4 + `scripts/serve.py`（配置全环境变量，零硬编码） |
| 五页面数据源端点活体回归 | 8 条 GET 全 200（home/tax/sandbox/notifier/academy/audit/attestation/cluster；/studio 依 F3 签批件无后端依赖） |
| 鉴权线上行为 | 带令牌写 200 / 无令牌写 401（fail-closed） |
| **重启数据不丢** | 写入 SBX-1d5bf183 → 杀进程 → 重启 → 读回存在，行数 0→1 保留 |

## 二、启动命令（部署目标机）

```bash
cd gateway
export TDCA_GATEWAY_AUTH=1            # 启用鉴权（M3）
export TDCA_GATEWAY_TOKEN=<静态降级令牌>   # 生产务必替换演示值
export TDCA_FOUNDER_PASSWORD=<口令>    # 仅首种时需要，种后移除
python -m alembic upgrade head        # 建库/迁移（幂等）
python -m db.seed                     # 种子（幂等；founder 缺口令拒种）
unset TDCA_FOUNDER_PASSWORD
python scripts/serve.py               # TDCA_HOST/TDCA_PORT 可配，默认 0.0.0.0:8000
```

依赖：Python 3.11+ / fastapi / uvicorn / sqlalchemy / alembic（+ 工作区内 11 个依赖包副本随库走）。

## 三、阻塞项（如实披露，需创始人裁定）

| # | 阻塞 | 影响 | 处置选项 |
|---|---|---|---|
| 1 | ~~前端 src 不在本机可访问位置~~ **已解决（2026-08-21）**：源码在 `AppData\Roaming\reasonix\global-workspace\tdca-frontend`，已拷入工作区 `tdca-web/tdca-frontend` 并完成接缝施工 + dist 重建 + 整站活体复验全过 | 整站一体化本机就绪 | — |
| 2 | **公开 URL 发布动作本身** | 任务书口径为「Kimi 网站部署功能」发布——该发布按钮在 Kimi 应用侧，本会话无对应工具可直接调用 | 创始人在 Kimi 侧执行发布，或指定其他托管口径（如自有服务器），我按口径出部署包 |

## 四、额度与止损

- M4 已耗在本预算线内（≤15%，累计 ≤85% 在轨）
- 发布后日扣 ~0.08% 云服务费：不需要在线时及时取消发布止损（任务书 §五）

---

> 结论：**M4 后端侧全部就绪且活体验证通过；验收①「公开 URL 可访问」卡在两个外部前提（前端源码 + 发布通道），待创始人裁定即续。**
