// 批 2 骨架：顶部频道横轴（五频道＋右端 我的/管理员）
// 硬约束落实：⛔ 零内部编号（仅通俗名）；管理员入口只做归位、不加门（门槛属制度题，另案）
import { Link, useLocation } from 'react-router'

const CHANNELS: { to: string; label: string }[] = [
  { to: '/channel/portal', label: '门户' },
  { to: '/channel/agents', label: '智能体' },
  { to: '/channel/registry', label: '登记与存证' },
  { to: '/channel/market', label: '市场与经济' },
  { to: '/channel/tools', label: '工具与运维' },
]

export function TopNav() {
  const { pathname } = useLocation()
  const active = (to: string) =>
    to === '/channel/portal'
      ? pathname === '/' || pathname.startsWith('/channel/portal')
      : pathname.startsWith(to)

  return (
    <nav data-testid="app-nav" className="flex items-center justify-between gap-2 border-b bg-background px-4 py-2">
      <div className="flex items-center gap-1">
        <Link to="/" className="mr-3 text-sm font-bold">
          TDCA
        </Link>
        {CHANNELS.map((c) => (
          <Link
            key={c.to}
            to={c.to}
            className={`rounded px-3 py-1 text-sm ${
              active(c.to) ? 'bg-muted font-semibold' : 'text-muted-foreground hover:bg-muted/60'
            }`}
          >
            {c.label}
          </Link>
        ))}
      </div>
      <div className="flex items-center gap-1 text-sm">
        <Link to="/me" className="rounded px-3 py-1 text-muted-foreground hover:bg-muted/60">
          我的
        </Link>
        {/* 管理员空间入口（只做归位，⛔ 不加门；门槛另案裁定） */}
        <Link
          to="/ops"
          data-testid="nav-admin"
          className="rounded px-3 py-1 text-muted-foreground hover:bg-muted/60"
        >
          管理员
        </Link>
      </div>
    </nav>
  )
}
