// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /audit 审计透明（A-7 公共账本只读 BV-3）
// 约束矩阵: FRAMEWORK-001 §四 /audit + A-7 契约 + BV-3（只读）+ ID92
// =============================================================================
import { useState } from 'react'
import { useApiGet } from '@/lib/useApi'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'

/** 031 令 §四 标注原文（⛔ 不得省） */
const SELFCHECK_DISCLAIMER =
  '本查询可证：该条记录存在于台账，且其内容与写入时一致；台账当日形态与公开锚一致。历史各日是否被改写，取决于每日锚是否连续可核。'

interface LedgerData {
  events: { event_id: string; type: string; ts: string; amount: string }[]
  total: number
  note: string
}

interface SelfCheckRecord {
  nca_id: string
  action: string
  ts: string
  artifact_filename_sha256_16: string
  artifact_ext: string
  sha256_8: string
  rec_hash: string
  prev_hash: string
  detached: number
  detach_reason: string
  actor_hash: string
}

interface SelfCheckResult {
  record: SelfCheckRecord
  page_disclaimer: string
  note: string
}

/** 接缝适配（CONTENT-LIVE-ALL-001 AMEND-1）：reason 机读令牌映人话，⛔ 裸错误码上屏 */
const REASON_HUMAN: Record<string, string> = {
  http_error: '服务暂时不可用，请稍后再试',
  unauthorized: '须登录后查询',
  forbidden: '当前账号无查询权限',
  watermark_missing: '存证水印缺失，拒绝渲染',
  fail_closed: '入口不可用',
}

/** A-24 存证自查（M1″）：按 nca_id 查单行存证——白名单十字段，⛔ 不出 actor 原值 */
function SelfCheckBlock() {
  const [input, setInput] = useState('')
  const [result, setResult] = useState<SelfCheckResult | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async () => {
    const id = input.trim()
    if (!id) return
    setBusy(true)
    setError('')
    setResult(null)
    const res = await api.get<SelfCheckResult>(`/api/v1/selfcheck/nca/${encodeURIComponent(id)}`)
    setBusy(false)
    if (res.ok && res.data) {
      setResult(res.data)
    } else {
      setError('reason' in res ? (res.reason ?? 'fail_closed') : 'fail_closed')
    }
  }

  return (
    <div data-testid="selfcheck-block" className="mt-6 space-y-3 border-t border-gray-200 pt-4">
      <div className="text-sm font-medium">存证自查（M1″ · 单行级）</div>
      <p className="text-xs text-gray-500">{SELFCHECK_DISCLAIMER}</p>
      <div className="flex gap-2">
        <input
          data-testid="selfcheck-input"
          className="w-64 rounded border border-gray-300 px-2 py-1 font-mono text-xs"
          placeholder="输入 nca_id（如 example-nca-demo）"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
        />
        <button
          data-testid="selfcheck-run"
          className="rounded bg-blue-600 px-3 py-1 text-xs text-white"
          onClick={run}
          disabled={busy}
        >
          {busy ? '查询中…' : '查询'}
        </button>
      </div>
      {error && (
        <p data-testid="selfcheck-fail" className="rounded bg-red-50 p-2 text-xs text-red-600">
          [fail-closed] 未查到该存证（记录不存在于公开清单，或服务不可用）：{REASON_HUMAN[error] ?? '入口不可用'}
        </p>
      )}
      {result?.note && (
        <p data-testid="selfcheck-note" className="rounded bg-amber-50 p-2 text-xs text-amber-700">
          {result.note}
        </p>
      )}
      {result && (
        <table data-testid="selfcheck-record" className="w-full text-xs">
          <tbody>
            {(
              [
                ['nca_id', result.record.nca_id],
                ['action', result.record.action],
                ['ts', result.record.ts],
                ['artifact_filename_sha256_16',
                 `件名校验码 ${result.record.artifact_filename_sha256_16}（台账件名原值不对外显示）`],
                ['artifact_ext', result.record.artifact_ext || '—'],
                ['sha256_8', `${result.record.sha256_8}（artifact_path 之哈希，非记录哈希）`],
                ['rec_hash', result.record.rec_hash],
                ['prev_hash', result.record.prev_hash],
                ['detached', String(result.record.detached)],
                ['detach_reason', result.record.detach_reason || '—'],
                ['actor_hash', `${result.record.actor_hash}（脱敏值，不出原值）`],
              ] as const
            ).map(([k, v]) => (
              <tr key={k} className="border-b border-gray-100">
                <td className="py-1 pr-3 font-mono text-gray-500">{k}</td>
                <td className="py-1 font-mono text-gray-700">{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

/** 审计透明：公共账本（制度即公开，O(n) 可审计，只读 BV-3） */
export function AuditPage() {
  const { status, data, nature } = useApiGet<LedgerData>('/api/v1/audit/ledger-public')

  return (
    <PageShell
      title="审计透明"
      dataSource="A-7 GET /api/v1/audit/ledger-public + /nca/chain"
      permission="公开（制度即公开）"
      description="NCA 存证链 + 熔断历史 + 哈希审计（宪法第十六条 可观测）。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中（NCA 水印校验）…</p>}
      {status === 'fail' && (
        <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="audit-fail-closed">
          [fail-closed] 后端不可用或 NCA 水印缺失，拒绝渲染
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="audit-ledger" className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            公共账本（只读，BV-3）：共 {data.total} 条 <SimulatedBadge nature={nature ?? 'simulated'} />
          </div>
          {data.events.length === 0 && <p className="text-sm text-gray-400">暂无账本事件（模拟态）</p>}
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
                <th className="py-1.5">event_id</th>
                <th className="py-1.5">类型</th>
                <th className="py-1.5">金额</th>
                <th className="py-1.5">时间戳</th>
              </tr>
            </thead>
            <tbody>
              {data.events.map((e) => (
                <tr key={e.event_id} data-event={e.event_id} className="border-b border-gray-100">
                  <td className="py-1.5 font-mono text-xs text-gray-700">{e.event_id}</td>
                  <td className="py-1.5 text-xs text-gray-600">{e.type}</td>
                  <td className="py-1.5 text-xs text-gray-600">{e.amount}</td>
                  <td className="py-1.5 font-mono text-[10px] text-gray-400">{e.ts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {/* CONTENT-LIVE-ALL-001 AMEND-1（第一优先）：存证链段如实标注 + NCA 按编号查询块（旧树直拷·接缝适配） */}
      <section data-testid="audit-chain-note" className="mt-6 space-y-2 border-t border-gray-200 pt-4">
        <div className="text-sm font-medium">存证链</div>
        <p className="text-xs text-gray-600" data-testid="audit-chain-offline">
          本页展示示例/混合来源数据（公开账本接口匿名可取，data_nature=mixed，样例 3 条）；正式存证链数据源上线后另行标注。本段不请求、不渲染链数据；公开账本见上表，熔断历史同页。
        </p>
      </section>
      <SelfCheckBlock />
    </PageShell>
  )
}
