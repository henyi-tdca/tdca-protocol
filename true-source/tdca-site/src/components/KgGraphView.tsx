// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 知识库·图谱视图（L1SI211-KG-SITE-001）
// 约束矩阵: 呈现三要件——分层浏览／搜索＋子图展开／节点可点开看出处（对外面显类与层）；
//           数字实读 manifest ⛔ 写死；⛔ 与文档库、制度库重复列表；匿名可读
// 数据源: GET /api/v1/kg/manifest|nodes|node/{id}|subgraph|edges ＋ /kg/v1/* 静态包
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/lib/client'

interface KgNode { id: string; layer: string; layer_name: string; type: string; type_name: string; label: string }
interface ManifestView { sha256_16: string; files: Record<string, string | null> }
interface NodeDetail {
  node: KgNode
  out_edges: { id: string; type: string; target: string }[]
  in_edges: { id: string; type: string; source: string }[]
}
interface SubgraphView { root: string; depth: number; nodes: KgNode[]; edges: { id: string; type: string; source: string; target: string }[] }

const LAYERS: { key: string; label: string }[] = [
  { key: 'L0', label: '宪法层' },
  { key: 'L1', label: '协议规范层' },
  { key: 'G', label: '治理层' },
  { key: 'L2', label: '场景论文层' },
]

export default function KgGraphView() {
  const [manifest, setManifest] = useState<ManifestView | null>(null)
  const [layer, setLayer] = useState('L0')
  const [q, setQ] = useState('')
  const [nodes, setNodes] = useState<KgNode[]>([])
  const [count, setCount] = useState(0)
  const [detail, setDetail] = useState<NodeDetail | null>(null)
  const [sub, setSub] = useState<SubgraphView | null>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    void api.get<ManifestView>('/api/v1/kg/manifest').then((r) => {
      if (r.ok) setManifest(r.data)
    })
  }, [])

  useEffect(() => {
    setDetail(null); setSub(null); setErr('')
    const params = new URLSearchParams({ layer, limit: '500' })
    if (q.trim()) params.set('q', q.trim())
    void api.get<{ count: number; nodes: KgNode[] }>(`/api/v1/kg/nodes?${params}`).then((r) => {
      if (r.ok) { setNodes(r.data.nodes); setCount(r.data.count) }
      else setErr(`图谱加载失败：${r.reason}`)
    })
  }, [layer, q])

  const onPick = (id: string) => {
    setSub(null)
    void api.get<NodeDetail>(`/api/v1/kg/node/${id}`).then((r) => {
      if (r.ok) setDetail(r.data)
      else setErr(`节点加载失败：${r.reason}`)
    })
  }

  const onExpand = (id: string) => {
    void api.get<SubgraphView>(`/api/v1/kg/subgraph?root=${id}&depth=2`).then((r) => {
      if (r.ok) setSub(r.data)
      else setErr(`子图展开失败：${r.reason}`)
    })
  }

  return (
    <div className="space-y-3" data-testid="kg-graph-view">
      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
        {LAYERS.map((l) => (
          <button
            key={l.key}
            data-testid={`kg-layer-${l.key}`}
            data-active={layer === l.key}
            className={`rounded-md border px-3 py-1 text-sm ${
              layer === l.key
                ? 'border-blue-600 bg-blue-600 text-white'
                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'}`}
            onClick={() => setLayer(l.key)}>
            {l.label}
          </button>
        ))}
        <input
          data-testid="kg-search"
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
          placeholder="搜索节点…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <span className="ml-auto" data-testid="kg-count">
          本层/检索：{count} 节点（实读接口）
        </span>
      </div>

      {err && <p className="rounded bg-red-50 p-3 text-sm text-red-600" role="alert">{err}</p>}

      <div className="grid gap-3 md:grid-cols-3">
        <ul className="max-h-[70vh] space-y-1 overflow-auto md:col-span-1" data-testid="kg-list">
          {nodes.map((n) => (
            <li key={n.id}>
              <button
                data-testid={`kg-node-${n.id}`}
                className={`w-full rounded border px-2 py-1 text-left text-sm ${
                  detail?.node.id === n.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 bg-white hover:bg-gray-50'}`}
                onClick={() => onPick(n.id)}>
                <span className="text-gray-800">{n.label}</span>
                <span className="ml-2 text-xs text-gray-400">{n.type_name}</span>
              </button>
            </li>
          ))}
          {nodes.length === 0 && !err && <li className="text-sm text-gray-400">无匹配节点</li>}
        </ul>

        <div className="space-y-3 md:col-span-2">
          {detail && (
            <article data-testid="kg-detail" className="rounded-lg border border-gray-200">
              <header className="border-b border-gray-100 px-4 py-2">
                <h2 className="text-base font-semibold text-gray-800">{detail.node.label}</h2>
                <p className="text-xs text-gray-500" data-testid="kg-detail-meta">
                  层：{detail.node.layer_name}（{detail.node.layer}）｜ 类：{detail.node.type_name}（{detail.node.type}）
                </p>
              </header>
              <div className="px-4 py-3 text-sm">
                <p className="mb-1 text-xs font-semibold text-gray-500">指出关系（{detail.out_edges.length}）</p>
                <ul className="mb-3 space-y-0.5">
                  {detail.out_edges.map((e) => (
                    <li key={e.id} className="text-gray-700">→ {e.target} ｜ <span className="text-xs text-gray-400">{e.type}</span></li>
                  ))}
                  {detail.out_edges.length === 0 && <li className="text-gray-400">无</li>}
                </ul>
                <p className="mb-1 text-xs font-semibold text-gray-500">指入关系（{detail.in_edges.length}）</p>
                <ul className="space-y-0.5">
                  {detail.in_edges.map((e) => (
                    <li key={e.id} className="text-gray-700">← {e.source} ｜ <span className="text-xs text-gray-400">{e.type}</span></li>
                  ))}
                  {detail.in_edges.length === 0 && <li className="text-gray-400">无</li>}
                </ul>
                <button
                  data-testid="kg-expand"
                  className="mt-3 rounded-md border border-blue-600 px-3 py-1 text-sm text-blue-600 hover:bg-blue-50"
                  onClick={() => onExpand(detail.node.id)}>
                  展开两层子图
                </button>
              </div>
            </article>
          )}

          {sub && (
            <section data-testid="kg-subgraph" className="rounded-lg border border-blue-100 bg-blue-50/40 p-3 text-sm">
              <p className="mb-2 text-xs font-semibold text-gray-500">
                子图（根 {sub.root} · {sub.depth} 层）：{sub.nodes.length} 节点 / {sub.edges.length} 关系
              </p>
              <ul className="grid gap-0.5 md:grid-cols-2">
                {sub.nodes.map((n) => (
                  <li key={n.id} className="text-gray-700">
                    <button className="text-blue-600 hover:underline" onClick={() => onPick(n.id)}>{n.label}</button>
                    <span className="ml-1 text-xs text-gray-400">{n.type_name}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {manifest && (
            <p className="text-xs text-gray-400" data-testid="kg-manifest">
              包版本 sha256_16={manifest.sha256_16} ｜ 静态包 /kg/v1/ 直取（manifest.yaml · nodes.yaml · edges.yaml · README.md）
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
