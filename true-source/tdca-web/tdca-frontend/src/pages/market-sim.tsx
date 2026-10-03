// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P9 /market-sim 规范索引与沙盒最小链（上站）
// 约束矩阵: 组四 P9 要件（索引入口·版本读件内不硬编码·与 P7 红线第八项同源·
//           沙盒最小链发布→准入→撮合→结算全 SIMULATED·NCA 全链留痕）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/api/client'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface SpecEntry {
  key: string
  name: string
  doc_id: string
  present: boolean
  version?: string
  version_source?: string
  effective_status?: string
  effective_source?: string
  note: string
}

interface StepView {
  step: string
  ok: boolean
  detail: string
  nca_ref: string
}

interface RunView {
  run_id: string
  result: string
  steps: StepView[]
}

export function MarketSimPage() {
  const [specs, setSpecs] = useState<SpecEntry[]>([])
  const [runs, setRuns] = useState<RunView[]>([])
  const [msg, setMsg] = useState('')
  const [seller, setSeller] = useState('')
  const [asset, setAsset] = useState('')
  const [scene, setScene] = useState('')
  const [price, setPrice] = useState('0')

  const loadSpecs = async () => {
    const r = await api.get<{ regulations: SpecEntry[] }>(
      '/api/v1/regulations/index')
    if (r.ok) setSpecs(r.data.regulations)
  }
  const loadRuns = async () => {
    const r = await api.get<{ runs: RunView[] }>('/api/v1/market-sim/chains')
    if (r.ok) setRuns(r.data.runs)
  }
  useEffect(() => {
    void loadSpecs()
    void loadRuns()
  }, [])

  const onChain = async () => {
    setMsg('')
    const r = await api.post<RunView>('/api/v1/market-sim/chain', {
      seller_ref: seller, asset_summary: asset, scene,
      price_points: Number(price) || 0,
    })
    setMsg(r.ok
      ? `最小链 ${r.data.run_id}：${r.data.result}（${r.data.steps.length} 步留痕）`
      : `最小链失败：${r.reason}`)
    if (r.ok) { setSeller(''); setAsset(''); setScene(''); void loadRuns() }
  }

  return (
    <PageShell
      title="规范索引与沙盒最小链（P9）"
      dataSource="A-20 /api/v1/regulations/* + A-21 /api/v1/market-sim/*"
      permission="登录 DID"
      description="规范入册＋最小可用挂接（⛔ 不承诺 L2 市场全功能）：索引入口只列名目；最小链发布→准入→撮合→结算全 SIMULATED。">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          期一承诺＝规范入册＋最小可用挂接；未入册规范依赖端点 503 fail-closed
          <SimulatedBadge nature="simulated" />
        </div>

        <section data-testid="ms-index">
          <h2>规范索引区（docs/regulations/ 唯一权威源）</h2>
          <ul>
            {specs.map((s) => (
              <li key={s.key}>
                {s.present ? '【已收录】' : '【未入册】'}{s.name}（{s.doc_id}）
                {!s.present && (
                  <span className="ml-1 rounded bg-amber-100 px-1 py-px text-[9px] font-medium text-amber-700">在建中</span>
                )}
                {s.present && (
                  <Link to="/library?family=regulation" className="ml-2 text-sm font-medium text-blue-600 underline">
                    读全文 →
                  </Link>
                )}
                {s.version && (
                  <span data-testid={`ms-version-${s.key}`}>
                    {' '}件内版本：{s.version}
                  </span>
                )}
                {s.effective_status && (
                  <span> ｜ 生效：{s.effective_status}（{s.effective_source}）</span>
                )}
                <span className="ml-2 text-xs text-gray-500">{s.note}</span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-gray-600">
            只列名目与索引入口：⛔ 不复制正文、⛔ 不另存副本、⛔ 不重写条文；
            与运维端红线第八项（登记制度）同源。
          </p>
        </section>

        <section data-testid="ms-chain">
          <h2>沙盒最小链（发布→准入审查→撮合→结算）</h2>
          <input placeholder="出让方主体引用（如：my-agent-01——须与 P2 授权件 subject_agent 一致）" value={seller}
            onChange={(e) => setSeller(e.target.value)} />
          <input placeholder="标的摘要·五阶资产形态（如：第2阶 数据资产包-写生场景）" value={asset}
            onChange={(e) => setAsset(e.target.value)} />
          <input placeholder="场景（如：scene-painting-01——按授权件场景约束比对）" value={scene}
            onChange={(e) => setScene(e.target.value)} />
          <input placeholder="报价·站内积分 SIMULATED（如：1200）" value={price}
            onChange={(e) => setPrice(e.target.value)} />
          <button onClick={onChain}>跑最小链</button>
          {msg && <p role="status">{msg}</p>}
        </section>

        <section data-testid="ms-chains">
          <h2>运行留痕（NCA 全链可查）</h2>
          <ul>
            {runs.map((r) => (
              <li key={r.run_id}>
                [{r.result}] {r.run_id}：
                {r.steps.map((s) => `${s.step}${s.ok ? '✓' : '✗'}`).join('→')}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </PageShell>
  )
}
