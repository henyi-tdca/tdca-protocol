// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P8b /authorization-registry 授权登记管理（上站）
// 约束矩阵: 组四 P8b 要件（登记二分·四缺一即拒·签名须本人·智能体不代持代填·
//           公开面四字段·四条不公开负空间·授权件仅内部存证不入主仓）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/api/client'
import { useAuth } from '@/app/auth-context'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface RuleView {
  registry_split: { ownership: string; authorization: string }
  four_requirements: { key: string; label: string; rule: string }[]
  operations: { op: string; label: string; to_status: string }[]
  public_four_fields: string[]
  non_public_four: string[]
  storage: string
}

interface RecordView {
  record_id: string
  status: string
  asset_ref: string
  grantee_ref: string
  scene: string
  scope_note: string | null
  term_note: string | null
  four_requirements: {
    scene_ok: boolean; five_forms_ok: boolean
    full_grant_ok: boolean; legal_signature_ok: boolean
  }
  nca_ref: string
  data_provenance: string
}

const OP_LABEL: Record<string, string> = {
  pre_accept: '预收权', activate: '实时授权', append: '追加授权',
  amend_terms: '许可变更', sub_grant: '多层级授权',
}

const PUBLIC_KEYS = ['权属信息', '授权信息', '授权状态', '获取方式'] as const

export function AuthorizationRegistryPage() {
  const { isAuthenticated } = useAuth()
  const [rules, setRules] = useState<RuleView | null>(null)
  const [records, setRecords] = useState<RecordView[]>([])
  const [msg, setMsg] = useState('')
  const [asset, setAsset] = useState('')
  const [grantee, setGrantee] = useState('')
  const [scene, setScene] = useState('')
  const [scopeNote, setScopeNote] = useState('')
  const [termNote, setTermNote] = useState('')
  const [reqScene, setReqScene] = useState(false)
  const [reqFive, setReqFive] = useState(false)
  const [reqFull, setReqFull] = useState(false)
  const [reqSign, setReqSign] = useState(false)
  const [amendId, setAmendId] = useState('')
  const [amendNote, setAmendNote] = useState('')
  const [cancelId, setCancelId] = useState('')
  const [opId, setOpId] = useState('')
  const [op, setOp] = useState('activate')
  const [opNote, setOpNote] = useState('')
  const [pubId, setPubId] = useState('')
  const [pubView, setPubView] = useState<Record<string, string> | null>(null)

  const loadRules = async () => {
    const r = await api.get<RuleView>('/api/v1/authorization/rules')
    if (r.ok) setRules(r.data)
  }
  const loadRecords = async () => {
    const r = await api.get<{ records: RecordView[] }>('/api/v1/authorization/query')
    if (r.ok) setRecords(r.data.records)
  }
  useEffect(() => {
    void loadRules()
    void loadRecords()
  }, [])

  const onRegister = async () => {
    setMsg('')
    const r = await api.post<{ record_id: string }>(
      '/api/v1/authorization/register',
      { asset_ref: asset, grantee_ref: grantee, scene,
        req_scene: reqScene, req_five_forms: reqFive,
        req_full_grant: reqFull, req_legal_signature: reqSign,
        scope_note: scopeNote, term_note: termNote })
    if (!r.ok) { setMsg(`登记失败：${r.reason}`); return }
    setMsg(`已登记：${r.data.record_id}（四要件自证齐全；授权件仅内部存证）`)
    setAsset(''); setGrantee(''); setScene(''); setScopeNote(''); setTermNote('')
    setReqScene(false); setReqFive(false); setReqFull(false); setReqSign(false)
    void loadRecords()
  }
  const onAmend = async () => {
    setMsg('')
    const r = await api.post<{ data: { status: string } }>(
      '/api/v1/authorization/amend',
      { record_id: amendId, note: amendNote })
    setMsg(r.ok ? `已变更：${amendId}` : `变更失败：${r.reason}`)
    if (r.ok) { setAmendId(''); setAmendNote(''); void loadRecords() }
  }
  const onCancel = async () => {
    setMsg('')
    const r = await api.post<{ data: { status: string } }>(
      '/api/v1/authorization/cancel', { record_id: cancelId })
    setMsg(r.ok ? `已注销：${cancelId}（留存为历史档案）` : `注销失败：${r.reason}`)
    if (r.ok) { setCancelId(''); void loadRecords() }
  }
  const onOperate = async () => {
    setMsg('')
    const r = await api.post<{ status: string; op_label: string }>(
      '/api/v1/authorization/operate',
      { record_id: opId, op, note: opNote })
    if (!r.ok) { setMsg(`操作失败：${r.reason}`); return }
    setMsg(`已操作：${r.data.op_label}（${opId}）→ 状态 ${r.data.status}（NCA 存证）`)
    setOpId(''); setOpNote('')
    void loadRecords()
  }
  const onPublicQuery = async () => {
    setMsg('')
    setPubView(null)
    const r = await api.get<Record<string, string>>(
      `/api/v1/authorization/public/${pubId}`)
    if (!r.ok) { setMsg(`公开查失败：${r.reason}`); return }
    setPubView(r.data)
  }

  return (
    <PageShell
      title="授权登记管理（P8b）"
      dataSource="A-24 /api/v1/authorization/*（登记／变更／注销／查询／操作＋公开查）"
      permission="登录 DID（公开查免会话）"
      description="登记二分之授权侧：谁能怎么用。四要件缺一即拒；签名须本人、智能体不代持代填；公开面仅四字段。">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          登记二分：权属登记＝归谁（P8a）／授权登记＝谁能怎么用（本页）
          <SimulatedBadge nature="simulated" />
        </div>

        {rules && (
          <section data-testid="ar-rules" className="rounded-lg border border-blue-200 bg-blue-50/50 p-4 text-sm">
            <h3 className="mb-2 font-semibold text-blue-800">登记口径</h3>
            <p>四要件（缺一即拒，不代填代证）：</p>
            <ul className="list-disc pl-5">
              {rules.four_requirements.map((x) => (
                <li key={x.key}>{x.label}——{x.rule}</li>
              ))}
            </ul>
            <p>
              五操作（授权状态随操作实时同步）：
              {rules.operations.map((x) => `${x.label}（→${x.to_status}）`).join('／')}
            </p>
            <p>公开面四字段：{rules.public_four_fields.join('／')}（初始条件必公开）。</p>
            <p className="text-xs text-gray-600">
              四条不公开负空间：{rules.non_public_four.join('／')}（写入拦截／读取脱敏）
            </p>
            <p className="text-xs text-gray-600">{rules.storage}</p>
          </section>
        )}

        {/* 二期改版批2块三：两面分隔——登记/操作/变更/注销/明细查询属私域办理面，未登录仅见登记口径＋公开查（免会话四字段） */}
        {isAuthenticated ? (
          <>
        <section data-testid="ar-register">
          <h2>授权登记</h2>
          <input placeholder="授权对象引用（如：deploy/core-go 等五族资产）" value={asset}
            onChange={(e) => setAsset(e.target.value)} />
          <input placeholder="被授权方引用（如：被授权企业标识）" value={grantee}
            onChange={(e) => setGrantee(e.target.value)} />
          <input placeholder="场景·必填（如：生产交付（内循环部署与运行））" value={scene}
            onChange={(e) => setScene(e.target.value)} />
          <input placeholder="权限范围说明·选填（未裁取值由人填，本端不自定）" value={scopeNote}
            onChange={(e) => setScopeNote(e.target.value)} />
          <input placeholder="期限说明·选填（未裁取值由人填）" value={termNote}
            onChange={(e) => setTermNote(e.target.value)} />
          <fieldset className="text-sm">
            <legend>四要件自证（逐条勾证，缺一即 fail-closed 拒收）</legend>
            <label><input type="checkbox" checked={reqScene}
              onChange={(e) => setReqScene(e.target.checked)} /> ① 场景约束</label>
            <label><input type="checkbox" checked={reqFive}
              onChange={(e) => setReqFive(e.target.checked)} /> ② 五阶资产形态</label>
            <label><input type="checkbox" checked={reqFull}
              onChange={(e) => setReqFull(e.target.checked)} /> ③ 全构成已授权</label>
            <label><input type="checkbox" checked={reqSign}
              onChange={(e) => setReqSign(e.target.checked)} /> ④ 法律主体签名（须本人）</label>
          </fieldset>
          <button onClick={onRegister}>登记</button>
        </section>

        <section data-testid="ar-operate">
          <h2>授权管理操作面板（五操作）</h2>
          <input placeholder="record_id（如：AR-a1b2c3d4e5）" value={opId}
            onChange={(e) => setOpId(e.target.value)} />
          <select value={op} onChange={(e) => setOp(e.target.value)} aria-label="操作">
            {Object.entries(OP_LABEL).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <input placeholder="操作附言·选填（逐笔落 NCA 存证）" value={opNote}
            onChange={(e) => setOpNote(e.target.value)} />
          <button onClick={onOperate}>执行操作</button>
        </section>

        <section data-testid="ar-amend">
          <h2>授权变更</h2>
          <input placeholder="record_id（如：AR-a1b2c3d4e5）" value={amendId}
            onChange={(e) => setAmendId(e.target.value)} />
          <input placeholder="变更附言（如：范围补充说明，须人填）" value={amendNote}
            onChange={(e) => setAmendNote(e.target.value)} />
          <button onClick={onAmend}>变更</button>
        </section>

        <section data-testid="ar-cancel">
          <h2>授权注销</h2>
          <input placeholder="record_id（如：AR-a1b2c3d4e5）" value={cancelId}
            onChange={(e) => setCancelId(e.target.value)} />
          <button onClick={onCancel}>注销</button>
          {msg && <p role="status">{msg}</p>}
        </section>

        <section data-testid="ar-query">
          <h2>授权查询</h2>
          <ul>
            {records.map((r) => (
              <li key={r.record_id}>
                [{r.status}] {r.asset_ref} → {r.grantee_ref}
                （场景：{r.scene}；四要件：
                {[r.four_requirements.scene_ok, r.four_requirements.five_forms_ok,
                  r.four_requirements.full_grant_ok, r.four_requirements.legal_signature_ok]
                  .map((x) => (x ? '✓' : '✗')).join('')}；
                NCA：{r.nca_ref}）
              </li>
            ))}
          </ul>
        </section>
          </>
        ) : (
          <section data-testid="ar-login-gate" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-600">
            登记／操作／变更／注销／明细查询属登录后的办理面；当前为未登录状态，仅见登记口径与公开查（免会话，仅四字段）。
            <Link to="/auth" className="ml-1 text-blue-700 underline hover:text-blue-900">登录后办理</Link>
          </section>
        )}

        <section data-testid="ar-public">
          <h2>公开查（免会话 · 仅四字段）</h2>
          <input placeholder="record_id（如：AR-a1b2c3d4e5）" value={pubId}
            onChange={(e) => setPubId(e.target.value)} />
          <button onClick={onPublicQuery}>公开查</button>
          {pubView && (
            <ul data-testid="ar-public-view">
              {PUBLIC_KEYS.map((k) => (
                <li key={k}>{k}：{String(pubView[k] ?? '—')}</li>
              ))}
              <li>状态：{pubView.status}</li>
            </ul>
          )}
        </section>
      </div>
    </PageShell>
  )
}
