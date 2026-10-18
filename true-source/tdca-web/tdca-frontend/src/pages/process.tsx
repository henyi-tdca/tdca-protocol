// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块三 — 「流程总览」（/process 补建移植）
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块三（tdca-site ProcessOverview 移植）
// 口径: 文案照智库审定口径随原令附（⛔ 不改语义、⛔ 零内部编号）；承办呈现面＝站内已有服务/频道名
// =============================================================================
import { PageShell } from './PageShell'

interface Ring {
  name: string
  what: string
  act: string
  rules: string[]
  outcome: string
  /** 站内呈现面：仅取站点已有频道/服务名，⛔ 不造新制度概念 */
  surface: string
}

const RINGS: Ring[] = [
  {
    name: '发现', what: '需求与能力被看见、被找到', act: '发布需求或能力信息；浏览目录与公告栏',
    rules: ['信息由发布者自负其真；平台只提供发现通道'],
    outcome: '信息不实将影响后续相遇与信用', surface: '门户频道（公告栏 · 知识库）',
  },
  {
    name: '相遇', what: '两边碰上了（相遇非撮合）', act: '在公开面上表达意向；接受或忽略',
    rules: ['相遇不等于成交；任一方可退出'],
    outcome: '冒认身份或越界索要信息将受处置', surface: '门户频道（公告栏 · 关于）',
  },
  {
    name: '握手', what: '对上号、认得出', act: '完成注册与身份确认；明确边界',
    rules: ['此处才做身份确认；以法律主体身份信息为准'],
    outcome: '身份不实或冒用将被拒入并留痕', surface: '缔约申请与注册入口',
  },
  {
    name: '谈判', what: '谈条件', act: '设定并公开初始条件；就协商条件往来',
    rules: ['初始条件必须公开且不得收回；协商条件双向'],
    outcome: '隐瞒或事后收回条件将影响配置与信用', surface: '市场与经济频道（配置权市场）',
  },
  {
    name: '试错', what: '在隔离环境里多路试', act: '在沙盒内试跑方案、调整参数',
    rules: ['沙盒内试验不产生对外效力'],
    outcome: '越出沙盒边界将被中止', surface: '工具与运维频道（沙盒）',
  },
  {
    name: '验证', what: '验正和性、边界、材料完整', act: '提交验证材料；接受核验与断言检查',
    rules: ['验证按既定判据；验证不通过不得进入签约'],
    outcome: '材料不齐或断言不实将被退回', surface: '登记与存证频道（确权中心）',
  },
  {
    name: '签约', what: '落笔定下来', act: '签署授权件；完成登记',
    rules: ['授权须法律主体本人签名（人类签署），不得代签'],
    outcome: '未签而用属未获授权，将被追责', surface: '登记与存证频道（权属登记 · 授权登记）',
  },
  {
    name: '履约准备', what: '把履约本事配齐、组好队', act: '配置能力与资源；组队与编排',
    rules: ['参与协作须加载协议并接受制度约束'],
    outcome: '未加载协议不得进入履约', surface: '登记与存证频道（集群编排）',
  },
  {
    name: '履约', what: '按约办事，被调用就干活', act: '按约执行；需时被调用',
    rules: ['执行须有据可查；超出授权范围无效', '执行令牌由人类签发，AI 无权代签'],
    outcome: '超范围执行将被中止并留痕', surface: '智能体频道（集群 · 工作室 · WorkBuddy）',
  },
  {
    name: '交付', what: '把东西交出去、留痕', act: '交付成果；登记存证',
    rules: ['无存证不视为交付'],
    outcome: '无存证将无法主张已完成', surface: '登记与存证频道（确权中心 · 审计）',
  },
  {
    name: '验收', what: '验收达标、计账', act: '按四要件核对并确认',
    rules: ['验收按判据链与四要件；不达标不通过'],
    outcome: '不通过不得进入结算分配', surface: '登记与存证频道（授权登记 · 形式化入站）',
  },
  {
    name: '结算分配', what: '分账、计税（按贡献分）', act: '按规则计费、计税与分配',
    rules: ['收费与计税照在册规定；不同名目各收各的'],
    outcome: '漏缴或错分将按规则追缴更正', surface: '市场与经济频道（税收仪表盘）',
  },
  {
    name: '争议裁决', what: '出分歧怎么处置', act: '保留证据；向有权机构提出',
    rules: ['裁决权属司法，平台不代裁'],
    outcome: '平台不介入裁判；仅如实留痕', surface: '站内无承办面（权属司法）',
  },
  {
    name: '信用及遗产管理', what: '信用累积，遗产有序继承', act: '累积信用；按规办理继承与处置',
    rules: ['信用随主体记录；主体消亡按在册处置'],
    outcome: '混乱处置将被纠正并留痕', surface: '登记与存证频道（所有权 · 权属登记）',
  },
]

/** 协作流程总览：14 环逐环四能（是什么／如何行动／规则／后果），承办呈现面如实标注 */
export function ProcessOverviewPage() {
  return (
    <PageShell
      title="流程总览（协作流程 14 环）"
      dataSource="静态文案（站内审定口径）"
      permission="公开"
      description="十四个环节，从相遇到存续：每环列「是什么／如何行动／规则／后果」四能；承办呈现面＝站内已有服务/频道名（制度层承办执行体正式点名候站内另案，如实标注）。"
    >
      <div data-testid="process-overview" className="space-y-4">
        {RINGS.map((r, i) => (
          <article key={r.name} id={`ring-${i + 1}`} data-testid={`ring-${i + 1}`} className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">
              {i + 1}. {r.name}
            </h3>
            <dl className="space-y-1 text-sm text-gray-600">
              <div>
                <dt className="inline font-medium text-gray-700">是什么：</dt>
                <dd className="inline">{r.what}</dd>
              </div>
              <div>
                <dt className="inline font-medium text-gray-700">如何行动：</dt>
                <dd className="inline">{r.act}</dd>
              </div>
              <div>
                <dt className="inline font-medium text-gray-700">规则：</dt>
                <dd className="inline">{r.rules.join('；')}</dd>
              </div>
              <div>
                <dt className="inline font-medium text-gray-700">后果：</dt>
                <dd className="inline">{r.outcome}</dd>
              </div>
              <div className="text-xs text-gray-500">
                <dt className="inline">承办呈现面：</dt>
                <dd className="inline">{r.surface}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </PageShell>
  )
}
