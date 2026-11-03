# 挂载登记片段 · MOUNT-LEDGER-20261103（现行生效 9 条如实立账）

> 件号：`TDCA-MOUNT-LEDGER-20261103` ｜ 版本：`V1.0` ｜ 日期：`2026-11-03`（+08）
> 会话框：`L1-SI-192` ｜ 依据令：`TDCA-HANDOFF-EXEC-L1SI192-MOUNTREG-001`（步 1：现行生效 9 条如实立账·立新不改旧）
> 性质：⚠️ 内部件 · ⛔ 非对外 ｜ 本片段为**账**，**⛔ 为运行配置**（运行时不读它）

---

## 一、登记本体：现行生效 9 条挂载（逐条照录·一行一条）

取证对象：`deploy-gateway-1`（站机 47.76.42.139）
取证命令（原文）：

```
docker inspect deploy-gateway-1 --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Mode}}){{println}}{{end}}'
```

取证时点：2026-11-03 18:47（+08）

1. `/root/tdca-site/gateway -> /app/tdca-site/gateway (ro)`
2. `/var/lib/docker/volumes/deploy_tdca-db/_data -> /data (rw)`
3. `/root/tdca/docs/help -> /docs/help (ro)`
4. `/root/tdca-site/gateway-channel-cc0c5fd -> /app/tdca-web/gateway (ro)`
5. `/root/tdca-site/ops-files -> /var/lib/tdca-ops-files (ro)`
6. `/root/tdca/docs/cop-library -> /docs/cop-library (ro)`
7. `/root/tdca/docs/regulations -> /docs/regulations (ro)`
8. `/root/tdca/docs/whitepapers -> /docs/whitepapers (ro)`
9. `/root/tdca/docs/papers -> /docs/papers (ro)`

其中 docs 相关 5 条（第 3、6、7、8、9 条）。

**以站机实况为准；本片段为登记，⛔ 为运行配置。**

## 二、附加一行（据 -022 回报照录）

容器 `deploy-gateway-1` 创建时点 `2026-11-02T08:40:07Z` 晚于 override `mtime 2026-10-16 06:10` ⟹ 现行 5 条系在册之外注入、**无 git 留痕**（据报照录，见 EXEC-DAILY-OPS-20261103-022）。

## 三、补充取证（同次只读·令面「必附三项」之外新增，供对账）

- 容器 compose 标签实测：`com.docker.compose.project.config_files = /root/tdca/deploy/docker-compose.yml`、`working_dir = /root/tdca/deploy` ⟹ 现行 9 条系 **compose 注入**，实际使用文件为 `/root/tdca/deploy/docker-compose.yml`（mtime 2026-11-02 16:39:48 +08，2,176 B，内含全部 5 条 docs 挂载行）。
- 漂移登记（据实测）：仓内 `deploy/docker-compose.yml` 为 2,014 B、docs 挂载仅 1 条（regulations），与站机生效版（2,176 B、5 条）**不同步**；`/root/tdca-site/tdca-site.override.yml`（mtime 2026-10-16 06:10）亦只含 1 条 docs 挂载。⟹ §二「在册之外注入」一句，精确化为：**注入源是站机 `/root/tdca/deploy/docker-compose.yml`，其内容未回写仓内同名件**。

## 四、边界

- ⛔ 本片段不改任何现有 compose／override／nsfl／nginx 配置；⛔ 不重启、⛔ 不部署。
- ⛔ 不把本片段当运行配置引用；⛔ 不补登「应当有」而未生效的挂载。
- 旧件原样：`tdca-site.override.yml`、`freeze-pair-1009-p1.yml`、仓内 `deploy/docker-compose.yml` 均未动。

---

*执行侧 · L1-SI-192 · 2026-11-03（+08）*
