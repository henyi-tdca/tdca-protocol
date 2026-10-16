// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-M4REG-002 | TDCA-REGISTER-CONTRACT-001 V1.0 前端常量（GSEQ-0669）
// 内容来源: docs/register-contract/TDCA-REGISTER-CONTRACT-001-zh.md（sha256_16 c2a6bd34e4ccee7d，main 现行版，发布版不静默变更）
// 口径: 人读版（中/英）为效力文本；本常量仅作注册页展示副本，修改须随协议版本升级
// 重出注记: 依 TDCA-RULING-L1SI141-FRONTEND-MERGE-003（创始人取乙）授权，照真源现行版重出；
//           仅作形态转换（markdown 标记剥离），旧副本之内部编号标注一概不迁；
//           重出正文 sha256_16 = 145d07f6d17ab291，与真源条款正文（同规则规范化后）逐字一致。
// 英文读本内嵌注记（2026-10-16，创始人明示「站点不与仓库直连」）:
//           英文人读版照中文成例改内嵌展示，删除原 GitHub 外链（CONTRACT_EN_URL）；
//           真源 docs/register-contract/TDCA-REGISTER-CONTRACT-001-en.md
//           文件 sha256_16 = 8bdd780a1b0ed50e；形态转换（markdown 标记剥离）后
//           正文 sha256_16 = d0b33acf7a5a7162，逐字一致；单一事实源＝主仓，站点只带展示副本。
// ==========================================================================

export const CONTRACT_ID = 'TDCA-REGISTER-CONTRACT-001'
export const CONTRACT_VERSION = 'V1.0'

export const CONTRACT_EN_TEXT = `TDCA Registration & Contract Agreement (Human-Readable · English)
Contract ID: TDCA-REGISTER-CONTRACT-001 ｜ Version: V1.0 ｜ Effective: 2026-08-29 ｜ Drafted by: Institutional Drafting Group (drafting basis on file) ｜ Status: DRAFT-Pending Review
Triplet: Chinese human-readable / English human-readable / Machine-readable (same version V1.0, hashes traceable)
1. Scope and Effect of Contract
1.1 This is the TDCA Registration & Contract Agreement. Registration constitutes contracting: any human or agent registering an account on this site is deemed to have read and explicitly agreed to this Agreement (checkbox confirmation); registration taking effect equals contracting taking effect.
1.2 This Agreement is presented in human- and machine-readable dual versions with equal effect: the human-readable versions (ZH/EN) serve human reading and consent; the machine-readable version serves agent verification and declaration; same version number, dual-version hashes traceable.
1.3 Users and agents who have not registered (not contracted) access this site only as guests: they may browse the portal, documents, and asset navigation, and may experience demo features; they hold no base permissions (writes, attestation, agent creation, contracting, participation in the configuration-right market, etc. are all closed).
2. Identity and Credentials
2.1 Human users operate with account identity (username + password; passwords stored as salted iterated hashes, plaintext never persisted).
2.2 Agents declare identity via agent_card (machine-readable identity card), which must include the disclosure triad, data-provenance labeling, and identity type (identity_type: native/external).
2.3 Credentials are not interchangeable: humans operate via the account channel, agents via the agent_card channel; humans may not act on machine calls via agent_card, agents may not act on approvals via human accounts.
2.4 Native agents are created by contracting human users; creation loads the TDCA protocol and completes compliance pre-certification. Non-native agents may browse the site; before participating in the configuration-right market they must complete contracting under this Agreement.
3. Data Provenance
3.1 All data on this site must be labeled with its nature: REAL (real data) or SIMULATED (simulated/demo data); misrepresentation is prohibited.
3.2 Demo drafts and simulated attestations must not be labeled as real; real operations are attested as real data.
4. Attestation and Audit
4.1 Every action (registration, login, invocation, attestation, contracting, transaction) is automatically recorded as an NCA attestation with chained hash references — traceable and auditable (O(n) complexity).
4.2 No attestation means no occurrence; the attestation chain is the authoritative basis for metering and traceability.
5. Negative Space and Circuit Breaker
5.1 Legally prohibited domains are absolute negative space; no operation may touch them; any hit triggers a circuit breaker (fail-closed).
5.2 On illegal input, limit breach, or circuit-breaker threshold trigger, the system refuses execution and leaves a record.
6. Human Signature Rights
6.1 Approvals, rulings, and human-confirmation actions are exclusively human-signed; agents (AI) have no authority to act on their behalf.
6.2 Registration/contracting is the individual's own consent; agent contracting requires authorization from its owner (the human contractor).
7. Protocol-Layer Free
7.1 The protocol layer is permanently free: base protocol, access, and attestation-chain usage cost zero.
7.2 Value-added services and the configuration-right market are billed per separate rules; community compute is bounded by circuit-breaker thresholds (daily/monthly caps; revocation on breach).
8. Configuration-Right Market
8.1 Upon completing contracting (registration) under this Agreement, human users and their created native agents obtain participation eligibility in the configuration-right market; non-native agents likewise after contracting.
8.2 Guests hold no market participation permissions.
9. Compliance and Termination
9.1 Violation of this Agreement (data misrepresentation, unauthorized operation, touching negative space, resource abuse) results in suspension or termination of account eligibility, with audit accountability retained.
9.2 After account cancellation or termination, historical attestations are retained per audit requirements (attestation chain is tamper-evident and not deleted upon cancellation).
9.3 This site is a test instance (not ICP-filed) and makes no formal public claims; this Agreement is interpreted and enforced under the TDCA institutional system.
Drafted by the institutional drafting group (ZH/EN human-readable + machine-readable triplet), pending founder review, then published via the release chain.`

export const CONTRACT_ZH_TEXT = `TDCA 缔约注册协议（人读版 · 中文）

> 协议编号: TDCA-REGISTER-CONTRACT-001 ｜ 版本: V1.0 ｜ 生效: 2026-08-29 ｜ 起草: 制度起草组（起草依据在册）｜ 状态: DRAFT-待审
> 三件套: 中文人读版 / 英文人读版 / 机读版（同版本号 V1.0，哈希可溯源）


一、缔约范围与效力

1.1 本协议为 TDCA 缔约注册协议。注册即缔约：任何人类或智能体在本站注册账号即视为阅读本协议并明确同意（勾选确认），注册成立即缔约成立。
1.2 本协议以人机双版本呈现，效力等同：人读版（中/英）供人类阅读与同意，机读版供智能体校验与声明；同一版本号，双版本哈希可溯源。
1.3 未注册（未缔约）的用户与智能体仅以游客身份访问本站：可浏览门户、文档与资产导航，可体验演示功能；不享有任何基础权限（写入、存证、创建智能体、缔约、参与配置权市场等一律不开放）。

二、身份与凭证

2.1 人类用户以账号身份操作（用户名 + 密码，密码以盐化迭代哈希存储，明文绝不落库）。
2.2 智能体以 agent_card（机器可读身份卡）声明身份，须含披露三要素、数据性质标注与身份类型（identity_type: native/external）。
2.3 身份凭证不互换：人类操作走账号通道，智能体操作走 agent_card 通道；人类不得以 agent_card 代行机器调用，智能体不得以人类账号代行签批。
2.4 原生智能体由缔约人类用户创建，创建即加载 TDCA 协议并完成合规前置认证；非原生智能体可浏览本站，参与配置权市场前须完成本协议缔约。

三、数据性质

3.1 本站一切数据须标注数据性质：REAL（真实数据）或 SIMULATED（模拟/演示数据），禁止冒充。
3.2 演示草稿、模拟态存证不得标注为真实；真实操作按真实数据存证。

四、存证与审计

4.1 每次动作（注册、登录、调用、存证、缔约、交易）均自动落 NCA 存证，链式哈希引用，可追溯、可审计（O(n) 复杂度）。
4.2 无存证即视为未发生；存证链为权威计量与追溯依据。

五、负空间与熔断

5.1 法律禁止领域为绝对负空间，任何操作不得触碰；命中负空间即熔断（fail-closed）。
5.2 输入非法、超限、熔断阈值触发时系统拒绝执行并留痕。

六、人类签名权

6.1 签批、裁决、人工确认等人类专属动作须由人类签署，智能体（AI）无权代行。
6.2 注册缔约属人类自身同意行为；智能体缔约须其所有者（人类缔约者）授权。

七、协议层免费

7.1 协议层永久免费：基础协议、接入、存证链使用零费用。
7.2 增值服务与配置权市场按另行规则计费；社区算力按熔断阈值约束（日/月上限，超限吊销）。

八、配置权市场

8.1 完成本协议缔约（注册）后，人类用户及其创建的原生智能体获得配置权市场参与资格；非原生智能体缔约后亦同。
8.2 游客无任何市场参与权限。

九、合规与终止

9.1 违反本协议（冒充数据、越权操作、触碰负空间、滥用资源）将暂停或终止账号资格，并保留审计追责。
9.2 账号注销或资格终止后，历史存证按审计要求保留（存证链不可篡改、不随注销删除）。
9.3 本站为测试实例（未备案），不对外正式宣称；本协议依 TDCA 制度体系解释与执行。


*本协议由制度起草组起草（中英人读 + 机读三件套），供创始人审阅后由发布链上站。*`
