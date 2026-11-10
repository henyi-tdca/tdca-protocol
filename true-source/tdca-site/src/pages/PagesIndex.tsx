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
//           用组批（L1SI206-USE-GROUP-B1）追加 /use/upload 与 /use/agent「用」组两面（24→26；
//           登录动作面照批3私域面先例入册站点地图，检索索引另按动作页豁免不收录）
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
  { path: '/overview', title: '制度总览 · 四层架构', layer: 'L0', dataSource: 'GET /api/v1/system/overview + /health', permission: '公开', description: 'TDCA 四层架构（L0 法律底层 → L1 所有权 → L2 配置权 → L3 效用计量）制度橱窗总览。' },
  { path: '/about', title: '关于 · 一页看懂 TDCA', layer: 'L0', dataSource: '静态文案（站内审定口径）', permission: '公开', description: '智能体世界的规则、账本与信任——面向普通读者的一页通俗说明。' },
  { path: '/pages', title: '站点地图', layer: 'L0', dataSource: '静态元数据（本件 PAGE_META）', permission: '公开', description: '本站各面索引与制度水印；未收录面不登记。' },
  { path: '/announcements', title: '公告栏', layer: 'L0', dataSource: 'GET /api/v1/announcements/list（公开读）', permission: '公开', description: '站点对外公告区：公告内容经明示后由运营发布；空栏为常态，不预置内容。' },
  { path: '/', title: '首页 · 三体可视化中心', layer: 'L0', dataSource: '静态文案', permission: '公开', description: 'TDCA 三体可视化中心落地页（新版既有面）。' },
  { path: '/register', title: '注册（缔约）', layer: 'L0', dataSource: 'POST /api/v1/auth/register（缔约落 NCA 链）', permission: '公开', description: '注册即缔约入口（注册流程内含缔约协议同意勾选）。' },
  { path: '/review', title: '审查', layer: 'L0', dataSource: '静态文案', permission: '公开', description: '审查面（新版既有面，Review ⛔ 不动）。' },
  { path: '/docs', title: '文档库', layer: 'L0', dataSource: '静态索引', permission: '公开', description: '协议文档站内索引（新版既有面）。' },
  { path: '/search', title: '全站检索', layer: 'L0', dataSource: '静态索引 search-index.json（构建时生成）', permission: '公开', description: '四族公开件＋术语＋栏目页一框检索；本地排序，无后端。' },
  { path: '/channel/my', title: '我的通道', layer: 'L0', dataSource: 'GET /api/v1/agent-channel/gate/{reg_no} ＋ deposits ＋ ns-review ＋ sandbox ＋ promotion-token ＋ promotion', permission: '私域（须登录；仅登记主体本人可操作）', description: '四步流水线：交押金⟹过闸（审查＋沙盒）⟹领转正令牌⟹办转正。' },
  { path: '/channel/register', title: '智能体自助登记（通道登记）', layer: 'L0', dataSource: 'POST /api/v1/agent-channel/register', permission: '公开（ANCHOR 路须登录；GUEST 路免会话）', description: '登记即创建：六要素 fail-closed、缺项点名、成功回登记号；原 /channel/registry 改路径。' },
  { path: '/channel', title: '智能体通道', layer: 'L0', dataSource: '在册《智能体定义条例》第 19 条（六步硬序）＋既有 /channel/* 路由', permission: '公开', description: '智能体经站点通道接入的总入口：先登记（前置），再按六步硬序走通。' },
  { path: '/curation', title: '严选池 · 精选项目一栏', layer: 'L0', dataSource: '严选池清单 public/curation.json（机读单一真源）', permission: '公开（匿名可读）', description: '经在册严选流程留池的项目清单：只出汇总数与逐项六字段，照单渲染。' },
  { path: '/contribute', title: '我要贡献 · 三级台阶', layer: 'L0', dataSource: '纯前端指路页（零接口调用）', permission: '公开', description: '从读者到贡献者到节点方：每阶写什么件、走哪条路、什么算成，只指路不代办。' },
  { path: '/public-face', title: '匿名可见面', layer: 'L0', dataSource: '包内路由表＋匿名实测状态码（实测口径照录）', permission: '公开', description: '匿名来访能看什么、什么要登录、什么不开放——三栏照实清单。' },
  { path: '/private', title: '私域与边界 · 公域守门人', layer: 'L0', dataSource: '纯前端说明页（零接口调用）', permission: '公开', description: '公域／私域分工与两权闸门：起私域节点之前先读这一页。' },
  { path: '/nodes', title: '节点网络', layer: 'L0', dataSource: '在册条例 V1.0 与节点现状（node-net-data 同源唯一源）', permission: '公开', description: '业务端节点接入公开面：可视图只画已披露真节点；接口九类空壳禁止。' },
  { path: '/me/node', title: '场景节点管理区（私域三空间）', layer: 'L0', dataSource: '纯前端样例态（页内状态）；载入门禁 GET /api/v1/auth/me', permission: '须登录（谁的数据谁可见）', description: '私域三空间：负空间／沙盒出盒／正空间；六项硬核只读锁定（API 401/403 把守）。' },
  { path: '/me/node/net', title: '我的节点 · 条例与契约', layer: 'L0', dataSource: '在册条例 V1.0 与本机节点配置；载入门禁 GET /api/v1/auth/me', permission: '登录 DID', description: '私域节点面：我的节点配置与在册条例契约（API 401/403 把守）。' },
  { path: '/me/compile', title: '编译转化（区 2A）', layer: 'L0', dataSource: '会话内草稿（骨架期，⛔入账）', permission: '须登录', description: '六步流水线：意图→目标函数→函数化→负空间→合约与协议→创建与发布；产物经负空间检查→沙盒验证→正空间，⛔跳步。' },
  { path: '/me/privacy', title: '数据开放档位（区 2）', layer: 'L0', dataSource: '本机申明（骨架期）＋在册口径', permission: '须登录', description: '开放程度由用户选择（默认最低档）；档位不足必告知三选项，不静默失败。' },
  { path: '/disclosure', title: '节点规则披露登记簿 · 公域可查', layer: 'L0', dataSource: '披露登记簿（仓内单源，只读渲染）', permission: '公开（匿名可读 · 只读）', description: '节点规则对外披露面：只登记不审批，三式查阅，形状不合 fail-closed。' },
  { path: '/lab', title: '模拟演练区', layer: 'L0', dataSource: '纯前端演练值（页内状态）；零接口调用、零后端写入', permission: '公开', description: '五张模拟卡＋三段剧本＋一张流水表：八场景逐项走一遍，积分面额照既定设计口径（演练值不入账不留存）。' },
  { path: '/demo', title: '体验期与模拟演示', layer: 'L0', dataSource: '纯前端演示值（页内状态）；零接口调用、零后端写入', permission: '公开', description: '体验期有什么、演示区在演什么、什么是真什么是假，一页讲清（演示值非真实交易）。' },
  { path: '/start', title: '新手指引 · 六步上手 TDCA', layer: 'L0', dataSource: '机读三表（单一事实源·仓内单源 ?raw 进包）', permission: '公开', description: 'S1~S6 六步了解 TDCA：每步挂接该步制度件，缺口步如实标「待补」；目录四维筛选与 147 条术语检索同读机读三表。' },
  { path: '/nca-guide', title: '存证（NCA）说明', layer: 'L0', dataSource: '静态文案（站内审定口径，依在册 NCA 格式标准）', permission: '公开', description: 'NCA 存证格式＝全站唯一标准：每一场景皆存、官方与用户一致、人类与智能体一致——十三字段／带链／义务块六键／合规六条之公众说明面。' },
  { path: '/rules', title: '制度地图', layer: 'L0', dataSource: '机读表 doc-map-rules.yaml（页面与检索同一源·仓内单源 ?raw 进包）', permission: '公开', description: '主表 57 件制度件（旧记 56，以实读原字节为准）按五类分组、五态如实标、S1~S6 六步导航；五态与版本以在册机读表为唯一口径。' },
  { path: '/help', title: '帮助与联系', layer: 'L0', dataSource: 'GET /api/site/docs/help（只读面）', permission: '公开', description: '站点帮助与官方联系入口；帮助族未入站则如实空栏（空栏为常态，不预置）。' },
  { path: '/negativespace', title: '负空间 · 什么不能做', layer: 'L0', dataSource: '静态文案（站内审定口径）', permission: '公开', description: 'TDCA 三空间之一：负空间管「什么不能做」——只讲原则与类别，是拒绝清单面向公众的说明面。' },
  { path: '/academy/outline', title: '教材目录（纲要）', layer: 'L0', dataSource: '静态文案（照贴）', permission: '公开', description: '商学院教材目录（纲要）：五卷 35 章编排（原文明载「章」），正文不入站。' },
  { path: '/start/three-questions', title: '三问向导 · 贡献前自述', layer: 'L0', dataSource: '纯前端表单（零接口调用）；提交功能待后端就绪', permission: '公开', description: '交素材前的三问：原创吗／用过 AI 吗／用在什么场景。系统只汇总成自述草稿，⛔ 代判；提交功能在建，如实标注。' },
  { path: '/verify', title: '怎么验证 · 5 分钟三件自查', layer: 'L0', dataSource: '匿名只读三件：/api/v1/audit/ledger-public ＋ /api/v1/ci/badge ＋ /api/v1/formal/conclusion/catalog', permission: '公开', description: '不注册 5 分钟三件自查全路径：公开账本 → 机验徽章 → 形式化清单；三个端点匿名只读：锚点摘要可复算，记录哈希可核对不可复算。' },
  { path: '/five-orders', title: '五序资产总览', layer: 'L0', dataSource: 'GET /api/v1/assets/five-orders（DB 实读）', permission: '公开', description: '五序资产池总览：效用权／配置权／NCA 资产／MOU 凭证／跨场景画像；真实资产待生态接入，本页只读展示，不含任何交易入口。' },
  { path: '/official-assets', title: '官方资产区', layer: 'L0', dataSource: '静态文案（站内审定口径）＋ 文库产物库只读面', permission: '公开', description: '官方工具（免费）在上、官方产物在下；调用计价未通支付渠道前如实标未开放，零支付集成。' },
  { path: '/status', title: '系统健康', layer: 'L0', dataSource: 'GET /api/v1/system/overview ＋ /api/v1/ci/badge ＋ /api/v1/eios/cluster-status', permission: '公开', description: '三源合一系统健康面；接口失败 fail-soft 人话兜底，不白屏。' },
  { path: '/terms', title: '术语检索', layer: 'L0', dataSource: 'GET /api/v1/knowledge/terms?q=（服务端过滤）', permission: '登录 DID（匿名面后端已脱敏）', description: '站内术语注册表检索：词与释义两列，服务端过滤；登录可见全量，⛔ 匿名开放。' },
  { path: '/use/upload', title: '交素材（上传一件）', layer: 'L0', dataSource: 'POST /api/v1/use/upload（登录后单件直传；哈希防重）', permission: '登录 DID（未登录请先登录）', description: '把素材原件交给站方：选一件文件传上来，当场看到哈希与归属。同一件重复传不会重复收。' },
  { path: '/use/agent', title: '代办登记（机器人只跑腿）', layer: 'L0', dataSource: '复用 POST /api/v1/ownership/register＋ GET /api/v1/use/upload/{id}；草稿仅本地态，不落库不出号', permission: '登录 DID（须本人登录态；未确认 ⛔ 出号）', description: '上传成功后接着办登记：机器人只问缺项、出草稿；本人看过草稿、显式点确认，才出登记号。机器人不代签、不代判、不对外承诺。' },
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
      dataSource="静态元数据（PAGE_META 38 条）"
      permission="公开"
      description="本站各面索引：每面标注数据源与访问权限；未收录面不登记。"
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
