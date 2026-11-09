// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI206-MIGRATE-B3 /me/node/net 我的节点 · 条例与契约
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B3-001 §一 G-2——权限照 route-parity.md
//   「登录 DID（本机数据只本人可见）」；§二-A 私域门槛 API 401/403 fail-closed 把守
// 并轨注记: MIGRATE 批3 自旧树 pages/me-node-net.tsx 同栈直拷适配——
//   ① 引路三换（PageShell→@/components、SimulatedBadge→@/lib、数据源 node-net-data 同目录）；
//   ② 私域门槛照 /channel/my 先例：载入门禁探针（PrivateGate），未登录 ⟹ 人话提示＋
//      私域内容零渲染（前端隐藏 ⛔ 作据——把守据是接口 401/403）；
//   ③ 卡面内容/testid 一字未动。
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from '@/components/PageShell'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'
import { CARD_FOOTER, MY_NODE, NINE_APIS, NODE_REGULATION } from './node-net-data'

export function MeNodeNetPage() {
  const gate = usePrivateGate()

  return (
    <PageShell
      title="我的节点 · 条例与契约"
      dataSource="在册条例 V1.0 与本机节点配置（配置未设处如实标「未设置／待复算」）；载入门禁 GET /api/v1/auth/me"
      permission="登录 DID（本机数据只本人可见）"
      description="私域节点面：卡一只读本人节点配置；卡二挂在册条例与契约。字段无真值如实标，不预填。"
    >
      <div data-testid="me-node-net-page" className="space-y-6">
        {/* 私域门槛：接口 401/403 把守（未登录零渲染） */}
        {gate !== 'ok' && <PrivateGateNotice state={gate} />}

        {gate === 'ok' && (
          <>
            {/* 卡 1「我的节点」（只读） */}
            <section data-testid="mn-card1" className="rounded-xl border border-gray-200 bg-white p-6">
              <h3 className="text-base font-bold text-gray-900">我的节点</h3>
              <dl className="mt-4 grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
                <div><dt className="font-medium text-gray-500">节点名</dt><dd className="mt-0.5 text-gray-900">{MY_NODE.nodeName}</dd></div>
                <div><dt className="font-medium text-gray-500">名分</dt><dd className="mt-0.5 text-gray-900">{MY_NODE.identity}（现网仅此一个节点）</dd></div>
                <div><dt className="font-medium text-gray-500">根指纹（前 8 位）</dt><dd className="mt-0.5 text-gray-900">{MY_NODE.rootFingerprint8}</dd></div>
                <div><dt className="font-medium text-gray-500">起站形态</dt><dd className="mt-0.5 text-gray-900">{MY_NODE.deployForm}</dd></div>
                <div><dt className="font-medium text-gray-500">首启时间</dt><dd className="mt-0.5 text-gray-900">{MY_NODE.firstStart}</dd></div>
                <div><dt className="font-medium text-gray-500">接入阶段</dt><dd className="mt-0.5 text-gray-900">{MY_NODE.phase}</dd></div>
                <div className="sm:col-span-2">
                  <dt className="font-medium text-gray-500">制度下沉（计法细则）</dt>
                  <dd className="mt-0.5 text-gray-900">{MY_NODE.sink}（a/b ＋ 六要素 ＋ 加严/冲突未计算）</dd>
                </div>
              </dl>
              <p className="mt-4 rounded bg-gray-50 p-3 text-sm font-medium text-gray-800">{CARD_FOOTER}</p>
            </section>

            {/* 卡 2「条例与契约」（只读） */}
            <section data-testid="mn-card2" className="rounded-xl border border-gray-200 bg-white p-6">
              <h3 className="text-base font-bold text-gray-900">条例与契约</h3>
              <dl className="mt-4 space-y-3 text-sm">
                <div>
                  <dt className="font-medium text-gray-500">在册条例</dt>
                  <dd className="mt-0.5 text-gray-900">
                    {NODE_REGULATION.name} · {NODE_REGULATION.version} · {NODE_REGULATION.effect}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">下载（对外公开版）</dt>
                  <dd className="mt-0.5 flex flex-wrap gap-x-4 gap-y-1">
                    <Link data-testid="mn-reg-human" to={`/docs/regulation/${encodeURIComponent(NODE_REGULATION.humanSlug)}`} className="text-blue-700 underline">人读版</Link>
                    <Link data-testid="mn-reg-machine" to={`/docs/regulation/${encodeURIComponent(NODE_REGULATION.machineSlug)}`} className="text-blue-700 underline">机读版（yaml）</Link>
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">九类接口清单（名称）</dt>
                  <dd className="mt-1 flex flex-wrap gap-1.5">
                    {NINE_APIS.map((a) => (
                      <span key={a.name} data-testid="mn-api-chip" className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-700">{a.name}</span>
                    ))}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">契约版本与弃用期</dt>
                  <dd className="mt-0.5 text-gray-900">{NODE_REGULATION.contractVersion}；弃用期：{NODE_REGULATION.contractDeprecation}</dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">变更公告</dt>
                  <dd className="mt-0.5 text-gray-900">{NODE_REGULATION.changelog}</dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">制度适配四态（本节点）</dt>
                  <dd className="mt-1 flex flex-wrap gap-1.5 text-xs">
                    <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-green-800">已适配（本站自承全套在册制度）</span>
                    <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-gray-600">待适配 · 尚无其他节点</span>
                    <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-gray-600">冲突·不可启用 · 尚无</span>
                    <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-gray-600">父级直承 · 尚无</span>
                  </dd>
                </div>
              </dl>
            </section>
          </>
        )}
      </div>
    </PageShell>
  )
}
