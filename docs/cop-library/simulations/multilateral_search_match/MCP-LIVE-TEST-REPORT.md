# 全网撮合 · MCP 连接器真实接入实测报告

- 实测时间: 2026-08-15
- 实测目标: 让搜索比配引擎**真实经 MCP 连接器**拉取全网主体（此前只跑通本地源与优雅回退），端到端验证「思维协议驱动算力 → 正和撮合 → NCA 确权」
- 结论: **实测通过（端到端真实接入）**，并在实测中暴露两处方法论缺陷，已披露并修正

---

## 一、实测链路（全部真实执行，无桩、无回退）

```
run_networkwide.py --provider mcp
   └─ MCPProvider (providers/mcp_provider.py)
        └─ _MCPStdioClient  ← JSON-RPC over stdio (Content-Length 帧)
             └─ subprocess: business_registry_mcp_server.py
                  initialize → notifications/initialized
                  → tools/list  (暴露 list_entities)
                  → tools/call(list_entities) → 12 个真实主体
   └─ 引擎: MECE 拆需求 → 并行遍历+负空间剪枝 → 互补比配
            → 夏普利精确分成 → NCA 可信承诺确权
```

实测输出关键行：

```
[候选源] mcp:business-registry
[MCP] 连接器 'list_entities' 拉取真实主体 12 个 (全网源已接入)
[候选库] 载入 12 个主体
```

即：候选**不再是本地 8 主体或合成 200/600**，而是经 MCP 协议握手从连接器实拉的 12 个主体（BR-001~BR-012，八维能力评分 + BATNA）。

---

## 二、握手死锁根因与修复（本次实测最耗时的部分）

实测初期持续报 `OSError: [Errno 22] Invalid argument`，server 在客户端管道模式下回完 initialize 即退出。逐层排除（沙箱 / 语法 / 缩进 / server 读取阻塞）后定位到**两个叠加缺陷**：

| # | 位置 | 缺陷 | 后果 | 修复 |
|---|------|------|------|------|
| 1 | `business_registry_mcp_server.py :: _send` | 只写了 `Content-Length` 头部，**从未写消息体**（整文件重写修缩进时丢失该行） | 客户端拿到头部声明 N 字节却永远等不到正文，帧永不完整 | 补 `sys.stdout.buffer.write(data)` |
| 2 | `providers/mcp_provider.py :: _recv` | 用 `stdout.read(4096)` 猜长度读取 | 管道上 `read(N)` **阻塞到读满 N 字节**，而响应远小于 4096 → 双向阻塞 → 管道断 | 改 `_recv_frame()`：头部逐字节读到 `\r\n\r\n`，正文按 `Content-Length` **精确读满** |

补充：server `__main__` 加 try/except 打印堆栈到 stderr（此前异常被静默吞掉，是排查耗时的主因）。

**教训（可复用）**：stdio 协议实现中，凡"按长度分帧"，收发两端都不得使用固定块 `read(n)` 猜读；且子进程 stderr 必须可见，否则故障不可诊断。

---

## 三、实测结果 · A/B 对照

同一真实候选源（12 主体），仅比配策略不同：

| | A 组（默认·朴素二值覆盖） | B 组（`--strength-weight 8`） |
|---|---|---|
| 稳定联盟 | 模型坊 / 联创工场 / 通联资本（3方） | 数擎云 / 联创工场 / 创投汇 / 知产所（4方） |
| 全覆盖 8 维 | True | True |
| 联合效用 V | **210.0** | 201.9 |
| 贴边脆弱维度 | **5 个**（渠道0.55/算力0.50/数据0.55/合规0.50/IP0.50） | **2 个**（渠道0.55/模型0.50） |
| 各方 ≥ BATNA | True | True |
| 正和满意解 | 达成 TRUE（附条件） | 达成 TRUE（附条件） |
| NCA 确权 | TDCA-REASONIX-20260815-010 | TDCA-REASONIX-20260815-014 |

---

## 四、实测暴露的方法论缺陷（如实披露，不掩盖）

### 缺陷 1：二值覆盖阈值制造"名义全覆盖"

原判定 `res >= 0.5 即算覆盖`，把 **0.50 与 0.97 视为等同**。A 组因此撮合出"处处贴边"的联盟——算力仅 0.50，而全网存在算力 0.97 的边算科技却未入选；合规仅 0.50，而中证合规有 0.97。

**已修**：新增 `compute/coalition.py :: fragile_dims()`，凡某维度联盟内最强值落在 `[0.5, 0.6)` 即判**脆弱覆盖**，引擎显式打印 NSFL 负空间告警 + 全网更强替代主体，并在判定行增加 `稳健覆盖(无贴边)` 字段，正和结论降级为**附条件达成**。同时发射 `TDCA-FC-NW-NSFL` 负空间 NCA 留痕。

### 缺陷 2：效用函数 V 与稳健性正交，甚至反向（更深层，尚未修）

A 组 V=210.0 **高于** B 组 201.9，但 A 组脆弱维度是 B 组的 2.5 倍。原因在 `coalition_value`：

```
V = value_base × coverage × (0.5 + 0.5 × 互补系数)
```

`coverage` 是**二值覆盖率**（不含强度），`互补系数` 奖励"人少、重叠低"。于是 3 方贴边联盟因重叠更低而拿到更高 V。**V 完全没有度量能力强度**。

推论：**"正和满意解 = TRUE" 在当前 V 定义下不足以保证联盟稳健**。这不是参数问题，是效用函数的建模缺陷。NSFL 披露因此是必要的结构性补丁，而非装饰性告警。

**建议后续修正方向**（未擅自改动，待确认）：把强度引入 coverage，例如 `coverage = Σ_d min(1, max_strength(d)/0.8) / |need|`，使 0.50 与 0.97 在效用层就不再等价；或对脆弱维度施加 V 折扣（脆弱惩罚项）。改 V 会改变全部历史模拟的可比性，属制度级变更，需用户拍板。

---

## 五、TDCA 三机制在本次实测中的落地

| 机制 | 落地位置 | 实测证据 |
|---|---|---|
| NCA 确权 | 每原语调用即发射 | 本轮新增 MECE/MATCH/NSFL/COMMIT 多条，工作区 NCA 总数 141 → **155** |
| NSFL 熔断/负空间 | 剪枝（无贡献主体）+ 新增脆弱覆盖告警 | 剪枝 12→12；告警拦下"名义全覆盖"误判 |
| MOU 正和底线 | 各方分得 ≥ BATNA 校验 | A/B 两组全部 ✓满意，无一方低于保留效用 |

---

## 六、可复现命令

```bash
PY="C:/Users/22850/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
cd .../simulations/multilateral_search_match

# A 组: 真实 MCP 源 + 默认比配
$PY run_networkwide.py --provider mcp --out SEARCH-MATCH-MCP-LIVE.md

# B 组: 真实 MCP 源 + 强度加权比配
$PY run_networkwide.py --provider mcp --strength-weight 8 --out SEARCH-MATCH-MCP-LIVE-SW.md
```

配置：`config/sources.yaml`（`active: mcp`，含 server_command / server_args）
连接器注册：`~/.workbuddy/mcp.json` → `mcpServers.business-registry`

---

## 七、待办

1. **效用函数 V 是否引入强度** —— 制度级变更，待用户拍板（见缺陷 2）
2. 真实外部数据源替换演示 ENTITIES（当前 12 主体为演示注册库；换成企业库/工商 API 只需改 server 的 `_list_entities` 实现，引擎与客户端零改动）
3. 多连接器并联（同时接多个 business_registry 类源，做跨源去重与冲突消解）
