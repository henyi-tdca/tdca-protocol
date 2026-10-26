// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B26 · 模拟演练区一页（批2.6）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B26-001（6194 拆批裁定·施工令）／积分面额照设计件 6146
//   五张卡＋一张流水表；纯前端零后端（页内 useState，⛔ localStorage、⛔ 接口、⛔ 后端）
// 红线: 五卡必带文案逐字；负余额即拦（提示语逐字「积分不足，去签到或做任务」）；
//   ⛔ 任何金额字样（¥／￥／元／价格／档位／付费），单位只用「积分」；示例比例须标 ⛔ 真实税率；
//   演练完成 +50 领取入口后批接入（本批只展示规则）；结算扣款随三剧本后批（本批不扣款，如实标注）；
//   零内部编号；会话限制句必写
// =============================================================================
import { useState } from 'react'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

/** 流水一条：八字段全值（流水号／时点／类型／来源或场景／变动值／变动后余额／关联 NCA 号／演练编号） */
interface Flow {
  no: string // SIM-FLOW-0001（四位序）
  time: string // YYYY-MM-DD HH:mm:ss +08
  type: '发放' | '消耗'
  scene: Scene
  delta: number // +10 / −30（全角减号展示）
  after: number // 变动后余额
  nca: string // SIM-NCA-0001（明标模拟）
  run: string // SIM-RUN-0001
}

type Scene = '签到' | '任务' | '充值' | '交付' | '结算' | '计税' | '锚认证'

const SCENES: Scene[] = ['签到', '任务', '充值', '交付', '结算', '计税', '锚认证']
const BLOCK_MSG = '积分不足，去签到或做任务'

/** 时点格式 YYYY-MM-DD HH:mm:ss +08（手动拼字段，不依赖时区库） */
function ts08(d: Date): string {
  const p = (n: number, w = 2) => String(n).padStart(w, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())} +08`
}

/** 积分面额规则（照设计件 6146，面额一个字不改） */
const RULES: { type: '发放' | '消耗'; scene: Scene; text: string }[] = [
  { type: '发放', scene: '签到', text: '签到 +10 积分／日（每日一次，断签不补）' },
  { type: '发放', scene: '任务', text: '做任务 +20 积分／件（每日 4 件）' },
  { type: '发放', scene: '充值', text: '充值面额 100／500／1000，支持自定义面额（发放路径，非改余额）' },
  { type: '发放', scene: '交付', text: '演练完成 +50 积分／次（每日一次，三步走完才算；领取入口后批接入，本批只展示规则）' },
  { type: '消耗', scene: '交付', text: '模拟交付 −30 积分／件（消耗随剧本后批，本批只展示规则）' },
  { type: '消耗', scene: '结算', text: '模拟结算按剧本额（扣款随三剧本后批，本批不扣款）' },
  { type: '消耗', scene: '计税', text: '模拟计税不额外扣（试算免费）' },
  { type: '消耗', scene: '锚认证', text: '模拟锚认证 −20 积分／次（本批唯一活消耗路径）' },
]

export function LabPage() {
  // 纯页内状态：刷新即复位，⛔ localStorage、⛔ 任何后端写入
  const [balance, setBalance] = useState(0)
  const [flows, setFlows] = useState<Flow[]>([])
  const [checkinDone, setCheckinDone] = useState(false)
  const [tasksDone, setTasksDone] = useState(0)
  const [flowSeq, setFlowSeq] = useState(0)
  const [ncaSeq, setNcaSeq] = useState(0)
  const [runNo, setRunNo] = useState('SIM-RUN-0001')
  const [blockMsg, setBlockMsg] = useState('')
  const [topupInput, setTopupInput] = useState('')
  const [taxBase, setTaxBase] = useState('')
  const [taxResult, setTaxResult] = useState<{ base: number; ratioPct: number; due: number } | null>(null)
  const [settleNote, setSettleNote] = useState('')
  const [anchorRecords, setAnchorRecords] = useState<string[]>([])
  const [typeFilter, setTypeFilter] = useState<'全部' | '发放' | '消耗'>('全部')
  const [sceneFilter, setSceneFilter] = useState<'全部' | Scene>('全部')
  const [exportNote, setExportNote] = useState('')

  function pushFlow(scene: Scene, delta: number, forceType?: '发放' | '消耗'): Flow {
    const nextFlow = flowSeq + 1
    const nextNca = ncaSeq + 1
    const f: Flow = {
      no: `SIM-FLOW-${String(nextFlow).padStart(4, '0')}`,
      time: ts08(new Date()),
      type: forceType ?? (delta >= 0 ? '发放' : '消耗'),
      scene,
      delta,
      after: balance + delta,
      nca: `SIM-NCA-${String(nextNca).padStart(4, '0')}（模拟）`,
      run: runNo,
    }
    setFlowSeq(nextFlow)
    setNcaSeq(nextNca)
    setBalance(f.after)
    setFlows((prev) => [f, ...prev])
    setBlockMsg('')
    return f
  }

  /** 负余额即拦：余额不足时出提示语，余额与流水都不动 */
  function tryConsume(scene: Scene, cost: number): boolean {
    if (balance < cost) {
      setBlockMsg(BLOCK_MSG)
      return false
    }
    pushFlow(scene, -cost)
    return true
  }

  function doCheckin() {
    if (checkinDone) {
      setBlockMsg('今日已签到，每日一次，断签不补')
      return
    }
    pushFlow('签到', 10)
    setCheckinDone(true)
  }

  function doTask() {
    if (tasksDone >= 4) {
      setBlockMsg('今日任务额度已用完（每日 4 件）')
      return
    }
    pushFlow('任务', 20)
    setTasksDone(tasksDone + 1)
  }

  function doTopup(amount: number) {
    if (!Number.isFinite(amount) || amount <= 0) return
    pushFlow('充值', Math.floor(amount))
  }

  function doAnchor() {
    if (!tryConsume('锚认证', 20)) return
    setAnchorRecords((prev) => [`模拟锚认证通过：${runNo} · 物理根为三期，演示不签发真证书`, ...prev])
  }

  function doTax() {
    const base = Number(taxBase)
    if (!Number.isFinite(base) || base <= 0) return
    const ratioPct = 2 // 示例比例，⛔ 真实税率
    setTaxResult({ base: Math.floor(base), ratioPct, due: Math.floor((base * ratioPct) / 100) })
    pushFlow('计税', 0, '消耗') // 模拟计税不额外扣（本批免费试算）
  }

  /** 每卡最新流水号；无操作显示「暂无，操作后生成」 */
  function lastNo(scene: Scene): string {
    return flows.find((f) => f.scene === scene)?.no ?? '暂无，操作后生成'
  }

  const filtered = flows.filter(
    (f) => (typeFilter === '全部' || f.type === typeFilter) && (sceneFilter === '全部' || f.scene === sceneFilter)
  )

  function exportFlows() {
    const text = filtered
      .map((f) => `${f.no}｜${f.time}｜${f.type}｜${f.scene}｜${f.delta > 0 ? `+${f.delta}` : f.delta === 0 ? '0' : `−${-f.delta}`}｜${f.after}｜${f.nca}｜${f.run}`)
      .join('\n')
    const p = navigator.clipboard?.writeText(text)
    if (p) void p.catch(() => undefined)
    setExportNote(`已复制 ${filtered.length} 行流水（复制为文本，⛔ 触发文件下载）`)
  }

  return (
    <PageShell
      title="模拟演练区"
      dataSource="纯前端演练值（页内状态）；零接口调用、零后端写入"
      permission="公开"
      description="与 /demo 分工：demo 看懂、lab 走一遍。五张模拟卡＋一张流水表；积分面额照设计件 6146，演练值不入账、不留存。"
    >
      <div data-testid="lab-page" className="space-y-6">
        {/* 页头模拟标识 */}
        <p data-testid="lab-banner" className="rounded-lg border-2 border-purple-300 bg-purple-50 p-4 text-center text-sm font-bold text-purple-800">
          演练区 · 数据为模拟值 · 非真实交易
        </p>

        {/* 会话限制句（页内显眼处，必写） */}
        <p data-testid="lab-session" className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-center text-xs font-semibold text-amber-800">
          本演示为单次会话，刷新即清空；不是你的资产，也不会保存
        </p>

        {/* 卡 1：演示钱包（发放入口：签到／做任务） */}
        <section data-testid="lab-wallet" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            演示钱包 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            演示钱包：站内虚拟积分，不可提现、不可转让、不可兑人民币
          </p>
          <p className="mt-2 text-xs text-gray-700">
            当前余额：<strong data-testid="lab-balance" className="text-gray-900">{balance}</strong> 积分
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              data-testid="lab-checkin"
              onClick={doCheckin}
              className="rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
            >
              签到 +10（每日一次）
            </button>
            <button
              data-testid="lab-task"
              onClick={doTask}
              className="rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
            >
              做任务 +20（今日 {tasksDone}/4）
            </button>
          </div>
          {checkinDone && <p className="mt-2 text-xs text-green-700">今日已签到 ✓（断签不补）</p>}
          <p className="mt-2 text-xs text-gray-500">流水号：{flows.find((f) => f.scene === '签到' || f.scene === '任务')?.no ?? '暂无，操作后生成'}</p>
          <p className="mt-1 text-xs text-gray-500">演示，不涉真实资金与真实税</p>
        </section>

        {/* 卡 2：模拟充值（发放路径：面额按钮＋自定义面额，非改余额） */}
        <section data-testid="lab-topup" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            模拟充值 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            模拟充值：点击即加积分，不发生任何真实支付
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {[100, 500, 1000].map((v) => (
              <button
                key={v}
                data-testid={`lab-topup-${v}`}
                onClick={() => doTopup(v)}
                className="rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
              >
                +{v}
              </button>
            ))}
            <input
              data-testid="lab-topup-custom"
              value={topupInput}
              onChange={(e) => setTopupInput(e.target.value)}
              placeholder="自定义面额（模拟）"
              inputMode="numeric"
              className="w-36 rounded border border-gray-300 px-2 py-1.5 text-xs"
            />
            <button
              data-testid="lab-topup-custom-go"
              onClick={() => {
                doTopup(Number(topupInput))
                setTopupInput('')
              }}
              className="rounded border border-gray-400 px-3 py-1.5 text-xs text-gray-700"
            >
              加入
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">自定义面额（模拟）属发放路径，⛔ 改余额输入框</p>
          <p className="mt-1 text-xs text-gray-500">流水号：{lastNo('充值')}</p>
          <p className="mt-1 text-xs text-gray-500">演示，不涉真实资金与真实税</p>
        </section>

        {/* 卡 3：模拟结算（本批不扣款，扣款随三剧本后批） */}
        <section data-testid="lab-settle" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            模拟结算 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            模拟结算：仅演示算法与流程，无真实资金流转
          </p>
          <button
            data-testid="lab-settle-run"
            onClick={() => {
              setSettleNote('本批演示规则与流程：结算扣款随三剧本后批，本批不扣款（如实标注）。算法路径见 /demo 模拟结算。')
              pushFlow('结算', 0, '消耗')
            }}
            className="mt-3 rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
          >
            走一遍结算流程（本批不扣款）
          </button>
          {settleNote && (
            <p data-testid="lab-settle-note" className="mt-2 text-xs text-gray-600">
              {settleNote}
            </p>
          )}
          <p className="mt-2 text-xs text-gray-500">流水号：{lastNo('结算')}</p>
          <p className="mt-1 text-xs text-gray-500">演示，不涉真实资金与真实税</p>
        </section>

        {/* 卡 4：模拟计税（试算免费，不额外扣；示例比例须标 ⛔ 真实税率） */}
        <section data-testid="lab-tax" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            模拟计税 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            模拟计税：按在册税率演算，不作任何申报依据
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <input
              data-testid="lab-tax-base"
              value={taxBase}
              onChange={(e) => setTaxBase(e.target.value)}
              placeholder="试算基数（积分）"
              inputMode="numeric"
              className="w-36 rounded border border-gray-300 px-2 py-1.5 text-xs"
            />
            <button data-testid="lab-tax-run" onClick={doTax} className="rounded bg-gray-800 px-3 py-1.5 text-xs text-white">
              免费试算
            </button>
            <span className="text-xs font-semibold text-amber-700">示例比例，⛔ 真实税率</span>
          </div>
          {taxResult && (
            <p data-testid="lab-tax-result" className="mt-2 text-xs text-gray-600">
              基数 {taxResult.base} 积分 × 示例比例 {taxResult.ratioPct}% ＝ 试算额 {taxResult.due} 积分（模拟，不额外扣、不作申报依据）
            </p>
          )}
          <p className="mt-2 text-xs text-gray-500">流水号：{lastNo('计税')}</p>
          <p className="mt-1 text-xs text-gray-500">演示，不涉真实资金与真实税</p>
        </section>

        {/* 卡 5：模拟锚认证（本批唯一活消耗路径 −20／次；负余额即拦） */}
        <section data-testid="lab-anchor" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            模拟锚认证 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            模拟认证：物理根为三期，演示不签发真证书
          </p>
          <button data-testid="lab-anchor-run" onClick={doAnchor} className="mt-3 rounded bg-gray-800 px-3 py-1.5 text-xs text-white">
            发起模拟锚认证（−20 积分／次）
          </button>
          {blockMsg && (
            <p data-testid="lab-block-msg" className="mt-2 text-xs font-bold text-red-600">
              {blockMsg}
            </p>
          )}
          {anchorRecords.length > 0 && (
            <ul data-testid="lab-anchor-records" className="mt-2 list-inside list-disc space-y-0.5 text-xs text-gray-600">
              {anchorRecords.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}
          <p className="mt-2 text-xs text-gray-500">流水号：{lastNo('锚认证')}</p>
          <p className="mt-1 text-xs text-gray-500">演示，不涉真实资金与真实税</p>
        </section>

        {/* 积分面额规则表（照设计件 6146，面额一个字不改） */}
        <section data-testid="lab-rules" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            积分面额规则（照设计件 6146） <SimulatedBadge nature="simulated" />
          </h3>
          <table className="w-full border-collapse">
            <tbody>
              {RULES.map((r, i) => (
                <tr key={i}>
                  <td className="w-14 border border-gray-200 px-2 py-1 text-xs">{r.type}</td>
                  <td className="border border-gray-200 px-2 py-1 text-xs text-gray-700">{r.text}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-gray-600">两条硬规矩：① 负余额即拦，提示语逐字「{BLOCK_MSG}」；② ⛔ 出「改余额」输入框。</p>
        </section>

        {/* 流水表：八字段全值；按类型／场景筛；导出＝复制为文本 */}
        <section data-testid="lab-ledger" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            流水表 <SimulatedBadge nature="simulated" />
          </h3>
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-gray-500">类型：</span>
            {(['全部', '发放', '消耗'] as const).map((t) => (
              <button
                key={t}
                data-testid={`lab-filter-type-${t}`}
                onClick={() => setTypeFilter(t)}
                className={`rounded-full border px-2 py-0.5 ${typeFilter === t ? 'border-purple-400 bg-purple-100 text-purple-800' : 'border-gray-300 text-gray-600'}`}
              >
                {t}
              </button>
            ))}
            <span className="ml-2 text-gray-500">场景：</span>
            {(['全部', ...SCENES] as const).map((s) => (
              <button
                key={s}
                data-testid={`lab-filter-scene-${s}`}
                onClick={() => setSceneFilter(s)}
                className={`rounded-full border px-2 py-0.5 ${sceneFilter === s ? 'border-purple-400 bg-purple-100 text-purple-800' : 'border-gray-300 text-gray-600'}`}
              >
                {s}
              </button>
            ))}
            <button
              data-testid="lab-export"
              onClick={exportFlows}
              className="ml-auto rounded bg-gray-800 px-3 py-1 text-xs text-white"
            >
              导出（复制为文本）
            </button>
          </div>
          {exportNote && <p data-testid="lab-export-note" className="mb-2 text-xs text-green-700">{exportNote}</p>}
          {filtered.length === 0 ? (
            <p data-testid="lab-ledger-empty" className="text-xs text-gray-500">
              还没有流水 —— 先签到，或点开任意一卡试一次
            </p>
          ) : (
            <table data-testid="lab-ledger-table" className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-50 text-left text-xs text-gray-600">
                  <th className="border border-gray-200 px-2 py-1">流水号</th>
                  <th className="border border-gray-200 px-2 py-1">时点</th>
                  <th className="border border-gray-200 px-2 py-1">类型</th>
                  <th className="border border-gray-200 px-2 py-1">来源或场景</th>
                  <th className="border border-gray-200 px-2 py-1">变动值</th>
                  <th className="border border-gray-200 px-2 py-1">变动后余额</th>
                  <th className="border border-gray-200 px-2 py-1">关联 NCA 号</th>
                  <th className="border border-gray-200 px-2 py-1">演练编号</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((f) => (
                  <tr key={f.no} data-testid={`lab-flow-${f.no}`} className="text-xs text-gray-700">
                    <td className="border border-gray-200 px-2 py-1">{f.no}</td>
                    <td className="border border-gray-200 px-2 py-1">{f.time}</td>
                    <td className="border border-gray-200 px-2 py-1">{f.type}</td>
                    <td className="border border-gray-200 px-2 py-1">{f.scene}</td>
                    <td className="border border-gray-200 px-2 py-1">{f.delta > 0 ? `+${f.delta}` : f.delta === 0 ? '0' : `−${-f.delta}`}</td>
                    <td className="border border-gray-200 px-2 py-1">{f.after}</td>
                    <td className="border border-gray-200 px-2 py-1">{f.nca}</td>
                    <td className="border border-gray-200 px-2 py-1">{f.run}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </PageShell>
  )
}
