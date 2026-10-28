// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B2 S2-6 · 私域入口＋边界标识（批2前三包）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B2-001 S2-6——讲清公域／私域与两权闸门；
//   三条铁句必写：获取方式≠已获授权／网站＝接口⛔私域仓库／私域内部可存在对外协作必经公域；
//   口径与体系结构说明（6132）一致，⛔ 造新说法新术语
// 口径附录（终稿）: 机器人不代签不代判（#5）／节点＝场景私域·我方管公域（#7）／
//   两权私域可存在·对外协作必经公域（#8）／获取方式≠已获授权（#14）
// 红线: 页面零内部编号零价格字样
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from './PageShell'

const IRON_SENTENCES = [
  '获取方式 ≠ 已获授权：能拿到手，不等于被允许使用；授权以登记簿里的登记为准，没登记就是没授权。',
  '网站＝接口，⛔ 私域仓库：本站是公域的接口与门面，不在站上替你保管私域内容；私域的东西存在你那一侧。',
  '私域内部可存在，对外协作必经公域：你的私域内部制度与协作由你管；一旦要跨出来协作，就必须走公域的登记与闸门。',
]

export function PrivateDomainPage() {
  return (
    <PageShell dataNature="real"
      title="私域与边界 · 公域守门人"
      dataSource="纯前端说明页（零接口调用）；口径与站内体系结构说明一致"
      permission="公开"
      description="哪一块归站上管（公域）、哪一块归节点所有者管（私域）、两权闸门怎么过——起私域节点之前，先读这一页。"
    >
      <div data-testid="private-page" className="space-y-6">
        <section data-testid="private-domains" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">两域分工</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <div data-testid="private-public" className="rounded border border-gray-200 p-3">
              <div className="mb-1 text-xs font-semibold text-gray-800">公域（站上管）</div>
              <ul className="list-inside list-disc space-y-0.5 text-xs leading-relaxed text-gray-600">
                <li>站点本身与各公开页面</li>
                <li>只读接口（任何第三方可复算的公开面）</li>
                <li>公开账本与存证核验</li>
                <li>沙盒（制度化学反应釜，全程留痕）</li>
                <li>负空间检查（「什么不能做」的公开面）</li>
              </ul>
            </div>
            <div data-testid="private-own" className="rounded border border-gray-200 p-3">
              <div className="mb-1 text-xs font-semibold text-gray-800">私域（节点所有者管）</div>
              <ul className="list-inside list-disc space-y-0.5 text-xs leading-relaxed text-gray-600">
                <li>私有库（你的数据、你的素材）</li>
                <li>内部制度（你的场景规则，⛔ 违背 TDCA 制度）</li>
                <li>自有智能体（你那一侧运行的）</li>
              </ul>
            </div>
          </div>
          <p className="mt-3 text-xs leading-relaxed text-gray-600">
            一个节点就是一个场景的私域。站上管公域、不管你的私域内部；但所有节点都守 TDCA 制度——私域内部制度我不干涉，违背者过不了共识门槛（机制性，非处罚）。
          </p>
        </section>

        <section data-testid="private-gates" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">两权闸门（对外协作前必过）</h3>
          <div className="space-y-2 text-xs leading-relaxed text-gray-600">
            <p>
              <span className="font-semibold text-gray-700">权属登记（这是谁的）：</span>
              凡具表达形式者皆可登记，须载生成来源谱系。入口：
              <Link data-testid="private-road-ownership" to="/ownership-registry" className="text-blue-700 underline underline-offset-2">权属登记页</Link>
              。
            </p>
            <p>
              <span className="font-semibold text-gray-700">授权登记（允许谁用、什么条件）：</span>
              四要件缺一即拒；签名须本人，智能体不代持代填。入口：
              <Link data-testid="private-road-auth" to="/authorization-registry" className="text-blue-700 underline underline-offset-2">授权登记页</Link>
              。
            </p>
          </div>
        </section>

        <section data-testid="private-iron" className="rounded-lg border border-gray-800 bg-gray-900 p-4 text-white">
          <h3 className="mb-2 text-sm font-semibold">三条铁句</h3>
          <ol className="list-inside list-decimal space-y-1.5 text-xs leading-relaxed text-gray-200">
            {IRON_SENTENCES.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ol>
        </section>

        <section data-testid="private-start-node" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">起一个节点</h3>
          <p className="mb-2 text-xs leading-relaxed text-gray-600">
            路径：先完成两权登记（上方两闸门），再走智能体通道登记（
            <Link data-testid="private-road-channel" to="/channel/registry" className="text-blue-700 underline underline-offset-2">通道登记入口</Link>
            ），最后取本地部署包在你那一侧把节点跑起来。
          </p>
          <p data-testid="private-pkg-pending" className="rounded bg-gray-50 p-2 text-xs text-amber-700">
            本地部署包：<span className="font-semibold">建设中</span>。真因：「私域可带走」段待后端就绪（预计后批）——两权登记与通道登记现在可以先走。
          </p>
        </section>

        <section data-testid="private-consistency" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-900">口径说明</h3>
          <p className="text-xs leading-relaxed text-gray-600">
            本页口径与站内体系结构说明一致，未引入任何新说法：网页只为人做，智能体走接口；机器人不代签、不代判；同构只到接口面。另有不清之处，以站内制度地图与公开账本为准。
          </p>
        </section>
      </div>
    </PageShell>
  )
}
