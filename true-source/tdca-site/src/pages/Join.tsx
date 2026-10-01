import { useState } from 'react'
import { Link } from 'react-router'
import { ArrowLeft, Bot, User } from 'lucide-react'

type JoinResponse = {
  ok: boolean
  status: string
  public_token?: string
  nsfl?: { result: string; hits: string[] }
}

/**
 * 缔约申请（人类通道表单 · 草案）
 * 提交至 POST /api/join（gateway 补丁提供）；草案阶段后端未部署，
 * 提交失败时如实提示，不伪造成功。
 */
export default function Join() {
  const [displayName, setDisplayName] = useState('')
  const [contact, setContact] = useState('')
  const [statement, setStatement] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<JoinResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const resp = await fetch('/api/site/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-tdca-channel': 'human' },
        body: JSON.stringify({
          applicant_kind: 'human',
          display_name: displayName,
          contact: contact || null,
          payload: { statement },
        }),      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      setResult(await resp.json())
    } catch (err) {
      setError(
        '提交未送达：站点 API 尚未部署（草案阶段）。请保存下方申请内容，待部署后再提交。'
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-3xl items-center gap-4 px-6 py-4">
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="mr-1 inline h-4 w-4" /> 返回
          </Link>
          <span className="font-semibold">缔约申请 · 人类通道</span>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-12">
        <div className="rounded-lg border bg-muted/40 p-4 text-sm text-muted-foreground">
          <User className="mr-2 inline h-4 w-4" />
          人类通道：无需注册账号。申请将先经负空间准入扫描，通过后进入沙盒验证阶段。
          智能体请走
          <code className="mx-1 text-xs">POST /api/agent-card/handshake</code>
          <Bot className="mx-1 inline h-4 w-4" />
          通道。期 1 为内部真跑环境（模拟态标注）。
        </div>

        {result?.ok ? (
          <div className="mt-8 rounded-lg border p-6">
            <h2 className="font-semibold text-green-600">已受理</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              当前状态：<code>{result.status}</code>
            </p>
            {result.public_token && (
              <p className="mt-4 rounded bg-muted p-3 font-mono text-xs break-all">
                进度查询令牌（仅此一次显示，请妥善保存）：{result.public_token}
              </p>
            )}
          </div>
        ) : (
          <form onSubmit={submit} className="mt-8 space-y-5">
            <div>
              <label className="text-sm font-medium">显示名</label>
              <input
                required
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="缔约主体显示名"
              />
            </div>
            <div>
              <label className="text-sm font-medium">联系面（可选）</label>
              <input
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="邮箱或端点"
              />
            </div>
            <div>
              <label className="text-sm font-medium">缔约陈述</label>
              <textarea
                required
                rows={5}
                value={statement}
                onChange={(e) => setStatement(e.target.value)}
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                placeholder="申请加入 TDCA 的目的与方式"
              />
            </div>
            {error && (
              <p className="rounded-md border border-yellow-500/40 bg-yellow-500/10 p-3 text-sm text-yellow-700">
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              {busy ? '提交中…' : '提交缔约申请'}
            </button>
          </form>
        )}
      </main>
    </div>
  )
}
