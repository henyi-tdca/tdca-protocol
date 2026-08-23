# TDCA Protocol · 可信数字协作架构协议包

> **TDCA 是锚定主权信用的智能体协作制度协议：结算只走数字人民币（法偿性），协作价值以税收为最低可见效用锚（财政事实），认知资产经国家可信版权链/天平链获得法律赋予（司法事实）。当前为制度演示态（simulated），全部数据带性质标注（ID92）。**

| 结算锚 | 效用锚 | 权利锚 |
|---|---|---|
| 数字人民币 e-CNY（唯一结算轨道，法偿性 + 央行负债 + 结算终局性） | 税收 MOU = tax_in + tax_out（国家财政审计背书的最低可见效用） | 国家可信版权链 / 天平链（法律赋予而非技术赋予，存证具司法证据效力） |

**与现有协议栈的关系**：通信层（MCP/A2A）与支付层（AP2/x402/ACP）锚定的是私人信用；TDCA 的治理层（NSFL 负空间 / NCA 存证链 / CCP 契约）可挂载于 MCP/A2A 之上，但结算轨道不接受私人信用资产。三锚叠加，全球无对标。

---

## 两包导航

| 目录 | 内容 | 版本/状态 |
|---|---|---|
| [`pack/`](pack/) | **TDCA 智能体编程协议包（PACK-001）**：30 分钟制度注入入门——7 份规范 + 5 个机器可读模板 | V1.3 ✅ 已签批（NCA-002~005） |
| [`dual/`](dual/) | **双协议化合引擎（DUAL-PROTOCOL）**：场景协议 × 制度协议运行时化合——4 引擎模块 + 测试 + 四行业示例 | V1.1 ✅ 已签批 |
| [`core-go/`](core-go/) | **Go 强类型生产级核心引擎**：enforce / nca / nsfl 核心三件 + tdcad 守护进程 + Python↔Go 桥接（Apache-2.0 独立许可，与根 MIT 双许可并存） | V1.0.0 ✅ 已签批（GSEQ-0377） |

## tools/ 工具货架（全部开源可跑，零第三方依赖）

| 套件 | 能力 | 快速开始 |
|---|---|---|
| [`tools/enforce_entry.py`](tools/enforce_entry.py) | OPC S0 准入自检（R1~R10 + NSFL 熔断） | `python tools/enforce_entry.py --check <NCA文件>` |
| [`tools/cts_l1/`](tools/cts_l1/) | CTS-L1 一致性自测套件（C-1~C-6 + 声明生成） | `cd tools && python -m pytest cts_l1 -q` |
| [`tools/mcp_bridge/`](tools/mcp_bridge/) | TDCA ↔ MCP 协议桥（NCA 水印 / NSFL 熔断 / 挂载 / 存证查询） | `cd tools && python -m pytest mcp_bridge -q` |
| [`tools/cog_align/`](tools/cog_align/) | 认知对齐评测：思想病毒防御 / 认知漂移 / 对齐度分档（M2 场景包） | `cd tools && python -m cog_align.cli --help` |
| [`tools/util_value/`](tools/util_value/) | 效用价值评估：会计口径入表 / 版权链存证 / 完整报告（M2 入表服务） | `cd tools && python -m util_value.cli --help` |
| [`tools/value_services/`](tools/value_services/) | 增值服务统一入口 V2.0-M2（双服务编排） | `cd tools && python -m pytest value_services -q` |
| [`tools/maka_nca/`](tools/maka_nca/) | 五项目① Maka 对接：Event Log → NCA 存证 + 正和计量 | `cd tools && python -m pytest maka_nca -q` |
| [`tools/paperclip_nca/`](tools/paperclip_nca/) | 五项目② Paperclip 对接：编排 → 协作编译 | `cd tools && python -m pytest paperclip_nca -q` |
| [`tools/pi_nca/`](tools/pi_nca/) | 五项目③ Pi 对接：MIT 层制度编译 + Fair Source | `cd tools && python -m pytest pi_nca -q` |
| [`tools/cypress_pool/`](tools/cypress_pool/) | 五项目④ Cypress 对接：配置权计量 + L2 | `cd tools && python -m pytest cypress_pool -q` |
| [`tools/thingsboard_pool/`](tools/thingsboard_pool/) | 五项目⑤ ThingsBoard 对接：IoT 计量 + L2 | `cd tools && python -m pytest thingsboard_pool -q` |

基座模块（同层）：`tdca_cognitive_distance.py`（定义 3.36/3.37，命题 3.10）/ `tdca_cognitive_state.py`（五维状态 ID8）/ `tdca_fuzzy_distance.py`（模糊层）。全量回归：`cd tools && python -m pytest -q`（详见 [`tools/README.md`](tools/README.md)）。

## 增值服务（TDCA-VALUE-PRICING-001 已确认生效）

协议层永久免费（ID77，见合规红线）；以下增值服务面向需要制度化落地的团队，收益反哺协议迭代：

| 档位 | 内容 | 定价 |
|---|---|---|
| L1 订阅 · 专业版 | tools/ 全货架使用权 + 存证链托管 + 月度对齐报告 | ¥99/月 |
| L1 订阅 · 企业版 | 专业版全量 + 思想病毒防御专项 + 优先响应 | ¥999/月 |
| L2 项目制 · 对齐评测 | 认知对齐评测项目（思想病毒防御 + 认知漂移治理） | ¥1–20 万/项目 |
| L2 项目制 · 入表评估 | 认知资产入表评估（会计口径 + 版权链存证，合规审查档） | 按合规审查档报价 |
| 年度维护 | 项目制交付物的年度维护 | 项目额 15–20%/年 |

定价纪律：MOU 地板语义 + 归零规则（效用不成立不收费）/ 日抛优先（ID90）/ 人类签名权（ID71）；L1 订阅保留 ID27 校准条款（沙盒激活系数 >1.2 后校准）。双服务打包（评测 + 入表）另有组合口径，接洽见 GitHub [Discussions](https://github.com/henyi-tdca/tdca-protocol/discussions)。

## 快速开始（3 步）

1. **读取** `pack/docs/01-启动清单.md` —— 制度基线 7 项检查 + 工作空间初始化 + 会话 6/6 校验
2. **复制** `pack/templates/fc-six-elements.md` —— 为当前任务填写六要素声明，人类签批后开工
3. **开发全程** 遵循 `pack/docs/04-编码规范.md`（水印 + docstring + NSFL 熔断），产出即按 `pack/docs/06-NCA与审查链.md` 存证

运行引擎测试：`cd dual && python -m pytest tests/ -q`

## 社区与参与（OPC S0）

本社区是**缔约者网络**而非用户群（TDCA-OPC-COMMUNITY-001）。参与方式见 [`CONTRIBUTING.md`](CONTRIBUTING.md)：签署准入 NCA → 成为 L1 缔约者，全程由 `tools/enforce_entry.py` 自检（R1~R10 + NSFL 熔断），缔约名录见 [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md)。发布文与立项记录见 [`docs/release/`](docs/release/) 与 [`docs/community/`](docs/community/)。

**官网制度橱窗**：https://lku76tmluhatu.ok.kimi.link （M4a 静态演示站：四层架构制度橱窗）

**发布叙事**：[《我们花 168 块钱，跑通了 33.5 亿 Token 的智能体主权信用结算框架》](https://juejin.cn/post/7676330290206113798)（掘金，2026-08-22 首发；[知乎专栏](https://zhuanlan.zhihu.com/p/2074417591234322652)同步；[English @ dev.to](https://dev.to/henyitdca/we-built-a-sovereign-credit-settlement-framework-for-agents-with-168-cny-and-335b-tokens-2m97)）

## 合规红线（必须遵守）

| 红线 | 依据 |
|---|---|
| 协议层永久免费开源，禁止"标准授权费"等零和表述 | ID77 |
| 法律禁止领域 = 绝对负空间，无替代路径、只识别并熔断 | NSFL-V0.2（ID86） |
| 人类签名权不可绕过（快系统执行、慢系统裁决） | ID71 + 宪法第 4 条 C01 |
| 不发币、不公售、不承诺分红；真实态结算只走 e-CNY 法币轨道 | 合规声明（央行 42 号文同向） |
| 要求破例即伪创新信号 | ID38 |
| 术语一致性：引用注册表概念附 T-编号，禁止同义私造词 | TERMS 术语防火墙 |

## 数据性质声明（ID92）

本仓库全部示例（`dual/examples/`）与模板（`pack/templates/`）均为 **simulated（制度演示态）**——演示制度机制如何运转，不构成真实配置权执行路径。真实态里程碑：e-CNY 可编程接口接入 / 税收系统数据通道 / 版权链登记通道（时间表受外部基础设施制约，不承诺日期）。

## 治理与状态

- 变更通道：FROZEN 交付物只走 DCD 流程（提案 → 六要素 → 变更明细 → 制度审查 REV → 人类签批 → 升版存证）
- 存证纪律：里程碑动作必生成 NCA 存证（链式哈希引用），无存证 = 未发生
- 状态：PACK-001 V1.3 / DUAL V1.1 ｜ 制度审查 PASSED ｜ 签批 NCA-20260811-002~005 ｜ 引擎测试全绿（发布前门禁复核）

## License

MIT（见 [LICENSE](LICENSE)，含 TDCA 附注）。指针引用的制度文本（TDCA-CONST / UPDA / NSFL / TERMS）保留其自身治理条款。
