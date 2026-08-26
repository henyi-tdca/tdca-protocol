# 全网多主体正和协作 · 思维协议驱动算力搜索比配引擎（可插拔连接器版）

将"候选库"从本地 8 主体升级为**可插拔连接器**架构：候选源（本地 / MCP / 任意 Provider）热插拔，
算力层（并行遍历 + 负空间剪枝 + 夏普利精确/蒙特卡洛）可扩展。这是"全网正和撮合"从原型到生产形态的关键一步。

## 架构
```
run_networkwide.py        # 入口 (CLI: --provider local|mcp --scale N --workers W)
   │
   └─ PositiveSumMatcher   # 编排器: MECE→搜索→比配→夏普利→NCA承诺
        │
        ├─ CandidateProvider (接口, providers/base.py)
        │     ├─ LocalProvider       # 内置8范式主体 + 合成"海量"压测
        │     └─ MCPProvider         # 真实全网接入点 + 优雅回退本地
        │
        └─ compute/ (算力层, 可扩展)
              ├─ traversal.py  # 并行遍历候选库 + 负空间剪枝 (防 2^n 爆炸)
              ├─ coalition.py  # 覆盖驱动贪心比配 + 稳定校验
              └─ shapley.py    # 精确 2^n(小规模) / 蒙特卡洛(海量) 公平分成
```

## 可插拔的核心
引擎**只依赖 `CandidateProvider` 接口**（`load(dims)->List[Candidate]`），与候选来源彻底解耦。
换"全网源" = 换一个 Provider 实现，**引擎零改动**：
- `LocalProvider`：本地 YAML + 合成器（`--scale N` 模拟海量）
- `MCPProvider`：实现同一接口；若配置的 MCP 工具可用则拉取真实主体，
  不可用（未连接/无权限）则**自动回退** LocalProvider，保证引擎始终可运行。

## 算力层可扩展
- **并行遍历**：`ThreadPoolExecutor` 遍历候选库，规模由 `--workers` 控制
- **负空间剪枝**：`prune()` 砍掉对任务任何关键维度都无贡献的噪声主体，压搜索空间
- **夏普利自适应**：最终联盟规模 ≤ `mc_threshold`(默认12) 走精确 2^n；更大走蒙特卡洛近似
  `O(samples·n)` 替代 `O(2^n)`，海量规模可控

## 复用真实基础设施
- `nca_generator.generate_nca`：每个思维协议原语步骤发射 NCA 确权（mece/search/match/commit）
- 囚徒困境 COP 原语名（pd_payoff_build / repetition_transform / tit_for_tat / credible_commit）作为比配智慧内核

## 运行
```bash
# 本地 8 主体 (与 v1 引擎对照)
python run_networkwide.py --provider local

# 合成 200 候选, 压测算力层
python run_networkwide.py --provider local --scale 200 --workers 16

# 强制蒙特卡洛夏普利 (演示海量近似路径)
python run_networkwide.py --provider local --scale 200 --mc-threshold 2

# 尝试 MCP 连接器 (未接则优雅回退本地)
python run_networkwide.py --provider mcp
```

## 接入真实全网连接器（生产形态）
1. 在 MCP 配置中加入"主体注册 / 企业库"类连接器（如提供 `list_entities` 工具）
2. 编辑 `config/sources.example.yaml`：
   ```yaml
   active: mcp
   mcp:
     connector_name: tdca-wan-registry
     tool_name: mcp__tdca_wan_registry__list_entities   # 连接器实际暴露的工具名
     query: "智能硬件生态相关主体"
   ```
3. `MCPProvider._call_mcp` 已定义接入契约：连接器返回
   `[{id,name,cop,res:{dim:score},batna}, ...]`，引擎自动转为 `Candidate`
4. 真实主体入库后，剪枝 + 并行遍历 + 夏普利自动在海量规模生效

> 注：当前沙箱未连接 tdca-wan-registry 类连接器，`MCPProvider` 会显式回退本地源——
> 这是"可插拔"的演示，而非"已接入"。接入点代码已就位，连接器一接即用。

## 已知修正
- 精确夏普利原按"子集等权平均"实现，导致 `sum(phi)≠V(联盟)`（违反效率公理）。
  已改为按子集在随机排列中的出现频数加权 `1/(n·C(n-1,|S|))`，两版引擎（v1/v2）均已修正。
  蒙特卡洛版按排列采样，本就满足效率公理。
