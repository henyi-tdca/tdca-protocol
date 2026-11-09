// 批 2 骨架：全局壳——细横条（意图直达＋登录状态，原样保留）＋频道横轴＋协作流程竖列＋内容区
// ⛔ 不改任何现有页内容与现有路由路径；仅作包裹层
// 移动修复批·甲案（AMEND-2 改判必做）：ProcessNav 小屏收起（hidden md:block＋汉堡）——
// 旧版本手机端侧栏本可收起（创始人 2026-11-09 逐字「之前就是这样」），属追平缺项 ⛔ 优化项；
// main 小屏净宽 199px→375px 全宽。
import type { ReactNode } from 'react'
import { useState } from 'react'
import { IntentBar } from './IntentBar'
import { AuthStatus } from './AuthStatus'
import { TopNav } from './TopNav'
import { ProcessNav } from './ProcessNav'

export function SiteLayout({ children }: { children: ReactNode }) {
  // 甲案：小屏侧栏默认收起，汉堡展开；md 及以上恒显（md:block 覆盖 hidden）
  const [navOpen, setNavOpen] = useState(false)
  return (
    <div className="flex min-h-screen flex-col">
      {/* 全局细横条：原有二件原样保留（意图直达左、登录状态/登出右） */}
      <div className="flex items-center justify-between gap-2 border-b bg-background px-4 py-1.5">
        <IntentBar />
        <AuthStatus />
      </div>
      <TopNav />
      {/* 甲案：汉堡仅小屏可见（md:hidden）；展开态侧栏压内容上方（absolute），⛔改桌面布局 */}
      <div className="relative border-b bg-background md:hidden">
        <button
          type="button"
          data-testid="process-nav-toggle"
          onClick={() => setNavOpen(!navOpen)}
          className="w-full px-4 py-1.5 text-left text-xs font-semibold text-muted-foreground"
        >
          协作流程 {navOpen ? '▾' : '▸'}
        </button>
        {navOpen && (
          <div className="absolute left-0 top-full z-40 w-56 border-r border-b bg-background shadow-lg">
            <ProcessNav />
          </div>
        )}
      </div>
      <div className="flex flex-1">
        {/* 甲案：aside 小屏 hidden（汉堡控展开），md 及以上恒显 */}
        <div className="hidden md:block" data-testid="process-nav-desktop">
          <ProcessNav />
        </div>
        <main className="min-w-0 flex-1 p-4">{children}</main>
      </div>
    </div>
  )
}
