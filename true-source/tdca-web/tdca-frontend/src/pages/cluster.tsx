// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P2 /cluster 集群编排与准入闸门（上站）
// 约束矩阵: 期一开工令口径 5（配置类调用须授权件；谱系账本增授权谱系）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface GrantView {
  grant_id: string
  status: string
  asset_order: number
  parent_grant_id: string | null
}

interface LineageView {
  entry_id: string
  kind: string
  grant_id: string | null
  parent_grant_id: string | null
  ts: string
}

export function ClusterPage() {
  const [subject, setSubject] = useState('')
  const [scene, setScene] = useState('')
  const [order, setOrder] = useState('2')
  const [signer, setSigner] = useState('')
  const [hwSig, setHwSig] = useState('')
  const [grant, setGrant] = useState<GrantView | null>(null)
  const [msg, setMsg] = useState('')
  const [agentId, setAgentId] = useState('')
  const [verdict, setVerdict] = useState('')
  const [lineage, setLineage] = useState<LineageView[]>([])
  const [owId, setOwId] = useState('')
  const [arId, setArId] = useState('')
  const [sandbox, setSandbox] = useState(false)

  const onRegister = async () => {
    setMsg('')
    const r = await api.post<GrantView>('/api/v1/cluster/grant/register', {
      subject_agent: subject, scene_constraint: scene,
      asset_order: Number(order), full_composition: true,
      legal_signer: signer, signature: hwSig,
    })
    if (!r.ok) { setMsg(`登记失败：${r.reason}`); return }
    setGrant(r.data)
    setMsg('授权件已登记（首授）')
  }

  const onCheck = async () => {
    setMsg('')
    const r = await api.post<{ verdict: string }>(
      '/api/v1/cluster/admission/check', {
        agent_id: agentId, call_type: 'config',
        ownership_record_id: owId, authorization_record_id: arId,
        sandbox,
      })
    setVerdict(r.ok ? `准入判定：${r.data.verdict}` : `准入拒绝：${r.reason}`)
  }

  const onLineage = async () => {
    setMsg('')
    const r = await api.get<{ lineage: LineageView[] }>(
      `/api/v1/cluster/lineage/${agentId}`)
    if (!r.ok) { setMsg(`谱系查询失败：${r.reason}`); return }
    setLineage(r.data.lineage)
  }

  return (
    <PageShell
      title="集群编排与准入闸门（P2）"
      dataSource="A-13 /api/v1/cluster/*（授权件四要件机验 + 配置类调用闸门 + 谱系账本）"
      dataSourceAnon="制度件 · 公开可读（协作规则与谱系说明）· 明细登录可见"
      permission="登录 DID（登记须法律主体签名）"
      description="授权件登记与多层转授链；配置类调用须凭有效授权件过闸门——可信联通 ≠ 可信协作，仅握手不成立。">
      <section data-testid="cluster-grant">
        <h2>授权件登记（四要件）</h2>
        <SimulatedBadge nature="simulated" />
        <div>
          <input placeholder="智能体标识" value={subject} onChange={(e) => setSubject(e.target.value)} />
          <input placeholder="场景约束（要件①）" value={scene} onChange={(e) => setScene(e.target.value)} />
          <select value={order} onChange={(e) => setOrder(e.target.value)} aria-label="五阶资产形态">
            <option value="1">一阶</option><option value="2">二阶</option>
            <option value="3">三阶</option><option value="4">四阶</option>
            <option value="5">五阶</option>
          </select>
          <input placeholder="法律主体签名（要件④）" value={signer} onChange={(e) => setSigner(e.target.value)} />
          <input placeholder="模拟硬件签（≥8 字符）" value={hwSig} onChange={(e) => setHwSig(e.target.value)} />
          <button onClick={onRegister}>登记授权件</button>
        </div>
        {grant && <p>已登记：{grant.grant_id}（状态 {grant.status}）</p>}
        {msg && <p role="status">{msg}</p>}
      </section>
      <section data-testid="cluster-admission">
        <h2>准入闸门（配置类调用 · 五闸门合取）</h2>
        <input placeholder="智能体标识" value={agentId} onChange={(e) => setAgentId(e.target.value)} />
        <input placeholder="权属登记成件 ID（G-2）" value={owId} onChange={(e) => setOwId(e.target.value)} />
        <input placeholder="授权登记成件 ID（G-3~G-5）" value={arId} onChange={(e) => setArId(e.target.value)} />
        <label>
          <input type="checkbox" checked={sandbox} onChange={(e) => setSandbox(e.target.checked)} />
          沙盒／演练例外（出盒须授权）
        </label>
        <button onClick={onCheck}>准入判定</button>
        <button onClick={onLineage}>谱系查询</button>
        {verdict && <p role="status">{verdict}</p>}
        {lineage.length > 0 && (
          <ul>
            {lineage.map((e) => (
              <li key={e.entry_id}>{e.kind} · {e.grant_id ?? '-'}
                {e.parent_grant_id ? ` ← ${e.parent_grant_id}` : ''}</li>
            ))}
          </ul>
        )}
      </section>
    </PageShell>
  )
}
