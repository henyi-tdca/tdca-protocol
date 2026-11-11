// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期 C-3 验收记录页（L1SI195-B1-001）
// 约束矩阵: 施工令 §四——标准须事前登记（验收时临时加 → 页内拒绝并提示）；
//   逐条结论须对应事前标准＋依据＋差距（不通过必填差距）；无 delivery_id 不许开验；
//   结算衔接：passed 只显示「可结算」，⛔ 触发结算（S-4）
// 复用: PageShell / 会话令牌直注；后端 POST /api/v1/acceptance/standard|verdict|rectify
//   ＋ GET /api/v1/acceptance/{acceptance_id}（公开读免会话）
// =============================================================================
import { useState } from 'react'
import { sessionToken } from '@/api/client'
import { PageShell } from './PageShell'

interface Std { item: string; criterion: string }
interface Verdict { item: string; pass: boolean; basis: string; gap: string }
interface Rectify { item: string; deadline: string }

interface AcceptanceView {
  acceptance_id: string
  delivery_id: string
  auth_id: string
  status: string
  standards: Std[]
  verdicts: Array<Verdict & { pass: boolean }>
  rectifications: Rectify[]
  nca_seq: string
  settlement?: string
}

export function AcceptancePage() {
  // ── 登记标准 ──
  const [dlvId, setDlvId] = useState('')
  const [stds, setStds] = useState<Std[]>([{ item: '', criterion: '' }])
  const [created, setCreated] = useState<{ acceptance_id: string; nca_seq: string } | null>(null)
  // ── 判定 ──
  const [accId, setAccId] = useState('')
  const [verdicts, setVerdicts] = useState<Verdict[]>([{ item: '', pass: true, basis: '', gap: '' }])
  const [verdictResult, setVerdictResult] = useState<{ status: string; note: string } | null>(null)
  // ── 整改 ──
  const [rectifies, setRectifies] = useState<Rectify[]>([{ item: '', deadline: '' }])
  // ── 查询 ──
  const [queryId, setQueryId] = useState('')
  const [view, setView] = useState<AcceptanceView | null>(null)
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

  const onStandard = async () => {
    if (busy) return
    setBusy(true); setErr(''); setCreated(null)
    try {
      const clean = stds.filter((s) => s.item.trim() || s.criterion.trim())
      const data = await post('/api/v1/acceptance/standard', {
        delivery_id: dlvId, standards: clean })
      setCreated(data)
      setAccId((data as { acceptance_id: string }).acceptance_id)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const onVerdict = async () => {
    if (busy) return
    setBusy(true); setErr(''); setVerdictResult(null)
    try {
      const clean = verdicts.filter((v) => v.item.trim())
      const data = await post('/api/v1/acceptance/verdict', {
        acceptance_id: accId,
        verdicts: clean.map((v) => ({ item: v.item, pass: v.pass,
          basis: v.basis, gap: v.pass ? undefined : v.gap })),
      })
      setVerdictResult(data)
      setQueryId(accId); await onQuery(accId)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const onRectify = async () => {
    if (busy) return
    setBusy(true); setErr('')
    try {
      const clean = rectifies.filter((r) => r.item.trim())
      await post('/api/v1/acceptance/rectify', { acceptance_id: accId, items: clean })
      setQueryId(accId); await onQuery(accId)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const onQuery = async (id?: string) => {
    setErr('')
    const q = (id ?? queryId).trim()
    const res = await fetch(`/api/v1/acceptance/${encodeURIComponent(q)}`)
    const raw = await res.json().catch(() => ({}))
    if (!res.ok) { setView(null); setErr(raw.detail ?? '没查到——请核对编号。'); return }
    setView(raw.data as AcceptanceView)
  }

  return (
    <PageShell dataNature="simulated"
      title="验收记录（C-3）"
      dataSource="POST /api/v1/acceptance/standard|verdict|rectify ＋ GET /api/v1/acceptance/{id}（公开读）"
      permission="登记/判定/整改须登录 DID；查询公开"
      description="先登记验收标准（事前），再逐条判定：通过/不通过＋依据＋差距；不通过须登记整改（条目／期限）后复判；通过只显示「可结算」。">
      <div data-testid="acceptance" className="max-w-3xl space-y-6">

        {/* ── 登记标准 ── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">① 登记验收标准（须事前；无 delivery_id 不许开验）</h2>
          <input data-testid="acceptance-dlv-id" className="w-full rounded border px-2 py-1 text-sm"
            placeholder="delivery_id（DLV- 开头，必填）" value={dlvId} onChange={(e) => setDlvId(e.target.value)} />
          {stds.map((s, i) => (
            <div key={i} className="grid grid-cols-2 gap-2">
              <input className="rounded border px-2 py-1 text-sm" placeholder="验收条目（必填）" value={s.item}
                onChange={(e) => setStds(stds.map((x, j) => (j === i ? { ...x, item: e.target.value } : x)))} />
              <input className="rounded border px-2 py-1 text-sm" placeholder="判据（可量化优先）" value={s.criterion}
                onChange={(e) => setStds(stds.map((x, j) => (j === i ? { ...x, criterion: e.target.value } : x)))} />
            </div>
          ))}
          <button type="button" className="text-sm text-blue-700 hover:underline"
            onClick={() => setStds([...stds, { item: '', criterion: '' }])}>＋加一条标准</button>
          <p className="text-xs text-amber-700">标准一经登记即在验——验收时临时加标准一律拒绝（页内提示并停链复核）。</p>
          <button type="button" data-testid="acceptance-standard-submit" disabled={busy}
            className="rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:bg-gray-300"
            onClick={() => void onStandard()}>{busy ? '登记中…' : '登记标准'}</button>
          {created && (
            <p data-testid="acceptance-created" className="rounded bg-green-50 p-3 text-sm text-green-800">
              验收单已立：acceptance_id=<b>{created.acceptance_id}</b> ｜ 存证 nca_seq={created.nca_seq}
            </p>
          )}
        </section>

        {/* ── 判定 ── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">② 逐条判定（结论须对应事前标准）</h2>
          <input data-testid="acceptance-id" className="w-full rounded border px-2 py-1 text-sm"
            placeholder="acceptance_id（ACC- 开头）" value={accId} onChange={(e) => setAccId(e.target.value)} />
          {verdicts.map((v, i) => (
            <div key={i} className="space-y-1 rounded border p-2">
              <div className="grid grid-cols-2 gap-2">
                <input className="rounded border px-2 py-1 text-sm" placeholder="条目（须与事前标准一致）" value={v.item}
                  onChange={(e) => setVerdicts(verdicts.map((x, j) => (j === i ? { ...x, item: e.target.value } : x)))} />
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={v.pass}
                    onChange={(e) => setVerdicts(verdicts.map((x, j) => (j === i ? { ...x, pass: e.target.checked } : x)))} />
                  通过
                </label>
              </div>
              <input className="w-full rounded border px-2 py-1 text-sm" placeholder="依据哪一条标准（必填）" value={v.basis}
                onChange={(e) => setVerdicts(verdicts.map((x, j) => (j === i ? { ...x, basis: e.target.value } : x)))} />
              {!v.pass && (
                <input data-testid="acceptance-gap" className="w-full rounded border px-2 py-1 text-sm"
                  placeholder="差距（不通过必填）" value={v.gap}
                  onChange={(e) => setVerdicts(verdicts.map((x, j) => (j === i ? { ...x, gap: e.target.value } : x)))} />
              )}
            </div>
          ))}
          <button type="button" className="text-sm text-blue-700 hover:underline"
            onClick={() => setVerdicts([...verdicts, { item: '', pass: true, basis: '', gap: '' }])}>＋加一条结论</button>
          <button type="button" data-testid="acceptance-verdict-submit" disabled={busy}
            className="block rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:bg-gray-300"
            onClick={() => void onVerdict()}>{busy ? '判定中…' : '提交判定'}</button>
          {verdictResult && (
            <p data-testid="acceptance-verdict-result" className="rounded bg-green-50 p-3 text-sm text-green-800">
              结论：<b>{verdictResult.status}</b>——{verdictResult.note}
            </p>
          )}
        </section>

        {/* ── 整改 ── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">③ 整改登记（rejected 后；→ re_judging 复判）</h2>
          {rectifies.map((r, i) => (
            <div key={i} className="grid grid-cols-2 gap-2">
              <input className="rounded border px-2 py-1 text-sm" placeholder="整改条目" value={r.item}
                onChange={(e) => setRectifies(rectifies.map((x, j) => (j === i ? { ...x, item: e.target.value } : x)))} />
              <input className="rounded border px-2 py-1 text-sm" placeholder="整改期限" value={r.deadline}
                onChange={(e) => setRectifies(rectifies.map((x, j) => (j === i ? { ...x, deadline: e.target.value } : x)))} />
            </div>
          ))}
          <button type="button" className="text-sm text-blue-700 hover:underline"
            onClick={() => setRectifies([...rectifies, { item: '', deadline: '' }])}>＋加一条整改</button>
          <button type="button" disabled={busy}
            className="block rounded-md border px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50 disabled:text-gray-400"
            onClick={() => void onRectify()}>登记整改</button>
        </section>

        {/* ── 查询（公开读）── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">④ 查验收单（公开，免登录）</h2>
          <div className="flex gap-2">
            <input data-testid="acceptance-query-id" className="flex-1 rounded border px-2 py-1 text-sm"
              placeholder="acceptance_id（ACC- 开头）" value={queryId} onChange={(e) => setQueryId(e.target.value)} />
            <button type="button" data-testid="acceptance-query-submit"
              className="rounded-md border border-blue-600 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50"
              onClick={() => void onQuery()}>查询</button>
          </div>
          {view && (
            <div data-testid="acceptance-view" className="rounded bg-gray-50 p-3 text-sm">
              <p>状态：<b>{view.status}</b> ｜ delivery_id={view.delivery_id} ｜ nca_seq={view.nca_seq}</p>
              <p className="mt-1 font-semibold">事前标准：</p>
              <ul className="space-y-0.5">
                {view.standards.map((s) => <li key={s.item}>· {s.item}：{s.criterion}</li>)}
              </ul>
              {view.verdicts.length > 0 && (
                <>
                  <p className="mt-1 font-semibold">逐条结论：</p>
                  <ul className="space-y-0.5">
                    {view.verdicts.map((v) => (
                      <li key={v.item}>· {v.item}：<b>{v.pass ? '通过' : '不通过'}</b>（依据：{v.basis}）
                        {v.gap ? <span className="text-red-700">——差距：{v.gap}</span> : null}</li>
                    ))}
                  </ul>
                </>
              )}
              {view.rectifications.length > 0 && (
                <>
                  <p className="mt-1 font-semibold">整改单：</p>
                  <ul className="space-y-0.5">
                    {view.rectifications.map((r) => <li key={r.item}>· {r.item}：限 {r.deadline} 前</li>)}
                  </ul>
                </>
              )}
              {/* S-4：结算衔接只显示「可结算」，⛔ 触发结算 */}
              {view.settlement === '可结算' && (
                <p data-testid="acceptance-settlement" className="mt-2 rounded bg-blue-50 p-2 text-blue-800">
                  验收通过——可结算（结算触发不在本页，另行办理）。
                </p>
              )}
            </div>
          )}
        </section>

        {err && (
          <p data-testid="acceptance-error" className="rounded bg-amber-50 p-3 text-sm text-amber-800" role="alert">
            {err.includes('未登录') || err.includes('会话')
              ? <>请先<a className="underline" href="/auth">登录</a>再操作。</>
              : err}
          </p>
        )}
      </div>
    </PageShell>
  )
}
