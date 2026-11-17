// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI218-OPSACCEPT-001-001 验收记录私域面（运维栏目）
// 约束矩阵: AMEND「结论可公示·作业入私域」——本页藏作业（全量记录/处置/留痕）：
//   noindex 随 nginx 默认谢绝（⛔ sitemap·⛔ 预渲染）；访问须登录或机面 O-1（端内闸守）；
//   公示结论面在 /acceptance（公开·入 sitemap）；两面人机互链
// 复用: PageShell / api（会话令牌自动注入）；GET /api/v1/ops/acceptance-records（私域机面）
// =============================================================================
import { Fragment, useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'

interface AccDoc {
  acceptance_id: string
  delivery_id: string
  auth_id?: string
  status: string
  standards?: { item: string; criterion: string }[]
  verdicts?: { item: string; pass: boolean; basis: string; gap?: string }[]
  rectifications?: { item: string; deadline: string }[]
  nca_seq?: string
  rec_hash?: string
  settlement?: string
  created_at?: string
  updated_at?: string
  actor?: string
}

export function OpsAcceptanceRecordsPage() {
  const [rows, setRows] = useState<AccDoc[] | null>(null)
  const [err, setErr] = useState('')
  const [open, setOpen] = useState<string | null>(null)

  useEffect(() => {
    void (async () => {
      const r = await api.get<{ count: number; records: AccDoc[] }>(
        '/api/v1/ops/acceptance-records')
      if (!r.ok) {
        setErr(r.reason === 'unauthorized' || r.reason === 'forbidden'
          ? '须登录（operator/founder）或持 O-1 授权件访问。'
          : `取件失败：${r.reason ?? ''}`)
        setRows(null)
        return
      }
      setRows(r.data.records)
    })()
  }, [])

  return (
    <PageShell
      title="验收记录全量（私域运维面）"
      dataSource="GET /api/v1/ops/acceptance-records（私域机面；登录或 O-1 授权）"
      permission="须登录 DID 或机面 O-1 授权；本页 noindex、⛔ sitemap"
      description="运维私域面：全量验收记录（含作业、逐条判定依据、整改、存证号与内部字段）。
        公示只露结论——公开查询面在 /acceptance（免登录，按号查）。">
      <div data-testid="ops-acceptance-records" className="max-w-4xl space-y-4">
        <p className="text-sm">
          <Link to="/acceptance" className="text-blue-600 underline hover:text-blue-800"
            data-testid="ops-acceptance-records-public-link">← 公示结论面（/acceptance · 公开查询）</Link>
        </p>

        {/* ── 验收结论全量（L1SI218-ACCTABLE-001：私域栏五字段·会话或O-1·C-3 归入 batch_construction）── */}
        <section className="space-y-2 rounded-lg border p-4">
          <h2 className="text-base font-semibold">验收结论全量（含作业五字段·私域）</h2>
          <p className="text-xs text-muted-foreground">
            acceptance_verdicts 全列：公示四字段＋作业过程／处置动作／留痕细节／凭据引用／内部编号。
            C-3 交付验收单链归入 batch_construction 类（⛔另建套），单链视图在下方。
          </p>
          <VerdictsOpsTable />
        </section>
        {err && (
          <p data-testid="ops-acceptance-records-error" role="alert"
            className="rounded bg-amber-50 p-3 text-sm text-amber-800">{err}</p>
        )}
        {rows === null && !err && <p className="text-sm text-muted-foreground">取件中…</p>}
        {rows !== null && rows.length === 0 && (
          <p className="rounded border p-4 text-sm">仓内暂无验收记录（空仓为常态，如实标）。</p>
        )}
        {rows !== null && rows.length > 0 && (
          <table data-testid="ops-acceptance-records-table" className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-1 pr-2">acceptance_id</th>
                <th className="py-1 pr-2">delivery_id</th>
                <th className="py-1 pr-2">状态</th>
                <th className="py-1 pr-2">标准/结论/整改</th>
                <th className="py-1 pr-2">存证</th>
                <th className="py-1 pr-2">更新时点</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((d) => (
                <Fragment key={d.acceptance_id}>
                  <tr className="border-b align-top"
                    data-testid={`ops-acc-row-${d.acceptance_id}`}>
                    <td className="py-1 pr-2 font-mono text-xs">{d.acceptance_id}</td>
                    <td className="py-1 pr-2 font-mono text-xs">{d.delivery_id}</td>
                    <td className="py-1 pr-2">{d.status}</td>
                    <td className="py-1 pr-2">
                      {(d.standards?.length ?? 0)}/{(d.verdicts?.length ?? 0)}/{(d.rectifications?.length ?? 0)}
                    </td>
                    <td className="py-1 pr-2 font-mono text-xs">{d.nca_seq ?? '—'}</td>
                    <td className="py-1 pr-2 text-xs">{d.updated_at ?? d.created_at ?? '—'}</td>
                    <td className="py-1 pl-2">
                      <button type="button" className="text-blue-700 hover:underline"
                        data-testid={`ops-acc-toggle-${d.acceptance_id}`}
                        onClick={() => setOpen(open === d.acceptance_id ? null : d.acceptance_id)}>
                        {open === d.acceptance_id ? '收起' : '展开'}
                      </button>
                    </td>
                  </tr>
                  {open === d.acceptance_id && (
                    <tr key={`${d.acceptance_id}-detail`}>
                      <td colSpan={7} className="bg-muted/40 p-3 text-xs">
                        <p className="font-semibold">作业明细（私域）：</p>
                        <p>验收人/经手：{d.actor ?? '—'} ｜ rec_hash：{d.rec_hash ?? '—'} ｜ settlement：{d.settlement ?? '—'}</p>
                        {d.standards && d.standards.length > 0 && (
                          <ul className="mt-1 space-y-0.5">
                            {d.standards.map((s) => <li key={s.item}>· 标准 {s.item}：{s.criterion}</li>)}
                          </ul>
                        )}
                        {d.verdicts && d.verdicts.length > 0 && (
                          <ul className="mt-1 space-y-0.5">
                            {d.verdicts.map((v) => (
                              <li key={v.item}>· 结论 {v.item}：<b>{v.pass ? '通过' : '不通过'}</b>（依据 {v.basis}）
                                {v.gap ? <span className="text-red-700">——差距 {v.gap}</span> : null}</li>
                            ))}
                          </ul>
                        )}
                        {d.rectifications && d.rectifications.length > 0 && (
                          <ul className="mt-1 space-y-0.5">
                            {d.rectifications.map((r) => <li key={r.item}>· 整改 {r.item}：限 {r.deadline} 前</li>)}
                          </ul>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </PageShell>
  )
}

interface VerdictFull {
  id: number; verdict: string; decided_at: string; subject_type: string
  subject_ref: string; evidence_nca_id: string
  ops_process?: string; ops_actions?: string; ops_trace?: string
  credential_ref?: string; internal_ref?: string
}

const SUBJECT_LABEL: Record<string, string> = {
  institution_effective: '制度件生效', doc_ingest: '件入站',
  site_function: '站点功能', batch_construction: '施工批（含C-3）',
  agent_network: '智能体入网',
}

function VerdictsOpsTable() {
  const [rows, setRows] = useState<VerdictFull[] | null>(null)
  const [vErr, setVErr] = useState('')
  useEffect(() => {
    void (async () => {
      const r = await api.get<{ verdicts: VerdictFull[] }>('/api/v1/ops/acceptance-verdicts')
      if (!r.ok) { setVErr(`取件失败：${r.reason ?? ''}`); return }
      setRows(r.data.verdicts)
    })()
  }, [])
  if (vErr) return <p role="alert" className="rounded bg-amber-50 p-3 text-sm text-amber-800">{vErr}</p>
  if (rows === null) return <p className="text-sm text-muted-foreground">取件中…</p>
  if (rows.length === 0) return <p className="rounded border p-3 text-sm">空表为常态（台账无可派生验收结论，-414 S-AC1；谁判谁登后此栏渐填）。</p>
  return (
    <table data-testid="ops-acceptance-verdicts" className="w-full text-sm">
      <thead>
        <tr className="border-b text-left">
          <th className="py-1 pr-2">结论</th>
          <th className="py-1 pr-2">时点</th>
          <th className="py-1 pr-2">类型</th>
          <th className="py-1 pr-2">对象</th>
          <th className="py-1 pr-2">存证号</th>
          <th className="py-1 pr-2">作业/处置/留痕/凭据/编号</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((v) => (
          <tr key={v.id} className="border-b align-top">
            <td className="py-1 pr-2">{v.verdict}</td>
            <td className="py-1 pr-2 text-xs">{v.decided_at}</td>
            <td className="py-1 pr-2 text-xs">{SUBJECT_LABEL[v.subject_type] ?? v.subject_type}</td>
            <td className="py-1 pr-2 font-mono text-xs">{v.subject_ref}</td>
            <td className="py-1 pr-2 font-mono text-xs">{v.evidence_nca_id}</td>
            <td className="py-1 pr-2 text-xs">
              {v.ops_process ?? '—'}／{v.ops_actions ?? '—'}／{v.ops_trace ?? '—'}／
              {v.credential_ref ?? '—'}／{v.internal_ref ?? '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
