// 批 2 骨架：全局壳——细横条（意图直达＋登录状态，原样保留）＋频道横轴＋协作流程竖列＋内容区
// ⛔ 不改任何现有页内容与现有路由路径；仅作包裹层
import type { ReactNode } from 'react'
import { IntentBar } from './IntentBar'
import { AuthStatus } from './AuthStatus'
import { TopNav } from './TopNav'
import { ProcessNav } from './ProcessNav'

export function SiteLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* 全局细横条：原有二件原样保留（意图直达左、登录状态/登出右） */}
      <div className="flex items-center justify-between gap-2 border-b bg-background px-4 py-1.5">
        <IntentBar />
        <AuthStatus />
      </div>
      <TopNav />
      <div className="flex flex-1">
        <ProcessNav />
        <main className="min-w-0 flex-1 p-4">{children}</main>
      </div>
    </div>
  )
}
