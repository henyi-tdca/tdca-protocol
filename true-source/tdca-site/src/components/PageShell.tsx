// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-2 页面占位壳（制度水印三字段）
// 约束矩阵: FRAMEWORK-001 §四（路由表：界面域/层级/数据源/权限）+ ID92（模拟态）
// 预期分配: PageShell（标题/数据源/权限/说明 + 占位内容容器）
// 并轨注记: 自旧版 src/pages/PageShell.tsx 迁入（FRONTEND-MERGE 批1）；
//           视觉改书新版 shadcn/tailwind 体系（border/muted 语义类），
//           制度契约三字段（数据源/权限/模拟态标注）原样保留，⛔ 不引旧版独立样式体系
// =============================================================================
import type { ReactNode } from 'react'
import { SimulatedBadge } from '@/lib/SimulatedBadge'

export interface PageShellProps {
  title: string
  /** 数据源（三级接口标注，如 A-1 GET /api/v1/system/overview） */
  dataSource: string
  /** 访问权限（公开 / 登录 DID / HUF 强制鉴权） */
  permission: string
  description: string
  children?: ReactNode
}

/** 通用页面壳：标题 + 制度水印（数据源/权限）+ 模拟态标注 + 内容容器 */
export function PageShell({ title, dataSource, permission, description, children }: PageShellProps) {
  return (
    <section data-testid="page-shell" className="rounded-xl border bg-card p-6 shadow-sm">
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-lg font-bold text-card-foreground">{title}</h2>
        <SimulatedBadge nature="simulated" />
      </div>
      <p className="mb-3 text-sm text-muted-foreground">{description}</p>
      <div className="mb-4 flex flex-wrap gap-2 text-[11px]">
        <span className="rounded bg-muted px-2 py-0.5 text-muted-foreground">数据源：{dataSource}</span>
        <span className="rounded bg-muted px-2 py-0.5 text-muted-foreground">权限：{permission}</span>
        <span className="rounded bg-purple-50 px-2 py-0.5 text-purple-600">制度水印（数据源/权限/模拟态）</span>
      </div>
      {children ?? (
        <div className="rounded-lg border border-dashed bg-muted/50 p-6 text-center text-sm text-muted-foreground">
          本面内容随对应批次逐步填充
        </div>
      )}
    </section>
  )
}
