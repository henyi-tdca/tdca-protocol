// 批 2 骨架：频道首页（极轻：一句话＋入口卡片＋相关协作环节）
// 五个频道照现五组口径；⛔ 零内部编号；/ops 已归管理员空间，不在公共频道入口
import { Link } from 'react-router'

export type ChannelKey = 'portal' | 'agents' | 'registry' | 'market' | 'tools'

const CHANNELS: Record<
  ChannelKey,
  { title: string; tagline: string; entries: { to: string; label: string }[]; rings: string[] }
> = {
  portal: {
    title: '门户',
    tagline: '了解 TDCA：公告、知识库与学院——信息公开与交互的入口。',
    entries: [
      { to: '/about', label: '关于' },
      { to: '/announcements', label: '公告栏' },
      { to: '/library', label: '知识库' },
      { to: '/academy', label: '商学院（在建中）' },
    ],
    rings: ['发现', '相遇'],
  },
  agents: {
    title: '智能体',
    tagline: '智能体相遇、协作与作业：集群、工作室与工具面。',
    entries: [
      { to: '/agents', label: '智能体集群' },
      { to: '/studio', label: 'Agent Studio' },
      { to: '/workbuddy', label: 'WorkBuddy' },
      { to: '/agent-shelf', label: '智能体区' },
    ],
    rings: ['握手', '履约准备', '履约', '信用及遗产管理'],
  },
  registry: {
    title: '登记与存证',
    tagline: '权属、授权与存证：登记合一与可核验台账。',
    entries: [
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
    rings: ['验证', '签约', '交付', '验收'],
  },
  market: {
    title: '市场与经济',
    tagline: '配置权市场与结算：谈判、计量与分配的规则面。',
    entries: [
      { to: '/market', label: '配置权市场（在建中）' },
      { to: '/market-sim', label: '规范与沙盒链（在建中）' },
      { to: '/tax', label: '税收仪表盘' },
    ],
    rings: ['谈判', '结算分配'],
  },
  tools: {
    title: '工具与运维',
    tagline: '工具、通知与沙盒：试错与验证的公共操作面。',
    entries: [
      { to: '/toolshelf', label: '工具货架' },
      { to: '/notifier', label: '通知机（在建中）' },
      { to: '/sandbox', label: '沙盒' },
    ],
    rings: ['试错', '验证'],
  },
}

export function ChannelHome({ channel }: { channel: ChannelKey }) {
  const c = CHANNELS[channel]
  return (
    <section data-testid="channel-home" className="mx-auto max-w-3xl space-y-4">
      <header>
        <h1 className="text-xl font-bold">{c.title}</h1>
        <p className="text-sm text-muted-foreground">{c.tagline}</p>
      </header>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
        {c.entries.map((e) => (
          <Link
            key={e.to}
            to={e.to}
            className="rounded-lg border bg-card p-3 text-sm hover:bg-muted/60"
          >
            {e.label}
          </Link>
        ))}
      </div>
      <footer className="text-xs text-muted-foreground">
        相关协作环节：{c.rings.join(' · ')}
      </footer>
    </section>
  )
}
