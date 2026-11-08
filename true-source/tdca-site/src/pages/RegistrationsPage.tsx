// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-REGPAGE-001 | 目标函数: 「内部权属登记（建设期）」公域查询页
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI205-REGISTRY-PAGE-001——匿名免登录只读一页；
//           三组字与双向两行逐字必带（自接口原样渲染，⛔ 前端另写定稿）；
//           不公开四条对渲染文本同样成立（面侧遮蔽形原样展示，⛔ 重新展开）；
//           条目总数⛔写入公告式文案（页内计数为实拉实显之功能读数）；
//           证据包用途声明⛔去除；零新后端／零写操作／零登录面改动。
// 口径: 接口映射（全匿名 GET）：
//       列表   GET /api/public/registrations
//       详情   GET /api/public/registrations/{record_id}
//       证据包 GET /api/public/registrations/{record_id}/evidence
// =============================================================================
import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/client'

interface ListItem {
  record_id: string
  title: string
  family: string
  content_sha256_16: string
  registered_at: string
  nca_ref: string
  status: string
}

interface ListData {
  face: string
  count: number
  items: ListItem[]
  labels: string[]
  proof_boundary: { provable: string; not_provable: string }
}

interface DetailData {
  face: string
  family: string
  fields: {
    ownership_info: Record<string, string>
    authorization_info: string
    authorization_status: string
    access_method: string
  }
  note_section: string
  record_meta: Record<string, string>
  labels: string[]
  proof_boundary: { provable: string; not_provable: string }
}

interface EvidenceData {
  用途声明: string
  栏一_件名与路径: Record<string, string>
  栏二_内容哈希与字节: Record<string, unknown>
  栏三_登记时间戳与记录号: Record<string, string>
  栏四_链段: Record<string, unknown>
}

const FAMILY_LABEL: Record<string, string> = {
  regulation: '制度',
  'cop-library': '素材库',
  whitepaper: '白皮书',
}

function FieldList({ obj }: { obj: Record<string, unknown> }) {
  return (
    <dl className="mt-1 space-y-1">
      {Object.entries(obj).map(([k, v]) => (
        <div key={k} className="flex gap-2 text-xs">
          <dt className="shrink-0 font-medium text-muted-foreground">{k}</dt>
          <dd className="break-all text-slate-800">{String(v ?? '—')}</dd>
        </div>
      ))}
    </dl>
  )
}

/** 公域登记查询页：匿名只读（页内计数为实拉实显功能读数，非公告式文案） */
export function RegistrationsPage() {
  const [list, setList] = useState<ListData | null>(null)
  const [err, setErr] = useState('')
  const [keyword, setKeyword] = useState('')
  const [family, setFamily] = useState('all')
  const [detail, setDetail] = useState<DetailData | null>(null)
  const [detailErr, setDetailErr] = useState('')
  const [evidence, setEvidence] = useState<EvidenceData | null>(null)
  const [evidenceErr, setEvidenceErr] = useState('')
  const [detailId, setDetailId] = useState('')

  useEffect(() => {
    api
      .get<ListData>('/api/public/registrations', { tolerateMissingWatermark: true })
      .then((r) => {
        if (r.ok) setList(r.data)
        else setErr(r.detail ?? r.reason)
      })
  }, [])

  const shown = useMemo(() => {
    if (!list) return []
    const kw = keyword.trim().toLowerCase()
    return list.items.filter((it) => {
      if (family !== 'all' && it.family !== family) return false
      if (kw && !it.title.toLowerCase().includes(kw)) return false
      return true
    })
  }, [list, keyword, family])

  const openDetail = (rid: string) => {
    setDetailId(rid)
    setDetail(null)
    setEvidence(null)
    setEvidenceErr('')
    setDetailErr('')
    api
      .get<DetailData>(`/api/public/registrations/${rid}`, { tolerateMissingWatermark: true })
      .then((r) => {
        if (r.ok) setDetail(r.data)
        else setDetailErr(r.detail ?? r.reason)
      })
  }

  const openEvidence = (rid: string) => {
    setEvidence(null)
    setEvidenceErr('')
    api
      .get<EvidenceData>(`/api/public/registrations/${rid}/evidence`, { tolerateMissingWatermark: true })
      .then((r) => {
        if (r.ok) setEvidence(r.data)
        else setEvidenceErr(r.detail ?? r.reason)
      })
  }

  const face = detail?.face ?? list?.face ?? '内部权属登记（建设期）'
  const labels = detail?.labels ?? list?.labels ?? []
  const boundary = detail?.proof_boundary ?? list?.proof_boundary

  return (
    <section data-testid="registrations-page" className="mx-auto max-w-5xl space-y-6 px-6 py-8">
      <header>
        <h1 className="text-2xl font-bold">{face}·公域查询</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          数据源：GET /api/public/registrations* ｜ 权限：公开（匿名只读） ｜ 面名口径：内部权属登记（建设期）
        </p>
      </header>

      {/* 三组字与双向两行（自接口原样渲染，逐字必带） */}
      <div className="rounded-xl border bg-card p-4 shadow-sm">
        <div className="flex flex-wrap gap-2">
          {labels.map((t) => (
            <span key={t} className="rounded bg-muted px-2 py-1 text-xs font-medium text-slate-800">
              {t}
            </span>
          ))}
        </div>
        {boundary && (
          <div className="mt-3 space-y-2 border-l-4 border-slate-300 pl-3 text-sm text-slate-700">
            <p data-testid="boundary-provable">{boundary.provable}</p>
            <p data-testid="boundary-not-provable">{boundary.not_provable}</p>
          </div>
        )}
      </div>

      {/* 检索（题名关键字＋族筛选；页内计数为实拉实显功能读数） */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          data-testid="reg-search"
          placeholder="按登记题名检索…"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="w-64 rounded border px-3 py-1.5 text-sm"
        />
        <select
          data-testid="reg-family"
          value={family}
          onChange={(e) => setFamily(e.target.value)}
          className="rounded border px-2 py-1.5 text-sm"
        >
          <option value="all">全部族</option>
          <option value="regulation">制度</option>
          <option value="cop-library">素材库</option>
          <option value="whitepaper">白皮书</option>
        </select>
        <span data-testid="reg-count" className="text-xs text-muted-foreground">
          实拉 {list?.count ?? '—'} 条 · 实显 {shown.length} 条
        </span>
      </div>

      {err && <p className="text-sm text-red-600">列表加载失败：{err}</p>}
      {!list && !err && <p className="text-sm text-muted-foreground">加载中…</p>}

      {/* 列表 */}
      {list && (
        <ul data-testid="reg-list" className="divide-y rounded-xl border bg-card shadow-sm">
          {shown.map((it) => (
            <li key={it.record_id}>
              <button
                type="button"
                data-testid={`reg-item-${it.record_id}`}
                onClick={() => openDetail(it.record_id)}
                className="block w-full px-4 py-3 text-left hover:bg-muted/50"
              >
                <div className="text-sm font-medium text-slate-900">{it.title}</div>
                <div className="mt-1 flex flex-wrap gap-x-4 text-xs text-muted-foreground">
                  <span>记录号 {it.record_id}</span>
                  <span>族 {FAMILY_LABEL[it.family] ?? it.family}</span>
                  <span>登记时间 {it.registered_at}</span>
                  <span>链上序号 {it.nca_ref}</span>
                </div>
              </button>
            </li>
          ))}
          {shown.length === 0 && (
            <li className="px-4 py-6 text-center text-sm text-muted-foreground">无符合检索条件之登记记录</li>
          )}
        </ul>
      )}

      {/* 详情 */}
      {detailErr && <p className="text-sm text-red-600">详情加载失败：{detailErr}</p>}
      {detail && (
        <div data-testid="reg-detail" className="rounded-xl border bg-card p-4 shadow-sm">
          <h2 className="text-lg font-bold">{detail.fields.ownership_info['登记题名']}</h2>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold">权属信息（四项可查字段之一）</h3>
              <FieldList obj={detail.fields.ownership_info} />
            </div>
            <div className="space-y-3 text-sm">
              <div>
                <h3 className="text-sm font-semibold">授权信息</h3>
                <p data-testid="reg-auth-info">{detail.fields.authorization_info}</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold">授权状态</h3>
                <p data-testid="reg-auth-status">{detail.fields.authorization_status}</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold">获取方式</h3>
                <p data-testid="reg-access-method">{detail.fields.access_method}</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold">登记记录备注（四件套）</h3>
                <pre data-testid="reg-note" className="mt-1 whitespace-pre-wrap rounded bg-muted p-3 text-xs">
                  {detail.note_section}
                </pre>
              </div>
              <button
                type="button"
                data-testid="reg-evidence-btn"
                onClick={() => openEvidence(detailId)}
                className="rounded border px-3 py-1 text-sm hover:bg-muted"
              >
                查看证据包
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 证据包（用途声明⛔去除） */}
      {evidenceErr && <p className="text-sm text-red-600">证据包加载失败：{evidenceErr}</p>}
      {evidence && (
        <div data-testid="reg-evidence" className="rounded-xl border border-amber-300 bg-amber-50 p-4">
          <p data-testid="reg-evidence-purpose" className="mb-3 text-sm font-medium text-amber-900">
            {evidence.用途声明}
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold">栏一 · 件名与路径</h3>
              <FieldList obj={evidence.栏一_件名与路径} />
            </div>
            <div>
              <h3 className="text-sm font-semibold">栏二 · 内容哈希与字节</h3>
              <FieldList obj={evidence.栏二_内容哈希与字节} />
            </div>
            <div>
              <h3 className="text-sm font-semibold">栏三 · 登记时间戳与记录号</h3>
              <FieldList obj={evidence.栏三_登记时间戳与记录号} />
            </div>
            <div>
              <h3 className="text-sm font-semibold">栏四 · 链段</h3>
              <FieldList obj={evidence.栏四_链段} />
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
