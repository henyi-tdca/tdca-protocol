// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期 C-2 交付清单页（L1SI195-B1-001）
// 约束矩阵: 施工令 §三——逐件哈希必填（⛔「稍后补」顶替）·auth_id 必填（提示上一步未完成）
//   状态机 draft→uploading→delivered→received（received 须报哈希，无哈希视同未收）；
//   单件大小阈值在册未定 → 页内标「待运维核定」（⛔ 自设数字 S-5）
// 复用: PageShell / 会话令牌直注；后端 POST /api/v1/delivery/manifest|items|confirm
//   ＋ GET /api/v1/delivery/{delivery_id}（公开读免会话）
// =============================================================================
import { useState } from 'react'
import { sessionToken } from '@/api/client'
import { PageShell } from './PageShell'

interface Item {
  name: string
  version: string
  hash: string
  size_bytes: string
  volume_note: string
}

interface DeliveryView {
  delivery_id: string
  auth_id: string
  receiver: string
  batches: string
  deliver_at: string
  status: string
  items: Array<{ name: string; version: string; hash: string; size_bytes: number | null; volume_note: string }>
  total_items: number
  nca_seq: string
  note?: string
}

const EMPTY_ITEM: Item = { name: '', version: '', hash: '', size_bytes: '', volume_note: '' }

export function DeliveryPage() {
  // ── 开清单 ──
  const [authId, setAuthId] = useState('')
  const [receiver, setReceiver] = useState('')
  const [batches, setBatches] = useState('')
  const [deliverAt, setDeliverAt] = useState('')
  const [items, setItems] = useState<Item[]>([{ ...EMPTY_ITEM }])
  const [created, setCreated] = useState<{ delivery_id: string; nca_seq: string; status: string } | null>(null)
  // ── 查清单（公开读）──
  const [queryId, setQueryId] = useState('')
  const [view, setView] = useState<DeliveryView | null>(null)
  // ── 补件／确认 ──
  const [opId, setOpId] = useState('')
  const [addItems, setAddItems] = useState<Item[]>([{ ...EMPTY_ITEM }])
  const [receivedHashes, setReceivedHashes] = useState<Array<{ name: string; hash: string }>>([])
  const [confirmResult, setConfirmResult] = useState<{ status: string; checks: Array<{ name: string; match: boolean }>; note: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const post = async (url: string, body: unknown) => {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: sessionToken() ?? '' },
      body: JSON.stringify(body),
    })
    const raw = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(raw.detail ?? `没成功（HTTP ${res.status}）`)
    return raw.data as never
  }

  const onManifest = async () => {
    if (busy) return
    setBusy(true); setErr(''); setCreated(null)
    try {
      const clean = items.filter((it) => it.name.trim() || it.hash.trim())
      const data = await post('/api/v1/delivery/manifest', {
        auth_id: authId, receiver, batches, deliver_at: deliverAt,
        items: clean.map((it) => ({
          name: it.name, version: it.version, hash: it.hash,
          size_bytes: it.size_bytes ? Number(it.size_bytes) : undefined,
          volume_note: it.volume_note,
        })),
      })
      setCreated(data)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const onQuery = async () => {
    setErr('')
    const res = await fetch(`/api/v1/delivery/${encodeURIComponent(queryId.trim())}`)
    const raw = await res.json().catch(() => ({}))
    if (!res.ok) { setView(null); setErr(raw.detail ?? '没查到——请核对编号。'); return }
    setView(raw.data as DeliveryView)
    setReceivedHashes((raw.data as DeliveryView).items.map((it) => ({ name: it.name, hash: it.hash })))
  }

  const onAddItems = async () => {
    if (busy) return
    setBusy(true); setErr('')
    try {
      const clean = addItems.filter((it) => it.name.trim() || it.hash.trim())
      await post('/api/v1/delivery/items', {
        delivery_id: opId,
        items: clean.map((it) => ({ name: it.name, version: it.version, hash: it.hash,
          size_bytes: it.size_bytes ? Number(it.size_bytes) : undefined, volume_note: it.volume_note })),
      })
      setAddItems([{ ...EMPTY_ITEM }])
      setErr(''); setQueryId(opId); await onQuery()
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const onConfirm = async () => {
    if (busy) return
    setBusy(true); setErr(''); setConfirmResult(null)
    try {
      const data = await post('/api/v1/delivery/confirm', {
        delivery_id: opId, received: receivedHashes })
      setConfirmResult(data)
      setQueryId(opId); await onQuery()
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const itemRow = (it: Item, set: (v: Item) => void) => (
    <div className="grid grid-cols-5 gap-2">
      <input className="rounded border px-2 py-1 text-sm" placeholder="名称（必填）" value={it.name}
        onChange={(e) => set({ ...it, name: e.target.value })} />
      <input className="rounded border px-2 py-1 text-sm" placeholder="版本" value={it.version}
        onChange={(e) => set({ ...it, version: e.target.value })} />
      <input className="rounded border px-2 py-1 text-sm" placeholder="哈希（必填，⛔稍后补）" value={it.hash}
        onChange={(e) => set({ ...it, hash: e.target.value })} />
      <input className="rounded border px-2 py-1 text-sm" placeholder="大小（字节）" value={it.size_bytes}
        onChange={(e) => set({ ...it, size_bytes: e.target.value })} />
      <input className="rounded border px-2 py-1 text-sm" placeholder="分卷注明" value={it.volume_note}
        onChange={(e) => set({ ...it, volume_note: e.target.value })} />
    </div>
  )

  return (
    <PageShell dataNature="simulated"
      title="交付清单（C-2）"
      dataSource="POST /api/v1/delivery/manifest|items|confirm ＋ GET /api/v1/delivery/{id}（公开读）"
      permission="开单/补件/确认须登录 DID；查询公开"
      description="按清单逐件交付：每件填名称与哈希（缺哈希提交不了），拿到 delivery_id；接收确认须报齐哈希，无哈希视同未收。">
      <div data-testid="delivery" className="max-w-3xl space-y-6">

        {/* ── 开清单 ── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">① 开清单（auth_id 必填）</h2>
          <p className="text-sm text-gray-500">上一步未完成（无 auth_id）不许开清单——请先在授权配置面板拿到编号。</p>
          <div className="grid grid-cols-2 gap-2">
            <input data-testid="delivery-auth-id" className="rounded border px-2 py-1 text-sm"
              placeholder="auth_id（AP- 开头，必填）" value={authId} onChange={(e) => setAuthId(e.target.value)} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="接收方主体（必填）"
              value={receiver} onChange={(e) => setReceiver(e.target.value)} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="分批与分卷关系"
              value={batches} onChange={(e) => setBatches(e.target.value)} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="交付时点"
              value={deliverAt} onChange={(e) => setDeliverAt(e.target.value)} />
          </div>
          <div className="space-y-2">
            {items.map((it, i) => (
              <div key={i}>{itemRow(it, (v) => setItems(items.map((x, j) => (j === i ? v : x))))}</div>
            ))}
            <button type="button" className="text-sm text-blue-700 hover:underline"
              onClick={() => setItems([...items, { ...EMPTY_ITEM }])}>＋加一件</button>
          </div>
          <p className="text-xs text-amber-700">单件大小阈值：待运维核定（在册未定，本站未设数字）；超限请拆件并在此注明分卷。</p>
          <button type="button" data-testid="delivery-manifest-submit" disabled={busy}
            className="rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:bg-gray-300"
            onClick={() => void onManifest()}>{busy ? '提交中…' : '开清单'}</button>
          {created && (
            <p data-testid="delivery-created" className="rounded bg-green-50 p-3 text-sm text-green-800">
              清单已立（{created.status}）：delivery_id=<b>{created.delivery_id}</b> ｜ 存证 nca_seq={created.nca_seq}
            </p>
          )}
        </section>

        {/* ── 查清单（公开读）── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">② 查清单（公开，免登录）</h2>
          <div className="flex gap-2">
            <input data-testid="delivery-query-id" className="flex-1 rounded border px-2 py-1 text-sm"
              placeholder="输入 delivery_id（DLV- 开头）" value={queryId} onChange={(e) => setQueryId(e.target.value)} />
            <button type="button" data-testid="delivery-query-submit"
              className="rounded-md border border-blue-600 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50"
              onClick={() => void onQuery()}>查询</button>
          </div>
          {view && (
            <div data-testid="delivery-view" className="rounded bg-gray-50 p-3 text-sm">
              <p>状态：<b>{view.status}</b> ｜ 共 {view.total_items} 件 ｜ nca_seq={view.nca_seq}</p>
              <ul className="mt-1 space-y-0.5">
                {view.items.map((it) => (
                  <li key={it.name}>· {it.name}（{it.version || '无版本'}）哈希 <code className="break-all">{it.hash}</code>
                    {it.volume_note ? ` ｜ 分卷：${it.volume_note}` : ''}</li>
                ))}
              </ul>
              <p className="mt-1 text-xs text-gray-500">接收确认须报齐以上各件哈希——无哈希视同未收。</p>
            </div>
          )}
        </section>

        {/* ── 补件／确认 ── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">③ 补件与交付确认（须登录）</h2>
          <input data-testid="delivery-op-id" className="w-full rounded border px-2 py-1 text-sm"
            placeholder="delivery_id" value={opId} onChange={(e) => setOpId(e.target.value)} />
          <div className="space-y-2">
            {addItems.map((it, i) => (
              <div key={i}>{itemRow(it, (v) => setAddItems(addItems.map((x, j) => (j === i ? v : x))))}</div>
            ))}
            <button type="button" className="text-sm text-blue-700 hover:underline"
              onClick={() => setAddItems([...addItems, { ...EMPTY_ITEM }])}>＋加一件</button>
          </div>
          <button type="button" disabled={busy}
            className="rounded-md border px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50 disabled:text-gray-400"
            onClick={() => void onAddItems()}>补件（→ uploading）</button>
          <div className="space-y-1">
            <p className="text-sm text-gray-600">接收回执哈希（确认签收须逐件报哈希；可直接改）：</p>
            {receivedHashes.map((r, i) => (
              <div key={r.name} className="grid grid-cols-2 gap-2">
                <span className="py-1 text-sm">{r.name}</span>
                <input className="rounded border px-2 py-1 text-sm" value={r.hash}
                  onChange={(e) => setReceivedHashes(receivedHashes.map((x, j) => (j === i ? { ...x, hash: e.target.value } : x)))} />
              </div>
            ))}
          </div>
          <button type="button" data-testid="delivery-confirm-submit" disabled={busy}
            className="rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:bg-gray-300"
            onClick={() => void onConfirm()}>{busy ? '确认中…' : '交付确认'}</button>
          {confirmResult && (
            <div data-testid="delivery-confirm-result" className="rounded bg-green-50 p-3 text-sm">
              <p>状态：<b>{confirmResult.status}</b>——{confirmResult.note}</p>
              <ul className="mt-1 space-y-0.5">
                {confirmResult.checks.map((c) => (
                  <li key={c.name}>· {c.name}：<b className={c.match ? 'text-green-700' : 'text-red-700'}>{c.match ? '符' : '不符'}</b></li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {err && (
          <p data-testid="delivery-error" className="rounded bg-amber-50 p-3 text-sm text-amber-800" role="alert">
            {err.includes('未登录') || err.includes('会话')
              ? <>请先<a className="underline" href="/auth">登录</a>再操作。</>
              : err}
          </p>
        )}
      </div>
    </PageShell>
  )
}
