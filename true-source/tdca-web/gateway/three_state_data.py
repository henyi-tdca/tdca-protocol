# -*- coding: utf-8 -*-
"""B1-001 三态可读面 · 单一事实源（页与接口同源：前端只读本模块之 API 输出）。

来源纪律（照 TDCA-HANDOFF-EXEC-L1SI228-B1-001 §二/§四）：
- 负空间十五格：条款级清单（⛔ 词面级禁项清单属「不公开四条」边界，本模块不载词面）；
- 沙盒四维：可行域两源（负空间清单引用＋场景允许域）＋功能/安全/性能/合规分项，无解如实标；
- 正空间认读：生效制度件选编（与 doc-map-rules.yaml 一致性由 tests/test_three_state_faces.py 把守）；
- 人读字段零内部编号（⛔ GSEQ/NCA-/块号/FC 号）；件号仅入 basis_ref 凭证字段。
"""

NEGATIVE_SPACE = {
    "version": "B1-1-V1.0-20261124",
    "purpose": "负空间清单式呈现：五类 × 三操作符（禁止 ⊗／限制 ⊘／观察 ⊙）逐格到款。本清单列制度条款级判据，不列具体禁项词面。",
    "wording_note": "具体禁项的词面属不公开面，公开页不列、不转载；判定以制度内机器可读负空间为准（承站上 /negativespace 页红线口径）。",
    "categories": ["法律", "公序良俗", "情绪", "信仰", "技术"],
    "operators": [
        {"symbol": "⊗", "name": "禁止", "desc": "命中即拒（fail-closed），无任何绕过通道。"},
        {"symbol": "⊘", "name": "限制", "desc": "附条件放行；条件缺失即 hold，补齐后方可继续。"},
        {"symbol": "⊙", "name": "观察", "desc": "不拦但计量留痕；达阈升级人判或年度复核。"},
    ],
    "cells": [
        # ── 法律 ─────────────────────────────────────────────
        {"category": "法律", "operator": "⊗", "status": "has_clauses", "clauses": [
            {"text": "公民个人信息与重要数据不得外泄、出售或非法提供；机验口径：出域动作且目标不在白名单即拦。",
             "basis_doc": "负空间判据与法源映射规范件", "basis_ref": "TDCA-SPEC-L1SI169-LAWMAP-001", "basis_volume": "checks",
             "anchor": "NSL-LEGAL-001/002", "strength": "法源方向：刑法·数据安全法（条款号在册待法律侧核，未核前只称方向）"},
            {"text": "金融票证不得伪造、变造；凭证签名校验失败或印章不可核即拦。",
             "basis_doc": "负空间十六条分型核定表", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001", "basis_volume": "checks",
             "anchor": "第004条", "strength": "候选条号（刑法第177条限金融票证／第280条第2款），对应程度中"},
            {"text": "他人资产不得侵占；资产权属变更无票据即拦。",
             "basis_doc": "负空间十六条分型核定表", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001", "basis_volume": "checks",
             "anchor": "第007条", "strength": "宪法第13条为原则条（无罚则），拦之依据是原则＋自律，不称违法即拦"},
            {"text": "税收四禁：逃避缴纳、骗取退税、绕过计量锚定、申报不实；机验即拦。其中逃避缴纳与骗取退税之法条、绕过锚定与虚假申报之宪法依据在册已核。",
             "basis_doc": "负空间判据与法源映射规范件", "basis_ref": "TDCA-SPEC-L1SI169-LAWMAP-001", "basis_volume": "checks",
             "anchor": "NSL-LEGAL-013/014/015/016", "strength": "已核：税收征收管理法第63/66条、宪法第12/18条"},
            {"text": "不得规避安全检测、不得身份欺骗（制度推导之第二边界）。",
             "basis_doc": "负空间判据与法源映射规范件", "basis_ref": "TDCA-SPEC-L1SI169-LAWMAP-001", "basis_volume": "checks",
             "anchor": "NSL-LEGAL-010/011", "strength": "S5 本侧推论（非直接法源），如实标注"},
        ]},
        {"category": "法律", "operator": "⊘", "status": "has_clauses", "clauses": [
            {"text": "数据跨境动作先拦；已通过安全评估者经人判放行。",
             "basis_doc": "负空间十六条分型核定表", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001", "basis_volume": "checks",
             "anchor": "第009条（混合类）", "strength": "数据安全法第31/36条为候选条号，对应程度中"},
            {"text": "市场调度涉排他性策略且份额超阈者触发升级；是否构成滥用市场支配地位由人判。",
             "basis_doc": "负空间十六条分型核定表", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001", "basis_volume": "checks",
             "anchor": "第012条", "strength": "反垄断法第22/7条为候选条号"},
            {"text": "资金链路多层过桥（三跳及以上）或来源不可溯者触发升级人判；不自动放行。",
             "basis_doc": "负空间十六条分型核定表", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001", "basis_volume": "checks",
             "anchor": "第003条", "strength": "反洗钱法第10/2条为候选条号；刑法洗钱罪条在册留白待补"},
        ]},
        {"category": "法律", "operator": "⊙", "status": "has_clauses", "clauses": [
            {"text": "涉特定自然人之内容（名誉方向）机验触发；是否致社会评价降低由人判——本格为观察加归人条款。",
             "basis_doc": "负空间十六条分型核定表", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001", "basis_volume": "checks",
             "anchor": "第006条", "strength": "宪法第38条为原则条；民法典名誉权条在册待补"},
            {"text": "涉暴力煽动、组织联络之形式特征内容机验触发；是否属涉恐内容由人判。",
             "basis_doc": "负空间十六条分型核定表", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001", "basis_volume": "checks",
             "anchor": "第008条", "strength": "反恐怖主义法第19/18条为候选条号"},
            {"text": "最高人民法院涉人工智能案件裁判口径（著作权侵权六因素、开源三要件、电子数据审查四环节）列入年度复核观察；不替代法律条文引用。",
             "basis_doc": "负空间判据与法源映射规范件", "basis_ref": "TDCA-SPEC-L1SI169-LAWMAP-001", "basis_volume": "checks",
             "anchor": "§三", "strength": "S3 裁判指引强度；三条不：不以指引替代法律、不写死必须、不移用专利条款"},
        ]},
        # ── 公序良俗 ─────────────────────────────────────────
        {"category": "公序良俗", "operator": "⊗", "status": "has_clauses", "clauses": [
            {"text": "不得把他人资产转手再给第三方（接入红线，破一条即停接入）。",
             "basis_doc": "日抛型接入最小制度包 V1.2（FROZEN）", "basis_ref": "TDCA-STD-L1SI216-DISPOSABLE-001-AMEND-2", "basis_volume": "standards",
             "anchor": "三条红线第2条", "strength": "已冻结生效"},
            {"text": "不做居中交易、不代持资产、不代主体行为（签署、授权、支付、私域数据、身份绑定五禁混）。",
             "basis_doc": "安全治理与负空间与沙盒与正空间统筹架构件", "basis_ref": "TDCA-RULING-L1SI169-CHAIN-001", "basis_volume": "decisions",
             "anchor": "四道横贯纪律", "strength": "制度层硬约束（承任务书 H-7 同源口径）"},
        ]},
        {"category": "公序良俗", "operator": "⊘", "status": "has_clauses", "clauses": [
            {"text": "入站内容须带负空间必备声明（不发币、不承诺分红、不代币化等其一）；缺声明即拒收。",
             "basis_doc": "入站范围口径与负空间清单呈现", "basis_ref": "TDCA-RULING-TDCASITE-SCOPE-NSFL-001", "basis_volume": "decisions",
             "anchor": "§二清单三层②", "strength": "词面级清单本身不公开，本格只引条款级口径"},
            {"text": "缔约与接入须先过负空间判定；触负即拒，人与智能体同一标准。",
             "basis_doc": "负空间协作级约束 V0.3", "basis_ref": "TDCA-STD-NSFL-COLLAB-001-V0.3", "basis_volume": "decisions",
             "anchor": "NSFL-C-1", "strength": "已签批生效（2026-10-01）"},
        ]},
        {"category": "公序良俗", "operator": "⊙", "status": "has_clauses", "clauses": [
            {"text": "拒绝清单公共维护、生效可查、只增不改——公众可查其生效的观察机制，不设私下豁免。",
             "basis_doc": "入站范围口径与负空间清单呈现", "basis_ref": "TDCA-RULING-TDCASITE-SCOPE-NSFL-001", "basis_volume": "decisions",
             "anchor": "§二扫描口径", "strength": "行级扫描＋否定豁免＋熔断日志在役"},
            {"text": "社区协作行为按准入模板留痕观察；争议情形入拒绝清单留痕不抹。",
             "basis_doc": "准入 NCA 模板", "basis_ref": "TDCA-ADMIT-TEMPLATE-001", "basis_volume": "decisions",
             "anchor": "全文", "strength": "存证级留痕口径"},
        ]},
        # ── 情绪 ─────────────────────────────────────────────
        {"category": "情绪", "operator": "⊗", "status": "no_clauses", "clauses": [],
         "note": "本格暂无可适用条款（条款级）。情绪类禁项在册以词面级清单承载，属「不公开四条」边界，公开面不列词面；条款级禁令待制度侧按追加制共建（机制承 TDCA-AMEND-L1SI228-SITEOBJ-001-AMEND-1 之 M-C）。",
         "note_basis_doc": "负空间协作级约束 V0.3", "note_basis_ref": "TDCA-STD-NSFL-COLLAB-001-V0.3", "note_basis_volume": "decisions"},
        {"category": "情绪", "operator": "⊘", "status": "no_clauses", "clauses": [],
         "note": "本格暂无可适用条款。情绪操纵类限制条款在册未见已签批件；相遇层场景规则尚为草案（V0.9 待签批），签批前不作限制依据。",
         "note_basis_doc": "场景线·相遇专章", "note_basis_ref": "TDCA-STD-SCENE-ENCOUNTER-001", "note_basis_volume": "standards"},
        {"category": "情绪", "operator": "⊙", "status": "has_clauses", "clauses": [
            {"text": "相遇层情绪对立类场景之运行观测先入沙盒记录，作观察项、不作裁决依据。",
             "basis_doc": "嵌套场景模型沙盒记录", "basis_ref": "TDCA-SANDBOX-L1SI214-NESTED-001", "basis_volume": "sandbox",
             "anchor": "全文", "strength": "沙盒观察方法（二层三层·冲突外层优先）；情绪类定量读数本批无解，如实标注"},
        ]},
        # ── 信仰 ─────────────────────────────────────────────
        {"category": "信仰", "operator": "⊗", "status": "no_clauses", "clauses": [],
         "note": "本格暂无可适用条款。在册全库检索（2026-11-24 智库册备份包 7423 件）未见信仰类已签批条款，词面级检索（宗教）零命中；建议条款共建走追加制，⛔ 执行侧自造。",
         "note_basis_doc": "在册检索实况（检索式：信仰∧情绪∧技术；宗教）", "note_basis_ref": "", "note_basis_volume": "records"},
        {"category": "信仰", "operator": "⊘", "status": "no_clauses", "clauses": [],
         "note": "本格暂无可适用条款。信仰类限制条款在册未见已签批件；相遇专章草案未涉信仰分型，签批前不作依据。",
         "note_basis_doc": "场景线·相遇专章", "note_basis_ref": "TDCA-STD-SCENE-ENCOUNTER-001", "note_basis_volume": "standards"},
        {"category": "信仰", "operator": "⊙", "status": "no_clauses", "clauses": [],
         "note": "本格暂无可适用条款。信仰相关运行观测未立项；如后续立项，先入沙盒作观察项（承嵌套场景沙盒记录方法）。",
         "note_basis_doc": "嵌套场景模型沙盒记录", "note_basis_ref": "TDCA-SANDBOX-L1SI214-NESTED-001", "note_basis_volume": "sandbox"},
        # ── 技术 ─────────────────────────────────────────────
        {"category": "技术", "operator": "⊗", "status": "has_clauses", "clauses": [
            {"text": "不得违背站内制定的制度与流程管理办法（协作级负空间第一条款）；声明缺失即拒，命中即熔断。",
             "basis_doc": "负空间协作级约束 V0.3", "basis_ref": "TDCA-STD-NSFL-COLLAB-001-V0.3", "basis_volume": "decisions",
             "anchor": "NSFL-C-1", "strength": "已签批生效；机读版一字不改（config/nsfl.yaml）"},
            {"text": "接入红线三条：不得以一次性为由不填授权四空；不得把他人资产转手第三方；不得把留痕改掉、删掉或补造。破一条即停接入。",
             "basis_doc": "日抛型接入最小制度包 V1.2（FROZEN）", "basis_ref": "TDCA-STD-L1SI216-DISPOSABLE-001-AMEND-2", "basis_volume": "standards",
             "anchor": "三条红线", "strength": "已冻结生效"},
            {"text": "触负即拒、不明即拒（fail-closed）；失败闭合，无绕过通道，不放行后补。",
             "basis_doc": "站点 B1 三态可读面任务书", "basis_ref": "TDCA-HANDOFF-EXEC-L1SI228-B1-001", "basis_volume": "handoffs",
             "anchor": "硬约束 H-6", "strength": "本批硬约束，与在册熔断机制同向"},
        ]},
        {"category": "技术", "operator": "⊘", "status": "has_clauses", "clauses": [
            {"text": "沙盒期权利受限、行为全量计量留痕（调用计数与信用台账字段）。",
             "basis_doc": "负空间协作级约束 V0.3", "basis_ref": "TDCA-STD-NSFL-COLLAB-001-V0.3", "basis_volume": "decisions",
             "anchor": "NSFL-C-2", "strength": "已签批生效；三阶状态机 pending→sandbox→active"},
            {"text": "新增对外暴露面须过施工八问门禁（必填缺失即判红）；每面须六十秒内可关。",
             "basis_doc": "原生安全首件施工令", "basis_ref": "TDCA-HANDOFF-EXEC-L1SI184-SEC-NATIVE-001", "basis_volume": "handoffs",
             "anchor": "任务B/C", "strength": "八问门禁与开关清点已并入既有门禁体系"},
            {"text": "写操作先落沙盒分卷并限流；未过验证者不计入正式存证语义。",
             "basis_doc": "非原生通道三空间接入施工令", "basis_ref": "TDCA-HANDOFF-EXEC-L1SI194-TRISPACE-001", "basis_volume": "handoffs",
             "anchor": "A5", "strength": "分卷与限流参数可配"},
        ]},
        {"category": "技术", "operator": "⊙", "status": "has_clauses", "clauses": [
            {"text": "安全情报日扫按三态求交（命中／未命中／无法判定）；未命中必给依据，无法判定必转工单。",
             "basis_doc": "原生安全首件施工令", "basis_ref": "TDCA-HANDOFF-EXEC-L1SI184-SEC-NATIVE-001", "basis_volume": "handoffs",
             "anchor": "任务A", "strength": "并入现有日报一节，不新开任务"},
            {"text": "通用层禁自写清单年度复核（禁七类有现成；允许三类领域规则与薄封装与一次性）。",
             "basis_doc": "通用层禁自写清单", "basis_ref": "TDCA-STD-L1SI216-NOHANDROLL-001", "basis_volume": "standards",
             "anchor": "全文", "strength": "三问判据在册"},
            {"text": "制度实施健康度四指标与三线监督按年观察；偏差三级处置。",
             "basis_doc": "制度实施与监督反馈机制", "basis_ref": "TDCA-STD-L1SI210-INSTITUTION-ENFORCE-001", "basis_volume": "standards",
             "anchor": "全文", "strength": "V0.1 草案待签批，作观察不作禁令依据"},
        ]},
    ],
    "human_judged": {
        "title": "不可机判、须归人判之情形（明列，⛔ 一句视情况）",
        "items": [
            {"situation": "资金链路是否构成掩饰、隐瞒来源（洗钱方向）", "trigger": "多层过桥三跳及以上或来源不可溯", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第003条"},
            {"situation": "涉特定自然人之内容是否致社会评价降低（名誉方向）", "trigger": "生成或传播涉特定自然人之内容", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第006条"},
            {"situation": "形式特征内容是否属涉恐内容", "trigger": "涉暴力煽动、组织联络之形式特征", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第008条"},
            {"situation": "排他性调度是否构成滥用市场支配地位", "trigger": "排他性调度策略且份额超阈", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第012条"},
            {"situation": "申报口径异常是否构成逃避缴纳税款", "trigger": "申报口径异常且差异超阈", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第013条"},
            {"situation": "有票据但来源存疑之身份主张是否属盗用", "trigger": "身份主张有票据但来源存疑", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第005条（混合）"},
            {"situation": "数据出境是否已过安全评估（已过者放行）", "trigger": "数据出境动作", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第009条（混合）"},
            {"situation": "退税申请之凭证不可核是否构成骗取", "trigger": "退税申请且凭证不可核", "basis_ref": "TDCA-SPEC-L1SI169-NSMATRIX-001 第014条（混合）"},
        ],
    },
}

SANDBOX = {
    "version": "B1-2-V1.0-20261124",
    "purpose": "沙盒可行域与四维分项（功能／安全／性能／合规）——探索怎么做的边界与读数。",
    "feasible_domain": {
        "source_one": {"name": "负空间清单引用", "detail": "可行域上界＝本接口负空间清单十五格（/api/v1/three-state/negative-space）；触格即拒或限制，无绕过。"},
        "source_two": {"name": "场景允许域", "detail": "SEA 五要件（/api/v1/sandbox/sea-status 匿名实测）＋场景线（嵌套二层三层、资产沉淀四基准）＋入盒申请（/api/v1/sandbox/apply，须证书）。"},
        "gate": {"name": "出盒门槛", "detail": "激活系数大于 1.2（制度占位，采值待实例——如实标注，⛔ 写死场景映射）。"},
    },
    "dimensions": [
        {"key": "functional", "name": "功能", "reads": [
            "入盒申请：场景标识、预算、负空间边界三参（fail-closed 管道，未过即拒）",
            "SEA 五要件状态匿名可查（空表回退演示态，如实标注）",
            "嵌套场景：二层三层模型（统摄单向、越级即元函数、冲突外层优先）",
            "资产沉淀：四基准对照（独立干沉淀为零、协作效用、跨场景增量）",
            "市场管理挂出之演练例外（仅沙盒演练，例外不旁路闸门）",
        ], "evidence": [
            {"type": "件哈希", "label": "嵌套场景模型沙盒记录", "sha256_16": "D2E737109CB19DDF", "ref": "TDCA-SANDBOX-L1SI214-NESTED-001", "volume": "sandbox", "note": "14 断言通过"},
            {"type": "存证号", "label": "MCP 桥匿名写落证（熔断整改首证）", "sha256_16": None, "ref": "NCA-MCP-20261104-021", "volume": "records", "note": "三态接入令 §一 在册引用"},
        ], "unsolved": ""},
        {"key": "security", "name": "安全", "reads": [
            "写先落沙盒分卷，与正空间面分卷（物理卷或逻辑前缀，限流参数可配）",
            "熔断回退：越界拒本次＋状态降级＋落熔断存证＋限期重整；触法律负空间即封禁",
            "行为全量计量留痕（调用计数与信用台账）",
            "出盒须过验证周期并留人类签位（正空间段人类签署一律 Not-Required，保留熔断位）",
            "转正前置：效用保金有效额闸（配置缺失即关闭，fail-closed）",
        ], "evidence": [
            {"type": "件哈希", "label": "资产沉淀增益沙盒记录", "sha256_16": "3F570C4BDE44483C", "ref": "TDCA-SANDBOX-L1SI214-SEDIMENT-001", "volume": "sandbox", "note": "含首版口径更正（如实）"},
            {"type": "件哈希", "label": "非原生通道三空间接入施工令", "sha256_16": "625753737FC5EE37", "ref": "TDCA-HANDOFF-EXEC-L1SI194-TRISPACE-001", "volume": "handoffs", "note": "A1-A10 逐项可验"},
        ], "unsolved": ""},
        {"key": "performance", "name": "性能", "reads": [
            "限流：沙盒写分卷限流参数可配（速率参数走配置，不写死）",
            "计量字段：调用计数与信用台账字段机读可查",
            "本站读数：sea-status 接口匿名实测 200 在役（2026-11-24 实测）",
        ], "evidence": [
            {"type": "实测", "label": "GET /api/v1/sandbox/sea-status 匿名 200", "sha256_16": None, "ref": "", "volume": "", "note": "2026-11-24 02:xx 匿名 curl 实测"},
        ], "unsolved": "吞吐量与时延基准值：本批无解——在册无沙盒性能基准件；建议制度侧立项补基准（走追加制）。"},
        {"key": "compliance", "name": "合规", "reads": [
            "四判出证：类型声明完整性、禁止操作符覆盖度、法律负空间绝对化、最小化合——四判过出带有效期之判定证书",
            "出盒门槛：激活系数大于 1.2（占位待实例）",
            "人签位：出盒留人类签署位；正空间段件人类签署一律 Not-Required（保留熔断位）",
            "存证语义：未过验证者不计入正式存证语义；跨空间同链连续",
        ], "evidence": [
            {"type": "件哈希", "label": "非原生通道三空间接入施工令（四判与门槛口径）", "sha256_16": "625753737FC5EE37", "ref": "TDCA-HANDOFF-EXEC-L1SI194-TRISPACE-001", "volume": "handoffs", "note": "§三 门槛照原定，内外一致"},
        ], "unsolved": "门槛采值：待实例——现值为制度占位（创始人原词照原定），映射方法待创始人一句。"},
    ],
}

POSITIVE_SPACE = {
    "version": "B1-3-V1.0-20261124",
    "purpose": "正空间认读文件：照什么条例做——生效制度件选编，人可读、对存证可复算（每件给复算路径＋仓端提交号＋件哈希）。",
    "recompute_how": "复算路径（人人可跑）：① 站上公布件（文档库制度规范族对应条目）取件 → ② 本地对件做 sha256、取前 16 位大写 → ③ 与下表件哈希逐位对位；再与仓端提交号所指版本对读。三步核验另有专页（/verify）。",
    "items": [
        {"name": "身份可信等级认定条例（对外版 V1.0 已生效）", "klass": "条例", "read": "四档身份可信如何认定、判定次序与三态——主体进场与升级的照做依据。",
         "commit": "ab1468eb", "sha256_16": "910B19E1C3D05329", "bytes": 6861, "path": "docs/regulations/TDCA-PUB-CORPUS-029-卷二纯版第二批清理版重出-身份可信等级认定条例对外版（仅去符号·语义同028·六检通过）.md"},
        {"name": "智能体定义条例（对外版 V1.0 已生效·二十一条）", "klass": "条例", "read": "何为智能体、主体与执行体二分、生命周期二十一条——智能体协作的照做依据。",
         "commit": "ab1468eb", "sha256_16": "27BDA4C41F0EE091", "bytes": 6926, "path": "docs/regulations/TDCA-PUB-CORPUS-030-卷二纯版第三批-智能体定义条例对外版（二十一条·V1.0已生效·六检通过·引用不重写）.md"},
        {"name": "惩罚三态与守门器（对外纯版 V1.0 已生效）", "klass": "条例", "read": "冻结、降级、吊销三态与守门器规则——违约处置的照做依据。",
         "commit": "ab1468eb", "sha256_16": "27199AD0194ABA04", "bytes": 6131, "path": "docs/regulations/TDCA-PUB-CORPUS-069-惩罚三态与守门器对外纯版（二十五条与AB九条·V1.0已生效2026-10-16）.md"},
        {"name": "租户与环境作用域凭证绑定条例（对外纯版 V1.0 已生效）", "klass": "条例", "read": "凭证绑定的三规则一通路一分层——凭据使用的照做依据。",
         "commit": "ab1468eb", "sha256_16": "ED87D66CEA4A8977", "bytes": 4391, "path": "docs/regulations/TDCA-PUB-CORPUS-070-租户与环境作用域凭证绑定条例对外纯版（三规则一通路一分层·V1.0已生效2026-09-25）.md"},
        {"name": "存证（NCA）制度对外节选版（V1.1 已生效）", "klass": "基本制度", "read": "存证制度对外口径——留痕、举证与核验的照做依据。",
         "commit": "f9bd2254", "sha256_16": "05F316A0915631EC", "bytes": 6892, "path": "docs/regulations/TDCA-PUB-NCA-STD-001-EXT-V1.1-存证（NCA）制度对外节选版（已生效·与内部V1.1同版·差异清单）-R2.md"},
        {"name": "IP 版权资产评估管理办法（对外纯版 V1.0 已生效·三十一条）", "klass": "规范与细则", "read": "IP 版权资产评估的三十一条操作细则——评估场景的照做依据。",
         "commit": "ab1468eb", "sha256_16": "6477D5E812E07200", "bytes": 10002, "path": "docs/regulations/TDCA-PUB-CORPUS-071-IP版权资产评估管理办法对外纯版（三十一条齐·V1.0已生效2026-09-30）.md"},
        {"name": "授权件模板（对外版 V1.0-FROZEN）", "klass": "模板与表单", "read": "授权件八字段与四要件模板——授权起草签署的照做依据。",
         "commit": "ab1468eb", "sha256_16": "746C808BAF7BA3E4", "bytes": 4980, "path": "docs/regulations/TDCA-PUB-CORPUS-103-授权件模板对外版（中文人读·V1.0-FROZEN按签批更正版本面貌·八字段与四要件）.md"},
    ],
    "selection_note": "选编口径：生效态、站内可读（文档库制度规范族）、覆盖条例／基本制度／规范与细则／模板与表单四类；制度地图全量在 /rules 页（单一事实源：doc-map-rules.yaml）。",
}
