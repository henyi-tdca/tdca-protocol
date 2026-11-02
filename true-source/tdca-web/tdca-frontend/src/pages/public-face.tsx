// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI188-NAV-FIX-006 P2-2 匿名可见面清单一页三栏
// 约束矩阵: NAV-FIX-006 §一——只读事实页：照包内路由表＋匿名实测状态码取数（2026-11-02 线上实测），
//           ⛔ 凭印象、⛔ 抄设计稿、⛔ 承诺、⛔ 营销语、⛔ 「即将上线」类表述、⛔ 为凑数放开接口
// =============================================================================
import { PageShell } from './PageShell'

/** 可看：匿名可读内容面（页面匿名 200 且内容可读；状态码 2026-11-02 实测） */
const FACE_PUBLIC: { route: string; note: string; code: string }[] = [
  { route: '/', note: '门户首页：三体可视化与四层架构制度总览', code: '200' },
  { route: '/about', note: '一页看懂 TDCA：面向普通读者的通俗说明', code: '200' },
  { route: '/five-orders', note: '五序资产总览：名称、说明与在册数量（只读）', code: '200' },
  { route: '/channel', note: '智能体通道总入口：前置登记与六步硬序（照在册条例）', code: '200' },
  { route: '/audit', note: '审计透明：公开账本与 NCA 链说明（制度即公开）', code: '200' },
  { route: '/rules', note: '制度地图：56 件制度件五类五态六步', code: '200' },
  { route: '/verify', note: '怎么验证：不注册 5 分钟三件自查全路径', code: '200' },
  { route: '/terms', note: '术语检索：匿名可读脱敏版（内部编号不出）', code: '200' },
  { route: '/attestation/history', note: '确权历史：公开留痕（时间／事件类型／公开状态）', code: '200' },
]

/** 需登录：页在册，匿名只见登录墙（页面路由 200，受保护内容不出现；私域接口匿名 401） */
const FACE_LOGIN: { route: string; note: string; code: string }[] = [
  { route: '/me', note: '私域总栏：谁的数据谁可见（接口匿名 401）', code: '200（登录墙）' },
  { route: '/studio', note: '作业办理面：全生命周期操作须会话（接口匿名 401）', code: '200（登录墙）' },
  { route: '/agents', note: '集群观测面：面板数据须会话取数', code: '200（登录墙）' },
  { route: '/attestation', note: '确权办理面：队列与操作须登录＋HUF', code: '200（登录墙）' },
  { route: '/governance', note: '治理操作面：四大操作须 HUF 签批', code: '200（登录墙）' },
  { route: '/review', note: '缔约评审面：须审核身份与写令牌', code: '200（登录墙）' },
  { route: '/use/upload', note: '交素材：须登录归属（后端同守 401）', code: '200（登录墙）' },
  { route: '/use/agent', note: '代办登记：须本人在场确认（后端同守 401）', code: '200（登录墙）' },
  { route: '/me/node/net', note: '本机节点数据：只本人可见', code: '200（登录墙）' },
]

/** 不开放：运营门与内部面（匿名不可读；接口匿名 401） */
const FACE_CLOSED: { route: string; note: string; code: string }[] = [
  { route: '/ops', note: '站点运维端：operator 门，匿名只见「须管理员身份」提示，内容不露', code: '200（无权限提示）' },
  { route: '/ops/manual', note: '运维手册直读：operator/founder 门内', code: '200（无权限提示）' },
  { route: '/ops/logs', note: '运维日志：operator/founder 门内', code: '200（无权限提示）' },
  { route: '/api/v1/ops/*', note: '运维接口：匿名 401', code: '401' },
  { route: '/api/v1/me/dashboard', note: '私域接口：匿名 401（页面对应 /me 登录墙）', code: '401' },
]

function FaceTable({ testid, rows, accent }: { testid: string; rows: typeof FACE_PUBLIC; accent: string }) {
  return (
    <table data-testid={testid} className="w-full text-left text-xs">
      <thead>
        <tr className={`border-b ${accent}`}>
          <th className="py-1.5 pr-2 font-medium">路由</th>
          <th className="py-1.5 pr-2 font-medium">一句话</th>
          <th className="py-1.5 font-medium">匿名实测</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.route} className="border-b border-gray-100">
            <td className="py-1.5 pr-2 font-mono text-blue-700">{r.route}</td>
            <td className="py-1.5 pr-2 text-gray-700">{r.note}</td>
            <td className="py-1.5 whitespace-nowrap text-gray-500">{r.code}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/** 匿名可见面清单一页（NAV-FIX-006 P2-2）：三栏照实，取数日 2026-11-02 */
export function PublicFacePage() {
  return (
    <PageShell
      title="匿名可见面"
      dataSource="包内路由表＋匿名实测状态码（2026-11-02 线上只读直核）；口径：页面路由状态码＋匿名态实际渲染"
      permission="公开（本页匿名可读）"
      description="匿名来访这一站能看什么、什么要登录、什么不开放——三栏照实清单，逐条可复核。"
    >
      <div data-testid="public-face-page" className="space-y-6">
        <p className="text-xs text-gray-500">
          「需登录」栏页面路由匿名返回 200 但只见登录墙（受保护内容不出现），私域接口匿名 401；
          「不开放」栏为运营门与内部面。本清单只读事实，不含承诺。
        </p>
        <section data-testid="public-face-public">
          <h3 className="mb-2 text-sm font-semibold text-emerald-800">可看（匿名可读）</h3>
          <FaceTable testid="public-face-table-public" rows={FACE_PUBLIC} accent="border-emerald-200 text-emerald-700" />
        </section>
        <section data-testid="public-face-login">
          <h3 className="mb-2 text-sm font-semibold text-amber-800">需登录（匿名只见登录墙）</h3>
          <FaceTable testid="public-face-table-login" rows={FACE_LOGIN} accent="border-amber-200 text-amber-700" />
        </section>
        <section data-testid="public-face-closed">
          <h3 className="mb-2 text-sm font-semibold text-gray-700">不开放（运营门与内部面）</h3>
          <FaceTable testid="public-face-table-closed" rows={FACE_CLOSED} accent="border-gray-300 text-gray-600" />
        </section>
      </div>
    </PageShell>
  )
}
