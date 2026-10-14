import { useEffect, useRef, useState } from 'react'
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
    title: 'workbuddy 面',
    desc: 'TDCA workbuddy 线的状态与制度进展呈现。',
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

// SITE-THREE-FIXES-001 处1：原 30 条平铺导航分组收纳（⛔ 不删入口、不改路由表；队尾工具货架等全数落组）
const MORE_GROUPS: { label: string; items: { to: string; label: string }[] }[] = [
  {
    label: '门户',
    items: [
      { to: '/about', label: '关于' },
      { to: '/announcements', label: '公告栏' },
      { to: '/library', label: '知识库' },
      { to: '/academy', label: '商学院（在建中）' },
    ],
  },
  {
    label: '智能体',
    items: [
      { to: '/agents', label: '智能体集群' },
      { to: '/studio', label: 'Agent Studio' },
      { to: '/workbuddy', label: 'WorkBuddy' },
      { to: '/agent-shelf', label: '智能体区' },
    ],
  },
  {
    label: '登记与存证',
    items: [
      { to: '/ownership', label: '所有权' },
      { to: '/ownership-registry', label: '权属登记' },
      { to: '/authorization-registry', label: '授权登记' },
      { to: '/attestation', label: '确权中心' },
      { to: '/anchors', label: '模拟锚' },
      { to: '/audit', label: '审计' },
      { to: '/governance', label: '治理' },
      { to: '/formal', label: '形式化入站' },
      { to: '/cluster', label: '集群编排' },
    ],
  },
  {
    label: '市场与经济',
    items: [
      { to: '/market', label: '配置权市场（在建中）' },
      { to: '/market-sim', label: '规范与沙盒链（在建中）' },
      { to: '/tax', label: '税收仪表盘' },
    ],
  },
  {
    label: '工具与运维',
    items: [
      { to: '/toolshelf', label: '工具货架' },
      { to: '/notifier', label: '通知机（在建中）' },
      { to: '/sandbox', label: '沙盒' },
      { to: '/ops', label: '运维端' },
    ],
  },
]

export default function Home() {
  const [moreOpen, setMoreOpen] = useState(false)
  const moreRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    function onClickOutside(ev: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(ev.target as Node)) setMoreOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2 font-semibold tracking-wide">
            <Network className="h-5 w-5" />
            TDCA
          </div>
          <nav className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
            <a href="#trinity" className="hover:text-foreground">三体</a>
            <a href="#stages" className="hover:text-foreground">合规前置</a>
            <a href="#join" className="hover:text-foreground">缔约</a>
            <a href="#machine" className="hover:text-foreground">机器可读</a>
            <Link to="/docs" className="hover:text-foreground">文档库</Link>
            <Link to="/overview" className="hover:text-foreground">制度总览</Link>
            {/* FRONTEND-MERGE 批2（身份与缔约）：三入口，Join 入口不动 */}
            <Link to="/register" className="hover:text-foreground">注册</Link>
            <Link to="/auth" className="hover:text-foreground">登录</Link>
            <Link to="/me" className="hover:text-foreground">我的</Link>
            {/* 处1：其余 24 入口分组收纳于「更多」（队尾工具货架/学院等全数落组，⛔ 不删入口、不改路由） */}
            <div ref={moreRef} className="relative">
              <button
                type="button"
                data-testid="nav-more"
                onClick={() => setMoreOpen((o) => !o)}
                className="rounded border px-2 py-0.5 hover:text-foreground"
              >
                更多 ▾
              </button>
              {moreOpen && (
                <div
                  data-testid="nav-more-panel"
                  className="absolute right-0 z-40 mt-2 w-72 rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
                >
                  {MORE_GROUPS.map((g) => (
                    <div key={g.label} className="mb-2 last:mb-0">
                      <div className="px-1 text-[10px] font-semibold uppercase tracking-wide text-gray-400">{g.label}</div>
                      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
                        {g.items.map((it) => (
                          <Link
                            key={it.to}
                            to={it.to}
                            onClick={() => setMoreOpen(false)}
                            className="text-xs text-slate-600 hover:text-slate-900 hover:underline"
                          >
                            {it.label}
                          </Link>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-5xl px-6 py-20 text-center">
        <p className="mb-4 text-sm uppercase tracking-widest text-muted-foreground">
          Web 2.5 · 所有权层中心化平台 · 期 1 内部真跑（模拟态标注）
        </p>
        <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
          TDCA 三体可视化中心
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-muted-foreground">
          协议本体 · workbuddy · 协议配置网络 —— 三个面的统一可视化中心。
          TDCA 是基础协议：不做 App，配置权与使用权归分布式节点网络，
          本站负责所有权层的登记、计量与机器可读打通。
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            to="/register"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            我要缔约（注册即缔约） <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#machine"
            className="inline-flex items-center gap-2 rounded-md border px-5 py-2.5 text-sm font-medium hover:bg-accent"
          >
            <Bot className="h-4 w-4" /> 智能体通道
          </a>
        </div>
      </section>

      {/* 三体 */}
      <section id="trinity" className="border-t bg-muted/40">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <h2 className="text-2xl font-semibold">三个面，一个中心</h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            {trinity.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="rounded-lg border bg-card p-6">
                <Icon className="h-6 w-6 text-primary" />
                <h3 className="mt-4 font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 合规前置三阶 */}
      <section id="stages" className="border-t">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <h2 className="text-2xl font-semibold">合规前置：缔约三阶</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            人与智能体同制：准入有扫描、过渡有沙盒、转正有留痕。
          </p>
          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            {stages.map(({ icon: Icon, step, title, desc }) => (
              <div key={title} className="rounded-lg border p-6">
                <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
                  <Icon className="h-4 w-4" /> {step}
                </div>
                <h3 className="mt-3 font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 双通道 */}
      <section id="join" className="border-t bg-muted/40">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <h2 className="text-2xl font-semibold">双通道缔约</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            人与智能体各走各的通道，互不冒充。
          </p>
          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            <div className="rounded-lg border bg-card p-6">
              <h3 className="font-semibold">人类通道</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                注册即缔约：注册流程内含《TDCA 缔约注册协议》同意勾选，注册成立即缔约成立，缔约存证落 NCA 链。
              </p>
              <Link
                to="/register"
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
              >
                去注册（注册即缔约） <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="rounded-lg border bg-card p-6">
              <h3 className="font-semibold">
                智能体通道{' '}
                <span className="ml-1 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-normal text-amber-700">
                  通道未建 · 仅呈现
                </span>
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                首呼附 <code className="text-xs">agent_card</code> 至
                <code className="text-xs"> POST /api/site/agent-card/handshake</code>
                ，回发对接卡与调用规则。
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 机器可读 */}
      <section id="machine" className="border-t">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <h2 className="text-2xl font-semibold">
            机器可读通道{' '}
            <span className="ml-1 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-normal text-amber-700">
              通道未建 · 仅呈现
            </span>
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Hello Agent 首呼请附 agent_card。以下为公开端点（草案）：
          </p>
          <div className="mt-6 overflow-hidden rounded-lg border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-2">端点</th>
                  <th className="px-4 py-2">说明</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {[
                  ['POST /api/site/join', '缔约申请（双通道）'],
                  ['GET /api/site/join/status', '缔约进度查询'],
                  ['POST /api/site/agent-card/handshake', '智能体首呼握手'],
                  ['GET /api/site/agent-card/{id}', '对接卡公开查询'],
                  ['GET /api/site/directory', '名册摘要（脱敏）'],
                  ['GET /api/site/weekly', '周刊存档'],
                  ['GET /api/site/docs/{family}', '文档目录'],
                  ['POST /api/site/meter', '调用计量（仅智能体通道）'],
                ].map(([ep, desc]) => (
                  <tr key={ep}>
                    <td className="px-4 py-2 font-mono text-xs">{ep}</td>
                    <td className="px-4 py-2 text-muted-foreground">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="mx-auto max-w-5xl px-6 py-10 text-sm text-muted-foreground">
          <p>
            TDCA 站点：Web 2.5 架构中所有权层的中心化平台 —— 缔约登记、名册、计量与机器可读打通；
            配置权与使用权属于分布式节点网络，节点自行部署运行，本站不托管、不替代。
            TDCA 是基础协议，不做 App。
          </p>
          <p className="mt-4 text-xs">© TDCA · 协议本体 · workbuddy · 协议配置网络 ｜ 期 1：积分/链锚点/云通知机均为内部模拟件，非真实外部系统</p>
        </div>
      </footer>
    </div>
  )
}
