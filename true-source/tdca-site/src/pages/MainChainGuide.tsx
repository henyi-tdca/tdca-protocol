// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI188-NAV-FIX-006 P2-1 主链导轨（横向导引条）
// 约束矩阵: NAV-FIX-006 §一——环节照令面建议序列（仓内无「主链」在册定义，取用依据回报注明）；
//           纯新增导引面，⛔ 替换/隐藏/重排既有导航，⛔ 自造环节
// =============================================================================
import { Link, useLocation } from 'react-router'

/** 主链八环节（照 NAV-FIX-006 令面建议序列取用，逐环为在册实路由） */
export const MAIN_CHAIN = [
  { to: '/', label: '门户首页' },
  { to: '/five-orders', label: '五序资产' },
  { to: '/channel', label: '智能体通道' },
  { to: '/agents', label: '能力与观测' },
  { to: '/attestation', label: '确权中心' },
  { to: '/authorization-registry', label: '合约备案' },
  { to: '/market', label: '配置权市场' },
  { to: '/audit', label: '审计与账本' },
] as const

/** 主链页面集合（导轨挂载面：主链八环节各自落地页） */
export const MAIN_CHAIN_PAGES: ReadonlySet<string> = new Set(MAIN_CHAIN.map((s) => s.to))

/** 主链导轨（横向导引条）：串主链八环节，当前环节高亮，不遮挡正文 */
export function MainChainGuide() {
  const { pathname } = useLocation()
  return (
    <nav
      data-testid="main-chain-guide"
      aria-label="主链导轨"
      className="mx-auto mb-3 flex max-w-6xl flex-wrap items-center gap-1 px-4 pt-3 text-xs"
    >
      <span className="mr-1 font-medium text-gray-400">主链</span>
      {MAIN_CHAIN.map((s, i) => {
        const current = s.to === '/' ? pathname === '/' : pathname.startsWith(s.to)
        return (
          <span key={s.to} className="flex items-center gap-1">
            {i > 0 && <span className="text-gray-300">→</span>}
            <Link
              to={s.to}
              data-testid={`main-chain-step-${i + 1}`}
              data-current={current}
              className={
                current
                  ? 'rounded bg-slate-800 px-2 py-1 font-medium text-white'
                  : 'rounded border border-gray-200 bg-white px-2 py-1 text-blue-700 hover:bg-gray-50'
              }
            >
              {s.label}
            </Link>
          </span>
        )
      })}
    </nav>
  )
}
