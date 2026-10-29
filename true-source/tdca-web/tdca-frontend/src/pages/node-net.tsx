// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 节点网络公开面（NODE-NET-A-001 公域四块）
// 约束矩阵: 可视图只画已披露真节点（现仅创世节点一个）·空位固定句；状态栏「数据截至 HH:MM」
//   ⛔「实时」字样·无心跳固定句；接口九类空壳禁止一律「建设中 · 未开放」（唯文档/协议包
//   分发可用）；条例入口固定抬头＋三处互链；⛔ 假地址、⛔ 示例响应、⛔ 内部编号进文案
// 数据源: node-net-data.ts（三处同源唯一源·硬约束八）
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from './PageShell'
import { ADAPT_STATES, LINK_KINDS, NINE_APIS, NODES, NODE_EMPTY_TEXT, NODE_REGULATION } from './node-net-data'

export function NodeNetPage() {
  // 「数据截至 HH:MM」：页面载入时刻（⛔ 实时；心跳通道归后续批次）
  const stamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })

  return (
    <PageShell
      title="节点网络"
      dataSource="在册条例 V1.0 与节点现状（真值缺失处如实标「未设置／待复算／尚无」）"
      permission="公开"
      description="业务端节点接入的公开面：可视图只画已披露真节点；状态只给最后心跳与数据截至时刻；接口未实现一律不开放。"
      dataNature="real"
    >
      <div data-testid="node-net-page" className="space-y-8">
        {/* ── 块一 · 可视图（只画已披露真节点；⛔ 演示点、⛔ 占位名） ── */}
        <section data-testid="nn-viz" className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="text-base font-bold text-gray-900">节点可视图</h3>
          <div className="mt-4 grid grid-cols-3 items-center gap-4">
            {/* 唯一真节点：创世节点 */}
            {NODES.map((n) => (
              <div key={n.name} data-testid="nn-viz-node"
                   className="flex flex-col items-center rounded-lg border-2 border-blue-600 bg-blue-50 p-4">
                <span className="h-4 w-4 rounded-full bg-blue-600" aria-hidden="true" />
                <span className="mt-2 text-sm font-semibold text-gray-900">{n.name}</span>
                <span className="text-xs text-gray-600">{n.adaptation}</span>
              </div>
            ))}
            {/* 其余位置固定句（⛔ 占位名） */}
            {[0, 1].map((i) => (
              <div key={i} data-testid="nn-viz-empty"
                   className="flex h-full min-h-24 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-center text-xs text-gray-500">
                {NODE_EMPTY_TEXT}
              </div>
            ))}
          </div>
          {/* 图例：四态＋两种连线 */}
          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-gray-600">
            <span className="font-semibold text-gray-700">图例 · 制度适配四态：</span>
            {ADAPT_STATES.map((s) => (
              <span key={s} data-testid="nn-legend-state">{s}</span>
            ))}
            <span className="font-semibold text-gray-700">连线：</span>
            {LINK_KINDS.map((k) => (
              <span key={k} data-testid="nn-legend-link">{k}</span>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-500">图上节点 ↔ 条例第 16 条（准入：一切接入过闸门与审核）。</p>
        </section>

        {/* ── 块二 · 状态栏（⛔ 实时；最后心跳＋截至时刻） ── */}
        <section data-testid="nn-status" className="rounded-xl border border-gray-200 bg-white p-6">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-base font-bold text-gray-900">节点状态</h3>
            <span data-testid="nn-status-stamp" className="text-xs text-gray-500">数据截至 {stamp}</span>
          </div>
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                <th className="py-2 pr-4 font-medium">节点</th>
                <th className="py-2 pr-4 font-medium">状态</th>
                <th className="py-2 pr-4 font-medium">最后心跳</th>
                <th className="py-2 pr-4 font-medium">制度版本</th>
                <th className="py-2 pr-4 font-medium">下沉完整性</th>
                <th className="py-2 font-medium">阶段</th>
              </tr>
            </thead>
            <tbody>
              {NODES.map((n) => (
                <tr key={n.name} data-testid="nn-status-row" className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-medium text-gray-900">{n.name}</td>
                  <td className="py-2 pr-4 text-gray-700">{n.status}</td>
                  <td className="py-2 pr-4 text-gray-700">{n.heartbeat}</td>
                  <td className="py-2 pr-4 text-gray-700">{n.regulationVersion}</td>
                  <td className="py-2 pr-4 text-gray-700">{n.sink}</td>
                  <td className="py-2 text-gray-700">{n.phase}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-gray-500">状态口径 ↔ 条例第 10 条（制度对象必要状态必回站点；隐私最小化）。</p>
        </section>

        {/* ── 块三 · 接口信息（九类；空壳禁止一律未开放） ── */}
        <section data-testid="nn-apis" className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="text-base font-bold text-gray-900">接口信息（九类）</h3>
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                <th className="py-2 pr-4 font-medium">接口</th>
                <th className="py-2 pr-4 font-medium">用途</th>
                <th className="py-2 pr-4 font-medium">版本</th>
                <th className="py-2 font-medium">现在能不能用</th>
              </tr>
            </thead>
            <tbody>
              {NINE_APIS.map((a) => (
                <tr key={a.name} data-testid="nn-api-row" className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-medium text-gray-900">{a.name}</td>
                  <td className="py-2 pr-4 text-gray-700">{a.name}（同构接口）</td>
                  <td className="py-2 pr-4 text-gray-700">{NODE_REGULATION.version}</td>
                  <td className="py-2">
                    {a.usable
                      ? <span className="text-green-700">可用（条例人读／机读本页可下载）</span>
                      : <span className="text-gray-500">建设中 · 未开放</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-gray-500">接口口径 ↔ 条例第 12 条（九类同构接口）与第 14 条（未实现即不开放）。⛔ 本表不含接入地址与示例响应。</p>
        </section>

        {/* ── 块四 · 条例入口（固定抬头＋三处互链） ── */}
        <section data-testid="nn-reg" className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="text-base font-bold text-gray-900">条例入口</h3>
          <p className="mt-2 text-sm font-medium text-gray-800">
            制度随场景层级向下细化，子级须向其上一层适配，⛔ 不得低于上层门槛。
          </p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-gray-700">
            <li><Link to={`/docs/regulation/${encodeURIComponent(NODE_REGULATION.humanSlug)}`} className="text-blue-700 underline">人读版：{NODE_REGULATION.name} {NODE_REGULATION.version}（{NODE_REGULATION.effect}）</Link></li>
            <li><Link to={`/docs/regulation/${encodeURIComponent(NODE_REGULATION.machineSlug)}`} className="text-blue-700 underline">机读版（yaml，同源同版）</Link></li>
          </ul>
          <p className="mt-3 text-xs text-gray-500">
            互链索引：可视图 ↔ 第 16 条｜状态栏 ↔ 第 10 条｜接口信息 ↔ 第 12 条。
          </p>
        </section>
      </div>
    </PageShell>
  )
}
