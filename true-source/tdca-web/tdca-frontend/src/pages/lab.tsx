// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B26 · 模拟演练区一页（批2.6 前＋后）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B26-001（6194·前五卡流水）＋ TDCA-HANDOFF-EXEC-L1SI175-B26-003（6206·后三剧本）
//   口径照 TDCA-RULING-L1SI175-B26-002（6205）；积分面额照设计件 6146 §四；纯前端零后端
//   （页内 useState，⛔ localStorage、⛔ 接口、⛔ 后端）
// 红线: 五卡必带文案逐字；负余额即拦（提示语逐字「积分不足，去签到或做任务」）；
//   ⛔ 任何金额字样（¥／￥／元／价格／档位／付费），单位只用「积分」；税率处必标「示例比例，⛔ 真实税率」；
//   小数允许一位（120 × 2% = 2.4），⛔ 四舍五入成整数；单据复制为文本、不触发文件下载；
//   S3 哈希用 crypto.subtle.digest('SHA-256') 真算，⛔ 写死假串，环境不支持须明示；锚四档照在册
//   （TDCA-PUB-CORPUS-046：固锚级／移锚级／记名级／未达门槛）；零内部编号；会话限制句必写
// =============================================================================
import { useState } from 'react'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

/** 流水一条：八字段全值（流水号／时点／类型／来源或场景／变动值／变动后余额／关联 NCA 号／演练编号） */
interface Flow {
  no: string // SIM-FLOW-0001（四位序）
  time: string // YYYY-MM-DD HH:mm:ss +08
  type: '发放' | '消耗' | '不计量'
  scene: Scene
  delta: number // +10 / −30 / −2.4（全角减号展示）
  after: number // 变动后余额
  nca: string // SIM-NCA-0001（明标模拟）
  run: string // SIM-RUN-0001
}

type Scene = '签到' | '任务' | '充值' | '交付' | '结算' | '计税' | '锚认证' | '跨域引用'

const SCENES: Scene[] = ['签到', '任务', '充值', '交付', '结算', '计税', '锚认证', '跨域引用']
const BLOCK_MSG = '积分不足，去签到或做任务'
const TAX_RATIO_PCT = 2 // 示例比例，⛔ 真实税率（在册调度税默认档 T-031）

/** 积分展示：整数不带小数点，一位小数保留一位（87.6） */
function fmt(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(1)
}

/** 锚四档（照在册 TDCA-PUB-CORPUS-046 定名与判定语，⛔ 自造档名；「待补」为过渡态非档位，不入四档） */
const ANCHOR_TIERS = [
  { name: '固锚级', desc: '设备唯一且物理地址保持' },
  { name: '移锚级', desc: '设备唯一但物理地址可移' },
  { name: '记名级', desc: '设备非唯一但持有注册实名认证账号' },
  { name: '未达门槛', desc: '匿名（不称「不可信」；匿名不等于没有身份）' },
]

/** 时点格式 YYYY-MM-DD HH:mm:ss +08（手动拼字段，不依赖时区库） */
function ts08(d: Date): string {
  const p = (n: number, w = 2) => String(n).padStart(w, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())} +08`
}

/** 积分面额规则（照设计件 6146 与在册口径，面额一个字不改） */
const RULES: { type: '发放' | '消耗' | '不计量'; scene: Scene; text: string }[] = [
  { type: '发放', scene: '签到', text: '签到 +10 积分／日（每日一次，断签不补）' },
  { type: '发放', scene: '任务', text: '做任务 +20 积分／件（每日 4 件）' },
  { type: '发放', scene: '充值', text: '充值面额 100／500／1000，支持自定义面额（发放路径，非改余额）' },
  { type: '发放', scene: '交付', text: '演练完成 +50 积分／次（每日一次，三步走完才算；领取入口后续批次接入，本批只展示规则）' },
  { type: '消耗', scene: '交付', text: '模拟交付 −30 积分／件（剧本一 步 1 已开通）' },
  { type: '消耗', scene: '结算', text: '模拟结算额 120 积分（剧本一环销：乙 −120／甲 +120，已开通）' },
  { type: '消耗', scene: '计税', text: '剧本一内按示例比例 2% 演算调度税（120 × 2% = 2.4）；本页独立试算仍免费' },
  { type: '消耗', scene: '锚认证', text: '模拟锚认证 −20 积分／次（剧本二：选等级＋设备／令牌／见证三要素）' },
  { type: '不计量', scene: '跨域引用', text: '跨域引用不扣积分（剧本三：只传哈希与件名，⛔ 传内容；类型记「不计量」）' },
]

interface Receipt {
  ordNo: string // SIM-ORD-0001
  kind: '结算单' | '税单'
  text: string
}

export function LabPage() {
  // 纯页内状态：刷新即复位，⛔ localStorage、⛔ 任何后端写入
  const [balance, setBalance] = useState(0)
  const [flows, setFlows] = useState<Flow[]>([])
  const [checkinDone, setCheckinDone] = useState(false)
  const [tasksDone, setTasksDone] = useState(0)
  const [flowSeq, setFlowSeq] = useState(0)
  const [ncaSeq, setNcaSeq] = useState(0)
  const [ordSeq, setOrdSeq] = useState(0)
  const [linkSeq, setLinkSeq] = useState(0)
  const [runNo] = useState('SIM-RUN-0001')
  const [blockMsg, setBlockMsg] = useState('')
  const [topupInput, setTopupInput] = useState('')
  const [taxBase, setTaxBase] = useState('')
  const [taxResult, setTaxResult] = useState<{ base: number; ratioPct: number; due: number } | null>(null)
  const [settleNote, setSettleNote] = useState('')
  const [anchorRecords, setAnchorRecords] = useState<string[]>([])
  const [typeFilter, setTypeFilter] = useState<'全部' | '发放' | '消耗' | '不计量'>('全部')
  const [sceneFilter, setSceneFilter] = useState<'全部' | Scene>('全部')
  const [exportNote, setExportNote] = useState('')
  // 剧本一：交付 → 结算 → 计税（步 0~4）
  const [s1Step, setS1Step] = useState(0)
  const [s1Receipts, setS1Receipts] = useState<Receipt[]>([])
  const [s1CopyNote, setS1CopyNote] = useState('')
  // 剧本二：模拟锚认证（等级四档＋三要素）
  const [s2Tier, setS2Tier] = useState('')
  const [s2Device, setS2Device] = useState(true)
  const [s2Token, setS2Token] = useState(true)
  const [s2Witness, setS2Witness] = useState(true)
  const [s2Records, setS2Records] = useState<string[]>([])
  // 剧本 S3：跨域引用（哈希真算）
  const [s3Name, setS3Name] = useState('示例件 A')
  const [s3Content, setS3Content] = useState('模拟交付件内容（算法真算、数据假）')
  const [s3Hash, setS3Hash] = useState('')
  const [s3Link, setS3Link] = useState('')
  const [s3Stage, setS3Stage] = useState<'idle' | 'generated' | 'verified' | 'unsupported'>('idle')

  function pushFlow(scene: Scene, delta: number, forceType?: '发放' | '消耗' | '不计量'): Flow {
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

  /** 卡 5 速通路径（2.6-前已上线，本批不动其行为） */
  function doAnchor() {
    if (!tryConsume('锚认证', 20)) return
    setAnchorRecords((prev) => [`模拟锚认证通过：${runNo} · 物理根为三期，演示不签发真证书`, ...prev])
  }

  function doTax() {
    const base = Number(taxBase)
    if (!Number.isFinite(base) || base <= 0) return
    const ratioPct = TAX_RATIO_PCT // 示例比例，⛔ 真实税率
    setTaxResult({ base: Math.floor(base), ratioPct, due: Math.floor((base * ratioPct) / 100) })
    pushFlow('计税', 0, '消耗') // 独立试算免费
  }

  // ---------- 剧本 S1：交付 → 结算 → 计税 ----------
  const S1_SETTLE_AMOUNT = 120 // 照设计件 6146 §四 S1 步 2，⛔ 改数
  const S1_DELIVER_COST = 30 // 照设计件 6146 §2.2，⛔ 改数
  const S1_TAX = (S1_SETTLE_AMOUNT * TAX_RATIO_PCT) / 100 // 2.4

  function s1Deliver() {
    if (!tryConsume('交付', S1_DELIVER_COST)) return
    setS1Step(1)
  }

  function s1Settle() {
    pushFlow('结算', S1_SETTLE_AMOUNT, '发放') // 甲 +120；乙 −120 为对侧模拟，不入本方账本
    setS1Step(2)
  }

  function s1Tax() {
    pushFlow('计税', -S1_TAX) // 甲 −2.4（示例比例，⛔ 真实税率）
    setS1Step(3)
  }

  function s1Issue() {
    const no1 = `SIM-ORD-${String(ordSeq + 1).padStart(4, '0')}`
    const no2 = `SIM-ORD-${String(ordSeq + 2).padStart(4, '0')}`
    setOrdSeq(ordSeq + 2)
    setS1Receipts([
      {
        ordNo: no2,
        kind: '税单',
        text: [`模拟税单 ${no2}`, `演练编号 ${runNo}`, `计税基数 ${S1_SETTLE_AMOUNT} 积分`, `示例比例 ${TAX_RATIO_PCT}%（⛔ 真实税率）`, `税额 ${fmt(S1_TAX)} 积分（120 × 2% = 2.4）`, '演示，不涉真实资金与真实税'].join('\n'),
      },
      {
        ordNo: no1,
        kind: '结算单',
        text: [`模拟结算单 ${no1}`, `演练编号 ${runNo}`, `环销结算额 ${S1_SETTLE_AMOUNT} 积分（乙 −120／甲 +120，对侧为模拟）`, 'SIMULATED · 复制为文本，不触发文件下载'].join('\n'),
      },
    ])
    setS1Step(4)
  }

  function copyReceipt(r: Receipt) {
    const p = navigator.clipboard?.writeText(r.text)
    if (p) void p.catch(() => undefined)
    setS1CopyNote(`${r.kind} ${r.ordNo} 已复制（复制为文本，不触发文件下载）`)
  }

  // ---------- 剧本 S2：模拟锚认证（选等级＋三要素，可不过） ----------
  function s2Run() {
    if (!s2Tier) {
      setBlockMsg('请先选择锚等级（四档，档名以在册为准）')
      return
    }
    if (!tryConsume('锚认证', 20)) return
    const missing: string[] = []
    if (!s2Device) missing.push('设备要素')
    if (!s2Token) missing.push('令牌要素')
    if (!s2Witness) missing.push('见证要素')
    if (missing.length > 0) {
      setS2Records((prev) => [`模拟不通过：缺${missing.join('、')} · ${s2Tier} · ${runNo}`, ...prev])
      return
    }
    setS2Records((prev) => [`模拟通过：${s2Tier} · ${runNo} · 三期换真根（SIMULATED）`, ...prev])
  }

  // ---------- 剧本三：跨域引用（哈希真算，⛔ 写死假串） ----------
  async function sha256Hex(content: string): Promise<string | null> {
    if (!globalThis.crypto?.subtle) return null
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(content))
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
  }

  function s3Generate() {
    if (!s3Content.trim()) return
    void (async () => {
      // 哈希覆盖范围：件名 + 换行 + 正文（分隔符固定为换行一种；换件名即改哈希，消「同名异件」歧义）
      const covered = `${s3Name}\n${s3Content}`
      const hex = await sha256Hex(covered)
      if (hex === null) {
        setS3Stage('unsupported')
        return
      }
      const link = `SIM-LINK-${String(linkSeq + 1).padStart(4, '0')}`
      setLinkSeq(linkSeq + 1)
      setS3Hash(hex)
      setS3Link(link)
      setS3Stage('generated')
      pushFlow('跨域引用', 0, '不计量') // 生成即留痕，零额不计量（⛔ 标消耗）
    })()
  }

  function s3Verify() {
    void (async () => {
      const covered = `${s3Name}\n${s3Content}`
      const hex = await sha256Hex(covered)
      if (hex === null) {
        setS3Stage('unsupported')
        return
      }
      // 真比对：公域只读验哈希，⛔ 搬内容
      if (hex === s3Hash) setS3Stage('verified')
    })()
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
      .map((f) => `${f.no}｜${f.time}｜${f.type}｜${f.scene}｜${f.delta > 0 ? `+${fmt(f.delta)}` : f.delta === 0 ? '0' : `−${fmt(-f.delta)}`}｜${fmt(f.after)}｜${f.nca}｜${f.run}`)
      .join('\n')
    const p = navigator.clipboard?.writeText(text)
    if (p) void p.catch(() => undefined)
    setExportNote(`已复制 ${filtered.length} 行流水（复制为文本，不触发文件下载）`)
  }

  return (
    <PageShell
      title="模拟演练区"
      dataSource="纯前端演练值（页内状态）；零接口调用、零后端写入"
      permission="公开"
      description="与 /demo 分工：demo 看懂、lab 走一遍。五张模拟卡＋三段剧本＋一张流水表；积分面额照设计件 6146，演练值不入账、不留存。"
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

        {/* 拦截／提示语横幅（全页共用一处，负余额即拦逐字「积分不足，去签到或做任务」） */}
        {blockMsg && (
          <p data-testid="lab-block-msg" className="rounded-lg border border-red-300 bg-red-50 p-2 text-center text-xs font-bold text-red-600">
            {blockMsg}
          </p>
        )}

        {/* 卡 1：演示钱包（发放入口：签到／做任务） */}
        <section data-testid="lab-wallet" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            演示钱包 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            演示钱包：站内虚拟积分，不可提现、不可转让、不可兑人民币
          </p>
          <p className="mt-2 text-xs text-gray-700">
            当前余额：<strong data-testid="lab-balance" className="text-gray-900">{fmt(balance)}</strong> 积分
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

        {/* 卡 3：模拟结算（独立试流程；剧本 S1 的环销扣款见下方剧本区） */}
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
              setSettleNote('独立流程演示：环销扣款走下方剧本一（额 120，照设计件）。算法路径见 /demo 模拟结算。')
              pushFlow('结算', 0, '消耗')
            }}
            className="mt-3 rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
          >
            走一遍结算流程（独立演示，不扣款）
          </button>
          {settleNote && (
            <p data-testid="lab-settle-note" className="mt-2 text-xs text-gray-600">
              {settleNote}
            </p>
          )}
          <p className="mt-2 text-xs text-gray-500">流水号：{lastNo('结算')}</p>
          <p className="mt-1 text-xs text-gray-500">演示，不涉真实资金与真实税</p>
        </section>

        {/* 卡 4：模拟计税（独立试算免费；剧本 S1 的 2.4 演算见下方剧本区） */}
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

        {/* 卡 5：模拟锚认证（速通路径 −20／次；剧本 S2 的等级＋三要素见下方剧本区） */}
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
          <p className="mt-2 text-xs text-gray-600">每次尝试计 20 积分，无论通过与否（按次计，照设计件 6146 §2.2）。</p>
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

        {/* 积分面额规则表（照设计件 6146 与在册口径，面额一个字不改） */}
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

        {/* 选剧本区：三段能走完的剧本（2.6-后新增，各 entry 可展开） */}
        <section data-testid="lab-scripts" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            选一段剧本开始 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="mb-3 text-xs text-gray-600">
            三段剧本把「加积分 → 花积分 → 出单据 → 留痕」连成一条路；算法真、数据假。积分变动照常记入下方流水表。
          </p>

          {/* 剧本 S1：交付 → 结算 → 计税（一条直线） */}
          <details data-testid="lab-s1" className="mb-3 rounded-lg border border-gray-200">
            <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-gray-800">
              剧本一 · 交付 → 结算 → 计税（一条直线，四步走完）
            </summary>
            <div className="space-y-2 border-t border-gray-100 p-3 text-xs text-gray-700">
              <p>① 甲把一件素材交付给乙（模拟）−30 积分 → ② 双方确认发起环销结算 +120 积分（乙 −120 为对侧模拟）→ ③ 按示例比例 {TAX_RATIO_PCT}% 演算调度税 −2.4 积分 → ④ 出模拟结算单＋模拟税单（单号可回查）。</p>
              <p className="font-semibold text-amber-700">示例比例 {TAX_RATIO_PCT}%，⛔ 真实税率</p>
              <ol className="list-inside list-decimal space-y-1">
                <li>
                  <button data-testid="lab-s1-deliver" onClick={s1Deliver} disabled={s1Step !== 0} className="rounded bg-gray-800 px-3 py-1 text-xs text-white disabled:bg-gray-300">
                    步 1 · 模拟交付给乙（−30 积分）
                  </button>
                  {s1Step >= 1 && <span className="ml-2 text-green-700">✓ 已交付，流水已记</span>}
                </li>
                <li>
                  <button data-testid="lab-s1-settle" onClick={s1Settle} disabled={s1Step !== 1} className="rounded bg-gray-800 px-3 py-1 text-xs text-white disabled:bg-gray-300">
                    步 2 · 双方确认并环销结算（+120 积分）
                  </button>
                  {s1Step >= 2 && <span className="ml-2 text-green-700">✓ 已结算（乙 −120 对侧模拟）</span>}
                </li>
                <li>
                  <button data-testid="lab-s1-tax" onClick={s1Tax} disabled={s1Step !== 2} className="rounded bg-gray-800 px-3 py-1 text-xs text-white disabled:bg-gray-300">
                    步 3 · 演算调度税（120 × {TAX_RATIO_PCT}% = 2.4，−2.4 积分）
                  </button>
                  {s1Step >= 3 && <span className="ml-2 text-green-700">✓ 已演算（一位小数，⛔ 四舍五入）</span>}
                </li>
                <li>
                  <button data-testid="lab-s1-issue" onClick={s1Issue} disabled={s1Step !== 3} className="rounded bg-gray-800 px-3 py-1 text-xs text-white disabled:bg-gray-300">
                    步 4 · 出模拟结算单＋模拟税单
                  </button>
                  {s1Step >= 4 && <span className="ml-2 text-green-700">✓ 两单已出，可复制</span>}
                </li>
              </ol>
              {s1Receipts.length > 0 && (
                <div data-testid="lab-s1-receipts" className="space-y-2">
                  {s1Receipts.map((r) => (
                    <div key={r.ordNo} className="rounded border border-gray-200 bg-gray-50 p-2">
                      <pre data-testid={`lab-s1-receipt-${r.kind}`} className="whitespace-pre-wrap text-[11px] text-gray-700">{r.text}</pre>
                      <button data-testid={`lab-s1-copy-${r.kind}`} onClick={() => copyReceipt(r)} className="mt-1 rounded border border-gray-400 px-2 py-0.5 text-[11px] text-gray-700">
                        复制{r.kind}（复制为文本，不触发文件下载）
                      </button>
                    </div>
                  ))}
                  {s1CopyNote && <p data-testid="lab-s1-copy-note" className="text-[11px] text-green-700">{s1CopyNote}</p>}
                </div>
              )}
            </div>
          </details>

          {/* 剧本 S2：通知机模拟锚认证（等级四档＋三要素，必须能不通过） */}
          <details data-testid="lab-s2" className="mb-3 rounded-lg border border-gray-200">
            <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-gray-800">
              剧本二 · 通知机模拟锚认证（选等级＋设备／令牌／见证三要素）
            </summary>
            <div className="space-y-2 border-t border-gray-100 p-3 text-xs text-gray-700">
              <p>
                步 1 选锚等级（四档，照在册 TDCA-PUB-CORPUS-046 定名，档名以在册为准）→ 步 2 走模拟认证（设备／令牌／见证三要素，缺一即「模拟不通过＋原因」）→ 步 3 出模拟认证记录（SIMULATED＋三期换真根）。
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-gray-500">锚等级：</span>
                {ANCHOR_TIERS.map((t) => (
                  <button
                    key={t.name}
                    data-testid={`lab-s2-tier-${t.name}`}
                    onClick={() => setS2Tier(t.name)}
                    className={`rounded-full border px-2 py-0.5 ${s2Tier === t.name ? 'border-purple-400 bg-purple-100 text-purple-800' : 'border-gray-300 text-gray-600'}`}
                  >
                    {t.name}
                  </button>
                ))}
              </div>
              {s2Tier && (
                <p data-testid="lab-s2-tier-desc" className="text-gray-600">
                  {s2Tier}：{ANCHOR_TIERS.find((t) => t.name === s2Tier)?.desc}
                </p>
              )}
              <ul data-testid="lab-s2-tier-descs" className="list-inside list-disc space-y-0.5 rounded border border-gray-100 bg-gray-50 p-2 text-gray-600">
                {ANCHOR_TIERS.map((t) => (
                  <li key={t.name}>
                    <strong>{t.name}</strong>：{t.desc}
                  </li>
                ))}
              </ul>
              <p className="text-gray-500">四档定名与判定语照在册 TDCA-PUB-CORPUS-046，档名以在册为准；「待补」为过渡态，非档。</p>
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-1">
                  <input data-testid="lab-s2-elem-device" type="checkbox" checked={s2Device} onChange={(e) => setS2Device(e.target.checked)} /> 设备要素
                </label>
                <label className="flex items-center gap-1">
                  <input data-testid="lab-s2-elem-token" type="checkbox" checked={s2Token} onChange={(e) => setS2Token(e.target.checked)} /> 令牌要素
                </label>
                <label className="flex items-center gap-1">
                  <input data-testid="lab-s2-elem-witness" type="checkbox" checked={s2Witness} onChange={(e) => setS2Witness(e.target.checked)} /> 见证要素
                </label>
              </div>
              <button data-testid="lab-s2-run" onClick={s2Run} className="rounded bg-gray-800 px-3 py-1 text-xs text-white">
                发起模拟锚认证（−20 积分／次）
              </button>
              {s2Records.length > 0 && (
                <ul data-testid="lab-s2-records" className="list-inside list-disc space-y-0.5 text-gray-600">
                  {s2Records.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          </details>

          {/* 剧本 S3：跨域引用（哈希真算 SHA-256，只引哈希 ⛔ 搬内容） */}
          <details data-testid="lab-s3" className="rounded-lg border border-gray-200">
            <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-gray-800">
              剧本三 · 跨域引用（接 NCA 两域一致，哈希真算）
            </summary>
            <div className="space-y-2 border-t border-gray-100 p-3 text-xs text-gray-700">
              <p>步 1 私域沙盒生成一枚 NCA（simulated，有链位与自哈希）→ 步 2 交「件＋哈希」给公域，公域只读验 → 步 3 公域出「已验」标记（只引哈希，⛔ 搬内容）。哈希用浏览器内置 SHA-256 真算，⛔ 写死假串。</p>
              <p className="text-gray-500">哈希覆盖范围：件名＋换行＋正文（分隔符固定为换行一种；换件名即改哈希，消「同名异件」歧义）。</p>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  data-testid="lab-s3-name"
                  value={s3Name}
                  onChange={(e) => setS3Name(e.target.value)}
                  placeholder="件名"
                  className="w-32 rounded border border-gray-300 px-2 py-1 text-xs"
                />
              </div>
              <textarea
                data-testid="lab-s3-content"
                value={s3Content}
                onChange={(e) => setS3Content(e.target.value)}
                rows={2}
                className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
              />
              <div className="flex flex-wrap gap-2">
                <button data-testid="lab-s3-generate" onClick={s3Generate} className="rounded bg-gray-800 px-3 py-1 text-xs text-white">
                  步 1 · 私域沙盒生成 NCA
                </button>
                <button data-testid="lab-s3-verify" onClick={s3Verify} disabled={s3Stage === 'idle' || s3Stage === 'unsupported'} className="rounded bg-gray-800 px-3 py-1 text-xs text-white disabled:bg-gray-300">
                  步 2 · 交给公域只读验
                </button>
              </div>
              {s3Stage === 'unsupported' && (
                <p data-testid="lab-s3-unsupported" className="font-semibold text-red-600">
                  本环境不支持真算（无 crypto.subtle）——⛔ 静默退回假串，本剧本在此环境停步。
                </p>
              )}
              {s3Stage !== 'idle' && s3Stage !== 'unsupported' && (
                <div data-testid="lab-s3-public" className="rounded border border-gray-200 bg-gray-50 p-2">
                  <p>公域侧（只显示哈希与件名，⛔ 搬内容）：</p>
                  <p>件名：{s3Name}</p>
                  <p data-testid="lab-s3-link">链位：{s3Link}（simulated）</p>
                  <p data-testid="lab-s3-hash" className="break-all">自哈希（SHA-256 真算）：{s3Hash}</p>
                  <p data-testid="lab-s3-verdict" className="font-semibold">
                    {s3Stage === 'verified' ? '已验 ✓ 两域互认（哈希吻合）' : '待公域验哈希'}
                  </p>
                </div>
              )}
            </div>
          </details>
        </section>

        {/* 流水表：八字段全值；按类型／场景筛；导出＝复制为文本 */}
        <section data-testid="lab-ledger" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            流水表 <SimulatedBadge nature="simulated" />
          </h3>
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-gray-500">类型：</span>
            {(['全部', '发放', '消耗', '不计量'] as const).map((t) => (
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
                    <td className="border border-gray-200 px-2 py-1">{f.delta > 0 ? `+${fmt(f.delta)}` : f.delta === 0 ? '0' : `−${fmt(-f.delta)}`}</td>
                    <td className="border border-gray-200 px-2 py-1">{fmt(f.after)}</td>
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
