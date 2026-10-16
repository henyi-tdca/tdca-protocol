// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P8a /ownership-registry 权属登记管理（上站）
// 约束矩阵: 组四 P8a 要件（登记二分·凡具表达形式者皆可登记·场景非必须·
//           法域四支仅索引·四条不公开负空间·转让许可归 8b）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/api/client'
import { useAuth } from '@/app/auth-context'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface RuleView {
  entry: string
  lineage_required: string
  scene_optional: boolean
  jurisdiction_branches: { key: string; branch: string; entry: string }[]
  no_legal_judgement: string
  out_of_scope: string
  non_public_four: string[]
}

interface RecordView {
  record_id: string
  status: string
  jurisdiction_branch: string
  work_title: string
  owner_ref: string
  source_lineage: string
  scene: string | null
  nca_ref: string
  data_provenance: string
}

const BRANCH_LABEL: Record<string, string> = {
  copyright: '表达形式→著作权',
  patent: '发明→专利法',
  data: '数字结构化→数据法',
  trademark: '标识→商标法',
  unspecified: '不预判法域',
}

export function OwnershipRegistryPage() {
  const { isAuthenticated } = useAuth()
  const [rules, setRules] = useState<RuleView | null>(null)
  const [records, setRecords] = useState<RecordView[]>([])
  const [msg, setMsg] = useState('')
  const [title, setTitle] = useState('')
  const [owner, setOwner] = useState('')
  const [lineage, setLineage] = useState('')
  const [branch, setBranch] = useState('unspecified')
  const [scene, setScene] = useState('')
  const [amendId, setAmendId] = useState('')
  const [amendNote, setAmendNote] = useState('')
  const [cancelId, setCancelId] = useState('')

  const loadRules = async () => {
    const r = await api.get<RuleView>('/api/v1/ownership/rules')
    if (r.ok) setRules(r.data)
  }
  const loadRecords = async () => {
    const r = await api.get<{ records: RecordView[] }>('/api/v1/ownership/query')
    if (r.ok) setRecords(r.data.records)
  }
  useEffect(() => {
    void loadRules()
    void loadRecords()
  }, [])

  const onRegister = async () => {
    setMsg('')
    const r = await api.post<{ record_id: string }>(
      '/api/v1/ownership/register',
      { work_title: title, owner_ref: owner, source_lineage: lineage,
        jurisdiction_branch: branch, scene })
    if (!r.ok) { setMsg(`登记失败：${r.reason}`); return }
    setMsg(`已登记：${r.data.record_id}（场景非必须；未载明不影响登记）`)
    setTitle(''); setOwner(''); setLineage(''); setScene('')
    void loadRecords()
  }
  const onAmend = async () => {
    setMsg('')
    const r = await api.post<{ data: { status: string } }>(
      '/api/v1/ownership/amend',
      { record_id: amendId, note: amendNote })
    setMsg(r.ok ? `已变更：${amendId}` : `变更失败：${r.reason}`)
    if (r.ok) { setAmendId(''); setAmendNote(''); void loadRecords() }
  }
  const onCancel = async () => {
    setMsg('')
    const r = await api.post<{ data: { status: string } }>(
      '/api/v1/ownership/cancel', { record_id: cancelId })
    setMsg(r.ok ? `已注销：${cancelId}（留存为历史档案）` : `注销失败：${r.reason}`)
    if (r.ok) { setCancelId(''); void loadRecords() }
  }

  return (
    <PageShell
      title="权属登记管理（P8a）"
      dataSource="A-19 /api/v1/ownership/*（登记／变更／注销／查询）"
      permission="登录 DID"
      description="登记二分之权属侧：凡具表达形式者皆可登记；须载生成来源谱系；场景非必须；法域四支仅索引不代法律判定。">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          登记二分：权属登记＝归谁（本页）／授权登记＝谁能怎么用（8b，⛔ 一期不做）
          <SimulatedBadge nature="simulated" />
        </div>

        {rules && (
          <section data-testid="or-rules" className="rounded-lg border border-blue-200 bg-blue-50/50 p-4 text-sm">
            <h3 className="mb-2 font-semibold text-blue-800">登记口径</h3>
            <p>入口：{rules.entry}；{rules.lineage_required}。</p>
            <p>
              法域四支（仅索引分支）：
              {rules.jurisdiction_branches.map((b) => `${b.entry}→${b.branch}`).join('／')}
            </p>
            <p className="text-xs text-gray-600">{rules.no_legal_judgement}</p>
            <p className="text-xs text-gray-600">
              四条不公开负空间：{rules.non_public_four.join('／')}（写入拦截／读取脱敏）
            </p>
            <p className="text-xs text-gray-600">{rules.out_of_scope}</p>
          </section>
        )}

        {/* 二期改版批2块三：两面分隔——登记/变更/注销属私域办理面，未登录只见查询公示面 */}
        {isAuthenticated ? (
          <>
        <section data-testid="or-register">
          <h2>权属登记</h2>
          <input placeholder="登记对象·表达形式（如：智能体生成绘画《渡口》数字图）" value={title}
            onChange={(e) => setTitle(e.target.value)} />
          <input placeholder="权利人引用（如：did:tdca:founder 或本账号用户名）" value={owner}
            onChange={(e) => setOwner(e.target.value)} />
          <input placeholder="生成来源谱系·必填（如：agent-001 × 场景写生 × 2026-10）" value={lineage}
            onChange={(e) => setLineage(e.target.value)} />
          <select value={branch} onChange={(e) => setBranch(e.target.value)}
            aria-label="法域分支">
            <option value="unspecified">不预判法域</option>
            <option value="copyright">表达形式→著作权</option>
            <option value="patent">发明→专利法</option>
            <option value="data">数字结构化→数据法</option>
            <option value="trademark">标识→商标法</option>
          </select>
          <input placeholder="场景·选填（如：scene-painting-01；无场景不拒登记）" value={scene}
            onChange={(e) => setScene(e.target.value)} />
          <button onClick={onRegister}>登记</button>
        </section>

        <section data-testid="or-amend">
          <h2>权属变更</h2>
          <input placeholder="record_id（如：OWR-20261004-a1b2c3）" value={amendId}
            onChange={(e) => setAmendId(e.target.value)} />
          <input placeholder="变更附言（如：权利人更名，附新引用）" value={amendNote}
            onChange={(e) => setAmendNote(e.target.value)} />
          <button onClick={onAmend}>变更</button>
        </section>

        <section data-testid="or-cancel">
          <h2>权属注销</h2>
          <input placeholder="record_id（如：OWR-20261004-a1b2c3）" value={cancelId}
            onChange={(e) => setCancelId(e.target.value)} />
          <button onClick={onCancel}>注销</button>
          {msg && <p role="status">{msg}</p>}
        </section>
          </>
        ) : (
          <section data-testid="or-login-gate" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-600">
            登记／变更／注销属登录后的办理面；当前为未登录状态，仅见查询公示面。
            <Link to="/auth" className="ml-1 text-blue-700 underline hover:text-blue-900">登录后办理</Link>
          </section>
        )}

        <section data-testid="or-query">
          <h2>权属查询</h2>
          <ul>
            {records.map((r) => (
              <li key={r.record_id}>
                [{r.status}] {r.work_title} —— {r.owner_ref}
                （{BRANCH_LABEL[r.jurisdiction_branch] ?? r.jurisdiction_branch}；
                谱系：{r.source_lineage}；NCA：{r.nca_ref}）
              </li>
            ))}
          </ul>
        </section>
      </div>
    </PageShell>
  )
}
