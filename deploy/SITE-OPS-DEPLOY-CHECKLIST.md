# TDCA 站点部署核对清单（期一 · 运维侧）

> 用途：每次站点部署（新端点／网关改动／dist 发布／nginx 变更）逐项照勾。
> 口径：只增不改；挂账项如实登记，⛔ 不自行越界。

## 一、新 API 端点上线（必勾）

- [ ] **nginx 白名单同步**：`/root/tdca-site/nginx/default.conf` 白名单正则加入新端点组；
      漏项症状＝前端 fail-closed（站点面 404 `NOT_FOUND`），而网关直连 200。
- [ ] 白名单改动**保 inode 写入**（`cat 新文件 > 原文件`，⛔ 禁用 `sed -i` 直接改挂载单文件——
      `sed -i` 换新 inode，容器内仍见旧内容；改动后须**整容器重建**（`compose up -d --force-recreate nginx`），
      `nginx -s reload` 不足以刷新文件挂载）。
- [ ] 经站点面回读（nginx 容器内 `wget http://127.0.0.1/<新端点>`），不得只测网关直连。
- [ ] 网关新模块同时同步三处：镜像内（`/root/tdca` 源码树重建）、`/root/tdca-site/app.py.mounted`（如改 app.py）、
      `/root/tdca-site/gateway/`（如涉挂载遮蔽模块——挂载目录在 sys.path 前，会遮蔽镜像同名模块）。
- [ ] 新表建表只在容器内经 `Base.metadata.create_all`（只建缺失表，⛔ 不动既有表）。

## 二、前端 dist 发布（必勾）

- [ ] 替换 dist 用**目录内换内容**（备份后解压回同一目录），⛔ 不 `mv dist dist.bak && mkdir dist`
      （目录换新＝新 inode，bind mount 仍指旧目录，nginx 继续 serve 旧版）。
- [ ] 发布后核对：nginx 容器内 `grep` 新包 hash 与页面标记词；入口 `index.html` 引用新 js。
- [ ] 提示创始人 **Ctrl+F5**（index.html 为 no-cache，但 js/css 按 hash 缓存）。

## 三、变更执行方式（必勾）

- [ ] 嵌套 heredoc 经 ssh 会吞输出/错乱——一律 **scp 脚本文件 + `docker cp` + `docker exec python`**。
- [ ] 单文件挂载（app.py.mounted / default.conf / .htpasswd）改动一律保 inode；目录挂载可原位换内容。
- [ ] 站前置 basic auth 口令**永不复述、永不改动**；回报只报「维持不动／位置／权限」。

## 四、纪律（照在册）

- [ ] 合并/部署必等创始人逐字放行；PR 改动面与回报数字逐字吻合（文件数/增删行）。
- [ ] 件内与回报：零凭据值、零人名、零内部编号词面。
- [ ] 权限变更（角色提升、直连库改权限）须先呈请创始人，⛔ 不做先斩后奏。

## 挂账

- 自动 CI 门禁待白名单（期一后半再补）；GitHub 端账号冻结，镜像端＝AtomGit＋Gitee。
- dist 备份（`dist.bak-*`）累积未清理，待创始人示下。
