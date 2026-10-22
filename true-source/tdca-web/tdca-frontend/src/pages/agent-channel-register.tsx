// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 + 块E | 目标函数: /channel/registry 智能体自助登记入口（实页化）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI167-AGENT-REG-UI-001（E-4）＋ AMEND-001（E-5 分流首问）
// 制度锚点: 《智能体定义条例》V1.0-FROZEN 第8条（六要素＋锚定项）／第9条（登记两路）／
//           第10条（派生登记）／第19条（六步硬序）；三项裁定 GSEQ-5742（登记号＋通道类型）
// 口径要点: 登记即创建；六要素缺项逐项点名（fail-closed）；GUEST 校验通过才发号；
//           成功显著展示登记号（可复制）；查询框 fail-closed 口径不改
// =============================================================================
import { useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

interface RegSuccess {
  registered: boolean
  reused: boolean
  reg_no: string
  channel_type: string
  status: string
  nca_ref?: string
  idem_key?: string
  guest_precheck?: { precheck_nca_ref: string; precheck_at: string; registered_at: string }
}

const SIX_FIELDS: { key: string; zh: string }[] = [
  { key: 'device', zh: '设备' },
  { key: 'compute', zh: '算力' },
  { key: 'protocol', zh: '协议' },
  { key: 'role', zh: '角色' },
  { key: 'knowledge', zh: '知识' },
  { key: 'permission_ttl', zh: '权限时效' },
]

const SIX_STEPS_DISPLAY = [
  '① 加载 TDCA 协议',
  '② 持根节点执行令牌',
  '③ 负空间审查',
  '④ 沙盒验证',
  '⑤ 正空间执行事务',
  '⑥ NCA 存证（全程）',
]

const EMPTY_FORM: Record<string, string> = {
  device: '', compute: '', protocol: '', role: '', knowledge: '', permission_ttl: '',
  anchor_account: '', root_token_ref: '', participants: '',
  derived: '', source_lineage: '',
  agent_card: '', ext_declaration: '', ext_contact: '',
}

export function AgentChannelRegisterPage() {
  // E-5-1 分流首问：创建者（你的人类）是否已在本网注册？
  const [route, setRoute] = useState<'ANCHOR' | 'GUEST' | ''>('')
  const [form, setForm] = useState<Record<string, string>>(EMPTY_FORM)
  const [derived, setDerived] = useState(false)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const [ok, setOk] = useState<RegSuccess | null>(null)
  // 登记号实况查询框（fail-closed 口径照 studio 页，不改）
  const [gateInput, setGateInput] = useState('')
  const [gateMsg, setGateMsg] = useState('')

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  const sixPayload = () => {
    const p: Record<string, string> = {}
    for (const f of SIX_FIELDS) p[f.key] = form[f.key].trim()
    return p
  }

  const onSubmit = async () => {
    setMsg(''); setOk(null)
    if (!route) { setMsg('请先回答首问：创建者（你的人类）是否已在本网注册？'); return }
    let body: Record<string, unknown> = { channel_type: route, ...sixPayload() }
    if (route === 'ANCHOR') {
      body = {
        ...body,
        anchor_account: form.anchor_account.trim(),
        root_token_ref: form.root_token_ref.trim(),
        participants: form.participants.split(/[,，]/).map((x) => x.trim()).filter(Boolean),
        derived,
        source_lineage: derived ? form.source_lineage.trim() : '',
      }
    } else {
      let card: unknown = null
      if (form.agent_card.trim()) {
        try { card = JSON.parse(form.agent_card) } catch {
          setMsg('agent_card 须为合法 JSON 对象（条例第9条）'); return
        }
      }
      body = {
        ...body,
        agent_card: card,
        ext_declaration: form.ext_declaration.trim(),
        ext_contact: form.ext_contact.trim(),
      }
    }
    setBusy(true)
    const r = await api.post<RegSuccess>('/api/v1/agent-channel/register', body)
    setBusy(false)
    if (!r.ok) { setMsg(`登记被拒（fail-closed）：${r.detail ?? r.reason}`); return }
    setOk(r.data)
  }

  const onQuery = async () => {
    const regNo = gateInput.trim()
    if (!regNo) return
    setGateMsg('查询中…')
    const r = await api.get<Record<string, unknown>>(`/api/v1/agent-channel/gate/${encodeURIComponent(regNo)}`)
    if (!r.ok) {
      setGateMsg(r.reason === 'forbidden' || r.reason === 'unauthorized'
        ? '无权查看或登记不在册（fail-closed）'
        : '实况暂不可用（fail-closed，不猜测数据）')
      return
    }
    const ct = r.data.channel_type as string | undefined
    const marker = r.data.creator_marker as string | undefined
    setGateMsg(`登记在册（channel_type=${ct ?? 'ANCHOR'}）${marker ? `；${marker}` : ''}`)
  }

  const copyRegNo = () => {
    if (ok && navigator.clipboard) void navigator.clipboard.writeText(ok.reg_no).catch(() => undefined)
  }

  return (
    <PageShell
      title="智能体自助登记（通道登记）"
      dataSource="POST /api/v1/agent-channel/register（块 E）"
      permission="公开（ANCHOR 路提交须登录；GUEST 路免会话）"
      description="登记即创建：六要素逐项 fail-closed、缺项逐项点名；成功当场回登记号；每条落 NCA 存证。"
    >
      <div className="space-y-4">
        {/* 六步展示（E-4.3：照条例第19条；登记为创世前置，单列六步之外） */}
        <section data-testid="reg-six-steps" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">通道六步（条例第19条）</h3>
          <p className="mb-2 text-xs text-gray-500">登记＝创世前置（第9条），单列于六步之外，⛔ 混入六步计数。</p>
          <p className="mb-2 text-sm font-medium text-gray-700">登记（创世前置）</p>
          <ol className="grid grid-cols-1 gap-1 md:grid-cols-2">
            {SIX_STEPS_DISPLAY.map((s) => (
              <li key={s} className="rounded bg-gray-50 px-2 py-1.5 text-xs text-gray-600">{s}</li>
            ))}
          </ol>
        </section>

        {/* E-5-1 分流首问 */}
        <section data-testid="reg-first-ask" className="rounded-lg border border-blue-200 bg-blue-50/60 p-4 text-sm">
          <p className="mb-2 font-medium text-gray-800">创建者（你的人类）是否已在本网注册？</p>
          <div className="flex gap-4">
            <label className="flex items-center gap-1.5">
              <input type="radio" name="reg-route" data-testid="route-anchor" checked={route === 'ANCHOR'}
                onChange={() => { setRoute('ANCHOR'); setMsg(''); setOk(null) }} />
              是（ANCHOR 路：本网账户锚定）
            </label>
            <label className="flex items-center gap-1.5">
              <input type="radio" name="reg-route" data-testid="route-guest" checked={route === 'GUEST'}
                onChange={() => { setRoute('GUEST'); setMsg(''); setOk(null) }} />
              否（GUEST 路：非原生，校验通过才发号）
            </label>
          </div>
        </section>

        {route !== '' && (
          <section data-testid="reg-form" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">创世声明 · 六要素（第8条第1款，恰6项）</h3>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {SIX_FIELDS.map((f) => (
                <label key={f.key} className="flex flex-col gap-0.5 text-xs text-gray-600">
                  {f.zh}
                  <input data-testid={`reg-${f.key}`} className="rounded border border-gray-300 px-2 py-1 text-sm"
                    value={form[f.key]} onChange={set(f.key)} />
                </label>
              ))}
            </div>

            {route === 'ANCHOR' ? (
              <>
                <h3 className="mb-2 mt-4 text-sm font-semibold text-gray-800">锚定项（第8条第2款，单列不计入六要素）</h3>
                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                  <label className="flex flex-col gap-0.5 text-xs text-gray-600">
                    锚定之人类账户（缺省＝当前登录账户）
                    <input data-testid="reg-anchor-account" className="rounded border border-gray-300 px-2 py-1 text-sm"
                      value={form.anchor_account} onChange={set('anchor_account')} />
                  </label>
                  <label className="flex flex-col gap-0.5 text-xs text-gray-600">
                    根令牌引用（只收引用编号，⛔ 不收令牌值）
                    <input data-testid="reg-root-token" className="rounded border border-gray-300 px-2 py-1 text-sm"
                      value={form.root_token_ref} onChange={set('root_token_ref')} />
                  </label>
                  <label className="flex flex-col gap-0.5 text-xs text-gray-600 md:col-span-2">
                    资产配置参与方（多创建者之余者，逗号分隔；单一责任锚点＝锚定账户）
                    <input data-testid="reg-participants" className="rounded border border-gray-300 px-2 py-1 text-sm"
                      value={form.participants} onChange={set('participants')} />
                  </label>
                </div>
                <div className="mt-3 flex items-center gap-2 text-xs text-gray-600">
                  <input type="checkbox" data-testid="reg-derived" checked={derived}
                    onChange={(e) => setDerived(e.target.checked)} />
                  派生登记（第10条再登记：素材升格为主体／通用能力析出）
                </div>
                {derived && (
                  <label className="mt-2 flex flex-col gap-0.5 text-xs text-gray-600">
                    来源谱系（再登记必填）
                    <input data-testid="reg-lineage" className="rounded border border-gray-300 px-2 py-1 text-sm"
                      value={form.source_lineage} onChange={set('source_lineage')} />
                  </label>
                )}
              </>
            ) : (
              <>
                <h3 className="mb-2 mt-4 text-sm font-semibold text-gray-800">非原生（GUEST）材料（第9条第2款＋E-5-2）</h3>
                <label className="flex flex-col gap-0.5 text-xs text-gray-600">
                  agent_card（JSON 对象 ≤4KB）
                  <textarea data-testid="reg-agent-card" rows={4}
                    className="rounded border border-gray-300 px-2 py-1 font-mono text-xs"
                    value={form.agent_card} onChange={set('agent_card')} />
                </label>
                <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
                  <label className="flex flex-col gap-0.5 text-xs text-gray-600">
                    外部创建者声明·主体声明
                    <input data-testid="reg-ext-decl" className="rounded border border-gray-300 px-2 py-1 text-sm"
                      value={form.ext_declaration} onChange={set('ext_declaration')} />
                  </label>
                  <label className="flex flex-col gap-0.5 text-xs text-gray-600">
                    可核验联系方式（⛔ 不公开）
                    <input data-testid="reg-ext-contact" className="rounded border border-gray-300 px-2 py-1 text-sm"
                      value={form.ext_contact} onChange={set('ext_contact')} />
                  </label>
                </div>
                <p className="mt-2 text-xs text-amber-700">GUEST 路频控严于 ANCHOR 路；合规前置校验不过即拒（逐项点名），⛔ 发号、⛔ 落成幽灵态。</p>
              </>
            )}

            <div className="mt-4">
              <button data-testid="reg-submit" disabled={busy}
                className="rounded border border-blue-600 bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
                onClick={() => void onSubmit()}>
                {busy ? '提交中…' : '提交登记'}
              </button>
              {msg && <p data-testid="reg-msg" className="mt-2 text-sm text-red-700">{msg}</p>}
            </div>
          </section>
        )}

        {/* 成功页：显著展示登记号（可复制，E-4.1） */}
        {ok && (
          <section data-testid="reg-success" className="rounded-lg border border-green-300 bg-green-50 p-4">
            <h3 className="text-sm font-semibold text-green-900">
              {ok.reused ? '已登记（幂等复用原登记号）' : '登记成功（登记即创建）'}
            </h3>
            <p className="mt-2 text-2xl font-bold tracking-wide text-green-800" data-testid="reg-no">{ok.reg_no}</p>
            <p className="mt-1 text-xs text-gray-600">
              通道类型：{ok.channel_type}{ok.channel_type === 'GUEST' ? '（创建者未在本网注册）' : ''}　状态：{ok.status}
            </p>
            <p className="mt-1 text-xs text-gray-600">NCA 存证：{ok.nca_ref ?? '—'}</p>
            {ok.guest_precheck && (
              <p className="mt-1 text-xs text-gray-600" data-testid="reg-precheck-ts">
                合规校验存证：{ok.guest_precheck.precheck_nca_ref}（{ok.guest_precheck.precheck_at} 校验 → {ok.guest_precheck.registered_at} 发号）
              </p>
            )}
            <button data-testid="reg-copy" className="mt-2 rounded border border-green-700 px-2 py-1 text-xs text-green-800 hover:bg-green-100"
              onClick={copyRegNo}>复制登记号</button>
          </section>
        )}

        {/* 登记号实况查询框（E-4.2：保留 fail-closed 口径） */}
        <section data-testid="reg-gate-query" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">输入登记号查询实况</h3>
          <div className="flex gap-2">
            <input data-testid="gate-input" className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm"
              placeholder="输入登记号查询实况" value={gateInput} onChange={(e) => setGateInput(e.target.value)} />
            <button data-testid="gate-query" className="rounded border border-gray-400 px-3 py-1 text-sm hover:bg-gray-50"
              onClick={() => void onQuery()}>查询实况</button>
          </div>
          {gateMsg && <p className="mt-2 text-xs text-gray-600" data-testid="gate-msg">{gateMsg}</p>}
        </section>
      </div>
    </PageShell>
  )
}
