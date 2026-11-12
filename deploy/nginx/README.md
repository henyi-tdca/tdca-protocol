# deploy/nginx — nginx brotli 构建出处（BACKLOG-001 件3）

## 内容

- `Dockerfile.nginx-brotli`：多段构建。第一段拉 nginx-1.31.7 源码 + `google/ngx_brotli`（含子模块），`--with-compat --add-dynamic-module` 编译出 `ngx_http_brotli_filter_module.so` 与 `ngx_http_brotli_static_module.so`；第二段以同版基础像承载，装 `brotli` 运行时库，`COPY` 两模块至 `/usr/lib/nginx/modules/`，并以 `sed` 在 `nginx.conf` 首行注入两行 `load_module`（先 filter 后 static）。

## 版本锚点

- 基础像：`nginx:1.31.7-alpine`（构建段与运行段同版）。
- 模块：`google/ngx_brotli`（main，--depth=1 --recurse-submodules）。
- `load_module` 注入位置：`/etc/nginx/nginx.conf` 第 1 行（`1i`）。

## 旧像说明（一行）

生产环境此前冻结的 frozen-1009 旧像未载 brotli 模块，本 Dockerfile 为现行在架 brotli 像的构建出处，留档备重建。

## 边界

本目录只落构建出处与说明，⛔ 不含站机绝对路径、凭据；⛔ 构建脚本/CI 不在本件范围（触发重建须创始人明示）。
