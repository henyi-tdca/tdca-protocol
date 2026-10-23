// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-CHANNEL-MY-001 | 目标函数: L1SI167-CHANNEL-UI-001 四屏界面令
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI167-CHANNEL-UI-001 §一~§四 ＋ 点击演示档追加件（乙档）
// 制度锚点: 四步硬序（押金→令牌→转正→沙盒）｜前置状态可见｜人话提示｜演示徽标
// 配置权边界: L2 前端层；只接既有端点（⛔ 不改后端／⛔ 不改开关／⛔ 演示档不落真库）
// 审计轨迹: L1SI167-CHANNEL-UI-001
// 开发者: Reasonix（M）| 负空间版本: NSFL-V0.2 | MOU 锚定: 复用既有 gateway 契约
// =============================================================================
import { useCallback, useEffect, useMemo, useState } from 'react'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { api, ApiFailure, loadDraft, saveDraft } from '@/api/client'

// ---------------------------------------------------------------------------
// 后端应答形状（只读契约复用；字段名照后端，⛔ 不自造口径）
// ---------------------------------------------------------------------------
interface GateStep {
  step: number
  label: string
  state: 'satisfied' | 'pending' | 'failed'
}
interface GateResp {
  reg_no: string
  channel_type: string
  promoted: boolean
  promoted_at: string | null
  creator_marker?: string
  gate: { steps: Record<string, GateStep>; admitted: boolean; status?: string }
}
interface DepositEvent {
  event_no: string
  action: string
  amount_mou: number
  created_at: string
}
interface DepositStateResp {
  reg_no: string
  effective_mou: number
  frozen_mou: number
  events: DepositEvent[]
  required_min_mou: number | null
}
interface TokenIssueResp {
  issued: boolean
  token_no: string
  token_value: string
  fingerprint_sha256_16: string
}
interface PromotionResp {
  promoted: boolean
  promoted_at: string
}
interface PolicyResp {
  registered: boolean
  policy_no: string
  status: string
}
interface SandboxResp {
  bound: boolean
  result: string
}

// ---------------------------------------------------------------------------
// 人话译文（⛔ 不直抛错误码；码与原文折在「详情」里）
// ---------------------------------------------------------------------------
function humanize(fail: ApiFailure): string {
  const raw = (fail.rawDetail ?? fail.detail ?? '').toString()
  if (/无有效转正令牌/.test(raw)) return '还没有有效的转正令牌——先回第 2 步把转正令牌签了，再来办转正。'
  if (/无有效保单/.test(raw)) return '还没有在册的有效保单——先在第 3 步登记一张保障期覆盖今天的保单，再来办转正。'
  if (/无在册沙盒签批记录|④沙盒验证未过/.test(raw)) return '沙盒验证还没通过——这道闸门要求先通过沙盒验证才能签转正令牌（顺序不能倒）。'
  if (/③负空间审查未过|③ 负空间审查未过/.test(raw)) return '前置的合规审查还没通过，暂不能签转正令牌。'
  if (/DEPOSIT_REQUIRED/.test(raw)) return '押金还不够——回第 1 步补足押金，才进得了沙盒。'
  if (/DEPOSIT_CONFIG_MISSING/.test(raw)) return '站点还没配置押金门槛，沙盒闸门按安全默认关闭——请联系站点管理员配置后再试。'
  if (/STEP_ORDER/.test(raw)) return '前面的步骤还没走完——先过合规审查，再进沙盒。'
  if (/仅登记主体本人/.test(raw)) return '这个登记号不是你的——换你自己的登记号再操作。'
  if (/已转正/.test(raw)) return '这个登记号已经转正过了，不用重复办理。'
  if (/四要件不齐/.test(raw)) return '签批四要件没填齐——人、时、物、意四项都要填。'
  if (/沙盒要件缺失/.test(raw)) return '进沙盒要带上两样东西：要件绑定引用和沙盒运行号——两项都填上再点。'
  if (/押付金额须为正整数/.test(raw)) return '押付金额要填大于 0 的整数。'
  if (/保障期止须晚于保障期起/.test(raw)) return '保单的截止日要晚于开始日。'
  if (/保额须为正整数/.test(raw)) return '保额要填大于 0 的整数。'
  if (/保单要件不齐/.test(raw)) return '保单信息没填齐——承保方、保障起止日期都要填。'
  if (fail.reason === 'unauthorized') return '请先登录——登录后再走这四步。'
  if (fail.reason === 'forbidden') return '现在做不了这一步——原因见下方「详情」。'
  if (fail.reason === 'fail_closed') return '站点暂时连不上——稍后再试，页面不会瞎猜数据。'
  if (fail.reason === 'watermark_missing') return '站点回应缺了防伪水印——为保护你不展示这次结果，请稍后再试。'
  return raw ? `这一步没办成——原因见下方「详情」。` : '这一步没办成——请稍后再试。'
}

// 演示档用假令牌值（⛔ 非真值；只显一次；不入库不入日志）
const DEMO_TOKEN = 'TDCA-PRT-示例-DEMO-ONLY-9f3a7c51e2b84d60'

interface StepResult {
  kind: 'ok' | 'err' | 'demo'
  text: string
  detail?: string
}

export function ChannelMyPage() {
  // ----- 登记号与后端实况（真跑档回填；演示档不写库） -----
  const [regInput, setRegInput] = useState(() => loadDraft<string>('/channel/my:reg') ?? '')
  const [regNo, setRegNo] = useState('')
  const [gate, setGate] = useState<GateResp | null>(null)
  const [dep, setDep] = useState<DepositStateResp | null>(null)
  const [loadMsg, setLoadMsg] = useState('')
  const [busy, setBusy] = useState(false)

  // ----- 演示档 -----
  const [demo, setDemo] = useState(false)
  const [demoStep, setDemoStep] = useState(0) // 已走到的步数（0~4）

  // ----- 各步结果（留在页上；真跑档刷新后由后端状态回填判步） -----
  const [depResult, setDepResult] = useState<StepResult | null>(null)
  const [tokenResult, setTokenResult] = useState<StepResult | null>(null)
  const [promoResult, setPromoResult] = useState<StepResult | null>(null)
  const [sandboxResult, setSandboxResult] = useState<StepResult | null>(null)
  const [tokenValue, setTokenValue] = useState<string | null>(null) // 只显一次
  const [tokenShown, setTokenShown] = useState(false)

  // ----- 表单 -----
  const [amount, setAmount] = useState(1) // 默认 1（令 §一步 1）
  const [fPerson, setFPerson] = useState('')
  const [fTime, setFTime] = useState('')
  const [fThing, setFThing] = useState('')
  const [fIntent, setFIntent] = useState('')
  const [polInsurer, setPolInsurer] = useState('')
  const [polCoverage, setPolCoverage] = useState(1)
  const [polStart, setPolStart] = useState('')
  const [polEnd, setPolEnd] = useState('')
  const [seaRef, setSeaRef] = useState('')
  const [runRef, setRunRef] = useState('')

  const refresh = useCallback(async (rn: string) => {
    const [g, d] = await Promise.all([
      api.get<GateResp>(`/api/v1/agent-channel/gate/${encodeURIComponent(rn)}`),
      api.get<DepositStateResp>(`/api/v1/agent-channel/${encodeURIComponent(rn)}/deposits`),
    ])
    if (g.ok) setGate(g.data)
    if (d.ok) setDep(d.data)
  }, [])

  useEffect(() => {
    if (regNo && !demo) void refresh(regNo)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [regNo, demo])

  const onLoad = async () => {
    const rn = regInput.trim().toUpperCase()
    if (!rn) return
    // 演示档：登记号仅作页面演示，不连站点、不校验在册（乙档⛔ 演示数据落真库）
    if (demo) {
      setRegNo(rn)
      saveDraft('/channel/my:reg', rn)
      setGate(null); setDep(null)
      setLoadMsg(`演示模式：${rn} 仅用于页面演示（不连站点、不写真库）`)
      setDepResult(null); setTokenResult(null); setPromoResult(null); setSandboxResult(null)
      setTokenValue(null); setTokenShown(false); setDemoStep(0)
      return
    }
    setBusy(true)
    setLoadMsg('载入中…')
    const g = await api.get<GateResp>(`/api/v1/agent-channel/gate/${encodeURIComponent(rn)}`)
    setBusy(false)
    if (!g.ok) {
      setGate(null); setDep(null); setRegNo('')
      setLoadMsg(g.reason === 'forbidden' || g.reason === 'unauthorized'
        ? '无权查看这个登记号（须登记主体本人，或该号不在册）'
        : humanize(g))
      return
    }
    setRegNo(rn)
    saveDraft('/channel/my:reg', rn)
    setLoadMsg(`已载入：${rn}（${g.data.channel_type}）${g.data.creator_marker ? `；${g.data.creator_marker}` : ''}`)
    // 清旧结果，防串号
    setDepResult(null); setTokenResult(null); setPromoResult(null); setSandboxResult(null)
    setTokenValue(null); setTokenShown(false); setDemoStep(0)
    await refresh(rn)
  }

  // ----- 真跑档前置灯 -----
  const stepState = (key: string): 'satisfied' | 'pending' | 'failed' | 'unknown' =>
    gate?.gate?.steps?.[key]?.state ?? 'unknown'
  const depositPaid = (dep?.events ?? []).filter((e) => e.action === 'paid')
    .reduce((s, e) => s + e.amount_mou, 0)
  const depositConfiscated = (dep?.events ?? []).filter((e) => e.action === 'confiscated')
    .reduce((s, e) => s + e.amount_mou, 0)
  const depositRefunded = (dep?.events ?? []).filter((e) => e.action === 'refunded')
    .reduce((s, e) => s + e.amount_mou, 0)
  const threshold = dep?.required_min_mou ?? null

  // 第 2 步灯：合规审查（ns-review）／沙盒（sandbox）——后端硬序：先过后两项才签得出令牌
  const nsOk = stepState('ns-review') === 'satisfied'
  const sandboxOk = stepState('sandbox') === 'satisfied'
  const tokenGateOk = nsOk && sandboxOk
  // 第 3 步灯：保单无查询口（S-1 受理），只能靠办转正结果反推
  const policyUnknown = true
  // 第 4 步灯：押金 ≥ 门槛（门槛未配置＝闸关）
  const depositEnough = threshold !== null && (dep?.effective_mou ?? 0) >= threshold

  // ----- 总状态条 -----
  const progress = useMemo(() => {
    if (demo) return [demoStep >= 1, demoStep >= 2, demoStep >= 3, demoStep >= 4]
    return [
      (dep?.effective_mou ?? 0) > 0,
      gate?.promoted === true ? true : tokenResult?.kind === 'ok', // 无令牌查询口：以签发结果或已转正推
      gate?.promoted === true,
      sandboxOk,
    ]
  }, [demo, demoStep, dep, gate, tokenResult, sandboxOk])

  // ----- 第 1 步：交押金 -----
  const payDeposit = async () => {
    if (demo) {
      setDemoStep((s) => Math.max(s, 1))
      setDepResult({ kind: 'demo', text: `演示：已记账 ${amount} MOU（演示数据·非真实业务，未写库）` })
      return
    }
    if (!regNo || amount <= 0) return
    setBusy(true)
    const r = await api.post<DepositStateResp & { paid?: boolean }>(
      `/api/v1/agent-channel/${encodeURIComponent(regNo)}/deposits`,
      { amount_mou: amount, mou_ref: '' },
    )
    setBusy(false)
    if (!r.ok) {
      setDepResult({ kind: 'err', text: humanize(r), detail: r.rawDetail ?? r.detail })
    } else {
      setDepResult({
        kind: 'ok',
        text: `已记账 ${amount} MOU（当前有效 ${r.data.effective_mou} MOU）`,
      })
      await refresh(regNo)
    }
  }

  // ----- 第 2 步：领令牌 -----
  const issueToken = async () => {
    if (demo) {
      setDemoStep((s) => Math.max(s, 2))
      if (!tokenShown) {
        setTokenValue(DEMO_TOKEN)
        setTokenShown(true)
      }
      setTokenResult({ kind: 'demo', text: '演示：转正令牌已签发（演示数据·非真实业务）' })
      return
    }
    if (!regNo) return
    setBusy(true)
    const r = await api.post<TokenIssueResp>(
      `/api/v1/agent-channel/${encodeURIComponent(regNo)}/promotion-token`,
      { approver: fPerson.trim(), approved_at: fTime.trim(),
        sandbox_approval_ref: fThing.trim(), approval_intent: fIntent.trim() },
    )
    setBusy(false)
    if (!r.ok) {
      setTokenResult({ kind: 'err', text: humanize(r), detail: r.rawDetail ?? r.detail })
      return
    }
    if (!tokenShown) {
      setTokenValue(r.data.token_value) // 至多一次性回显（⛔ localStorage／⛔ URL／⛔ 日志）
      setTokenShown(true)
    }
    setTokenResult({
      kind: 'ok',
      text: `转正令牌已签发（${r.data.token_no}，指纹 ${r.data.fingerprint_sha256_16}…）`,
    })
    await refresh(regNo)
  }

  // ----- 第 3 步：办转正 -----
  const promote = async () => {
    if (demo) {
      setDemoStep((s) => Math.max(s, 3))
      setPromoResult({
        kind: 'demo',
        text: `演示：已转正 promoted_at＝${new Date().toISOString()}（演示数据·非真实业务）`,
      })
      return
    }
    if (!regNo) return
    setBusy(true)
    const r = await api.post<PromotionResp>(
      `/api/v1/agent-channel/${encodeURIComponent(regNo)}/promotion`, {},
    )
    setBusy(false)
    if (!r.ok) {
      setPromoResult({ kind: 'err', text: humanize(r), detail: r.rawDetail ?? r.detail })
      return
    }
    setPromoResult({ kind: 'ok', text: `已转正 promoted_at＝${r.data.promoted_at}` })
    await refresh(regNo)
  }

  const registerPolicy = async () => {
    if (demo) {
      setPromoResult({ kind: 'demo', text: '演示：保单已登记（演示数据·非真实业务，未写库）' })
      return
    }
    if (!regNo) return
    setBusy(true)
    const r = await api.post<PolicyResp>(
      `/api/v1/agent-channel/${encodeURIComponent(regNo)}/insurance-policies`,
      { insurer: polInsurer.trim(), coverage_mou: polCoverage,
        period_start: polStart.trim(), period_end: polEnd.trim() },
    )
    setBusy(false)
    if (!r.ok) {
      setPromoResult({ kind: 'err', text: humanize(r), detail: r.rawDetail ?? r.detail })
    } else {
      setPromoResult({ kind: 'ok', text: `保单已登记（${r.data.policy_no}，${r.data.status}）` })
    }
  }

  // ----- 第 4 步：进沙盒 -----
  const enterSandbox = async () => {
    if (demo) {
      setDemoStep((s) => Math.max(s, 4))
      setSandboxResult({ kind: 'demo', text: '演示：沙盒验证已通过（演示数据·非真实业务，未写库）' })
      return
    }
    if (!regNo) return
    setBusy(true)
    const r = await api.post<SandboxResp>('/api/v1/agent-channel/sandbox', {
      reg_no: regNo,
      sea_elements_ref: seaRef.trim(),
      sandbox_run_ref: runRef.trim(),
      result: 'passed',
    })
    setBusy(false)
    if (!r.ok) {
      setSandboxResult({ kind: 'err', text: humanize(r), detail: r.rawDetail ?? r.detail })
      return
    }
    setSandboxResult({ kind: 'ok', text: `已进沙盒：验证结果 ${r.data.result === 'passed' ? '通过' : '未通过'}` })
    await refresh(regNo)
  }

  // ----- 置灰判据（人话原因） -----
  const step1Disabled = !regNo || busy || amount <= 0
  const step1Why = !regNo ? '先在上面载入你的登记号' : amount <= 0 ? '押付金额要大于 0' : ''
  const step2Disabled = !regNo || busy || (!demo && !tokenGateOk) ||
    !fPerson.trim() || !fTime.trim() || !fThing.trim() || !fIntent.trim()
  const step2Why = !regNo ? '先载入登记号'
    : !demo && !tokenGateOk ? '沙盒验证还没通过——这道闸门要求先通过沙盒验证才能签转正令牌'
    : [fPerson, fTime, fThing, fIntent].some((v) => !v.trim()) ? '签批四要件（人／时／物／意）填齐才亮' : ''
  const step3Disabled = !regNo || busy
  const step3Why = !regNo ? '先载入登记号' : ''
  const step4Disabled = !regNo || busy || (!demo && !depositEnough)
  const step4Why = !regNo ? '先载入登记号'
    : !demo && threshold === null ? '押金门槛还没配置，沙盒闸按安全默认关着'
    : !demo && !depositEnough ? `押金还不够：当前有效 ${dep?.effective_mou ?? 0} MOU，门槛 ${threshold} MOU——回第 1 步补足`
    : ''

  const stepTitle = ['① 交押金', '② 领转正令牌', '③ 办转正', '④ 进沙盒']

  const ResultPanel = ({ r }: { r: StepResult | null }) => {
    if (!r) return null
    const tone = r.kind === 'ok' ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
      : r.kind === 'demo' ? 'border-purple-200 bg-purple-50 text-purple-800'
      : 'border-amber-200 bg-amber-50 text-amber-800'
    return (
      <div data-testid="step-result" className={`mt-3 rounded-lg border p-3 text-sm ${tone}`}>
        <div className="flex items-center gap-2">
          <span>{r.kind === 'ok' ? '✅' : r.kind === 'demo' ? '🎭' : '⚠️'}</span>
          <span>{r.text}</span>
          {r.kind === 'demo' && <SimulatedBadge nature="simulated" label="演示数据·非真实业务" />}
        </div>
        {r.detail && (
          <details className="mt-1 text-xs opacity-70">
            <summary>详情</summary>
            <p className="mt-1 whitespace-pre-wrap">{r.detail}</p>
          </details>
        )}
      </div>
    )
  }

  const Lamp = ({ ok, unknown, label }: { ok: boolean; unknown?: boolean; label: string }) => (
    <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] ${
      unknown ? 'bg-gray-100 text-gray-500'
      : ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
      {unknown ? '❔' : ok ? '✅' : '⛔'} {label}
    </span>
  )

  return (
    <PageShell
      title="我的通道"
      dataSource="GET /api/v1/agent-channel/gate/{reg_no} ＋ deposits ＋ promotion-token ＋ promotion ＋ sandbox（只接既有端点）"
      permission="私域（须登录；仅登记主体本人可操作）"
      description="四步流水线：交押金 ⟶ 领转正令牌 ⟶ 办转正 ⟶ 进沙盒。每步先看前置状态，满足了按钮才亮；没满足会一句话讲清原因。"
    >
      {/* —— 登记号载入 —— */}
      <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <label className="mb-1 block text-sm font-medium text-gray-700">你的登记号（从「自助登记」成功页复制）</label>
        <div className="flex flex-wrap gap-2">
          <input
            data-testid="reg-input"
            className="rounded border border-gray-300 px-2 py-1 text-sm uppercase"
            placeholder="SAR-…"
            value={regInput}
            onChange={(e) => setRegInput(e.target.value)}
          />
          <button
            data-testid="reg-load"
            onClick={onLoad}
            disabled={busy}
            className="rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-700 disabled:bg-gray-300"
          >
            载入
          </button>
          {regNo && <span className="self-center text-xs text-emerald-700">当前：{regNo}{gate?.promoted ? '（已转正）' : ''}</span>}
        </div>
        {loadMsg && <p className="mt-1 text-xs text-gray-500">{loadMsg}</p>}
      </div>

      {/* —— 演示模式开关 ＋ 总状态条 —— */}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 p-3">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            data-testid="demo-toggle"
            type="checkbox"
            checked={demo}
            onChange={(e) => {
              setDemo(e.target.checked)
              setDemoStep(0)
              if (!e.target.checked && regNo) void refresh(regNo)
            }}
          />
          演示模式（不写真库，供走流程体验链路）
        </label>
        {demo && <SimulatedBadge nature="simulated" label="演示数据·非真实业务" />}
        <div className="ml-auto flex gap-2 text-xs">
          {stepTitle.map((t, i) => (
            <span key={t} data-testid={`progress-${i + 1}`}
              className={`rounded px-2 py-1 ${progress[i] ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-400'}`}>
              {progress[i] ? '✅' : '⬜'} {t}
            </span>
          ))}
        </div>
      </div>

      {/* —— 第 1 步：交押金 —— */}
      <section data-testid="step-1" className="mb-4 rounded-lg border border-gray-200 p-4">
        <h3 className="mb-2 font-semibold text-gray-800">① 交押金</h3>
        <div className="mb-2 flex flex-wrap gap-2 text-xs">
          <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">当前有效额：{dep?.effective_mou ?? 0} MOU</span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">已押：{depositPaid} MOU</span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">已没收：{depositConfiscated} MOU</span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">已退：{depositRefunded} MOU</span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">
            进沙盒门槛：{threshold === null ? '未配置（沙盒闸关闭）' : `${threshold} MOU`}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            data-testid="deposit-amount"
            type="number" min={1} value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
          />
          <span className="text-sm text-gray-500">MOU</span>
          <button
            data-testid="deposit-pay"
            onClick={payDeposit}
            disabled={step1Disabled}
            className="rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-700 disabled:bg-gray-300"
          >
            押付
          </button>
          <span className="text-xs font-semibold text-amber-700">记账（模拟）· 非实收</span>
        </div>
        {step1Disabled && step1Why && <p className="mt-1 text-xs text-gray-500">{step1Why}</p>}
        <ResultPanel r={depResult} />
      </section>

      {/* —— 第 2 步：领转正令牌 —— */}
      <section data-testid="step-2" className="mb-4 rounded-lg border border-gray-200 p-4">
        <h3 className="mb-2 font-semibold text-gray-800">② 领转正令牌</h3>
        <div className="mb-2 flex flex-wrap gap-2">
          {!demo && (
            <>
              <Lamp ok={nsOk} label="合规审查已通过" />
              <Lamp ok={sandboxOk} label="沙盒验证已通过" />
            </>
          )}
          {demo && <Lamp ok={demoStep >= 1} label="演示前置已备" />}
        </div>
        <p className="mb-2 text-xs text-gray-500">签批四要件（谁批／何时批／哪次沙盒通过／批来做什么）：</p>
        <div className="grid gap-2 sm:grid-cols-2">
          <input data-testid="tok-person" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="人：谁批（你的登录用户名）" value={fPerson} onChange={(e) => setFPerson(e.target.value)} />
          <div className="flex gap-1">
            <input data-testid="tok-time" className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm" placeholder="时：何时批（如 2026-10-23T08:00:00）" value={fTime} onChange={(e) => setFTime(e.target.value)} />
            <button type="button" className="rounded border border-gray-300 px-2 text-xs text-gray-600 hover:bg-gray-100"
              onClick={() => setFTime(new Date().toISOString().slice(0, 19))}>填现在</button>
          </div>
          <input data-testid="tok-thing" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="物：哪次沙盒通过（沙盒运行号引用）" value={fThing} onChange={(e) => setFThing(e.target.value)} />
          <input data-testid="tok-intent" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="意：批来做什么用" value={fIntent} onChange={(e) => setFIntent(e.target.value)} />
        </div>
        <button
          data-testid="token-issue"
          onClick={issueToken}
          disabled={step2Disabled}
          className="mt-2 rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-700 disabled:bg-gray-300"
        >
          签发转正令牌
        </button>
        {step2Disabled && step2Why && <p className="mt-1 text-xs text-gray-500">{step2Why}</p>}
        {tokenValue && (
          <div data-testid="token-once" className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3">
            <p className="break-all font-mono text-lg font-bold text-red-800">{tokenValue}</p>
            {demo && <p className="mt-1 text-xs text-red-600">（示例值，仅演示用）</p>}
            <p className="mt-1 text-sm font-semibold text-red-700">此值只显示这一次，系统只存指纹——请立即复制收好。</p>
            <button
              data-testid="token-copy"
              className="mt-2 rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700"
              onClick={() => { if (navigator.clipboard) void navigator.clipboard.writeText(tokenValue).catch(() => undefined) }}
            >
              复制令牌
            </button>
          </div>
        )}
        <ResultPanel r={tokenResult} />
      </section>

      {/* —— 第 3 步：办转正 —— */}
      <section data-testid="step-3" className="mb-4 rounded-lg border border-gray-200 p-4">
        <h3 className="mb-2 font-semibold text-gray-800">③ 办转正</h3>
        <div className="mb-2 flex flex-wrap gap-2">
          {!demo && (
            <>
              <Lamp ok={tokenResult?.kind === 'ok'} unknown={tokenResult?.kind !== 'ok'}
                label="转正令牌有效（无查询口，以签发结果为准）" />
              <Lamp ok={false} unknown={policyUnknown}
                label="保单有效且覆盖今天（无查询口，办转正时一并校验）" />
            </>
          )}
          {demo && <Lamp ok={demoStep >= 2} label="演示前置已备" />}
        </div>
        <button
          data-testid="promotion-run"
          onClick={promote}
          disabled={step3Disabled}
          className="rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-700 disabled:bg-gray-300"
        >
          办转正
        </button>
        {step3Disabled && step3Why && <p className="mt-1 text-xs text-gray-500">{step3Why}</p>}
        <details className="mt-3 rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
          <summary className="cursor-pointer text-gray-700">还没有保单？先在这里登记一张</summary>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            <input data-testid="pol-insurer" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="承保方（人类可读名）" value={polInsurer} onChange={(e) => setPolInsurer(e.target.value)} />
            <div className="flex items-center gap-1">
              <input data-testid="pol-coverage" type="number" min={1} value={polCoverage}
                onChange={(e) => setPolCoverage(Number(e.target.value))}
                className="w-24 rounded border border-gray-300 px-2 py-1 text-sm" />
              <span className="text-xs text-gray-500">MOU 保额</span>
            </div>
            <input data-testid="pol-start" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="保障期起（如 2026-10-23T00:00:00）" value={polStart} onChange={(e) => setPolStart(e.target.value)} />
            <input data-testid="pol-end" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="保障期止（如 2027-10-23T00:00:00）" value={polEnd} onChange={(e) => setPolEnd(e.target.value)} />
          </div>
          <button
            data-testid="pol-register"
            onClick={registerPolicy}
            disabled={!regNo || busy || !polInsurer.trim() || !polStart.trim() || !polEnd.trim()}
            className="mt-2 rounded border border-indigo-600 px-3 py-1 text-sm text-indigo-700 hover:bg-indigo-50 disabled:border-gray-300 disabled:text-gray-300"
          >
            登记保单
          </button>
        </details>
        <ResultPanel r={promoResult} />
      </section>

      {/* —— 第 4 步：进沙盒 —— */}
      <section data-testid="step-4" className="mb-4 rounded-lg border border-gray-200 p-4">
        <h3 className="mb-2 font-semibold text-gray-800">④ 进沙盒</h3>
        <div className="mb-2 flex flex-wrap gap-2">
          {!demo && <Lamp ok={depositEnough} label={`押金 ≥ 门槛（${threshold === null ? '门槛未配置' : threshold + ' MOU'}）`} />}
          {demo && <Lamp ok={demoStep >= 3} label="演示前置已备" />}
        </div>
        <div className="mb-2 flex flex-wrap gap-2">
          <input data-testid="sb-sea" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="要件绑定引用（SEA 引用）" value={seaRef} onChange={(e) => setSeaRef(e.target.value)} />
          <input data-testid="sb-run" className="rounded border border-gray-300 px-2 py-1 text-sm" placeholder="沙盒运行号" value={runRef} onChange={(e) => setRunRef(e.target.value)} />
        </div>
        <button
          data-testid="sandbox-enter"
          onClick={enterSandbox}
          disabled={step4Disabled}
          className="rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-700 disabled:bg-gray-300"
        >
          进沙盒验证
        </button>
        {step4Disabled && step4Why && <p className="mt-1 text-xs text-gray-500">{step4Why}</p>}
        <ResultPanel r={sandboxResult} />
      </section>

      <p className="text-xs text-gray-400">
        刷新页面后，各步进度以站点记录为准重新回填；令牌值刷新后不再显示。
      </p>
    </PageShell>
  )
}
