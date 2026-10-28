// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块二 — 首页（正版门户内容 + 四层架构总览区并入）
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块二（首页＝正版内容＋总览区并入）
//          + FRAMEWORK-001 §四 /（A-1 契约）+ ID81（五元拓扑 Ω）+ ID92
// 来源: tdca-site 正版 Home.tsx（门户四段：三体／合规前置三阶／双通道缔约／机器可读通道）
//       —— standalone header/footer 不搬（壳归 AppShell）；样式变量类名按新基座调色板落；英文栏目名按创始人口径中文化
// =============================================================================
import { useApiGet } from '@/shared/useApi'
import { HomeNoticeBar } from '@/app/notice-bar'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { TopologyEngine, hashAgentId, type TopoData } from '@/components/workbuddy/TopologyEngine'
import { Link } from 'react-router'
import {
  ArrowRight,
  Bot,
  FileText,
  Globe2,
  Network,
  ScanSearch,
  Boxes,
  Users,
} from 'lucide-react'

const trinity = [
  {
    icon: FileText,
    title: '协议本体面',
    desc: '白皮书 · 论文 · 规范制度 · COP 权威库 · Weekly 周刊 —— 协议文档的站内真源呈现，运行时零平台依赖。',
  },
  {
    icon: Boxes,
    title: '人机协作面',
    desc: 'TDCA 人机协作线的状态与制度进展呈现。',
  },
  {
    icon: Network,
    title: '协议配置网络',
    desc: '分布式节点制度状态：缔约三阶、节点组件版本登记、调用计量 —— 全域一张图。',
  },
]

const stages = [
  {
    icon: ScanSearch,
    step: '第一阶',
    title: '负空间准入',
    desc: '缔约申请先过负空间扫描：触碰负面清单即拒，结果落库可审计。',
  },
  {
    icon: Users,
    step: '第二阶',
    title: '沙盒验证',
    desc: '通过后进沙盒态：权利受限、行为全量计量留痕，达标方可转正。',
  },
  {
    icon: Globe2,
    step: '第三阶',
    title: '正空间协作',
    desc: '转正为在空间成员，获得全量协作权利，入缔约名册。',
  },
]

interface OverviewData {
  total_deliveries: number
  total_tax_settled: string
  avg_latency_ms: number
  total_fused: number
  total_fail_closed: number
  tax_rates: { dispatch_tax: number; royalty: number; transaction_fee: number }
  theta: number
  phi: number
  system: string
}

/** 五元拓扑 Ω（ID81）：H/M/L 顶点 + 五关系边（官网 = Ω 前端坐标卡） */
const OMEGA_TOPO: TopoData = {
  nodes: [
    { id: hashAgentId('NODE-H'), label: 'H 人类', type: 'gov', status: 'active' },
    { id: hashAgentId('NODE-M'), label: 'M 智能体', type: 'official', status: 'active' },
    { id: hashAgentId('NODE-L'), label: 'L 学习体', type: 'user', status: 'active' },
  ],
  edges: [
    { from: hashAgentId('NODE-H'), to: hashAgentId('NODE-M'), label: '确权（HUF）', state: 'flowing' },
    { from: hashAgentId('NODE-M'), to: hashAgentId('NODE-L'), label: '教育（E-EDU）', state: 'flowing' },
    { from: hashAgentId('NODE-L'), to: hashAgentId('NODE-H'), label: '学习回馈', state: 'flowing' },
    { from: hashAgentId('NODE-M'), to: hashAgentId('NODE-H'), label: '税收锚定', state: 'flowing' },
    { from: hashAgentId('NODE-H'), to: hashAgentId('NODE-L'), label: '化合授权', state: 'flowing' },
  ],
}

export function HomePage() {
  const { status, data, nature } = useApiGet<OverviewData>('/api/v1/system/overview')

  return (
    <div data-testid="home-portal" className="space-y-0">
      {/* 批3 C块：首页公告条（一行高；无公告／后端不可用 → 不渲染，不占首屏） */}
      <HomeNoticeBar />
      {/* Hero（正版首屏） */}
      <section className="px-2 py-12 text-center">
        <p className="mb-4 text-sm uppercase tracking-widest text-gray-500">
          Web 2.5 · 所有权层中心化平台 · 期 1 内部真跑（模拟态标注）
        </p>
        <h1 className="text-4xl font-bold leading-tight text-gray-900 sm:text-5xl">
          TDCA 三体可视化中心
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-gray-600">
          协议本体 · 人机协作 · 协议配置网络 —— 三个面的统一可视化中心。
          TDCA 是基础协议：不做 App，配置权与使用权归分布式节点网络，
          本站负责所有权层的登记、计量与机器可读打通。
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            to="/register"
            className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
          >
            我要缔约（注册即缔约） <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#machine"
            className="inline-flex items-center gap-2 rounded-md border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            <Bot className="h-4 w-4" /> 智能体通道
          </a>
        </div>
      </section>

      {/* 三体 */}
      <section id="trinity" className="rounded-xl border border-gray-200 bg-gray-50/60 p-6">
        <h2 className="text-2xl font-semibold text-gray-900">三个面，一个中心</h2>
        <div className="mt-6 grid gap-6 sm:grid-cols-3">
          {trinity.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="rounded-lg border border-gray-200 bg-white p-6">
              <Icon className="h-6 w-6 text-blue-700" />
              <h3 className="mt-4 font-semibold text-gray-900">{title}</h3>
              <p className="mt-2 text-sm text-gray-500">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 合规前置三阶 */}
      <section id="stages" className="rounded-xl border border-gray-200 p-6">
        <h2 className="text-2xl font-semibold text-gray-900">合规前置：缔约三阶</h2>
        <p className="mt-2 text-sm text-gray-500">
          人与智能体同制：准入有扫描、过渡有沙盒、转正有留痕。
        </p>
        <div className="mt-6 grid gap-6 sm:grid-cols-3">
          {stages.map(({ icon: Icon, step, title, desc }) => (
            <div key={title} className="rounded-lg border border-gray-200 p-6">
              <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500">
                <Icon className="h-4 w-4" /> {step}
              </div>
              <h3 className="mt-3 font-semibold text-gray-900">{title}</h3>
              <p className="mt-2 text-sm text-gray-500">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 双通道缔约 */}
      <section id="join" className="rounded-xl border border-gray-200 bg-gray-50/60 p-6">
        <h2 className="text-2xl font-semibold text-gray-900">双通道缔约</h2>
        <p className="mt-2 text-sm text-gray-500">人与智能体各走各的通道，互不冒充。</p>
        <div className="mt-6 grid gap-6 sm:grid-cols-2">
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h3 className="font-semibold text-gray-900">人类通道</h3>
            <p className="mt-2 text-sm text-gray-500">
              注册即缔约：注册流程内含《TDCA 缔约注册协议》同意勾选，注册成立即缔约成立，缔约存证落 NCA 链。
            </p>
            <Link
              to="/register"
              className="mt-4 inline-flex items-center gap-2 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              去注册（注册即缔约） <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h3 className="font-semibold text-gray-900">智能体通道</h3>
            <p className="mt-2 text-sm text-gray-500">
              智能体走协议加载验证六步（register → protocol-load → token → ns-review → sandbox → execute），
              通道端点见下方机器可读面；网页此栏仅为对人的观测说明。
            </p>
          </div>
        </div>
      </section>

      {/* 机器可读通道（对人的说明书；⛔ 非智能体的门——照 AMEND-1） */}
      <section id="machine" className="rounded-xl border border-gray-200 p-6">
        <h2 className="text-2xl font-semibold text-gray-900">机器可读通道</h2>
        <p className="mt-2 text-sm text-gray-500">
          Hello Agent 首呼请附 agent_card。以下为公开端点（草案）：
        </p>
        <div className="mt-6 overflow-hidden rounded-lg border border-gray-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-2">端点</th>
                <th className="px-4 py-2">说明</th>
                <th className="px-4 py-2">状态</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[
                ['POST /api/site/join', '缔约申请（双通道）', '在建'],
                ['GET /api/site/join/status', '缔约进度查询', '在建'],
                ['POST /api/site/agent-card/handshake', '智能体首呼握手', '在建'],
                ['GET /api/site/agent-card/{id}', '对接卡公开查询', '在建'],
                ['GET /api/site/directory', '名册摘要（脱敏）', '在建'],
                ['GET /api/site/docs/{family}', '文档目录', '在线（help 族未入站）'],
                ['POST /api/site/meter', '调用计量（仅智能体通道）', '在建'],
              ].map(([ep, desc, st]) => (
                <tr key={ep}>
                  <td className="px-4 py-2 font-mono text-xs text-gray-700">{ep}</td>
                  <td className="px-4 py-2 text-gray-500">{desc}</td>
                  <td className="px-4 py-2 text-gray-500" data-testid={`home-machine-status-${ep.split(' ')[1].replace(/\//g, '-').replace(/{|}/g, '')}`}>{st}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 制度总览区（原四层架构总览并入，A-1 契约不动） */}
      <section id="overview" className="rounded-xl border border-gray-200 bg-gray-50/60 p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-gray-900">制度总览 · 四层架构（L0 法律底层 → L1 所有权 → L2 配置权 → L3 效用计量）</h2>
          <SimulatedBadge nature="simulated" />
        </div>
        {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
        {status === 'fail' && (
          <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="home-fail-closed">
            [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
          </p>
        )}
        {status === 'ok' && data && (
          <div data-testid="home-kpi" className="space-y-4">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              体系状态：{data.system} <SimulatedBadge nature={nature ?? 'simulated'} />
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
              {[
                { label: '累计微交付', value: data.total_deliveries },
                { label: '税收结算（模拟）', value: data.total_tax_settled },
                { label: '平均计税时延', value: `${data.avg_latency_ms} ms` },
                { label: '熔断次数', value: data.total_fused },
                { label: 'fail-closed 次数', value: data.total_fail_closed },
                { label: '正和阈值 θ/ϕ', value: `${data.theta} / ${data.phi}` },
              ].map((kpi) => (
                <div key={kpi.label} className="rounded-lg border border-gray-200 bg-white p-3">
                  <div className="text-xs text-gray-500">{kpi.label}</div>
                  <div className="mt-1 text-xl font-bold text-gray-900">{kpi.value}</div>
                </div>
              ))}
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-3 text-xs text-gray-600">
              税率（CALL-001 模拟态）：调度税 {data.tax_rates.dispatch_tax * 100}% / 版税{' '}
              {data.tax_rates.royalty * 100}% / 交易费 {data.tax_rates.transaction_fee * 100}%
            </div>

            {/* VISUAL-001：五元拓扑 Ω（ID81，官网 = Ω 前端坐标卡） */}
            <section data-testid="home-omega" className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-800">五元拓扑 Ω（H/M/L 顶点 + 五关系边）</h3>
                <SimulatedBadge nature="simulated" />
              </div>
              <TopologyEngine data={OMEGA_TOPO} height={260} />
            </section>
          </div>
        )}
      </section>

      <p className="px-2 pt-2 text-xs text-gray-400">
        TDCA 站点：Web 2.5 架构中所有权层的中心化平台 —— 缔约登记、名册、计量与机器可读打通；
        配置权与使用权属于分布式节点网络，节点自行部署运行，本站不托管、不替代。TDCA 是基础协议，不做 App。
      </p>
    </div>
  )
}
