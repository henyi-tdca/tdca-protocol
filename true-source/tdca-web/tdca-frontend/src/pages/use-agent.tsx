// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 「用」组 U-2 代办机器人（L1SI182-USE-U2-001）
// 约束矩阵: 施工令 §二——五步（收件→只问缺项→出草稿→人在场签→出号），⛔ 增步减步；
//   机器人只跑腿不做主：⛔ 代签／⛔ 代判／⛔ 对外承诺；⛔ 预填登记号；草稿不落库不出号；
//   限缩照令：草稿→签署全在前端层（本地态）；签署＝本人登录态＋显式点击＋时间留痕，
//   ⛔ 实装签名值／授权码（不入件不入库），页面⛔ 声称「已完成法律签署要件」，只写「已由本人确认」
// 复用: POST/GET /api/v1/use/upload（U-1 已交）＋ POST /api/v1/ownership/register（OR- 号沿用）；
//   ⛔ 不另建端点／⛔ 不改后端状态机（S-1）；⛔ 不触碰 authorization 面（8b 一期不做）
// 拒收第 4 类（外链下载式）语义层落点：只给链接不给件 → 人话退回（收件步拦）
// SIMULATED: 版权链维持模拟态——出号面必标 SIMULATED（ID92）
// =============================================================================
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

interface UploadRecord {
  upload_id: string
  sha256_16: string
  size_bytes: number
  original_filename: string
  accept_category: string
  uploaded_at: string
}

interface RegisterResult {
  record_id: string
  status: string
  nca_ref: string
  simulated: boolean
}

const SOURCE_OPTIONS = [
  { key: 'human/original', label: '本人独立创作（未使用生成工具）' },
  { key: 'human/collaborative', label: '与他人合作创作' },
  { key: 'commissioned', label: '受他人委托创作' },
  { key: 'derived', label: '在既有素材基础上改编（原权属仍归原权利人）' },
  { key: 'ai-assisted/human-led', label: '使用生成工具辅助、人主导完成' },
] as const

const FORM_OPTIONS = ['文字', '图像', '音频', '视频', '数据', '代码', '设计稿', '混合', '其他']
const JUR_OPTIONS = [
  { key: 'unspecified', label: '暂不定（unspecified）' },
  { key: 'copyright', label: '著作权（copyright）' },
  { key: 'patent', label: '专利（patent）' },
  { key: 'data', label: '数据（data）' },
  { key: 'trademark', label: '商标（trademark）' },
]

const URL_LIKE = /^https?:\/\//i

export function UseAgentPage() {
  const [params] = useSearchParams()
  const uploadId = params.get('u') ?? ''

  const [me, setMe] = useState('')
  const [rec, setRec] = useState<UploadRecord | null>(null)
  const [loadErr, setLoadErr] = useState('')
  const [fields, setFields] = useState({
    workTitle: '', authorName: '', createdAt: '',
    sourceKey: '', expressionForm: '', jurisdiction: 'unspecified', note: '',
  })
  const [draft, setDraft] = useState<Record<string, unknown> | null>(null)
  const [ack, setAck] = useState(false)            // ⛔ 默认勾选——须显式点击
  const [confirmed, setConfirmed] = useState<{ by: string; at: string } | null>(null)
  const [regResult, setRegResult] = useState<RegisterResult | null>(null)
  const [regErr, setRegErr] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    void api.get<{ username?: string }>('/api/v1/auth/me').then((r) => {
      if (r.ok && r.data.username) {
        setMe(r.data.username)
        setFields((f) => (f.authorName ? f : { ...f, authorName: r.data.username ?? '' }))
      }
    })
  }, [])

  useEffect(() => {
    if (!uploadId) return
    void api.get<UploadRecord>(`/api/v1/use/upload/${encodeURIComponent(uploadId)}`).then((r) => {
      if (r.ok) { setRec(r.data); return }
      setLoadErr(r.detail ?? '没查到这件——请先从「交素材」页上传。')
    })
  }, [uploadId])

  const missing = useMemo(() => {
    const m: string[] = []
    if (!fields.workTitle.trim()) m.push('作品名称（物之名）')
    if (!fields.authorName.trim()) m.push('权利人（人）')
    if (!fields.createdAt) m.push('完成时间（时）')
    if (!fields.sourceKey) m.push('来源谱系（意）')
    return m
  }, [fields])

  const draftSource = rec
    ? (key: string) => SOURCE_OPTIONS.find((o) => o.key === key)
    : null

  const makeDraft = (): Record<string, unknown> | null => {
    if (!rec || missing.length > 0) return null
    const src = SOURCE_OPTIONS.find((o) => o.key === fields.sourceKey)
    const lineage = `来源谱系：${src?.label ?? ''}（${fields.sourceKey}）`
    return {
      draft_version: 'U2-V1.0',
      mark: '草稿 · 未经签署 ⛔ 生效',
      work: {
        upload_id: rec.upload_id, sha256_16: rec.sha256_16,
        size_bytes: rec.size_bytes, original_filename: rec.original_filename,
        accept_category: rec.accept_category, uploaded_at: rec.uploaded_at,
      },
      four_elements: {
        人: fields.authorName.trim(), 时: fields.createdAt,
        物: `${rec.original_filename}（${rec.upload_id}）`, 意: lineage,
      },
      register_payload: {
        work_title: fields.workTitle.trim(),
        owner_ref: fields.authorName.trim(),
        source_lineage: lineage,
        expression_form: fields.expressionForm,
        jurisdiction_branch: fields.jurisdiction,
        note: fields.note.trim(),
      },
    }
  }

  const onMakeDraft = () => {
    // 拒收第 4 类（外链下载式）语义层：只给链接不给件 → 人话退回
    if (URL_LIKE.test(fields.workTitle.trim()) || URL_LIKE.test(fields.note.trim())) {
      setRegErr('只给链接不收——请把文件本身传上来，再填登记信息。')
      return
    }
    setRegErr('')
    setDraft(makeDraft())
  }

  const onConfirm = () => {
    if (!ack || !me) return
    setConfirmed({ by: me, at: new Date().toISOString() })  // 只记「已确认」与时间（⛔ 签名值入库）
  }

  const onRegister = async () => {
    if (!confirmed || !draft || busy) return
    const payload = (draft as { register_payload: Record<string, unknown> }).register_payload
    setBusy(true); setRegErr('')
    const r = await api.post<RegisterResult>('/api/v1/ownership/register', payload)
    setBusy(false)
    if (r.ok) { setRegResult(r.data); return }
    setRegErr(r.detail ?? '没登记成——请稍后重试，或联系站方。')
  }

  const set = (k: keyof typeof fields) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setFields((f) => ({ ...f, [k]: e.target.value }))

  return (
    <PageShell dataNature="real"
      title="代办登记（机器人只跑腿）"
      dataSource="复用 POST /api/v1/ownership/register（OR- 号沿用既有）＋ GET /api/v1/use/upload/{id}；草稿仅本地态，不落库不出号"
      permission="登录 DID（须本人登录态；未确认 ⛔ 出号）"
      description="上传成功后接着办登记：机器人只问缺项、出草稿；你本人看过草稿、显式点确认，才出登记号。机器人不代签、不代判、不对外承诺。">
      <div data-testid="use-agent" className="max-w-2xl space-y-4">

        {!uploadId && !rec && (
          <p className="rounded bg-amber-50 p-3 text-sm text-amber-800" role="alert">
            还没有收件——请先到 <Link className="underline" to="/use/upload">交素材（上传一件）</Link> 把文件传上来，成功后再回这里继续登记。
          </p>
        )}
        {uploadId && loadErr && (
          <p className="rounded bg-amber-50 p-3 text-sm text-amber-800" role="alert">{loadErr}</p>
        )}

        {rec && !regResult && (
          <>
            {/* 步 1 收件：四要件核对（物已齐；人／时／意待填） */}
            <section className="rounded-lg border border-gray-200 p-4 text-sm">
              <h2 className="font-semibold text-gray-800">第 1 步 · 收件（已收到你的文件）</h2>
              <dl className="mt-2 space-y-1 text-gray-700">
                <div><dt className="inline font-semibold">收件编号：</dt><dd className="inline">{rec.upload_id}</dd></div>
                <div><dt className="inline font-semibold">文件：</dt><dd className="inline">{rec.original_filename}（{rec.accept_category}，{rec.size_bytes} 字节）</dd></div>
                <div><dt className="inline font-semibold">哈希：</dt><dd className="inline break-all">{rec.sha256_16}</dd></div>
                <div><dt className="inline font-semibold">时间：</dt><dd className="inline">{rec.uploaded_at}</dd></div>
              </dl>
              <p className="mt-2 text-gray-600">四要件：物 ✓（文件已收）；人／时／意见下——<strong>缺哪项填哪项</strong>，别的不用管。</p>
            </section>

            {!draft && !confirmed && (
              <section className="space-y-3 rounded-lg border border-gray-200 p-4 text-sm">
                <h2 className="font-semibold text-gray-800">第 2 步 · 只问缺项</h2>
                {missing.length > 0 && (
                  <p data-testid="use-agent-missing" className="rounded bg-amber-50 p-3 text-amber-800" role="alert">
                    还差：{missing.join('、')}。
                  </p>
                )}
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="block">
                    <span className="font-semibold text-gray-700">作品名称（物之名）*</span>
                    <input data-testid="use-agent-title" value={fields.workTitle} onChange={set('workTitle')}
                      className="mt-1 w-full rounded border border-gray-300 px-2 py-1" placeholder="给这件作品起个名" />
                  </label>
                  <label className="block">
                    <span className="font-semibold text-gray-700">权利人（人）*</span>
                    <input data-testid="use-agent-author" value={fields.authorName} onChange={set('authorName')}
                      className="mt-1 w-full rounded border border-gray-300 px-2 py-1" placeholder="默认你的登录名，可改" />
                  </label>
                  <label className="block">
                    <span className="font-semibold text-gray-700">完成时间（时）*</span>
                    <input data-testid="use-agent-date" type="date" value={fields.createdAt} onChange={set('createdAt')}
                      className="mt-1 w-full rounded border border-gray-300 px-2 py-1" />
                  </label>
                  <label className="block">
                    <span className="font-semibold text-gray-700">来源谱系（意）*</span>
                    <select data-testid="use-agent-source" value={fields.sourceKey} onChange={set('sourceKey')}
                      className="mt-1 w-full rounded border border-gray-300 px-2 py-1">
                      <option value="">—— 选一项 ——</option>
                      {SOURCE_OPTIONS.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
                    </select>
                  </label>
                  <label className="block">
                    <span className="font-semibold text-gray-700">表现形式</span>
                    <select value={fields.expressionForm} onChange={set('expressionForm')}
                      className="mt-1 w-full rounded border border-gray-300 px-2 py-1">
                      <option value="">—— 可不填 ——</option>
                      {FORM_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </label>
                  <label className="block">
                    <span className="font-semibold text-gray-700">管辖分支</span>
                    <select value={fields.jurisdiction} onChange={set('jurisdiction')}
                      className="mt-1 w-full rounded border border-gray-300 px-2 py-1">
                      {JUR_OPTIONS.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
                    </select>
                  </label>
                </div>
                <label className="block">
                  <span className="font-semibold text-gray-700">补充说明（可不填）</span>
                  <textarea value={fields.note} onChange={set('note')} rows={2}
                    className="mt-1 w-full rounded border border-gray-300 px-2 py-1" placeholder="一句话说明即可" />
                </label>
                <button type="button" data-testid="use-agent-draft"
                  className="rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:border-gray-300"
                  onClick={onMakeDraft}>
                  生成草稿（先看后签）
                </button>
              </section>
            )}

            {/* 步 3 出草稿：人读＋机读同源；不落库不出号；⛔ 预填登记号 */}
            {draft && !confirmed && (
              <section className="space-y-3 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm" data-testid="use-agent-draft-view">
                <p className="inline-block rounded bg-amber-200 px-2 py-0.5 font-bold text-amber-900">
                  草稿 · 未经签署 ⛔ 生效
                </p>
                <p className="text-amber-800">这份草稿只在你的浏览器里，没落库、没出号——上面<strong>没有登记号</strong>。看完没问题再确认。</p>
                <dl className="space-y-1 text-gray-800">
                  <div><dt className="inline font-semibold">作品名称：</dt><dd className="inline">{fields.workTitle}</dd></div>
                  <div><dt className="inline font-semibold">权利人：</dt><dd className="inline">{fields.authorName}</dd></div>
                  <div><dt className="inline font-semibold">完成时间：</dt><dd className="inline">{fields.createdAt}</dd></div>
                  <div><dt className="inline font-semibold">对应文件：</dt><dd className="inline">{rec.original_filename}（{rec.upload_id}）</dd></div>
                  <div><dt className="inline font-semibold">来源谱系：</dt><dd className="inline">{draftSource?.(fields.sourceKey)?.label}</dd></div>
                </dl>
                <details>
                  <summary className="cursor-pointer font-semibold text-gray-700">机读稿（与上面同源）</summary>
                  <pre className="mt-2 overflow-auto rounded bg-white p-3 text-xs text-gray-700">{JSON.stringify(draft, null, 2)}</pre>
                </details>
                <div className="flex gap-3">
                  <button type="button" className="rounded-md border border-gray-300 px-4 py-1.5 text-sm text-gray-700"
                    onClick={() => setDraft(null)}>返回修改</button>
                  <button type="button" data-testid="use-agent-tosign"
                    className="rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700"
                    onClick={() => document.getElementById('use-agent-sign')?.scrollIntoView({ behavior: 'smooth' })}>
                    去确认
                  </button>
                </div>
              </section>
            )}

            {/* 步 4 人签：本人登录态＋显式点击（⛔ 默认勾选）＋时间留痕 */}
            {!confirmed && (
              <section id="use-agent-sign" className="space-y-3 rounded-lg border border-gray-200 p-4 text-sm">
                <h2 className="font-semibold text-gray-800">第 4 步 · 本人确认（人在场签）</h2>
                <p className="text-gray-600">确认是一次独立动作：勾了再点。本站只记「已确认」和时间，<strong>不收签名值、不收授权码</strong>；这不构成法律签署要件。</p>
                <label className="flex items-start gap-2">
                  <input data-testid="use-agent-ack" type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} className="mt-1" />
                  <span>我是 <strong>{me || '…'}</strong>，以上登记信息我看过、属实，确认申请登记。</span>
                </label>
                <button type="button" data-testid="use-agent-confirm"
                  disabled={!ack || !me}
                  className="rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:border-gray-300 disabled:bg-gray-300"
                  onClick={onConfirm}>
                  我确认，申请登记
                </button>
              </section>
            )}

            {/* 步 5 出号：未确认 ⛔ 出号（确认前本区块不出现） */}
            {confirmed && !regResult && (
              <section className="space-y-3 rounded-lg border border-green-300 bg-green-50 p-4 text-sm" data-testid="use-agent-register">
                <p className="text-green-800">已由本人确认：{confirmed.by} · {confirmed.at}。</p>
                <button type="button" data-testid="use-agent-register-btn"
                  disabled={busy}
                  className="rounded-md border border-green-700 bg-green-700 px-4 py-1.5 text-sm text-white hover:bg-green-800 disabled:bg-gray-300"
                  onClick={() => void onRegister()}>
                  {busy ? '出号中…' : '出登记号'}
                </button>
                {regErr && <p className="rounded bg-amber-100 p-3 text-amber-800" role="alert">{regErr}</p>}
              </section>
            )}
          </>
        )}

        {regResult && (
          <section className="space-y-2 rounded-lg border border-green-200 bg-green-50 p-4 text-sm" data-testid="use-agent-result">
            <p className="font-medium text-green-800">登记已成——你的登记号：</p>
            <p className="text-2xl font-bold tracking-wide text-green-900">{regResult.record_id}</p>
            <dl className="space-y-1 text-gray-700">
              <div><dt className="inline font-semibold">状态：</dt><dd className="inline">{regResult.status}</dd></div>
              <div><dt className="inline font-semibold">存证回链：</dt><dd className="inline break-all">{regResult.nca_ref}</dd></div>
              <div><dt className="inline font-semibold">确认留痕：</dt><dd className="inline">{confirmed?.by} · {confirmed?.at}（已由本人确认）</dd></div>
            </dl>
            <p className="inline-block rounded bg-amber-200 px-2 py-0.5 text-xs font-bold text-amber-900">SIMULATED · 版权链为站内模拟态，非对外法律凭据</p>
            <p className="text-xs text-gray-500">凭证下载（带存证回链）为下一步（U-3 另令）。本页只说可核事实，不声称「已获版权」或「已受法律保护」。</p>
          </section>
        )}
      </div>
    </PageShell>
  )
}
