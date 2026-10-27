// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-2 页面占位壳（15 路由骨架）
// 约束矩阵: FRAMEWORK-001 §四（路由表：界面域/层级/数据源/权限）+ ID92（模拟态）
// 预期分配: PageShell（标题/数据源/权限/说明 + 占位内容容器）
// =============================================================================
import type { ReactNode } from 'react'
import { useAuthOptional } from '@/app/auth-context'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

export interface PageShellProps {
  title: string
  /** 数据源（三级接口标注，如 A-1 GET /api/v1/system/overview） */
  dataSource: string
  /** 匿名态数据源文案（可选）：未登录且填写时替换展示（L1SI177 块一公开面表述清理）；
   *  登录态始终显示完整 dataSource；未填写本参的页两态均显原值 */
  dataSourceAnon?: string
  /** 访问权限（公开 / 登录 DID / HUF 强制鉴权） */
  permission: string
  description: string
  children?: ReactNode
}

/** 通用页面占位壳：F1~F5 阶段将替换为具体页面内容 */
export function PageShell({ title, dataSource, dataSourceAnon, permission, description, children }: PageShellProps) {
  const auth = useAuthOptional()
  const isAnon = !(auth?.isAuthenticated ?? false)
  const shownSource = isAnon && dataSourceAnon ? dataSourceAnon : dataSource
  return (
    <section data-testid="page-shell" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        <SimulatedBadge nature="simulated" />
      </div>
      <p className="mb-3 text-sm text-gray-600">{description}</p>
      <div className="mb-4 flex flex-wrap gap-2 text-[11px]">
        <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">数据源：{shownSource}</span>
        <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">权限：{permission}</span>
        <span className="rounded bg-purple-50 px-2 py-0.5 text-purple-600">本页部分内容还在完善中</span>
      </div>
      {children ?? (
        <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-400">
          本页内容将于后续阶段填充
        </div>
      )}
    </section>
  )
}
