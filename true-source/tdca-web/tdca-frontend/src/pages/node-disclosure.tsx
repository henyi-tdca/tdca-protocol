// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI197 节点规则披露登记簿 · 公域可查（私域期样例面平移）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI197-PUBLIC2-001 块 B——五项字段（node_id／rule_type／
//   rule_digest 16 位大写／rule_ref／effective_at ISO 8601 +08）＋簿字段（contract nd/1.0／
//   record_no／recorded_at／supersedes／status）；只登记不审批；只增不改；撤回置 WITHDRAWN ⛔ 删；
//   三式查（node_id／rule_type／effective_at）只读；形状不合 fail-closed；⛔ 全文入库 ⛔ 内部编号形态
// ENUMIDX-001 令 A：rule_type 查询由自由精确匹配收敛为下拉枚举（三值，照令面）；
//   形状闸兜底保留不撤，并补 rule_type 枚举校验（双层）；禁自增删枚举值
// =============================================================================
import { useMemo, useState } from 'react'
import { PageShell } from './PageShell'
import ledger from '@/data/node-rule-ledger.json'

interface LedgerRecord {
  record_no: string
  recorded_at: string
  node_id: string
  rule_type: string
  rule_digest: string
  rule_ref: string
  effective_at: string
  supersedes: string | null
  status: 'ACTIVE' | 'SUPERSEDED' | 'WITHDRAWN'
}

interface LedgerFile {
  contract: string
  records: LedgerRecord[]
}

const LEDGER = ledger as LedgerFile
// ENUMIDX-001 令 A：rule_type 枚举三值（照令面，禁自增删）
const RULE_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: 'negative_space', label: '负空间判据' },
  { value: 'sandbox_exit', label: '沙盒出盒条件' },
  { value: 'positive_space_internal', label: '正空间内部制度' },
]
const RULE_TYPE_LABEL: Record<string, string> = Object.fromEntries(
  RULE_TYPE_OPTIONS.map((o) => [o.value, o.label]),
)
const STATUS_LABEL: Record<LedgerRecord['status'], string> = {
  ACTIVE: '现行有效',
  SUPERSEDED: '已被替代',
  WITHDRAWN: '已撤回',
}

/** 形状闸（fail-closed）：任一条不合形状 ⟹ 整簿不渲染，只报形状不合 */
export function validateShape(file: LedgerFile): string | null {
  if (file.contract !== 'nd/1.0') return 'contract 字段不合（须为 nd/1.0）'
  if (!Array.isArray(file.records)) return 'records 非数组'
  const DIGEST = /^[0-9A-F]{16}$/
  const TS = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$/
  const DATE = /^\d{4}-\d{2}-\d{2}$/
  for (const r of file.records) {
    if (!r.record_no || typeof r.record_no !== 'string') return 'record_no 缺失或非串'
    if (!r.node_id || typeof r.node_id !== 'string') return 'node_id 缺失或非串'
    if (!r.rule_type || typeof r.rule_type !== 'string') return 'rule_type 缺失或非串'
    if (!RULE_TYPE_OPTIONS.some((o) => o.value === r.rule_type)) {
      return `rule_type 枚举不合（record_no=${r.record_no}）`
    }
    if (!DIGEST.test(r.rule_digest ?? '')) return `rule_digest 须 16 位大写十六进制（record_no=${r.record_no}）`
    if (!r.rule_ref || typeof r.rule_ref !== 'string') return 'rule_ref 缺失或非串'
    if (!TS.test(r.effective_at ?? '') && !DATE.test(r.effective_at ?? '')) {
      return `effective_at 须 ISO 8601（+08）（record_no=${r.record_no}）`
    }
    if (!['ACTIVE', 'SUPERSEDED', 'WITHDRAWN'].includes(r.status)) return `status 枚举不合（record_no=${r.record_no}）`
    if (r.supersedes !== null && typeof r.supersedes !== 'string') return 'supersedes 非串非空'
  }
  return null
}

/** 三式查：node_id 精确／rule_type 精确／effective_at 按 +08 日历日命中 */
function matchQuery(r: LedgerRecord, q: { node: string; type: string; date: string }): boolean {
  if (q.node && r.node_id !== q.node) return false
  if (q.type && r.rule_type !== q.type) return false
  if (q.date && !(r.effective_at ?? '').startsWith(q.date)) return false
  return true
}

export function NodeDisclosurePage() {
  const [node, setNode] = useState('')
  const [type, setType] = useState('')
  const [date, setDate] = useState('')

  const shapeError = useMemo(() => validateShape(LEDGER), [])
  const shown = useMemo(
    () => (shapeError ? [] : LEDGER.records.filter((r) => matchQuery(r, { node, type, date }))),
    [shapeError, node, type, date],
  )
  const activeCount = useMemo(
    () => (shapeError ? 0 : LEDGER.records.filter((r) => r.status === 'ACTIVE').length),
    [shapeError],
  )

  return (
    <PageShell
      title="节点规则披露登记簿 · 公域可查"
      dataSource="披露登记簿（仓内单源，只读渲染）"
      permission="公开（匿名可读 · 只读）"
      description="节点规则的对外披露面：只登记、不审批；披露不改变效力边界，未披露不构成对外依据。三式查阅，记录逐条可核。"
      dataNature="real"
    >
      <div data-testid="disclosure-page" className="space-y-5">
        {/* 页头 */}
        <div data-testid="disclosure-header" className="rounded-lg bg-teal-700 px-5 py-4 text-white">
          <div className="text-lg font-bold">节点规则披露登记簿 · 公域可查</div>
          <span className="mt-1.5 inline-block rounded-full bg-teal-100 px-3 py-0.5 text-xs text-teal-800">
            匿名可查 · 只读 · 只登记不审批
          </span>
        </div>

        {/* 登记约定（三条硬约束＋写入语义，照令面公示） */}
        <section data-testid="disclosure-contract" className="rounded-lg border border-gray-200 bg-white p-4 text-[13px] leading-relaxed">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">登记约定</h3>
          <ul className="list-disc space-y-1 pl-5 text-gray-700">
            <li>披露 ⛔ 改变规则效力边界；未披露之规则，⛔ 对外主张。</li>
            <li>本簿只登记、不审批：登记不构成认可，⛔ 评判规则优劣。</li>
            <li>只增不改：变更以新记录＋注明替代关系；撤回置「已撤回」，⛔ 删除。</li>
            <li>只登记引用与摘要，规则全文不入本簿。</li>
          </ul>
          <p className="mt-2 text-xs text-gray-500">
            每条登记五项：节点标识／规则类型／摘要指纹（16 位）／规则引用／生效时间；簿级字段：契约版本／登记号／登记时间／替代关系／状态。
          </p>
        </section>

        {/* 形状闸 fail-closed */}
        {shapeError && (
          <div data-testid="disclosure-shape-error" className="rounded-lg border border-red-300 bg-red-50 p-4 text-[13px] text-red-700">
            登记簿形状不合（fail-closed，整簿不予渲染）：{shapeError}
          </div>
        )}

        {/* 三式查 */}
        {!shapeError && (
          <>
            <div data-testid="disclosure-filters" className="flex flex-wrap items-end gap-3.5 rounded-lg border border-gray-200 bg-white p-3.5">
              <div>
                <label className="mb-1 block text-xs text-gray-500" htmlFor="pz-f-node">按节点标识查</label>
                <input
                  id="pz-f-node"
                  data-testid="disclosure-q-node"
                  value={node}
                  onChange={(e) => setNode(e.target.value.trim())}
                  placeholder="精确匹配"
                  className="min-w-[180px] rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500" htmlFor="pz-f-type">按规则类型查</label>
                {/* ENUMIDX-001 令 A：下拉枚举（三值）替代自由精确匹配；形状闸兜底仍在 */}
                <select
                  id="pz-f-type"
                  data-testid="disclosure-q-type"
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="min-w-[180px] rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]"
                >
                  <option value="">全部类型</option>
                  {RULE_TYPE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}（{o.value}）
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500" htmlFor="pz-f-date">按生效日查</label>
                <input
                  id="pz-f-date"
                  data-testid="disclosure-q-date"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="min-w-[180px] rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]"
                />
              </div>
              {(node || type || date) && (
                <button
                  type="button"
                  data-testid="disclosure-q-reset"
                  onClick={() => { setNode(''); setType(''); setDate('') }}
                  className="cursor-pointer rounded-md border border-gray-300 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                >
                  清空条件
                </button>
              )}
            </div>

            {/* 登记记录（只读） */}
            <div data-testid="disclosure-list" className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
              {shown.length === 0 ? (
                <p className="p-6 text-center text-sm text-gray-400">
                  {LEDGER.records.length === 0
                    ? '登记簿现无在册记录——有登记即在此公示，未登记即无可查。'
                    : '当前查询条件下暂无登记记录'}
                </p>
              ) : (
                <table className="w-full min-w-[880px] text-[13px]">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs text-gray-500">
                      <th className="px-3 py-2.5 font-medium">登记号</th>
                      <th className="px-3 py-2.5 font-medium">节点标识</th>
                      <th className="px-3 py-2.5 font-medium">规则类型</th>
                      <th className="px-3 py-2.5 font-medium">摘要指纹</th>
                      <th className="px-3 py-2.5 font-medium">规则引用</th>
                      <th className="px-3 py-2.5 font-medium">生效时间</th>
                      <th className="px-3 py-2.5 font-medium">登记时间</th>
                      <th className="px-3 py-2.5 font-medium">替代关系</th>
                      <th className="px-3 py-2.5 font-medium">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shown.map((r) => (
                      <tr key={r.record_no} data-testid={`disclosure-record-${r.record_no}`} className="border-b border-gray-100 last:border-0">
                        <td className="px-3 py-2.5 font-medium text-gray-900">{r.record_no}</td>
                        <td className="px-3 py-2.5 text-gray-700">{r.node_id}</td>
                        <td className="px-3 py-2.5 text-gray-700">{RULE_TYPE_LABEL[r.rule_type] ?? r.rule_type}（{r.rule_type}）</td>
                        <td className="px-3 py-2.5 font-mono text-xs text-gray-700">{r.rule_digest}</td>
                        <td className="px-3 py-2.5 text-gray-700">{r.rule_ref}</td>
                        <td className="px-3 py-2.5 text-gray-700">{r.effective_at}</td>
                        <td className="px-3 py-2.5 text-gray-700">{r.recorded_at}</td>
                        <td className="px-3 py-2.5 text-gray-700">{r.supersedes ?? '—'}</td>
                        <td className="px-3 py-2.5">
                          <span
                            className={`rounded px-2 py-0.5 text-xs ${
                              r.status === 'ACTIVE'
                                ? 'bg-green-100 text-green-700'
                                : r.status === 'SUPERSEDED'
                                  ? 'bg-amber-100 text-amber-700'
                                  : 'bg-red-100 text-red-700'
                            }`}
                          >
                            {STATUS_LABEL[r.status]}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        <footer data-testid="disclosure-footer" className="pb-6 text-xs leading-relaxed text-gray-400">
          本簿为节点规则的对外披露面：登记即可查，未登记不可主张；摘要指纹可复算核对，规则全文不入本簿。
          <br />
          在册记录共 {LEDGER.records.length} 条（现行 {activeCount} 条）；本页只读，⛔ 展示实现细节，⛔ 含凭据与自然人敏感信息。
        </footer>
      </div>
    </PageShell>
  )
}
