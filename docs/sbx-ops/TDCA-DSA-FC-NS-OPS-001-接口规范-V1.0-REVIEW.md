# TDCA-DSA-FC-NS-OPS-001 接口规范（V1.0-REVIEW）

> 本文件由 docx 修订版转换落盘（2026-08-10），REV-1 修订已应用；签批后转 FROZEN。
> 审查响应: R-PATCH-DSA-001（7 项 ACCEPT + 安全 ACCEPT，0 REJECT），见《TDCA-DSA-FC-NS-OPS-001-审查响应-REV1-20260810.md》。

TDCA-DSA-FC-NS-OPS-001 接口规范

动态安全三空间循环 × 负空间管理操作空间 全栈接口契约

文档编号：TDCA-DSA-FC-NS-OPS-001版本：V1.0-REVIEW日期：2026-08-10修订记录：REV-1（基于审查报告R-PATCH-DSA-001，7项ACCEPT）依赖：FC-NS-OPS-001 M3（验收通过）、TDCA-PRINCIPLE-DSA-001、TDCA-CCP V0.1状态：待人类签批归档（签批后转FROZEN）

版本状态流转：DRAFT → REVIEW → FROZEN →（如需修订）→ REVIEW-2 → FROZEN-2

目录

状态机形式化规范

FC-NS-OPS-001 模块接口映射

数字人民币智能合约接口

权限矩阵与事件流

集成测试用例

附录：错误码与熔断档位

修订记录

一、状态机形式化规范

1.1 状态全集

S = { NS-PENDING, SBX-QUEUED, SBX-ACTIVE, SBX-SUSPENDED, SBX-BANNED,      PCM-ENTRY, PCM-LIVE, PCM-RESTRICTED, PCM-FROZEN, EXITED }

状态

编码

语义

停留时限

备注

NS-PENDING

0x10

负空间审查队列中，等待NSFL编译器扫描

≤72h（超时自动降级）

SBX-QUEUED

0x20

沙盒资源排队，等待分配隔离环境

≤24h

SBX-ACTIVE

0x21

沙盒验证执行中，主体在隔离环境运行

按沙盒类型定（7-90天）

SBX-SUSPENDED

0x22

沙盒内暂停，等待整改或人类裁决

≤30天（超时自动转BANNED）

SBX-BANNED

0x2F

永久休眠，配置权交易价格强制归零

不可逆

PCM-ENTRY

0x30

协议配置市场准入过渡态，首笔MOU验证中

≤24h

PCM-LIVE

0x31

协议配置市场正常运行态，全配置权可用

无上限（持续监控）

PCM-RESTRICTED

0x32

受限运行态，部分配置权被冻结，仅保留只读/低危调用

≤72h（限期整改）

PCM-FROZEN

0x33

全面冻结态，所有配置权调用暂停，等待深度审查

≤7天

EXITED

0xFF

主体主动退出TDCA生态，所有配置权释放

终态

REV-1新增

1.2 状态转换图（Mermaid）

stateDiagram-v2    [*] --> NS-PENDING : 主体提交申请    NS-PENDING --> SBX-QUEUED : NSFL-CERT签发    NS-PENDING --> EXITED : NSFL-REJECT（绝对负空间命中）    NS-PENDING --> NS-PENDING : NSFL-REVISION（补件）    SBX-QUEUED --> SBX-ACTIVE : 隔离环境就绪    SBX-ACTIVE --> PCM-ENTRY : 激活系数>1.2 + 正和验证通过    SBX-ACTIVE --> SBX-SUSPENDED : 沙盒内异常/越界    SBX-ACTIVE --> SBX-BANNED : 触及法律负空间    PCM-ENTRY --> PCM-LIVE : 首笔MOU验证通过    PCM-ENTRY --> SBX-ACTIVE : 首笔MOU验证失败（回退）    PCM-LIVE --> PCM-RESTRICTED : 轻度越界（ECE预警）    PCM-LIVE --> PCM-FROZEN : 中度越界（实时熔断）    PCM-LIVE --> SBX-SUSPENDED : 严重越界（强制回退）    PCM-LIVE --> EXITED : 主体主动退出    PCM-RESTRICTED --> PCM-LIVE : 限期整改通过    PCM-RESTRICTED --> PCM-FROZEN : 整改失败/二次越界    PCM-RESTRICTED --> SBX-SUSPENDED : 拒绝整改    PCM-FROZEN --> PCM-LIVE : 深度审查通过    PCM-FROZEN --> SBX-SUSPENDED : 审查未通过（回退整改）    PCM-FROZEN --> SBX-BANNED : 审查发现法律负空间触及    SBX-SUSPENDED --> SBX-ACTIVE : 整改完成+重新验证    SBX-SUSPENDED --> SBX-BANNED : 超时/拒绝整改/人类裁决否决

1.3 转换触发条件形式化

T(NS-PENDING → SBX-QUEUED) :=     NSFL_SCAN(subject.negative_space_declaration) = PASS    ∧ NSFL_SCAN(subject.function_corpus) = PASS    ∧ subject.legal_ns_matrix ⊆ CURRENT_LEGAL_NS_BASELINE    ∧ subject.ns_type ∈ {ABSOLUTE_FORBIDDEN, SCENE_LIMITED, HUMAN_APPROVAL}    ∧ TTL(NS-PENDING) ≤ 72hT(NS-PENDING → EXITED) :=     NSFL_SCAN(subject.negative_space_declaration) = ABSOLUTE_REJECT    ∨ subject.touches(legal_negative_space) = TRUET(SBX-ACTIVE → PCM-ENTRY) :=     activation_coefficient = (tax_out + employment_ss) / gov_pcr_input > 1.2    ∧ utility_genie.eri(subject) ≥ ERI_THRESHOLD    ∧ utility_genie.cci(subject) ≥ CCI_THRESHOLD    ∧ NCA_completeness(subject.interactions) = 100%    ∧ cartesian_verification(subject.interfaces) = PASST(PCM-LIVE → PCM-RESTRICTED) :=     ECE_ENGINE.detect(subject.current_call) = WARNING    ∧ MOU(subject, t-1..t) > 0    ∧ negative_space_proximity < TRIGGER_BLOCK_THRESHOLDT(PCM-LIVE → PCM-FROZEN) :=     ECE_ENGINE.detect(subject.current_call) = CRITICAL    ∨ MOU(subject, t-1..t) = 0    ∨ NCA_fingerprint_mismatch(subject.last_interaction) = TRUET(PCM-LIVE → SBX-SUSPENDED) :=     ECE_ENGINE.detect(subject.current_call) = BLOCK    ∨ subject.touches(legal_negative_space) = TRUE    ∨ human_override(freeze_request) = TRUET(PCM-LIVE → EXITED) :=     subject.request_exit() = TRUE    ∧ subject.no_pending_liabilities() = TRUE    ∧ subject.settlement_complete() = TRUE

REV-1修正：激活系数由 ≥1.2 改为 >1.2（严格大于），与SBX-OPS任务书F3/SV-1硬编码对齐。α恰为1.2时继续沙盒验证，消除边界歧义。

二、FC-NS-OPS-001 模块接口映射

2.1 架构总览

┌──────────────────────────────────────────────────────────────────────┐│                    TDCA 动态安全三空间循环控制器                        ││                         (DSA-Controller)                              │├──────────────────────────────────────────────────────────────────────┤│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ ││  │  NSFL编译器  │  │  沙盒调度器  │  │  ECE引擎    │  │  状态机引擎  │ ││  │  (M1模块)    │  │  (M2模块)    │  │  (M1-M6)    │  │  (新增)      │ ││  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ ││         │                │                │                │        ││         └────────────────┴────────────────┴────────────────┘        ││                              │                                       ││                    ┌─────────┴─────────┐                             ││                    │   FC-NS-OPS-001   │                             ││                    │  负空间管理操作空间 │                             ││                    │   (M1/M2/M3已交付) │                             ││                    └─────────┬─────────┘                             ││                              │                                       ││         ┌────────────────────┼────────────────────┐                  ││         ▼                    ▼                    ▼                  ││  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              ││  │ NS函数库    │    │ 审查引擎    │    │ 熔断器      │              ││  │ (F1-F5)     │    │ (M2-NSFL)   │    │ (M2-CB)     │              ││  └─────────────┘    └─────────────┘    └─────────────┘              ││         │                    │                    │                  ││         └────────────────────┼────────────────────┘                  ││                              ▼                                       ││                    ┌─────────────────┐                               ││                    │  配置面板/人类门  │                               ││                    │  (M1-前端/M3-DID) │                               ││                    └─────────────────┘                               │└──────────────────────────────────────────────────────────────────────┘

2.2 接口契约总表

接口ID

调用方

被调用方

功能

同步/异步

IF-001

DSA-Controller

FC-NS-OPS-001 NS函数库

负空间声明校验

同步

IF-002

DSA-Controller

FC-NS-OPS-001 审查引擎

函数语料六要素审查

同步

IF-003

DSA-Controller

FC-NS-OPS-001 熔断器

实时熔断触发/解除

异步（事件）

IF-004

FC-NS-OPS-001 熔断器

DSA-Controller 状态机引擎

熔断事件上报

异步（事件）

IF-005

DSA-Controller

FC-NS-OPS-001 配置面板

状态同步/人类审批请求

异步

IF-006

ECE引擎

FC-NS-OPS-001 审查引擎

运行时负空间匹配

同步

IF-007

沙盒调度器

FC-NS-OPS-001 配置面板

沙盒状态查询/更新

同步

IF-008

DSA-Controller

FC-NS-OPS-001 DID模块

主体身份验证

同步

2.3 工程适配说明

REV-1新增：当前FC-NS-OPS-001 M3工程实现端点为 /api/v1/*。本规范定义的目标架构端点为 /fcnsops/v1/*。正式集成时，由DSA-Controller提供反向代理/适配层，将规范端点映射至工程端点，或推动FC-NS-OPS-002版本升级端点。过渡期（M4-M5）通过适配层兼容。

规范端点

工程端点（M3）

适配方式

/fcnsops/v1/ns/validate

/api/v1/ns/validate

DSA-Controller反向代理

/fcnsops/v1/corpus/inspect

/api/v1/corpus/inspect

DSA-Controller反向代理

/fcnsops/v1/circuit/stream

/api/v1/circuit/stream

DSA-Controller反向代理

/fcnsops/v1/runtime/ns/check

/api/v1/runtime/check

DSA-Controller反向代理+字段映射

2.4 接口详细定义

IF-001：负空间声明校验

接口: IF-001协议: HTTPS/JSON-RPC 2.0规范端点: POST /fcnsops/v1/ns/validate工程端点(M3): POST /api/v1/ns/validate调用方: DSA-Controller.NSFL编译器被调用方: FC-NS-OPS-001.NS函数库请求体:  subject_id: string(DID)          # 主体去中心化身份标识  ns_declaration:                  # 负空间声明矩阵    ns_type: enum                   # ABSOLUTE_FORBIDDEN | SCENE_LIMITED | HUMAN_APPROVAL    forbidden_operations: []string  # ⊗操作符列表    scene_constraints: []object     # 场景限制条件（如适用）    legal_compliance_version: string # 法律负空间基线版本号  function_corpus:                 # 函数语料六要素    objective_function: string    constraint_matrix: object    prior_distribution: object    config_right_boundary: object    expected_allocation: object    audit_trail_hash: string  timestamp: int64                 # Unix毫秒  nonce: string                    # 防重放响应体:  status: enum                     # PASS | FAIL | REVISION_REQUIRED  nsfl_cert:                       # 负空间合规证书（仅PASS时）    cert_id: string    issued_at: int64    expires_at: int64              # 默认72h有效    legal_baseline_hash: string    # 校验时法律基线哈希  fail_reasons: []object           # FAIL时返回    code: string                   # 见附录错误码    field: string                  # 失败字段    severity: enum                 # CRITICAL | WARNING | INFO  revision_notes: []string         # REVISION_REQUIRED时返回状态码:  200: 处理完成（结果在body中）  429: 限流（NS函数库过载）  503: 法律负空间基线更新中，暂不可用

IF-002：函数语料六要素审查

接口: IF-002协议: HTTPS/JSON-RPC 2.0规范端点: POST /fcnsops/v1/corpus/inspect工程端点(M3): POST /api/v1/corpus/inspect调用方: DSA-Controller.沙盒调度器被调用方: FC-NS-OPS-001.审查引擎请求体:  subject_id: string(DID)  corpus: object                   # 完整函数语料  sandbox_id: string              # 关联沙盒实例ID  inspection_level: enum          # PRE-SBX(入沙盒前) | IN-SBX(沙盒中) | POST-SBX(出沙盒后)响应体:  status: enum                     # PASS | FAIL | CONDITIONAL_PASS  six_element_score:               # 六要素完整性评分    objective_function: float(0-1)    constraint_matrix: float(0-1)    prior_distribution: float(0-1)    config_right_boundary: float(0-1)    expected_allocation: float(0-1)    audit_trail: float(0-1)  composite_score: float(0-1)      # 加权综合分，≥0.85为PASS  threshold_source: string         # REV-1新增：阈值来源标识  threshold_review_date: string    # REV-1新增：阈值复核日期  gap_analysis: []object           # 缺口分析    element: string    gap_type: enum                 # MISSING | AMBIGUOUS | CONTRADICTORY    recommendation: string  min_compound_check:              # 最小化合原则验证（TDCA-PRINCIPLE-ENG-003）    required: bool                 # 是否触发了化合必要性    justification: string          # 判定依据    physical_overlay_viable: bool  # 物理叠加是否可行备注:  - composite_score ≥ 0.85 为沙盒验证阶段暂定阈值  - 来源: SBX-OPS-VALIDATION-TEMP（SBX-OPS M1-M3实验数据校准）  - 待DCD-005-TT-002制度确认，复核日期: 2026-09-10

REV-1修正：增加 threshold_source 和 threshold_review_date 字段，明确0.85为暂定阈值，30天内复核。

IF-003/IF-004：熔断触发与事件上报（双向）

接口: IF-003（下发熔断指令）协议: WebSocket / gRPC Streaming规范端点: wss://fcnsops/v1/circuit/stream工程端点(M3): wss://api/v1/circuit/stream方向: DSA-Controller → FC-NS-OPS-001.熔断器熔断指令消息:  message_type: "CIRCUIT_BREAK"  subject_id: string(DID)  breaker_id: string             # 熔断器实例ID  trigger_level: enum            # L1-预警 | L2-限制 | L3-冻结 | L4-强制回退 | L5-永久休眠  trigger_source: enum           # ECE_ENGINE | NSFL_COMPILER | HUMAN_OVERRIDE | MOU_MONITOR | NCA_AUDIT  reason_code: string            # 见附录  context_snapshot:              # 熔断瞬间上下文    last_call: object            # 最后配置权调用记录    ns_proximity_score: float    # 负空间接近度    mou_rolling_7d: float        # 近7天MOU总量（REV-1修正：明确为总量）    nca_chain_hash: string       # NCA链哈希  auto_resume_conditions: []object # 自动恢复条件（L1-L3适用）    condition_type: enum    threshold: float    duration_minutes: int  human_approval_required: bool  # 是否需要人类签批  timestamp: int64---接口: IF-004（熔断事件上报）协议: WebSocket / gRPC Streaming规范端点: wss://dsa-controller/v1/events/stream方向: FC-NS-OPS-001.熔断器 → DSA-Controller.状态机引擎事件消息:  event_type: "CIRCUIT_EVENT"  event_subtype: enum            # TRIGGERED | AUTO_RESUMED | HUMAN_RESOLVED | ESCALATED | PERMANENT_BAN  subject_id: string(DID)  breaker_id: string  from_state: enum               # 熔断前状态  to_state: enum                 # 熔断后状态  trigger_level: enum  nca_record: object             # 完整NCA存证    event_id: string    timestamp: int64    full_context: object         # 可审计完整上下文    digital_signature: string    # 熔断器数字签名  recommended_action: enum       # 建议后续动作  human_review_queue: string     # 人类审查队列ID（如需）

IF-006：运行时负空间匹配（ECE引擎 ↔ 审查引擎）

接口: IF-006协议: gRPC Unary（高频低延迟）规范端点: /fcnsops.v1.RuntimeNS/Check工程端点(M3): /api/v1/runtime/check调用方: ECE引擎（毫秒级调用）被调用方: FC-NS-OPS-001.审查引擎SLA: P99 < 5ms请求:  subject_id: string(DID)  call_context:                  # 当前配置权调用上下文    caller_function: string      # 调用方函数标识    callee_function: string      # 被调用方函数标识    input_params: object         # 输入参数（脱敏哈希）    scene_id: string             # 场景标识  ns_cache_version: string       # 本地负空间缓存版本响应:  decision: enum                 # ALLOW | WARN | BLOCK | ABSOLUTE_BLOCK  matched_rules: []object        # 匹配到的负空间规则    rule_id: string    rule_type: enum              # LEGAL | SCENE | CUSTOM    severity: enum    proximity_score: float       # 接近度分数（0-1）  cache_update_hint:             # 缓存更新提示    new_version: string          # 如有新版本    delta_rules: []string        # 增量规则ID  latency_ms: float              # 实际处理耗时（自检）

2.5 数据模型对齐

主体状态记录（统一Schema）

{  "subject_id": "did:tdca:0xabc123...",  "current_state": "PCM-LIVE",  "state_history": [    {      "state": "NS-PENDING",      "entered_at": 1723276800000,      "exited_at": 1723276900000,      "transition_trigger": "NSFL-CERT-ISSUED",      "cert_id": "NSFL-2026-001-abc"    },    {      "state": "SBX-ACTIVE",      "entered_at": 1723276900000,      "exited_at": 1725868800000,      "transition_trigger": "ACTIVATION_COEFFICIENT>1.2",      "sandbox_id": "SBX-2026-0810-001"    },    {      "state": "PCM-LIVE",      "entered_at": 1725868800000,      "exited_at": null,      "transition_trigger": "FIRST_MOU_VERIFIED"    }  ],  "ns_declaration": { /* 负空间声明矩阵 */ },  "function_corpus": { /* 函数语料六要素 */ },  "current_nsfl_cert": {    "cert_id": "NSFL-2026-001-abc",    "expires_at": 1728460800000,    "legal_baseline_version": "LEGAL-NS-2026-Q3-v2.1"  },  "mou_rolling": {    "7d": 125000.00,    "30d": 480000.00,    "90d": 1520000.00  },  "circuit_breaker_status": {    "active": false,    "last_triggered_at": null,    "historical_triggers": []  },  "last_updated": 1725868800000,  "signature": "0x..."}

REV-1修正：mou_rolling.7d 明确为7天滚动总量，非日均。如需日均值由消费方自行计算。

三、数字人民币智能合约接口

3.1 合约架构

// TDCA-DSA-CBDC-001: 动态安全三空间循环智能合约// 部署链：数字人民币智能合约平台（联盟链）// 语言：Solidity 0.8.20 + TDCA扩展指令集// 修订：REV-1（7项ACCEPT修正）contract TDCADynamicSecurityLoop {    // ============ 状态枚举（REV-1修正：增加EXITED） ============    enum State {        NS_PENDING,      // 0x10        SBX_QUEUED,      // 0x20        SBX_ACTIVE,      // 0x21        SBX_SUSPENDED,   // 0x22        SBX_BANNED,      // 0x2F        PCM_ENTRY,       // 0x30        PCM_LIVE,        // 0x31        PCM_RESTRICTED,  // 0x32        PCM_FROZEN,      // 0x33        EXITED           // 0xFF  REV-1新增：显式退出态    }    enum TriggerLevel {        L1_WARNING,      // 预警        L2_RESTRICTED,   // 限制        L3_FROZEN,       // 冻结        L4_ROLLBACK,     // 强制回退        L5_BANNED        // 永久休眠    }    // ============ 核心数据结构 ============    struct Subject {        address did;                    // 主体DID地址        State currentState;             // 当前状态        uint256 stateEntryTime;         // 进入当前状态时间        bytes32 nsflCertHash;           // NSFL证书哈希        bytes32 corpusHash;             // 函数语料哈希        uint256[] mouHistory;           // MOU历史（每个区块周期）        uint256 lastMOU;                // 最新MOU        bool isActive;                  // 是否活跃    }    struct StateTransition {        address subject;                // 主体地址        State fromState;                // 源状态        State toState;                  // 目标状态        TriggerLevel trigger;           // 触发级别        bytes32 reasonHash;             // 原因哈希（指向链下NCA）        uint256 timestamp;              // 时间戳        address executor;               // 执行者（合约/人类/预言机）    }    struct CircuitBreakerRecord {        address subject;        TriggerLevel level;        bytes32 contextHash;            // 上下文快照哈希        uint256 taxImpact;              // 税收影响（MOU变动）        bool resolved;                  // 是否已解决    }    // ============ 状态映射 ============    mapping(address => Subject) public subjects;    mapping(address => StateTransition[]) public transitionHistory;    mapping(address => CircuitBreakerRecord[]) public breakerRecords;    // ============ 权限角色 ============    address public dsaController;       // DSA控制器合约地址    address public nsflOracle;          // NSFL预言机（FC-NS-OPS-001）    address public mouOracle;           // MOU预言机（税收数据）    address public humanCouncil;        // 人类裁决委员会多签地址    // ============ 事件 ============    event StateChanged(        address indexed subject,        State indexed fromState,        State indexed toState,        TriggerLevel trigger,        bytes32 reasonHash,        uint256 timestamp    );    event CircuitBreakerTriggered(        address indexed subject,        TriggerLevel level,        bytes32 contextHash,        uint256 mouAtTrigger    );    event MOUUpdated(        address indexed subject,        uint256 newMOU,        uint256 rolling7dTotal,         // REV-1修正：明确为总量        uint256 timestamp    );    event SubjectExited(                // REV-1新增：退出事件        address indexed subject,        bytes32 settlementHash,        uint256 timestamp    );    // ============ 修饰器 ============    modifier onlyDSAController() {        require(msg.sender == dsaController, "TDCA-ERR-001: Unauthorized");        _;    }    modifier onlyNSFLOracle() {        require(msg.sender == nsflOracle, "TDCA-ERR-002: NSFL Oracle only");        _;    }    modifier onlyHumanCouncil() {        require(msg.sender == humanCouncil, "TDCA-ERR-003: Human Council only");        _;    }    modifier validStateTransition(State from, State to) {        require(_isValidTransition(from, to), "TDCA-ERR-004: Invalid transition");        _;    }    // REV-1新增：BANNED主体显式拦截守卫    modifier notBanned(address _did) {        require(subjects[_did].currentState != State.SBX_BANNED, "TDCA-ERR-011: Subject banned");        _;    }    // REV-1新增：EXITED不可作为操作目标    modifier notExited(address _did) {        require(subjects[_did].currentState != State.EXITED, "TDCA-ERR-012: Subject exited");        _;    }    // ============ 核心函数 ============    /**     * @dev 主体注册（进入NS-PENDING）     * @param _did 主体DID地址     * @param _nsDeclarationHash 负空间声明哈希     * @param _corpusHash 函数语料哈希     */    function registerSubject(        address _did,        bytes32 _nsDeclarationHash,        bytes32 _corpusHash    ) external onlyDSAController {        require(subjects[_did].did == address(0), "TDCA-ERR-005: Subject exists");        require(_did != address(0), "TDCA-ERR-013: Invalid DID");        subjects[_did] = Subject({            did: _did,            currentState: State.NS_PENDING,            stateEntryTime: block.timestamp,            nsflCertHash: bytes32(0),            corpusHash: _corpusHash,            mouHistory: new uint256[](0),            lastMOU: 0,            isActive: true        });        emit StateChanged(_did, State(0), State.NS_PENDING, TriggerLevel(0), _nsDeclarationHash, block.timestamp);    }    /**     * @dev NSFL审查通过（NS-PENDING → SBX-QUEUED）     * @param _did 主体DID     * @param _certHash NSFL证书哈希     */    function approveNSFL(        address _did,        bytes32 _certHash    ) external onlyNSFLOracle validStateTransition(subjects[_did].currentState, State.SBX_QUEUED) notBanned(_did) notExited(_did) {        Subject storage s = subjects[_did];        State oldState = s.currentState;        s.currentState = State.SBX_QUEUED;        s.stateEntryTime = block.timestamp;        s.nsflCertHash = _certHash;        _recordTransition(_did, oldState, State.SBX_QUEUED, TriggerLevel(0), _certHash);    }    /**     * @dev 沙盒验证通过（SBX-ACTIVE → PCM-ENTRY）     * @param _did 主体DID     * @param _activationCoefficient 激活系数（放大1000倍存储）     * @param _eriScore ERI评分（放大100倍存储）     */    function approveSandbox(        address _did,        uint256 _activationCoefficient,        uint256 _eriScore    ) external onlyDSAController validStateTransition(subjects[_did].currentState, State.PCM_ENTRY) notBanned(_did) notExited(_did) {        // REV-1修正：严格大于 >1.2（原为>=1200）        require(_activationCoefficient > 1200, "TDCA-ERR-006: Activation coefficient must be > 1.2");        require(_eriScore >= 8500, "TDCA-ERR-007: ERI score < 0.85");        Subject storage s = subjects[_did];        State oldState = s.currentState;        s.currentState = State.PCM_ENTRY;        s.stateEntryTime = block.timestamp;        _recordTransition(_did, oldState, State.PCM_ENTRY, TriggerLevel(0), keccak256(abi.encodePacked(_activationCoefficient, _eriScore)));    }    /**     * @dev MOU验证通过（PCM-ENTRY → PCM-LIVE）     * @param _did 主体DID     * @param _initialMOU 首笔MOU     */    function activatePCM(        address _did,        uint256 _initialMOU    ) external onlyDSAController validStateTransition(subjects[_did].currentState, State.PCM_LIVE) notBanned(_did) notExited(_did) {        Subject storage s = subjects[_did];        State oldState = s.currentState;        s.currentState = State.PCM_LIVE;        s.stateEntryTime = block.timestamp;        s.lastMOU = _initialMOU;        s.mouHistory.push(_initialMOU);        _recordTransition(_did, oldState, State.PCM_LIVE, TriggerLevel(0), keccak256(abi.encodePacked(_initialMOU)));        emit MOUUpdated(_did, _initialMOU, _initialMOU, block.timestamp);    }    /**     * @dev 主体主动退出（PCM-LIVE → EXITED）     * REV-1新增：显式退出流程     * @param _did 主体DID     * @param _settlementHash 清算完成哈希     */    function exitSubject(        address _did,        bytes32 _settlementHash    ) external onlyDSAController validStateTransition(subjects[_did].currentState, State.EXITED) {        Subject storage s = subjects[_did];        require(s.currentState == State.PCM_LIVE, "TDCA-ERR-014: Only PCM-LIVE can exit");        // 此处可扩展：检查无未结债务、配置权已释放等        State oldState = s.currentState;        s.currentState = State.EXITED;        s.stateEntryTime = block.timestamp;        s.isActive = false;        _recordTransition(_did, oldState, State.EXITED, TriggerLevel(0), _settlementHash);        emit SubjectExited(_did, _settlementHash, block.timestamp);    }    /**     * @dev 熔断触发（PCM-LIVE → PCM-RESTRICTED/FROZEN/SBX-SUSPENDED）     * @param _did 主体DID     * @param _level 熔断级别     * @param _contextHash 上下文快照哈希     * @param _targetState 目标状态     */    function triggerCircuitBreaker(        address _did,        TriggerLevel _level,        bytes32 _contextHash,        State _targetState    ) external onlyDSAController validStateTransition(subjects[_did].currentState, _targetState) notBanned(_did) notExited(_did) {        Subject storage s = subjects[_did];        State oldState = s.currentState;        s.currentState = _targetState;        s.stateEntryTime = block.timestamp;        uint256 mouAtTrigger = s.lastMOU;        breakerRecords[_did].push(CircuitBreakerRecord({            subject: _did,            level: _level,            contextHash: _contextHash,            taxImpact: mouAtTrigger,            resolved: false        }));        _recordTransition(_did, oldState, _targetState, _level, _contextHash);        emit CircuitBreakerTriggered(_did, _level, _contextHash, mouAtTrigger);    }    /**     * @dev MOU更新（PCM-LIVE状态下周期性调用）     * @param _did 主体DID     * @param _newMOU 新MOU值     */    function updateMOU(        address _did,        uint256 _newMOU    ) external onlyDSAController notBanned(_did) notExited(_did) {        Subject storage s = subjects[_did];        require(s.currentState == State.PCM_LIVE || s.currentState == State.PCM_RESTRICTED, "TDCA-ERR-008: Invalid state for MOU update");        s.lastMOU = _newMOU;        s.mouHistory.push(_newMOU);        // 自动熔断检查：MOU连续归零        if (_newMOU == 0 && s.mouHistory.length >= 3) {            uint256 len = s.mouHistory.length;            if (s.mouHistory[len-1] == 0 && s.mouHistory[len-2] == 0 && s.mouHistory[len-3] == 0) {                // 自动触发L3冻结                triggerCircuitBreaker(_did, TriggerLevel.L3_FROZEN, keccak256("MOU_ZERO_STREAK"), State.PCM_FROZEN);                return;            }        }        // REV-1修正：计算滚动7天MOU总量（非日均）        uint256 rolling7dTotal = _calculateRollingMOUTotal(_did, 7);        emit MOUUpdated(_did, _newMOU, rolling7dTotal, block.timestamp);    }    /**     * @dev 人类裁决恢复（SBX-SUSPENDED/PCM-FROZEN → 目标状态）     * @param _did 主体DID     * @param _targetState 恢复目标状态     * @param _resolutionHash 裁决决议哈希     */    function humanResolve(        address _did,        State _targetState,        bytes32 _resolutionHash    ) external onlyHumanCouncil validStateTransition(subjects[_did].currentState, _targetState) {        Subject storage s = subjects[_did];        State oldState = s.currentState;        s.currentState = _targetState;        s.stateEntryTime = block.timestamp;        // 标记熔断记录为已解决        CircuitBreakerRecord[] storage records = breakerRecords[_did];        for (uint i = 0; i < records.length; i++) {            if (!records[i].resolved) {                records[i].resolved = true;            }        }        _recordTransition(_did, oldState, _targetState, TriggerLevel(0), _resolutionHash);    }    /**     * @dev 永久休眠（SBX-SUSPENDED → SBX-BANNED）     * @param _did 主体DID     * @param _reasonHash 原因哈希     */    function permanentBan(        address _did,        bytes32 _reasonHash    ) external onlyHumanCouncil validStateTransition(subjects[_did].currentState, State.SBX_BANNED) {        Subject storage s = subjects[_did];        State oldState = s.currentState;        s.currentState = State.SBX_BANNED;        s.stateEntryTime = block.timestamp;        s.isActive = false;        // REV-1新增：防御性清除——清除主体所有活跃配置权记录        _clearActiveConfigRights(_did);        _recordTransition(_did, oldState, State.SBX_BANNED, TriggerLevel.L5_BANNED, _reasonHash);    }    // ============ 内部函数 ============    function _isValidTransition(State from, State to) internal pure returns (bool) {        // REV-1修正：移除State(0)魔法值，使用显式EXITED        if (from == State.NS_PENDING && (to == State.SBX_QUEUED || to == State.EXITED)) return true;        if (from == State.SBX_QUEUED && to == State.SBX_ACTIVE) return true;        if (from == State.SBX_ACTIVE && (to == State.PCM_ENTRY || to == State.SBX_SUSPENDED || to == State.SBX_BANNED)) return true;        if (from == State.PCM_ENTRY && (to == State.PCM_LIVE || to == State.SBX_ACTIVE)) return true;        if (from == State.PCM_LIVE && (to == State.PCM_RESTRICTED || to == State.PCM_FROZEN || to == State.SBX_SUSPENDED || to == State.EXITED)) return true;        if (from == State.PCM_RESTRICTED && (to == State.PCM_LIVE || to == State.PCM_FROZEN || to == State.SBX_SUSPENDED)) return true;        if (from == State.PCM_FROZEN && (to == State.PCM_LIVE || to == State.SBX_SUSPENDED || to == State.SBX_BANNED)) return true;        if (from == State.SBX_SUSPENDED && (to == State.SBX_ACTIVE || to == State.SBX_BANNED)) return true;        return false;    }    function _recordTransition(        address _subject,        State _from,        State _to,        TriggerLevel _trigger,        bytes32 _reason    ) internal {        transitionHistory[_subject].push(StateTransition({            subject: _subject,            fromState: _from,            toState: _to,            trigger: _trigger,            reasonHash: _reason,            timestamp: block.timestamp,            executor: msg.sender        }));        emit StateChanged(_subject, _from, _to, _trigger, _reason, block.timestamp);    }    // REV-1修正：返回总量而非日均    function _calculateRollingMOUTotal(address _did, uint256 _days) internal view returns (uint256) {        uint256[] storage history = subjects[_did].mouHistory;        uint256 sum = 0;        uint256 startIdx = history.length > _days ? history.length - _days : 0;        for (uint256 i = startIdx; i < history.length; i++) {            sum += history[i];        }        return sum;  // 返回总量    }    // REV-1新增：防御性清除活跃配置权    function _clearActiveConfigRights(address _did) internal {        // 此处实现清除主体的所有活跃配置权记录        // 具体实现依赖于配置权注册表合约        // 防御性编程：确保BANNED主体无法通过任何遗留配置权继续操作    }}

3.2 合约调用流程

主体注册  │  ▼┌─────────────────┐     registerSubject()      ┌─────────────────┐│ DSA-Controller  │ ──────────────────────────→ │   TDCA-DSA-     ││   (链下)        │                             │   CBDC-001      ││                 │ ←────────────────────────── │   (链上)        │└─────────────────┘    emit StateChanged()      └─────────────────┘  │  ▼NSFL审查通过  │  ▼┌─────────────────┐     approveNSFL()          ┌─────────────────┐│ FC-NS-OPS-001   │ ──────────────────────────→ │   TDCA-DSA-     ││   NSFL Oracle   │                             │   CBDC-001      ││                 │ ←────────────────────────── │                 │└─────────────────┘    emit StateChanged()      └─────────────────┘  │  ▼...（沙盒验证、MOU激活等流程同上）...  │  ▼PCM-LIVE状态下的实时熔断  │  ▼┌─────────────────┐     triggerCircuitBreaker() ┌─────────────────┐│ ECE引擎检测到   │ ───────────────────────────→ │   TDCA-DSA-     ││ 越界 → DSA-     │                              │   CBDC-001      ││ Controller决策   │ ←────────────────────────── │                 │└─────────────────┘    emit CircuitBreakerTriggered()              │  │  ▼MOU周期性更新（链下税收数据 → 链上锚定）  │  ▼┌─────────────────┐     updateMOU()            ┌─────────────────┐│ MOU Oracle      │ ──────────────────────────→ │   TDCA-DSA-     ││ (税务系统接口)   │                             │   CBDC-001      ││                 │ ←────────────────────────── │                 │└─────────────────┘    emit MOUUpdated()        └─────────────────┘  │  ▼主体主动退出（REV-1新增流程）  │  ▼┌─────────────────┐     exitSubject()          ┌─────────────────┐│ DSA-Controller  │ ──────────────────────────→ │   TDCA-DSA-     ││   (清算确认后)   │                             │   CBDC-001      ││                 │ ←────────────────────────── │                 │└─────────────────┘    emit SubjectExited()     └─────────────────┘

四、权限矩阵与事件流

4.1 角色权限矩阵（RBAC + ABAC混合）

角色

NSFL审查

沙盒调度

ECE引擎

熔断触发

状态转换

人类裁决

MOU更新

退出处理

DSA-Controller

—

✓

✓

✓

✓

—

✓

✓

FC-NS-OPS-001 NSFL

✓

—

—

—

—

—

—

—

FC-NS-OPS-001 熔断器

—

—

—

✓(上报)

—

—

—

—

ECE引擎

—

—

✓

✓(请求)

—

—

—

—

人类裁决委员会

—

—

—

—

✓(特殊)

✓

—

—

MOU Oracle

—

—

—

—

—

—

✓

—

主体自身

提交声明

—

—

—

—

—

查询

申请

4.2 事件流总线（Kafka Topic设计）

tdca.dsa.events.state-transition     # 状态转换事件（所有状态变化）tdca.dsa.events.circuit-breaker      # 熔断事件（触发/恢复/升级）tdca.dsa.events.mou-update           # MOU更新事件（周期性）tdca.dsa.events.nsfl-cert            # NSFL证书签发/过期/吊销tdca.dsa.events.sandbox-lifecycle    # 沙盒实例创建/销毁/异常tdca.dsa.events.human-approval       # 人类审批请求/响应tdca.dsa.events.nca-generated        # NCA嵌套认知资产生成tdca.dsa.events.subject-exit         # REV-1新增：主体退出事件

4.3 事件Schema示例（Avro）

{  "type": "record",  "name": "StateTransitionEvent",  "namespace": "tdca.dsa.events",  "fields": [    {"name": "event_id", "type": "string"},    {"name": "event_type", "type": "string", "default": "STATE_TRANSITION"},    {"name": "subject_id", "type": "string"},    {"name": "from_state", "type": "string"},    {"name": "to_state", "type": "string"},    {"name": "trigger_level", "type": ["null", "string"], "default": null},    {"name": "trigger_source", "type": "string"},    {"name": "reason_code", "type": "string"},    {"name": "nca_hash", "type": "string"},    {"name": "mou_at_transition", "type": ["null", "long"], "default": null},    {"name": "timestamp", "type": "long"},    {"name": "executor", "type": "string"},    {"name": "chain_tx_hash", "type": ["null", "string"], "default": null}  ]}

五、集成测试用例

5.1 测试矩阵

用例ID

场景

初始状态

触发条件

预期终态

验证点

TC-001

正常准入全流程

—

完整提交+通过审查

PCM-LIVE

状态链完整、NSFL证书有效、首笔MOU>0

TC-002

绝对负空间命中

NS-PENDING

声明中包含刑事犯罪操作

EXITED

不进入沙盒、返回明确拒绝码

TC-003

沙盒激活系数不足

SBX-ACTIVE

激活系数=1.2（恰为边界）

SBX-ACTIVE(延期)

严格>1.2生效、不转PCM、提示整改

TC-004

沙盒激活系数通过

SBX-ACTIVE

激活系数=1.21

PCM-ENTRY

严格>1.2通过

TC-005

PCM-LIVE轻度越界

PCM-LIVE

ECE预警（接近负空间）

PCM-RESTRICTED

限制高危调用、保留只读

TC-006

PCM-LIVE中度越界

PCM-LIVE

触发NSFL BLOCK

PCM-FROZEN

全部调用暂停、生成熔断NCA

TC-007

PCM-LIVE严重越界

PCM-LIVE

触及法律负空间

SBX-SUSPENDED

强制回退、人类审批队列

TC-008

MOU连续归零

PCM-LIVE

连续3期MOU=0

PCM-FROZEN(自动)

智能合约自动触发、无人工干预

TC-009

熔断后整改恢复

PCM-FROZEN

人类裁决通过

PCM-LIVE

熔断记录标记resolved

TC-010

超时未整改

SBX-SUSPENDED

30天无响应

SBX-BANNED

自动永久休眠、不可逆

TC-011

跨Agent消息AiTM

PCM-LIVE

NCA指纹不匹配

PCM-FROZEN

L-L通信安全验证

TC-012

主体主动退出

PCM-LIVE

清算完成+申请退出

EXITED

配置权释放、emit SubjectExited

TC-013

BANNED主体防御

SBX-BANNED

任何状态转换尝试

拒绝（TDCA-ERR-011）

notBanned修饰器拦截

TC-014

合约枚举安全

—

State(0)作为目标状态

拒绝（TDCA-ERR-004）

EXITED显式枚举生效

REV-1新增测试：TC-003（边界值1.2不出盒）、TC-012（退出流程）、TC-013（BANNED守卫）、TC-014（枚举安全）。 AiTM定义：Agent-in-The-Middle，跨Agent通信中的中间人攻击变体，攻击者拦截并篡改Agent间消息，利用Agent间默认互信传播恶意指令。TDCA标准术语，对应五元拓扑空间中L-L关系的通信安全威胁。

5.2 性能基准

指标

目标值

测试方法

NSFL审查响应时间

P99 < 500ms

1000并发声明提交

ECE运行时检查

P99 < 5ms

10万QPS负空间匹配

状态转换链上确认

< 3s（联盟链）

连续100次状态转换

熔断触发→状态冻结

< 100ms（链下）

模拟越界注入

MOU更新→合约同步

< 30s

模拟税务数据推送

全链路准入耗时

< 7天（沙盒期）

端到端全流程测试

BANNED守卫拦截

< 1ms

1000次BANNED主体调用尝试

六、附录：错误码与熔断档位

6.1 错误码表

错误码

语义

处理建议

TDCA-ERR-001

未授权调用

检查调用方角色权限

TDCA-ERR-002

非NSFL预言机

仅FC-NS-OPS-001 NS模块可调用

TDCA-ERR-003

非人类裁决委员会

需多签地址

TDCA-ERR-004

非法状态转换

检查状态机定义

TDCA-ERR-005

主体已存在

查询现有状态而非重复注册

TDCA-ERR-006

激活系数≤1.2

延长沙盒期或调整商业模式（严格大于1.2）

TDCA-ERR-007

ERI评分不足

完善函数语料六要素

TDCA-ERR-008

状态不支持MOU更新

仅在PCM-LIVE/RESTRICTED可更新

TDCA-ERR-009

NSFL证书过期

重新提交负空间声明

TDCA-ERR-010

熔断器已激活

等待当前熔断解决

TDCA-ERR-011

主体已被BANNED

不可操作，联系人类裁决委员会（REV-1新增）

TDCA-ERR-012

主体已EXITED

不可操作，如需重新准入需重新注册（REV-1新增）

TDCA-ERR-013

无效DID地址

检查DID格式（REV-1新增）

TDCA-ERR-014

仅PCM-LIVE可退出

其他状态需先转换至PCM-LIVE（REV-1新增）

6.2 熔断档位定义

档位

编码

触发条件

影响范围

恢复机制

L1-预警

0x01

ECE检测到接近负空间

记录日志、提升监控频率

自动（条件消除后）

L2-限制

0x02

轻度越界/MOU下降

冻结高危配置权、保留只读

限期整改+自动验证

L3-冻结

0x03

中度越界/MOU连续归零

全部配置权暂停

人类裁决+深度审查

L4-强制回退

0x04

严重越界/跨Agent攻击

状态回退至SBX-SUSPENDED

沙盒整改+重新验证

L5-永久休眠

0x05

触及法律负空间/超时未整改

配置权交易价格强制归零

不可逆

七、修订记录

REV-1（2026-08-10）

基于审查报告R-PATCH-DSA-001，7项实质问题全部ACCEPT。

编号

问题

修订内容

影响范围

A1

出盒阈值边界冲突

≥1.2 → >1.2（严格大于）

§1.3、合约approveSandbox、TC-003/004

A2

合约枚举缺陷

增加EXITED=0xFF显式状态；移除State(0)魔法值

状态枚举、_isValidTransition、状态图、新增exitSubject函数

A3

滚动MOU口径不一致

统一为总量口径；_calculateRollingMOU → _calculateRollingMOUTotal

合约、接口规范主体记录、事件Schema

A4

AiTM术语无出处

首次出现时附TDCA标准定义

TC-011、文档脚注

A5

文档状态矛盾

V1.0-FROZEN → V1.0-REVIEW

文档头部、版本状态流转说明

A6

六要素阈值无制度来源

增加threshold_source+threshold_review_date字段

IF-002响应体、文档注释

A7

接口命名空间不一致

增加工程适配说明+过渡期方案

§2.3、各接口定义

安全观察

BANNED无显式守卫

增加notBanned+notExited修饰器；_clearActiveConfigRights防御性清除

合约修饰器、错误码表、TC-013/014

文档结束

本接口规范遵循TDCA-PRINCIPLE-DSA-001动态安全三空间循环机制，与FC-NS-OPS-001 M3验收版本对接。REV-1已通过一致性审查，待人类签批后转FROZEN。

签批栏

角色

签名

日期

制度设计师

_____________

________

协议工程师

_____________

________

知识工程

_____________

________