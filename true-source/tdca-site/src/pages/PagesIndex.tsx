// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-2 站点地图（页面元数据索引）
// 约束矩阵: FRAMEWORK-001 §四（路由表：界面域/层级/数据源/权限）+ ID92（模拟态）
// 并轨注记: 自旧版 pages.tsx 改造并入（FRONTEND-MERGE 批1）——
//           元数据裁至「本批已迁入之面 ＋ 新版既有之面」共 8 条；
//           未迁面 ⛔ 不登记（随后续批次渐进扩充）；
//           layer 降为纯数据字段（层级指示器未随迁，不引旧版 @/app/layer-indicator）
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from '@/components/PageShell'

export interface PageMeta {
  path: string
  title: string
  layer: string
  dataSource: string
  permission: string
  description: string
}

/** 站点地图元数据：本批四面（/overview /about /pages /announcements）＋ 新版既有四面（/ /register /review /docs）；缔约申请页已撤（ACCESS-FIX-001-AMEND-1 交付二：注册已含缔约同意） */
export const PAGE_META: PageMeta[] = [
  { path: '/overview', title: '制度总览 · 四层架构', layer: 'L0', dataSource: 'A-1 GET /api/v1/system/overview + /health', permission: '公开', description: 'TDCA 四层架构（L0 法律底层 → L1 所有权 → L2 配置权 → L3 效用计量）制度橱窗总览。' },
  { path: '/about', title: '关于 · 一页看懂 TDCA', layer: 'L0', dataSource: '静态文案（TDCA-PLAIN-001）', permission: '公开', description: '智能体世界的规则、账本与信任——面向普通读者的一页通俗说明。' },
  { path: '/pages', title: '站点地图', layer: 'L0', dataSource: '静态元数据（本件 PAGE_META）', permission: '公开', description: '本站已迁入之面的索引与制度水印；未迁面不登记，随批扩充。' },
  { path: '/announcements', title: '公告栏', layer: 'L0', dataSource: 'A-23 GET /api/v1/announcements/list（公开读）', permission: '公开', description: '站点对外公告区：公告内容经明示后由运营发布；空栏为常态，不预置内容。' },
  { path: '/', title: '首页 · 三体可视化中心', layer: 'L0', dataSource: '静态文案', permission: '公开', description: 'TDCA 三体可视化中心落地页（新版既有面）。' },
  { path: '/register', title: '注册（缔约）', layer: 'L0', dataSource: 'M4 POST /api/v1/auth/register（缔约落 NCA 链）', permission: '公开', description: '注册即缔约入口（注册流程内含缔约协议同意勾选）。' },
  { path: '/review', title: '审查', layer: 'L0', dataSource: '静态文案', permission: '公开', description: '审查面（新版既有面，Review ⛔ 不动）。' },
  { path: '/docs', title: '文档库', layer: 'L0', dataSource: '静态索引', permission: '公开', description: '协议文档站内索引（新版既有面）。' },
]

export const ROUTE_PATHS = PAGE_META.map((m) => m.path)

export function NotFoundPage() {
  return (
    <PageShell
      title="404 · 路由未找到"
      dataSource="—"
      permission="公开"
      description="未知路由 404 兜底。请从导航选择有效页面。"
    />
  )
}

/** 站点地图面：逐面卡片（标题/水印/直达链接），不内嵌页面本体 */
export function PagesIndexPage() {
  return (
    <PageShell
      title="站点地图"
      dataSource="静态元数据（PAGE_META 8 条）"
      permission="公开"
      description="本站已迁入之面的索引：每面标注数据源与访问权限；未迁面不登记，随批扩充。"
    >
      <div className="grid gap-3 md:grid-cols-2">
        {PAGE_META.map((m) => (
          <Link
            key={m.path}
            to={m.path}
            data-testid={`site-map-${m.path === '/' ? 'home' : m.path.slice(1)}`}
            className="rounded-lg border bg-card p-4 shadow-sm transition-colors hover:bg-muted/50"
          >
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-sm font-semibold text-card-foreground">{m.title}</h3>
              <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">{m.layer}</span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{m.description}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-muted-foreground">
              <span>数据源：{m.dataSource}</span>
              <span>权限：{m.permission}</span>
            </div>
          </Link>
        ))}
      </div>
    </PageShell>
  )
}
