// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 乙案 P2 运维日志列表（/ops/logs/list）
// 约束矩阵: TDCA-HANDOFF-OPS-STORAGE-P2-001 §四（区间筛选＋行内查看＋导出按钮）
// 复用: PageShell / api；导出 CSV 带会话头（⛔ 不含凭据值——入库已过 V-2）
// =============================================================================
import { useState } from 'react'
import { Link } from 'react-router'
import { api, sessionToken } from '@/api/client'
import { PageShell } from './PageShell'

interface LogRow {
  log_date: string; duty_role: string; duty_no: string; handover: string
  exceptions_count: number; unclosed_count: number
  backfill: boolean; backfill_reason: string | null
  filled_by: string; filled_at: string
  sections: Record<string, Record<string, unknown>> & {
    F_异常与收尾?: { exceptions?: Array<Record<string, unknown>> }
  }
}

export function OpsLogsListPage() {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [dutyNo, setDutyNo] = useState('')
  const [rows, setRows] = useState<LogRow[]>([])
  const [total, setTotal] = useState(0)
  const [msg, setMsg] = useState('')
  const [detail, setDetail] = useState<LogRow | null>(null)

  const query = () => {
    const p = new URLSearchParams()
    if (from) p.set('from', from)
    if (to) p.set('to', to)
    if (dutyNo) p.set('duty_no', dutyNo)
    return p.toString()
  }

  const load = async () => {
    setMsg('')
    const r = await api.get<{ total: number; logs: LogRow[] }>(`/api/v1/ops/logs?${query()}`)
    if (!r.ok) { setMsg(`读取失败：${r.reason}`); return }
    setRows(r.data.logs); setTotal(r.data.total)
  }

  const exportCsv = async () => {
    setMsg('')
    const tok = sessionToken()
    const r = await fetch(`/api/v1/ops/logs/export?${query()}`, {
      headers: tok ? { Authorization: tok } : {},
    })
    if (!r.ok) { setMsg(`导出失败：HTTP ${r.status}`); return }
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `ops_logs_${from || 'all'}_${to || 'all'}.csv`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <PageShell title="运维日志列表" dataSource="/api/v1/ops/logs（区间）＋ /export（CSV）"
      permission="operator/founder（运维门内）"
      description="按区间/值日筛选、行内查看、导出 CSV（周汇总/月报）；保留 12 个月不删行。">
      <p className="text-xs">
        <Link to="/ops/logs" className="text-blue-600 underline">← 返回填写表单</Link>
      </p>
      <div className="flex flex-wrap gap-2 items-center text-xs" data-testid="ops-logs-filter">
        <label>from <input className="border rounded px-1" value={from} onChange={(e) => setFrom(e.target.value)} placeholder="YYYY-MM-DD" /></label>
        <label>to <input className="border rounded px-1" value={to} onChange={(e) => setTo(e.target.value)} placeholder="YYYY-MM-DD" /></label>
        <label>工号 <input className="border rounded px-1" value={dutyNo} onChange={(e) => setDutyNo(e.target.value)} /></label>
        <button data-testid="ops-logs-search" onClick={load}>查询</button>
        <button data-testid="ops-logs-export" onClick={exportCsv}>导出 CSV</button>
        {msg && <span role="status">{msg}</span>}
        <span className="text-gray-400">共 {total} 条</span>
      </div>
      <table className="text-xs w-full mt-2" data-testid="ops-logs-table">
        <thead>
          <tr><th>日期</th><th>值班</th><th>工号</th><th>异常/未闭合</th><th>补记</th><th>填写</th><th /></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.log_date}-${r.duty_no}`}>
              <td>{r.log_date}</td>
              <td>{r.duty_role}</td>
              <td>{r.duty_no}</td>
              <td>{r.exceptions_count} / {r.unclosed_count}</td>
              <td>{r.backfill ? `是（${r.backfill_reason ?? ''}）` : '否'}</td>
              <td>{r.filled_by} @ {r.filled_at.slice(0, 16)}</td>
              <td><button onClick={() => setDetail(r)}>查看</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      {detail && (
        <details open data-testid="ops-logs-detail" className="mt-2 text-xs">
          <summary>{detail.log_date}（{detail.duty_no}）六组明细</summary>
          <pre className="bg-gray-50 p-2 overflow-auto max-h-96">
            {JSON.stringify(detail.sections, null, 2)}
          </pre>
          <button onClick={() => setDetail(null)}>收起</button>
        </details>
      )}
    </PageShell>
  )
}
