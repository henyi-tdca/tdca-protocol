import { useState } from 'react'
import { Link } from 'react-router'
import { sitePost, siteGet, GateRequired, getWriteToken, setWriteToken } from '../lib/siteApi'
import GatePrompt from '../components/GatePrompt'

type JoinResponse = {
  ok: boolean
  status: string
  public_token?: string
  nsfl?: { result: string; hits: string[] }
}

type StatusResponse = { status: string; history: { at: string; to: string; by: string; note?: string }[] }

const inputCls = 'w-full rounded border px-3 py-2 text-sm'
const labelCls = 'block text-sm font-medium mb-1'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border p-5">
      <h2 className="font-bold mb-3">{title}</h2>
      {children}
    </section>
  )
}

export default function Join() {
  // ── 申请表单 ────────────────────────────────────────────────
  const [kind, setKind] = useState<'human' | 'agent' | 'org'>('human')
  const [name, setName] = useState('')
  const [contact, setContact] = useState('')
  const [intent, setIntent] = useState('')
  const [declared, setDeclared] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<JoinResponse | null>(null)
  const [error, setError] = useState('')
  const [needGate, setNeedGate] = useState(false)
  const [needWrite, setNeedWrite] = useState(false)
  const [writeToken, setWriteTokenInput] = useState(getWriteToken())

  const submit = async () => {
    if (!declared) { setError('请先勾选声明'); return }
    setSubmitting(true); setError(''); setResult(null); setNeedWrite(false)
    try {
      const r = await sitePost<JoinResponse>('/join', {
        applicant_kind: kind,
        display_name: name,
        contact: contact || null,
        payload: { intent, declaration: '本人声明：不发币、不承诺分红、不代币化，自愿接受负空间协作约束。' },
      }, { 'x-tdca-channel': 'human' })
      setResult(r)
    } catch (e) {
      if (e instanceof GateRequired) setNeedGate(true)
      else {
        const err = e as Error & { status?: number }
        if (err.status === 401 || err.status === 403) setNeedWrite(true)
        setError(err.status === 403 ? '写令牌校验未过（口令门已过，还缺写令牌）' : `提交失败：HTTP ${err.status ?? ''}`)
      }
    } finally {
      setSubmitting(false)
    }
  }

  // ── 进度查询 ────────────────────────────────────────────────
  const [queryToken, setQueryToken] = useState('')
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [queryErr, setQueryErr] = useState('')
  const query = async () => {
    setQueryErr(''); setStatus(null)
    try {
      setStatus(await siteGet<StatusResponse>(`/join/status?token=${encodeURIComponent(queryToken.trim())}`))
    } catch (e) {
      if (e instanceof GateRequired) setNeedGate(true)
      else setQueryErr('未查到：请检查令牌是否抄全（令牌只在提交成功时显示一次）')
    }
  }

  if (needGate) return <GatePrompt onOk={() => setNeedGate(false)} />

  const statusLabel: Record<string, string> = {
    pending: '待审核', sandbox: '沙盒验证中', active: '已转正',
    rejected: '已谢绝', nsfl_rejected: '触负待人工复核',
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Link to="/" className="text-sm text-muted-foreground">← 返回首页</Link>
      <h1 className="mt-2 text-2xl font-bold">缔约申请</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        两步：① 下面填表提交；② 拿到一次性令牌，随时回来查进度。站点口令向管理员索取，只在本次浏览器会话内使用。
      </p>

      <div className="mt-8 space-y-6">
        <Section title="第一步 · 填表提交">
          <div className="space-y-4">
            <div>
              <label className={labelCls}>申请身份</label>
              <div className="flex gap-2">
                {([['human', '个人'], ['org', '组织'], ['agent', '智能体']] as const).map(([v, l]) => (
                  <button key={v} type="button" onClick={() => setKind(v)}
                    className={`rounded border px-4 py-2 text-sm ${kind === v ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className={labelCls}>名称（{kind === 'human' ? '怎么称呼你' : kind === 'org' ? '组织名' : '智能体名'}）</label>
              <input className={inputCls} maxLength={120} value={name} onChange={(e) => setName(e.target.value)} placeholder="必填" />
            </div>
            <div>
              <label className={labelCls}>联系方式（选填）</label>
              <input className={inputCls} maxLength={200} value={contact} onChange={(e) => setContact(e.target.value)} placeholder="邮箱或其他可达方式" />
            </div>
            <div>
              <label className={labelCls}>意向说明（选填）</label>
              <textarea className={inputCls} rows={3} value={intent} onChange={(e) => setIntent(e.target.value)} placeholder="想用什么场景、想接入什么能力" />
            </div>
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" checked={declared} onChange={(e) => setDeclared(e.target.checked)} />
              <span>我声明：不发币、不承诺分红、不代币化，自愿接受负空间协作约束。</span>
            </label>
            <button disabled={submitting || !name.trim() || !declared}
              onClick={submit}
              className="rounded bg-primary px-5 py-2 text-sm text-primary-foreground disabled:opacity-50">
              {submitting ? '提交中…' : '提交申请'}
            </button>
            {error && <p className="text-sm text-destructive">{error}</p>}
            {needWrite && (
              <div className="flex items-center gap-2 text-sm">
                <span className="shrink-0 text-muted-foreground">写令牌（向管理员索取，仅本次会话有效）：</span>
                <input type="password" className="flex-1 rounded border px-3 py-1.5" value={writeToken}
                  onChange={(e) => setWriteTokenInput(e.target.value)} placeholder="粘贴后点「提交申请」重试" />
                <button onClick={() => { setWriteToken(writeToken); submit() }}
                  className="shrink-0 rounded border px-3 py-1.5 hover:bg-muted">存并重试</button>
              </div>
            )}

            {result && (
              <div className="rounded-md border p-4 text-sm">
                {result.status === 'pending' ? (
                  <>
                    <p className="font-medium text-green-700">✅ 已受理，进入人工审核。</p>
                    <p className="mt-2">你的一次性令牌（只显示这一次，请当场抄存）：</p>
                    <code className="mt-1 block break-all rounded bg-muted p-2 text-xs">{result.public_token}</code>
                  </>
                ) : (
                  <>
                    <p className="font-medium text-amber-700">⏸ 已登记，状态：{statusLabel[result.status] ?? result.status}。</p>
                    <p className="mt-1 text-muted-foreground">你的申请触发了敏感词复核，将由管理员人工处理，请留下联系方式等候通知。</p>
                  </>
                )}
              </div>
            )}
          </div>
        </Section>

        <Section title="第二步 · 凭令牌查进度">
          <div className="flex gap-2">
            <input className={inputCls} type="password" value={queryToken} onChange={(e) => setQueryToken(e.target.value)} placeholder="粘贴你的一次性令牌" />
            <button onClick={query} disabled={!queryToken.trim()} className="shrink-0 rounded border px-4 py-2 text-sm hover:bg-muted disabled:opacity-50">查询</button>
          </div>
          {queryErr && <p className="mt-2 text-sm text-destructive">{queryErr}</p>}
          {status && (
            <div className="mt-3 text-sm">
              <p>当前状态：<strong>{statusLabel[status.status] ?? status.status}</strong></p>
              <ul className="mt-2 space-y-1 text-muted-foreground">
                {status.history.map((h, i) => (
                  <li key={i}>{h.at} · {statusLabel[h.to] ?? h.to}{h.note ? `（${h.note}）` : ''}</li>
                ))}
              </ul>
            </div>
          )}
        </Section>

        <p className="text-xs text-muted-foreground">
          内部审核入口：<Link to="/review" className="underline">/review</Link>（仅管理员）
        </p>
      </div>
    </div>
  )
}
