// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-2 站点地图（页面元数据索引）
// 约束矩阵: FRAMEWORK-001 §四（路由表：界面域/层级/数据源/权限）+ ID92（模拟态）
// 并轨注记: 自旧版 pages.tsx 改造并入（FRONTEND-MERGE 批1）——
//           元数据裁至「本批已迁入之面 ＋ 新版既有之面」；
//           未迁面 ⛔ 不登记（随后续批次渐进扩充）；
//           layer 降为纯数据字段（层级指示器未随迁，不引旧版 @/app/layer-indicator）；
//           MIGRATE 批1（2026-11-09）追加 /search 检索面（8→9）；
//           MIGRATE 批2（L1SI206）追加 /channel/my 与 /channel/register 通道两面（9→11）；
//           MIGRATE 批3（L1SI206）追加严选与节点八面＋/channel 总入口（11→20；权限照 route-parity.md 原栏）；
//           MIGRATE 批4（L1SI206）追加 /lab 与 /demo 演练实验两面（20→22；同栈直拷·场景数8不缩·仅人）
//           MIGRATE 批6（L1SI206）追加 /start 与 /nca-guide 入门指南两面（22→24；start-map.yaml 原字节随批）
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
  { path: '/search', title: '全站检索', layer: 'L0', dataSource: '静态索引 search-index.json（构建时生成）', permission: '公开', description: '四族公开件＋术语＋栏目页一框检索；本地排序，无后端（MIGRATE 批1 迁入）。' },
  { path: '/channel/my', title: '我的通道', layer: 'L0', dataSource: 'GET /api/v1/agent-channel/gate/{reg_no} ＋ deposits ＋ ns-review ＋ sandbox ＋ promotion-token ＋ promotion', permission: '私域（须登录；仅登记主体本人可操作）', description: '四步流水线：交押金⟹过闸（审查＋沙盒）⟹领转正令牌⟹办转正（MIGRATE 批2 迁入）。' },
  { path: '/channel/register', title: '智能体自助登记（通道登记）', layer: 'L0', dataSource: 'POST /api/v1/agent-channel/register', permission: '公开（ANCHOR 路须登录；GUEST 路免会话）', description: '登记即创建：六要素 fail-closed、缺项点名、成功回登记号；原 /channel/registry 改路径（MIGRATE 批2 迁入）。' },
  { path: '/channel', title: '智能体通道', layer: 'L0', dataSource: '在册《智能体定义条例》第 19 条（六步硬序）＋既有 /channel/* 路由', permission: '公开', description: '智能体经站点通道接入的总入口：先登记（前置），再按六步硬序走通（MIGRATE 批3 补做，批2 令面漏项）。' },
  { path: '/curation', title: '严选池 · 精选项目一栏', layer: 'L0', dataSource: '严选池清单 public/curation.json（机读单一真源）', permission: '公开（匿名可读）', description: '经在册严选流程留池的项目清单：只出汇总数与逐项六字段，照单渲染（MIGRATE 批3 迁入）。' },
  { path: '/contribute', title: '我要贡献 · 三级台阶', layer: 'L0', dataSource: '纯前端指路页（零接口调用）', permission: '公开', description: '从读者到贡献者到节点方：每阶写什么件、走哪条路、什么算成，只指路不代办（MIGRATE 批3 迁入）。' },
  { path: '/public-face', title: '匿名可见面', layer: 'L0', dataSource: '包内路由表＋匿名实测状态码（2026-11-02 旧版实测口径照录）', permission: '公开', description: '匿名来访能看什么、什么要登录、什么不开放——三栏照实清单（MIGRATE 批3 迁入）。' },
  { path: '/private', title: '私域与边界 · 公域守门人', layer: 'L0', dataSource: '纯前端说明页（零接口调用）', permission: '公开', description: '公域／私域分工与两权闸门：起私域节点之前先读这一页（MIGRATE 批3 迁入）。' },
  { path: '/nodes', title: '节点网络', layer: 'L0', dataSource: '在册条例 V1.0 与节点现状（node-net-data 同源唯一源）', permission: '公开', description: '业务端节点接入公开面：可视图只画已披露真节点；接口九类空壳禁止（MIGRATE 批3 迁入）。' },
  { path: '/me/node', title: '场景节点管理区（私域三空间）', layer: 'L0', dataSource: '纯前端样例态（页内状态）；载入门禁 GET /api/v1/auth/me', permission: '须登录（谁的数据谁可见）', description: '私域三空间：负空间／沙盒出盒／正空间；六项硬核只读锁定（MIGRATE 批3 迁入，API 401/403 把守）。' },
  { path: '/me/node/net', title: '我的节点 · 条例与契约', layer: 'L0', dataSource: '在册条例 V1.0 与本机节点配置；载入门禁 GET /api/v1/auth/me', permission: '登录 DID', description: '私域节点面：我的节点配置与在册条例契约（MIGRATE 批3 迁入，API 401/403 把守）。' },
  { path: '/disclosure', title: '节点规则披露登记簿 · 公域可查', layer: 'L0', dataSource: '披露登记簿（仓内单源，只读渲染）', permission: '公开（匿名可读 · 只读）', description: '节点规则对外披露面：只登记不审批，三式查阅，形状不合 fail-closed（MIGRATE 批3 迁入）。' },
  { path: '/lab', title: '模拟演练区', layer: 'L0', dataSource: '纯前端演练值（页内状态）；零接口调用、零后端写入', permission: '公开', description: '五张模拟卡＋三段剧本＋一张流水表：八场景逐项走一遍，积分面额照设计件 6146（MIGRATE 批4 迁入，演练值不入账不留存）。' },
  { path: '/demo', title: '体验期与模拟演示', layer: 'L0', dataSource: '纯前端演示值（页内状态）；零接口调用、零后端写入', permission: '公开', description: '体验期有什么、演示区在演什么、什么是真什么是假，一页讲清（MIGRATE 批4 迁入，演示值非真实交易）。' },
  { path: '/start', title: '新手指引 · 六步上手 TDCA', layer: 'L0', dataSource: '_START-MAP 三表（单一事实源·仓内单源 ?raw 进包）', permission: '公开', description: 'S1~S6 六步了解 TDCA：每步挂接该步制度件，缺口步如实标「待补」；目录四维筛选与 147 条术语检索同读 _START-MAP 三表（MIGRATE 批6 迁入）。' },
  { path: '/nca-guide', title: '存证（NCA）说明', layer: 'L0', dataSource: '静态文案（站内审定口径，依在册 NCA 格式标准）', permission: '公开', description: 'NCA 存证格式＝全站唯一标准：每一场景皆存、官方与用户一致、人类与智能体一致——十三字段／带链／义务块六键／合规六条之公众说明面（MIGRATE 批6 迁入）。' },
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
      dataSource="静态元数据（PAGE_META 20 条）"
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
