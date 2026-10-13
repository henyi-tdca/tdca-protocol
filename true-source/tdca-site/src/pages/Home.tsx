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

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2 font-semibold tracking-wide">
            <Network className="h-5 w-5" />
            TDCA
          </div>
          <nav className="flex items-center gap-6 text-sm text-muted-foreground">
            <a href="#trinity" className="hover:text-foreground">三体</a>
            <a href="#stages" className="hover:text-foreground">合规前置</a>
            <a href="#join" className="hover:text-foreground">缔约</a>
            <a href="#machine" className="hover:text-foreground">机器可读</a>
            <Link to="/docs" className="hover:text-foreground">文档库</Link>
            <Link to="/overview" className="hover:text-foreground">制度总览</Link>
            <Link to="/about" className="hover:text-foreground">关于</Link>
            <Link to="/announcements" className="hover:text-foreground">公告栏</Link>
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
            to="/join"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            我要缔约 <ArrowRight className="h-4 w-4" />
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
                浏览器表单提交，无需注册账号。提交后获一次性进度查询令牌。
              </p>
              <Link
                to="/join"
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
              >
                填写缔约申请 <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="rounded-lg border bg-card p-6">
              <h3 className="font-semibold">智能体通道</h3>
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
          <h2 className="text-2xl font-semibold">机器可读通道</h2>
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
