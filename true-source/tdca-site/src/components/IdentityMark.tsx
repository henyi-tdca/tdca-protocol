// =============================================================================
// TDCA 制度水印
// 目标函数: 可信锚点栏 · 身份维呈现（批 1 纯前端：注册选锚段／我的账户当前锚栏／协作方查看处）
// 制度锚点: 四档名原样引用（固锚级／移锚级／记名级／未达门槛）＋ 通知机锚如实标「模拟态」
//          ＋ 实名＋手机号锚标「待建」＋ 档位标「记名级 · 待补」＋ 协作可信维本批不上站
// 约束: 只述档名与事实，⛔ 不写可信／不可信结论、⛔ 不做评价物（无分数／等级／星标）
// =============================================================================
import { useState } from 'react'

/** 首批可选锚点（两选项；五字段：锚名／档位／现物状态／可得能力／核验方式） */
export interface AnchorOption {
  key: string
  name: string
  tier: string
  status: string
  capability: string
  verify: string
  /** 模拟态锚之说明句（点击展开；不得表述为已实机／已可核） */
  simulatedNote?: string
}

export const ANCHOR_OPTIONS: AnchorOption[] = [
  {
    key: 'notifier',
    name: '通知机锚',
    tier: '固锚级',
    status: '模拟态 · 预留',
    capability: '预留——现为模拟态，本批不发任何令牌',
    verify: '待实机后可核（设备唯一 ＋ 物理地址保持）',
    simulatedNote:
      '现为模拟态：演示性质，非已实机、非已可核；达标实机后方为可用之锚。',
  },
  {
    key: 'realname-phone',
    name: '实名 ＋ 手机号锚',
    tier: '记名级',
    status: '待建',
    capability: '访问令牌 ＋ 受限执行令牌（写操作须人类签发）——接入待建',
    verify: '实名 ＋ 手机号核验——待建',
  },
]

/** 免责句（对外口径，涉协作风险自担；一字不动） */
export const IDENTITY_DISCLAIMER =
  '本标识仅述锚点身份等级，供责任追溯参考；协作风险由协作方自担。'

/** 协作可信维度本批不上站之注明 */
export const COLLAB_TRUST_PENDING_NOTE =
  '协作可信维度待口径确立后另批呈现。'

/** 当前账号档位如实标（有账号、未实名：目标档＝记名级，态＝待补） */
export const CURRENT_TIER_LABEL = '记名级 · 待补'

/** 注册页「选择你的身份锚」段：选项卡单选＋选中显摘要（本批仅呈现与本地暂存） */
export function AnchorSelectSection() {
  const [selected, setSelected] = useState<string>('realname-phone')
  const [showNote, setShowNote] = useState(false)
  const cur = ANCHOR_OPTIONS.find((a) => a.key === selected) ?? ANCHOR_OPTIONS[1]
  return (
    <div data-testid="register-anchor" className="space-y-2 rounded border border-slate-200 bg-white p-3">
      <div className="text-xs font-semibold text-gray-700">选择你的身份锚（注册即缔约之一环）</div>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        {ANCHOR_OPTIONS.map((a) => (
          <label
            key={a.key}
            data-testid={`anchor-opt-${a.key}`}
            className={`block cursor-pointer rounded border p-2.5 text-xs ${
              selected === a.key ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 bg-white'
            }`}
          >
            <div className="flex items-center gap-2">
              <input
                type="radio"
                name="anchor-choice"
                checked={selected === a.key}
                onChange={() => setSelected(a.key)}
                data-testid={`anchor-radio-${a.key}`}
              />
              <span className="font-medium text-gray-800">{a.name}</span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">{a.tier}</span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                  a.key === 'notifier' ? 'bg-purple-100 text-purple-700' : 'bg-amber-100 text-amber-700'
                }`}
                data-testid={`anchor-status-${a.key}`}
              >
                {a.key === 'notifier' ? '模拟态' : a.status}
              </span>
            </div>
            <div className="mt-1.5 space-y-0.5 text-[11px] text-gray-600">
              <div>现物状态：{a.status}</div>
              <div>可得能力：{a.capability}</div>
              <div>核验方式：{a.verify}</div>
              {a.simulatedNote && (
                <button
                  type="button"
                  data-testid="anchor-sim-note-toggle"
                  className="mt-0.5 text-purple-700 underline"
                  onClick={(e) => {
                    e.preventDefault()
                    setShowNote((v) => !v)
                  }}
                >
                  {showNote ? '收起说明' : '什么是模拟态？'}
                </button>
              )}
            </div>
          </label>
        ))}
      </div>
      {cur.simulatedNote && showNote && (
        <div data-testid="anchor-sim-note" className="rounded border border-purple-200 bg-purple-50 px-3 py-2 text-[11px] text-purple-800">
          {cur.simulatedNote}
        </div>
      )}
      <div data-testid="anchor-summary" className="rounded border border-emerald-200 bg-emerald-50 px-3 py-2 text-[11px] text-emerald-900">
        已选：{cur.name}（{cur.tier}／{cur.status}）。本页仅作呈现；选择暂不生效，待登记通道开通后方随缔约存证记录。
      </div>
      <p className="text-[11px] text-gray-500">{IDENTITY_DISCLAIMER}</p>
    </div>
  )
}

/** 身份维标识卡（我的账户当前锚栏 ／ 协作方查看处共用；只述档名与事实） */
export function IdentityMarkCard({
  testid,
  heading,
  showPendingNote = false,
}: {
  testid: string
  heading: string
  showPendingNote?: boolean
}) {
  return (
    <div data-testid={testid} className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="text-xs text-gray-500">{heading}</div>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-gray-800">实名 ＋ 手机号锚</span>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{CURRENT_TIER_LABEL}</span>
        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700">待建</span>
      </div>
      <p className="mt-1 text-[11px] text-gray-500">
        现物状态：实名与手机号锚定待建；本标识仅述身份维，供协作方查看。
      </p>
      {showPendingNote && (
        <p data-testid="collab-trust-pending" className="mt-1 text-[11px] text-gray-400">
          {COLLAB_TRUST_PENDING_NOTE}
        </p>
      )}
      <p className="mt-1 text-[11px] text-gray-500">{IDENTITY_DISCLAIMER}</p>
    </div>
  )
}
