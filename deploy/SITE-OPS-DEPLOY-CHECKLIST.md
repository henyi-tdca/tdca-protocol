# TDCA 站点部署核对清单（期一 · 运维侧）

> 用途：每次站点部署（新端点／网关改动／dist 发布／nginx 变更）逐项照勾。
> 口径：只增不改；挂账项如实登记，⛔ 不自行越界。
> 部署一律使用 `deploy/docker-compose.station-20261103.yml`；⛔ 不得使用 `deploy/docker-compose.yml`（已停用）；⛔ 不得裸执行 `docker compose up`（默认读旧件）。
> 生效：自合并进 main 起对执行侧有约束力；每例事故后增补，⛔ 各案再摸索。

## 〇、操作指引族正文源（照在册）

- 操作指引族正文以仓内 `docs/ops-guides/` 为单一事实源；站机宿主 `/root/tdca/docs/ops-guides/` 为其运行副本，单向同步：仓 → 站机。改正文须改仓并走 PR，⛔ 只改站机。
- 新增一件须四步齐：入仓 → 放站机宿主 → 后端白名单加件名（逐字） → 冒烟 `count` 与单件 `200`；白名单缺则件在亦不可见。

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
- [ ] **挂载件覆盖前必 diff**：`app.py.mounted` 等挂载单文件含仓内没有的本地接线
      （如 `/api/site` 挂载块——2026-10-04 曾因整文件覆盖致站点面 40 分钟不可达）。
      同步覆盖前先 `diff 仓内件 挂载件`，本地差异段原样保留、新改动只叠加不替换；
      覆盖后回读挂载引入的关键路由（站点面端点须 200）方可视为完成。

## 二、前端 dist 发布（必勾）

- [ ] 替换 dist 用**目录内换内容**（备份后解压回同一目录），⛔ 不 `mv dist dist.bak && mkdir dist`
      （目录换新＝新 inode，bind mount 仍指旧目录，nginx 继续 serve 旧版）。
- [ ] **dist 发布一律经 `deploy/publish_dist_safe.sh`**（或严格同口径手工）：`downloads/` **只增、不删、不覆盖**
      （同名不覆盖——迭代＝重新打包新包名；2026-11-06 事故根因＝整目录替换清空 downloads）。
- [ ] 发布后核对：`downloads` **件数发布前后各记一次（应不减）**＋全部 `.zip` 经站点面直链 `200` 抽核
      （脚本自动报数；手工则 `find dist/downloads -maxdepth 1 -type f | wc -l` 与逐条 `curl -sk -o /dev/null -w '%{http_code}'`）。
- [ ] 打包产物版本留存：发布前 `backups/downloads-backup-<名>-<时间>.tgz` 与 `dist-backup-<名>-<时间>` 已建
      （⛔ 入仓 ⛔ 入 `docs/`，只留站机＋回退点）。
- [ ] 发布后核对：nginx 容器内 `grep` 新包 hash 与页面标记词；入口 `index.html` 引用新 js。
- [ ] 提示创始人 **Ctrl+F5**（index.html 为 no-cache，但 js/css 按 hash 缓存）。
- [ ] **dist ≠ 部署全貌（容器外件补灌纪律，2026-11-22 ENCNAME-002 / -545 起）**：dist 只含前端制品；
      文档实物（`/root/tdca/docs/<族>` ro 目录挂载）与网关代码挂载源
      （`/root/tdca-site/gateway-channel-cc0c5fd` 等）**不在 dist 内**。
      凡变更触及文档内容／README 固化值／白名单／公开清单者，dist 绿灯后**必须另行补灌容器外件**
      （docs 族 rsync 原位灌入＋网关码挂载源换发＋`docker compose restart gateway`，均先备份），
      并以站面直核收口（新名 200 且 sha 对固化值／旧名走向 404／README 固化值生效），
      ⛔ 凭 dist diff 干净即报完成。

## 三、变更执行方式（必勾）

- [ ] 嵌套 heredoc 经 ssh 会吞输出/错乱——一律 **scp 脚本文件 + `docker cp` + `docker exec python`**。
- [ ] 单文件挂载（app.py.mounted / default.conf / .htpasswd）改动一律保 inode；目录挂载可原位换内容。
- [ ] 站前置 basic auth 口令**永不复述、永不改动**；回报只报「维持不动／位置／权限」。

## 四、纪律（照在册）

- [ ] 合并/部署必等创始人逐字放行；PR 改动面与回报数字逐字吻合（文件数/增删行）。
- [ ] 件内与回报：零凭据值、零人名、零内部编号词面。
- [ ] 权限变更（角色提升、直连库改权限）须先呈请创始人，⛔ 不做先斩后奏。
- [ ] 回写仓内副本须**逐行对账**：线上实际配置与仓内副本逐行 diff，逐行标「一致」或「功能等价（注明差在何处）」；**「功能等价」不算通过**——须把差异点写进当次回报，并附差异清单件号。

## 五、bind mount 换件五例（照在册 · 2026-11-21 CANON-SLASH-001 T-4 · 2026-11-22 ENCNAME-002 补例四 · 2026-11-23 FAMNAME-011 补例五 · 2026-11-24 DUALCH-021 补例六·例七）

> 三例并列，今后同类⛔各案再摸索。总判据：**bind mount 在容器启动时解析目标 inode**——
> 单文件按文件 inode 钉住；目录按目录 inode 钉住（目录内换内容可见，整目录替换不可见）。

- [ ] **例一（-508）nginx 单文件挂载**（`default.conf` 等 `/etc/nginx/conf.d/*`：ro 单文件）：
      判据——编辑器/重命名落新 inode，容器内仍见旧内容，改「成功」却不生效；
      做法——**保 inode 原位写入**（`cat > 目标` 同路径覆写，⛔ mv 新件顶上），
      随后 `docker exec deploy-nginx-1 nginx -t` 过再 reload/restart，抽核行为读数。
- [ ] **例二（-513）gateway 代码目录挂载**（`/root/tdca-site/gateway-channel-cc0c5fd` ↔ 容器 `/app/tdca-web/gateway`）：
      判据——目录挂载随宿主机文件即时可见，但 Python 已加载旧码内存；
      做法——备份（`.bak-<令号>-predeploy-日期`）→ 换码 → `docker compose restart gateway`
      → 端点抽验（连通＋版本读数）再报部署时刻。
- [ ] **例三（-517）dist 目录整换**（`/root/tdca-site/dist` ↔ 容器 `/usr/share/tdca-site`：ro 目录）：
      判据——`mv dist dist-old && mv distnew dist` 后挂载仍指 dist-old 的 inode：
      表面换成功、实际在役旧件（本轮首包即中此坑，靠 chunk 404 抽核发现）；
      做法——**一律 `rsync -a --delete 新件/ dist/` 原位灌入**（目录 inode 不变、即时生效、
      ⛔ restart）；若已 mv 换目录，必须 `docker restart deploy-nginx-1` 重挂，
      并以新 chunk 名抽核 200 才算发布成功。
- [ ] **例四（-545）dist 外四件漏灌**（ENCNAME-002）：dist 发布绿灯、diff 干净，
      站面直核却旧名仍 200、README 固化值仍旧——根因文档实物与网关码在容器 ro 挂载宿主件，
      dist 本就不含此四件（文档族目录＋网关码双挂载源）；
      做法——凡触文档／白名单／公开清单之批，发布清单除 dist 外**必须列容器外件**：
      docs 族 rsync 原位灌入＋网关码挂载源换发＋网关容器重启（例二口径，均先备份），
      站面直核作收口（新名 200 且 sha 对固化值／旧名走向 404／README 固化值生效）。

- [ ] **例五（-553）容器内写 ro 挂载报 Read-only**（FAMNAME-011）：网关码挂载
      `Mode:"ro"`（`docker inspect` 可见）——容器内 `cp` 换发直接 `Read-only file system`
      失败（`set -eu` 下部署脚本中断，但**已执行的宿主侧步骤不回滚**，须防半态）；
      做法——ro bind 挂载件一律**宿主机通道目录原位换发**（`/root/tdca-site/gateway-channel-*`），
      ⛔容器内写；换发后必查「容器内 md5＝新值＋服务进程重启加载」（`docker restart`＋
      `docker exec md5sum`），站面直核收口。备份双份：通道目录内 `.bak-<批次>-<时间戳>`
      ＋宿主 `/root/` 旁存（`docker cp` 取出）。

- [ ] **例六（-556）scp 直覆通道目录致伪备份**（DUALCH-021）：`scp 源 宿主:通道目录/同名件`
      落盘即覆 live 件——事后 `cp live .bak` 备的是**新件**，旧版回滚点丢失（本轮初备
      `app.py.bak` 与 live 同 md5，回滚形同虚设）；
      做法——通道目录换发**先备后传**：`ssh 宿主 'cp 通道/件 通道/件.bak-<批次>-<ts>'`（先取旧件）
      **再** `scp` 新件，双证（宿主 md5＋容器内 md5）；若已直覆，旧件从 git 对应头
      `git show <sha>:<path>` 补立 `.bak-<批次>-predeploy-<ts>` 并验 md5 与线上在役版本一致，
      伪备份即删。教训锚点：2026-11-24 网关 `app.py` 换发（-556 §七留痕）。

- [ ] **例七（-556）nginx `/api/v1/` 前缀白名单「仓站双份，缺一即 404」**（DUALCH-021）：
      站面 nginx 对 `/api/v1/*` 走**显式前缀白名单正则**（`location ~ ^/api/(v1/(…|selfcheck|kg)|…)`），
      新增网关端点若只挂路由、不改白名单 ⟹ 请求在 **nginx 层即 404**（体为 `{"error":"NOT_FOUND"}`，
      ⛔网关错误格式，可据此判层），网关路由注册得再对也到不了；
      且白名单是**双份实物**——站机在役 `/root/tdca-site/nginx/default.conf`（ro 挂载入容器）
      ＋仓内 `deploy/nginx/default.conf`，**必须同批改**（站机先换发 reload＋`nginx -t`，
      仓内随批提交，⛔只改一份）；
      做法——新增 `/api/v1/<前缀>` 端点的发布清单固定三项：① 网关路由＋机验（pytest 端点图
      门禁会拦未登记者，见 -556 首跑 3449/1 实证）；② **站机 nginx 白名单换发**（备份
      `.bak-<批次>-<ts>`→sed 加前缀→`docker exec deploy-nginx-1 nginx -t`→restart→本机
      `curl -H "Host: …" https://127.0.0.1/<新端点>` 验 200）；③ **仓内 default.conf 同步提交**，
      站面直核收口（外网 200＋响应为网关格式非 `{"error":"NOT_FOUND"}`）。

## 挂账

- 自动 CI 门禁待白名单（期一后半再补）；GitHub 端账号冻结已解除（2026-11 更正），镜像端＝AtomGit＋Gitee＋GitHub 三端，GitHub 同步照 align-tree 法（树同头不同属）。
- dist 备份（`dist.bak-*`）累积未清理，待创始人示下。
