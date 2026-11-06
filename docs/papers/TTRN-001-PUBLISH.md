# TTRN-001

> 归档来源: 用户上传 2026-08-10 | 状态: 研究沙盒（课题解析前）

---

TDCA 过渡可信根节点技术规范（TTRN-001）
文档编号：TDCA-TTRN-001版本：V0.1-DRAFT状态：待 DCD 审查 / REASONIX-READY生成时间：2026-08-10 14:51 CST基线依赖：TDCA-FRAMEWORK-5CC-002 / TDCA-通知机-V2.1 / TDCA-CCP-V0.1 / TDCA-PRINCIPLE-CBDC-001格式规范：TDCA-WORKING-SPEC-001
一、问题定义：物理可信根节点的不可替代性与部署时差
1.1 通知机的制度定位
TDCA 通知机（TDCA-Notify-Machine）是 L0 法律底层与 L2 配置权市场之间的物理可信根锚点，其制度功能不可还原为纯软件实现（制度基座第一性）。通知机核心能力：
能力
制度意义
技术实现
硬件安全芯片（HSM）
私钥不可提取，DID 与物理实体不可分离绑定
国密 SM2/SM3/SM4 安全芯片
实时健康状态信号
节点存活即制度承诺有效，节点失效即配置权自动冻结
心跳协议 + 数字人民币智能合约状态联动
物理位置锚定
防止虚拟节点批量伪造，确保地理可追责
GPS/北斗 + 运营商基站三角定位
抗重放与抗克隆
每次令牌生成绑定物理不可复制特征（PUF）
芯片物理不可克隆函数
人机混合接口
人类最终签名权的物理承载（生物特征 + 硬件按键）
指纹/声纹传感器 + 物理确认键
1.2 部署时差风险
通知机从设计 - 流片 - 量产 - 部署至全国节点，预估周期 12-18 个月。在此期间： - TDCA-5CC 五柱生态需要启动，智能体需要进入协议配置网络 - 无物理可信根 = 无 DID 绑定 = 无配置权交易 = 生态无法运转 - 纯软件方案 = 私钥可提取 = DID 可伪造 = 制度基座崩塌
因此，必须在通知机部署完成前，建立 过渡可信根节点体系（TTRN, Transitional Trusted Root Node），满足最低制度安全水位，同时明确 与正式通知机的切换路径和熔断条件。
二、过渡可信根架构：分级复合锚定
2.1 核心原则
过渡方案遵循 多因素复合锚定、分级可信水位、半自动健康监测、限期切换熔断 四原则：
不追求单点等效，追求整体冗余：没有任何单一过渡设备等于通知机，但多因素交叉验证可逼近同等安全水平
国密基础设施复用：优先利用已大规模部署的国密硬件（USBKey、密码卡、加密机），降低部署摩擦
运营商网络物理锚定：利用 SIM 卡 + 运营商网络的不可伪造性，提供网络层物理位置证明
云 TEE 作为计算隔离：利用阿里云 Enclave / 腾讯云 TEE / 华为 TrustZone 提供运行时隔离
人工巡检作为健康信号补充：过渡期内，实时健康信号 = 自动化心跳 + 定期人工巡检签名
2.2 三级过渡可信根（TTRN-Tier）
+---------------------------------------------------------------------+|                    TDCA 协议配置网络准入网关                          ||                         （L2 配置权市场入口）                           |+---------------------------+-----------------------------------------+                            |        +-------------------+-------------------+        |                   |                   |        v                   v                   v+---------------+   +---------------+   +---------------+|  TTRN-Tier-1  |   |  TTRN-Tier-2  |   |  TTRN-Tier-3  ||  高安全级      |   |  中安全级      |   |  基础安全级    ||  （关键节点）   |   |  （普通节点）   |   |  （边缘节点）   |+---------------+   +---------------+   +---------------+| 国密密码机    |   | 国密 USBKey   |   | 运营商 eSIM   || + 云 TEE     |   | + 手机 TEE    |   | + 设备指纹    || + 人工双签    |   | + 生物特征    |   | + 行为生物    || + 运营商定位  |   | + 运营商定位  |   |              |+---------------+   +---------------+   +---------------+        |                   |                   |        +-------------------+-------------------+                            |                            v                +-----------------------+                |   健康状态聚合引擎      |                |  （半自动化监测中心）    |                |  自动化心跳 + 人工巡检   |                |  + 异常熔断决策         |                +-----------------------+
2.3 三级可信根详规
TTRN-Tier-1：高安全级（关键节点）
适用对象：政府节点、金融机构节点、核心企业节点、沙盒监管节点
组件
规格
制度功能
技术实现
国密密码机
符合 GM/T 0030 标准，具备 SM2/SM3/SM4 算法，密钥不可导出
物理私钥锚定，DID 生成与签名
江南天安 / 三未信安 / 卫士通 服务器密码机
云 TEE 实例
阿里云 Enclave / 华为云 TEE / 腾讯云 TEE
运行时隔离，确保智能体执行环境不可观测
阿里云 ECS Enclave / 华为云 Kunpeng TEE
人工双签
两名授权管理员物理在场，分别持独立 USBKey 签名
人类最终控制权的物理表达，防止单点内部人攻击
双人双岗制度，签名记录上链
运营商定位
基站三角定位 + 北斗/GPS 双模，精度 &lt;= 10 米
物理位置锚定，防止虚拟节点迁移
中国移动/电信/联通 位置能力 API
心跳频率
每 30 秒一次自动化心跳
实时健康状态信号
专用心跳服务，超时 2 分钟即触发预警
人工巡检
每日一次人工巡检签名
补充自动化盲区，确认物理设备在位
巡检 APP，扫码 + 生物特征 + 地理位置
准入条件：五因素全部通过，缺一不可。任何单一因素失效 - 节点状态降级为 SUSPENDED，配置权交易冻结。
TTRN-Tier-2：中安全级（普通节点）
适用对象：普通企业节点、OPC 节点、社区活跃成员节点
组件
规格
制度功能
技术实现
国密 USBKey
符合 GM/T 0017 标准，SM2 证书，PIN 码保护
个人/企业 DID 物理绑定
飞天诚信 / 恒宝 / 格尔 国密 USBKey
手机 TEE
ARM TrustZone / 华为 iTrustee / 高通 SPU
移动端私钥隔离，防止 APP 层提取
主流安卓手机 TEE 能力
生物特征
指纹 + 人脸 + 声纹（三选二）
人类身份绑定，防止 USBKey 被盗用
FIDO2 / 公安部一所认证算法
运营商定位
基站定位，精度 &lt;= 100 米
物理位置粗锚定
运营商网络位置能力
心跳频率
每 60 秒一次自动化心跳
实时健康状态信号
心跳服务，超时 5 分钟触发预警
人工巡检
每周一次人工巡检签名
定期确认设备与人格一致性
巡检 APP
准入条件：USBKey + 手机 TEE + 生物特征（二选二）+ 心跳通过。运营商定位作为辅助验证（失败不阻断，触发增强审计）。
TTRN-Tier-3：基础安全级（边缘节点）
适用对象：个人开发者、轻量级智能体、测试节点
组件
规格
制度功能
技术实现
运营商 eSIM
运营商远程配置证书，SIM 卡不可复制
网络层物理身份锚定
中国移动/电信/联通 eSIM 能力
设备指纹
硬件序列号 + MAC 地址 + 主板 ID 复合哈希
设备唯一性标识（弱可信）
设备指纹 SDK，防模拟器检测
行为生物
打字节奏、鼠标轨迹、滑动模式
持续身份验证，防止账号接管
行为生物特征引擎
心跳频率
每 300 秒一次自动化心跳
实时健康状态信号（低频率）
心跳服务，超时 15 分钟触发预警
人工巡检
每月一次人工巡检签名
最低限度人工确认
巡检 APP
准入条件：eSIM + 设备指纹 + 心跳通过。行为生物作为持续验证（异常触发二次认证）。 限制：Tier-3 节点 不得持有 P-Right（完全配置权），最高 S-Right（场景配置权）；不得发起跨场景 PCR；单笔交易限额 &lt;= 5000 元数字人民币。
三、实时健康状态信号的过渡实现
3.1 正式通知机的健康信号模型
正式通知机的健康信号是 全自动、实时、不可伪造 的：
健康信号 = HSM 心跳（30s）+ PUF 自检（每次签名）+ 位置漂移检测（实时）+ 温度/电压异常检测（实时）
3.2 过渡期的半自动化健康信号模型（TTRN-Health）
过渡期内，健康信号采用 自动化基线 + 人工巡检补充 + 社区众包验证 三层模型：
+--------------------------------------------------------------+|                    TTRN-Health 三层模型                        |+--------------------------------------------------------------+| Layer-1: 自动化基线（Automation Baseline）                    || +- 心跳服务：按 Tier 频率发送签名心跳包至联盟链               || +- 位置漂移检测：运营商定位 / GPS 坐标连续变化监控            || +- 设备指纹一致性：定期比对硬件特征哈希                        || +- 行为生物基线：持续学习用户行为模式，异常检测               |+--------------------------------------------------------------+| Layer-2: 人工巡检补充（Human Patrol）                        || +- Tier-1: 每日巡检，双人双签，扫码 + 生物 + 地理            || +- Tier-2: 每周巡检，单人签名，APP 自动记录                   || +- Tier-3: 每月巡检，单人签名，视频确认可选                   || +- 巡检结果上链存证，生成 NCA_Patrol                         |+--------------------------------------------------------------+| Layer-3: 社区众包验证（Community Verification）                || +- 邻近节点交叉验证：物理邻近节点互相 ping 验证存活           || +- 随机挑战响应：联盟链随机向节点发起密码学挑战               || +- 异常举报机制：社区成员可举报可疑节点，触发增强审计         |+--------------------------------------------------------------+
3.3 健康状态评分算法（TTRN-Health-Score）
class TTRNHealthScore:    def compute(self, node: TTRNNode) -&gt; HealthScore:        # 自动化基线分（60% 权重）        auto_score = (            self.heartbeat_score(node.last_heartbeat, node.tier) * 0.25 +            self.location_score(node.location_history) * 0.15 +            self.device_fingerprint_score(node.fp_history) * 0.10 +            self.behavioral_biometric_score(node.bb_history) * 0.10        )                # 人工巡检分（30% 权重）        patrol_score = self.patrol_score(            node.last_patrol_time,             node.patrol_signature_valid,            node.tier.patrol_frequency        ) * 0.30                # 社区众包分（10% 权重）        community_score = (            self.neighbor_verification_score(node.neighbor_pings) * 0.05 +            self.challenge_response_score(node.last_challenge) * 0.03 +            self.abuse_report_score(node.abuse_reports) * 0.02        )                total = auto_score + patrol_score + community_score                # 状态判定        if total &gt;= 0.85: return HealthScore.ACTIVE        elif total &gt;= 0.60: return HealthScore.DEGRADED        elif total &gt;= 0.30: return HealthScore.SUSPENDED        else: return HealthScore.BANNED
3.4 与数字人民币智能合约的联动
健康状态直接驱动智能合约状态：
contract TTRNHealthContract {    mapping(address =&gt; HealthStatus) public nodeStatus;        event HealthDegraded(address node, uint8 oldTier, uint8 newTier, string reason);    event ConfigRightFrozen(address node, uint256 timestamp, bytes32 ncaRef);        function updateHealth(address node, uint8 score, bytes32 patrolNCA) external {        require(msg.sender == authorizedOracle, &quot;TTRN-ERR-001: Unauthorized oracle&quot;);                HealthStatus old = nodeStatus[node];        HealthStatus new = _calculateStatus(score);                if (new == HealthStatus.SUSPENDED &amp;&amp; old != HealthStatus.SUSPENDED) {            _freezeConfigRights(node);            emit ConfigRightFrozen(node, block.timestamp, patrolNCA);        }                if (new == HealthStatus.BANNED) {            _revokeDID(node);        }                nodeStatus[node] = new;    }        function _freezeConfigRights(address node) internal {        CCPMarket.freeze(node, &quot;TTRN-HEALTH-DEGRADED&quot;);    }}
四、与 TDCA 现有协议的接口规范
4.1 DID 绑定接口（过渡版）
正式通知机的 DID 绑定：DID = HSM_PublicKey + PUF_Fingerprint + Location_Hash
过渡版 DID 绑定（按 Tier）：
interface Tier1DID {    type: &quot;TTRN-T1&quot;;    did: string;  // did:tdca:t1:...    publicKey: string;  // 国密密码机公钥    teeAttestation: string;  // 云 TEE 远程证明    locationHash: string;  // 运营商定位 + GPS 哈希    dualSignature: [string, string];  // 两名管理员签名    createdAt: timestamp;    expiresAt: timestamp;  // 过渡期 DID 有效期：通知机部署后 90 天自动过期}interface Tier2DID {    type: &quot;TTRN-T2&quot;;    did: string;  // did:tdca:t2:...    publicKey: string;  // USBKey 公钥    teeAttestation: string;  // 手机 TEE 证明    biometricHash: string;  // 生物特征模板哈希（非原始数据）    locationHash: string;  // 运营商定位哈希    createdAt: timestamp;    expiresAt: timestamp;  // 过渡期 DID 有效期：通知机部署后 60 天自动过期}interface Tier3DID {    type: &quot;TTRN-T3&quot;;    did: string;  // did:tdca:t3:...    esimCertificate: string;  // 运营商 eSIM 证书    deviceFingerprint: string;  // 设备指纹哈希    behavioralBiometricBaseline: string;  // 行为生物基线    createdAt: timestamp;    expiresAt: timestamp;  // 过渡期 DID 有效期：通知机部署后 30 天自动过期}
4.2 准入网关协议（TTRN-Gateway）
ttrn_gateway:  /did/register:    method: POST    body: { tier: &quot;T1&quot; | &quot;T2&quot; | &quot;T3&quot;, credentials: TierCredential[], physicalProof: PhysicalProof }    response: { did: string, status: &quot;PENDING_PATROL&quot; | &quot;ACTIVE&quot;, patrol_deadline: timestamp }      /health/heartbeat:    method: POST    headers: { &quot;X-TTRN-DID&quot;: string, &quot;X-TTRN-Signature&quot;: string }    body: { timestamp: number, location: GeoPoint, deviceFingerprint: string, teeQuote: string }    response: { accepted: bool, healthScore: float, nextHeartbeat: timestamp }      /health/patrol:    method: POST    body: { did: string, patrolType: &quot;DAILY&quot; | &quot;WEEKLY&quot; | &quot;MONTHLY&quot;, biometricProof: string, geoProof: string, signature: string }    response: { patrolNCA: string, healthScoreDelta: float }      /health/challenge:    method: POST    body: { did: string, challengeId: string, challengeResponse: string }    response: { verified: bool, responseNCA: string }      /config-right/verify:    method: GET    params: { did: string, requestedRight: &quot;P-Right&quot; | &quot;S-Right&quot; | &quot;PUCR&quot; }    response: { granted: bool, effectiveTier: &quot;T1&quot; | &quot;T2&quot; | &quot;T3&quot;, restrictions: string[] }    # Tier-3 永远返回 P-Right: false
4.3 与 CCP 市场的联动
class TTRNMarketAdapter:    &quot;&quot;&quot;TTRN 健康状态适配 CCP 配置权市场&quot;&quot;&quot;        def before_pcr_submit(self, pcr: PCR) -&gt; PCRValidation:        node_health = ttrn_gateway.get_health(pcr.caller_did)                if node_health.status == &quot;SUSPENDED&quot;:            return PCRValidation(                rejected=True,                 reason=&quot;TTRN-HEALTH-SUSPENDED&quot;,                 nca_ref=node_health.nca            )                if node_health.status == &quot;DEGRADED&quot;:            pcr.utility_budget = min(                pcr.utility_budget,                 node_health.tier_max_budget            )            return PCRValidation(                rejected=False,                 modified=True,                 warning=&quot;TTRN-HEALTH-DEGRADED-LIMITED&quot;            )                if pcr.requested_right == &quot;P-Right&quot; and node_health.tier != &quot;T1&quot;:            return PCRValidation(                rejected=True,                 reason=&quot;TTRN-TIER-INSUFFICIENT-FOR-P-RIGHT&quot;            )                return PCRValidation(rejected=False)
五、切换路径：从 TTRN 到正式通知机
5.1 切换阶段（Switch-Over Phases）
Phase-1: TTRN 独占期（当前 - 通知机首批部署）    +- 所有节点使用 TTRN 三级体系    +- 健康信号半自动化    +- 限制：Tier-3 无 P-Right，跨场景 PCR 需 Tier-1 或 Tier-2Phase-2: 混合期（通知机首批部署 - 全国覆盖 80%）    +- 关键节点强制迁移至通知机（政府/金融/核心企业）    +- 普通节点可选：TTRN-T2 或 通知机    +- 边缘节点仍可用 TTRN-T3    +- 健康信号：通知机全自动，TTRN 半自动化Phase-3: 通知机独占期（全国覆盖 &gt; 80%）    +- 所有新节点必须使用通知机    +- TTRN 现有节点进入 90 天过渡期（Tier-1）/ 60 天（Tier-2）/ 30 天（Tier-3）    +- 过渡期结束后，TTRN DID 自动过期，配置权冻结    +- 健康信号全自动Phase-4: TTRN 退役期    +- 所有 TTRN 节点完成迁移或退役    +- TTRN 网关关闭，代码归档    +- 历史 TTRN NCA 永久存证（制度考古价值）
5.2 自动切换熔断条件
class SwitchOverTrigger:    &quot;&quot;&quot;触发从 TTRN 向通知机切换的条件&quot;&quot;&quot;        def evaluate(self, metrics: NetworkMetrics) -&gt; SwitchDecision:        if metrics.notify_machine_coverage &gt;= 0.80:            return SwitchDecision(phase=&quot;PHASE-3&quot;, reason=&quot;COVERAGE_THRESHOLD&quot;)                if metrics.ttrn_security_incidents_30d &gt;= 3:            return SwitchDecision(phase=&quot;EMERGENCY-MIGRATION&quot;, reason=&quot;SECURITY_BREACH&quot;)                if metrics.ttrn_health_oracle_failure_rate &gt; 0.10:            return SwitchDecision(phase=&quot;EMERGENCY-MIGRATION&quot;, reason=&quot;ORACLE_FAILURE&quot;)                if cbdc_contract.requires_hardware_root():            return SwitchDecision(phase=&quot;PHASE-2&quot;, reason=&quot;CBDC_MANDATE&quot;)                return SwitchDecision(phase=&quot;MAINTAIN&quot;, reason=&quot;NO_TRIGGER&quot;)
5.3 迁移补偿机制
TTRN 节点向通知机迁移时，产生迁移成本（设备采购、部署、配置）。TDCA 提供迁移补偿： - Tier-1 节点：政府/核心企业迁移费用纳入财政预算直达（TDCA 宏观治理章节） - Tier-2 节点：OPC/普通企业可申请 PUCR（预售配置权请求）融资迁移 - Tier-3 节点：个人开发者免费发放入门级通知机（政府补贴 + 生态基金） - 所有迁移节点：迁移期间配置权交易不受中断，TTRN 与通知机并行运行 30 天
六、安全降级风险评估与负空间声明
6.1 TTRN 与正式通知机的安全差距分析
威胁模型
正式通知机
TTRN-Tier-1
TTRN-Tier-2
TTRN-Tier-3
私钥提取
不可能（HSM/PUF）
极难（密码机需物理拆解）
难（USBKey 需专业设备）
中等（eSIM 可复制）
DID 伪造
不可能
极难（需双签 + 密码机）
难（需生物 + USBKey）
可能（eSIM 克隆）
位置欺骗
不可能（PUF + GPS + 基站）
难（需多人共谋）
中等（虚拟定位 APP）
容易（改 GPS）
节点批量伪造
不可能（硬件成本 + 物理部署）
难（密码机成本高）
中等（USBKey 批量购买）
容易（多手机）
内部人攻击
难（单人无法操作）
难（双人双签）
中等（单人 + USBKey）
容易（单人）
实时健康盲区
无（全自动）
小（每日巡检）
中（每周巡检）
大（每月巡检）
6.2 负空间声明（NSFL 表达）
TTRN 作为过渡方案，其负空间边界必须显式声明：
TTRN-NEGATIVE-SPACE {    // 绝对禁止    otimes TTRN-Tier-3 持有 P-Right 或发起跨场景 PCR    otimes TTRN 任何 Tier 绕过人工巡检（自动化不可完全替代人类确认）    otimes TTRN 节点使用非国密算法（SM2/SM3/SM4 是底线）    otimes TTRN 健康评分算法被单一主体控制（必须多签治理）    otimes TTRN DID 永久有效（必须设置过期时间，强制切换通知机）        // 限制空间（需人类裁决）    warning TTRN-Tier-2 单笔交易 &gt; 10 万元数字人民币需人工审批    warning TTRN-Tier-1 密码机更换需双人双签 + 联盟链公告    warning TTRN 健康评分 &lt; 0.60 时，自动降级但保留审计权（不可直接删除数据）        // 过渡承诺    timer TTRN 最长有效期：通知机部署后 90 天（Tier-1）/ 60 天（Tier-2）/ 30 天（Tier-3）    timer TTRN 网关必须在通知机覆盖 80% 后 180 天内关闭}
6.3 风险接受声明
TDCA 制度设计师（H）签署：
“TTRN 过渡方案在制度安全上 低于正式通知机但高于纯软件方案，其风险已被量化、被监控、被熔断。在通知机部署完成前，TTRN 是 可接受的制度妥协，但绝非 制度终点。过渡期内的所有配置权交易，其税收锚定（MOU）效力与正式通知机等同，但 NCA 审计轨迹须附加 TTRN-Tier-X 标签，供未来制度考古与责任追溯。”
七、开发任务分解（Reasonix 可执行）
7.1 任务清单
任务 ID
内容
优先级
工时
依赖
负责人
T-TTRN-001
TTRN 网关核心开发（DID 注册/心跳/健康评分）
P0
3 周
无
协议工程师（M）
T-TTRN-002
国密密码机/USBKey 集成 SDK（Java/C++）
P0
2 周
T-TTRN-001
协议工程师（M）
T-TTRN-003
云 TEE 远程证明验证模块
P0
2 周
T-TTRN-001
协议工程师（M）
T-TTRN-004
运营商 eSIM/定位 API 集成
P1
1 周
T-TTRN-001
协议工程师（M）
T-TTRN-005
人工巡检 APP 开发（iOS/Android）
P1
2 周
T-TTRN-001
前端工程师
T-TTRN-006
健康评分算法实现 + 联盟链 Oracle
P0
2 周
T-TTRN-001
协议工程师（M）
T-TTRN-007
数字人民币智能合约联动（冻结/解冻/吊销）
P0
2 周
T-TTRN-006 + CCP-V0.1
协议工程师（M）
T-TTRN-008
社区众包验证模块（邻近节点交叉 ping）
P2
1 周
T-TTRN-006
协议工程师（M）
T-TTRN-009
切换路径自动化（Phase 检测 + 迁移补偿）
P1
2 周
T-TTRN-007
制度设计师（H）+ M
T-TTRN-010
与 TDCA-5CC 五柱集成测试
P1
2 周
全部完成
全团队
7.2 Reasonix 分支策略
branches:  ttrn-main: &quot;TTRN-001~010 主开发线&quot;  ttrn-hsm: &quot;国密硬件集成子模块&quot;  ttrn-tee: &quot;云 TEE 证明子模块&quot;  ttrn-mobile: &quot;巡检 APP 与 eSIM 子模块&quot;  ttrn-contract: &quot;数字人民币智能合约子模块&quot;  integration-5cc: &quot;与 TDCA-5CC 五柱集成测试&quot;
7.3 验收标准（MVP）
☐ TTRN-Tier-1 节点成功注册 DID，完成首笔 P-Right 配置权交易
☐ TTRN-Tier-2 节点成功注册 DID，完成首笔 S-Right 场景配置权交易
☐ TTRN-Tier-3 节点成功注册 DID，被拒绝 P-Right 申请（负空间验证）
☐ 人工巡检完成一次完整流程，巡检 NCA 上链存证
☐ 健康评分从 ACTIVE 降至 SUSPENDED，自动冻结配置权交易（数字人民币智能合约验证）
☐ 模拟通知机部署信号，TTRN DID 过期倒计时启动
八、签批栏
角色
签名
日期
裁决
制度设计师（H）
_____________
________
ACCEPT / REJECT / CONDITIONAL
协议工程师（M）
_____________
________
ACCEPT / REJECT / CONDITIONAL
安全红队
_____________
________
ACCEPT / REJECT / CONDITIONAL
签批条件：三方全部 ACCEPT，或两方 ACCEPT + 一方 CONDITIONAL（须附修正项清单）。冻结规则：签批后进入 FROZEN 态，后续修改须走 DCD 变更流程。特别条款：本规范在通知机部署完成前持续有效，通知机覆盖率达 80% 后自动触发 PHASE-3 切换。
本文档由 TDCA 制度工程协作基础设施生成，遵循 TDCA-WORKING-SPEC-001 格式规范。 术语基线：TDCA 术语防火墙 V2.1（FROZEN-20260808） 安全基线：国密 GM/T 系列标准 / FIDO2 / 运营商 eSIM 规范