// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /market 配置权市场（A-4 五阶资产池 + 管理面四操作）
// 约束矩阵: FRAMEWORK-001 §四 /market（L2）+ A-4 契约 + ID92 + 管理面规格件（已验收定稿 V1.0）
// =============================================================================
import { useState } from 'react'
import { useApiGet } from '@/lib/useApi'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { api } from '@/lib/client'

interface FiveOrdersData {
  assets: { order: number; name: string; desc: string; count: number }[]
  note: string
}

interface Listing {
  listing_id: string
  asset_summary: string
  scene: string
  scope_note: string
  term_note: string
  initial_conditions: string
  sandbox_flag: boolean
  status: 'active' | 'paused' | 'delisted'
  data_provenance: string
  ownership_record_id: string
  authorization_record_id: string
  published_at: string
}

interface PublicListing {
  listing_id: string
  权属信息: { ownership_record_id: string; owner_alias: string }
  授权信息: { scene: string; scope_note: string; term_note: string; sandbox: boolean }
  授权状态: { listing_status: string; data_provenance: string }
  获取方式: { initial_conditions: string }
  published_at: string
}

/** 管理面：挂出表单（先有成件闸门在后端 fail-closed；沙盒例外显式标记） */
function PublishPanel({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState({
    ownership_record_id: '',
    authorization_record_id: '',
    asset_summary: '',
    scene: '',
    scope_note: '',
    term_note: '',
    initial_conditions: '',
  })
  const [sandbox, setSandbox] = useState(false)
  const [msg, setMsg] = useState('')

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm({ ...form, [k]: e.target.value })

  const submit = async () => {
    setMsg('提交中…')
    const r = await api.post('/api/v1/market-admin/listings', { ...form, sandbox })
    if (r.ok) {
      setMsg('挂出成功（' + (sandbox ? '沙盒／演练例外，显式标记' : '成件＋四要件齐') + '）')
      setForm({ ownership_record_id: '', authorization_record_id: '', asset_summary: '', scene: '', scope_note: '', term_note: '', initial_conditions: '' })
      setSandbox(false)
      onDone()
    } else {
      setMsg('[fail-closed] ' + (r as { reason?: string }).reason)
    }
  }

  return (
    <div className="space-y-2 rounded-lg border border-gray-200 p-3" data-testid="market-admin-publish">
      <div className="text-sm font-semibold text-gray-800">挂出（A-1：先有成件——权属成件＋授权成件＋四要件齐；例外仅沙盒演练）</div>
      <div className="grid grid-cols-1 gap-2 text-xs">
        <input className="rounded border p-1.5" placeholder="权属登记成件号（OR-xxx，须本人）" value={form.ownership_record_id} onChange={set('ownership_record_id')} />
        <input className="rounded border p-1.5" placeholder="授权登记成件号（AR-xxx；沙盒例外可空）" value={form.authorization_record_id} onChange={set('authorization_record_id')} />
        <input className="rounded border p-1.5" placeholder="标的（五阶资产形态说明）" value={form.asset_summary} onChange={set('asset_summary')} />
        <input className="rounded border p-1.5" placeholder="场景" value={form.scene} onChange={set('scene')} />
        <input className="rounded border p-1.5" placeholder="权限范围（照授权件载明）" value={form.scope_note} onChange={set('scope_note')} />
        <input className="rounded border p-1.5" placeholder="期限（照在册已裁者）" value={form.term_note} onChange={set('term_note')} />
        <textarea className="rounded border p-1.5" placeholder="初始条件（必公开）" value={form.initial_conditions} onChange={set('initial_conditions')} />
        <label className="flex items-center gap-2 text-gray-600">
          <input type="checkbox" checked={sandbox} onChange={(e) => setSandbox(e.target.checked)} />
          沙盒／演练例外（出盒仍须授权）
        </label>
      </div>
      <button className="rounded bg-emerald-600 px-3 py-1 text-xs text-white" onClick={submit}>挂出</button>
      {msg && <p className="text-xs text-gray-500">{msg}</p>}
    </div>
  )
}

/** 管理面：本人挂出件列表＋暂停／恢复／下架 */
function MyListings({ refreshKey, onChanged }: { refreshKey: number; onChanged: () => void }) {
  const { status, data } = useApiGet<{ count: number; listings: Listing[]; note: string }>(
    '/api/v1/market-admin/listings',
  )
  const [msg, setMsg] = useState('')
  void refreshKey

  const act = async (id: string, action: 'pause' | 'resume' | 'delist') => {
    const path = action === 'delist'
      ? `/api/v1/market-admin/listings/${id}/delist`
      : `/api/v1/market-admin/listings/${id}/status`
    const r = await api.post(path, action === 'delist' ? {} : { action })
    setMsg(r.ok ? `已执行 ${action}` : '[fail-closed] ' + (r as { reason?: string }).reason)
    onChanged()
  }

  if (status === 'loading') return <p className="text-xs text-gray-400">挂出件加载中…</p>
  if (status === 'fail') return <p className="text-xs text-gray-500">管理面须登录（本人面 fail-closed）</p>
  const rows = data?.listings ?? []
  return (
    <div className="space-y-2" data-testid="market-admin-mine">
      <div className="text-sm font-semibold text-gray-800">我的挂出（{data?.count ?? 0}；含已下架）</div>
      {rows.map((l) => (
        <div key={l.listing_id} className="rounded-lg border border-gray-200 p-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-800">{l.asset_summary}</span>
            <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">
              {l.status}{l.sandbox_flag ? ' · 沙盒' : ''} · {l.data_provenance}
            </span>
          </div>
          <div className="mt-1 text-gray-500">场景 {l.scene}｜初始条件：{l.initial_conditions}</div>
          {l.status !== 'delisted' && (
            <div className="mt-2 flex gap-2">
              {l.status === 'active' && <button className="rounded border border-gray-300 bg-white px-2 py-0.5 text-gray-700 hover:bg-gray-50" onClick={() => act(l.listing_id, 'pause')}>暂停</button>}
              {l.status === 'paused' && <button className="rounded border border-gray-300 bg-white px-2 py-0.5 text-gray-700 hover:bg-gray-50" onClick={() => act(l.listing_id, 'resume')}>恢复</button>}
              <button className="rounded border border-red-200 bg-white px-2 py-0.5 text-red-600 hover:bg-red-50" onClick={() => act(l.listing_id, 'delist')}>下架（不溯及授权件）</button>
            </div>
          )}
        </div>
      ))}
      {msg && <p className="text-xs text-gray-500">{msg}</p>}
    </div>
  )
}

/** 公开面：四字段投影（免会话；下架即撤出） */
function PublicListings({ refreshKey }: { refreshKey: number }) {
  const { status, data } = useApiGet<{ count: number; listings: PublicListing[] }>(
    '/api/v1/market-admin/public/listings',
  )
  void refreshKey
  if (status === 'loading') return <p className="text-xs text-gray-400">公开面加载中…</p>
  if (status === 'fail') return null
  const rows = data?.listings ?? []
  return (
    <div className="space-y-2" data-testid="market-admin-public">
      <div className="text-sm font-semibold text-gray-800">在挂要约（公开面四字段：权属信息／授权信息／授权状态／获取方式）</div>
      {rows.length === 0 && <p className="text-xs text-gray-500">暂无在挂要约（空栏为常态）</p>}
      {rows.map((l) => (
        <div key={l.listing_id} className="rounded-lg border border-gray-200 p-3 text-xs">
          <div className="font-medium text-gray-800">{l.权属信息.ownership_record_id} · {l.授权信息.scene}</div>
          <div className="mt-1 text-gray-500">
            授权状态 {l.授权状态.listing_status}{l.授权信息.sandbox ? ' · 沙盒演练' : ''}｜
            获取方式：{l.获取方式.initial_conditions}
          </div>
        </div>
      ))}
    </div>
  )
}

/** L2 配置权市场：A-4 五阶资产池（只读优先）＋ 管理面四操作（挂出／查询／状态变更／下架） */
export function MarketPage() {
  const { status, data, nature } = useApiGet<FiveOrdersData>('/api/v1/assets/five-orders')
  const [refreshKey, setRefreshKey] = useState(0)
  const bump = () => setRefreshKey((k) => k + 1)

  return (
    <PageShell
      title="配置权市场（L2）"
      dataSource="A-4 GET /api/v1/assets/five-orders + 管理面 /api/v1/market-admin/*"
      permission="公开读 / 挂出与状态操作须本人登录"
      description="配置权协议化流转市场——使用权/配置权可流转，所有权不流转（防混淆）。管理面四操作：挂出（先有成件）／查询／状态变更／下架（不溯及授权件）。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="market-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="market-assets" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <SimulatedBadge nature={nature ?? 'simulated'} />
            <span>{data.note}</span>
          </div>
          {data.assets.map((a) => (
            <div key={a.order} className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
              <div>
                <div className="text-sm font-semibold text-gray-800">
                  #{a.order} {a.name}
                </div>
                <div className="text-xs text-gray-500">{a.desc}</div>
              </div>
              <span className="rounded bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                {a.count} 在册（模拟）
              </span>
            </div>
          ))}
        </div>
      )}

      <hr className="my-4 border-gray-100" />
      <div className="space-y-4">
        <PublicListings refreshKey={refreshKey} />
        <PublishPanel onDone={bump} />
        <MyListings refreshKey={refreshKey} onChanged={bump} />
      </div>
    </PageShell>
  )
}
