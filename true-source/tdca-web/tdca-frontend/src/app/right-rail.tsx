// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批1 — 右栏「我的」＋站内 AI 助手会话框骨架
// 约束矩阵: TDCA-HANDOFF-SITE-PHASE2-REVAMP-001 §二.3／§四批1（助手为意图直达栏升级位；正式移植批3）
//          应答口径：TDCA-SPEC-AI-ASSISTANT-ANSWER-001（真 AI＋规则表兜底；路由白名单强制纠正）
// =============================================================================
import { useState } from 'react'
import { NavLink } from 'react-router'
import { useAuth } from './auth-context'
import { api } from '@/api/client'

interface ChatMsg {
  role: 'user' | 'assistant'
  text: string
  route?: string
}

/** 私域栏目（二期改版批2块一）：属于我的操作权限的栏目在「我的」界面显示（⛔ 不入公域导航） */
const PRIVATE_NAV: { to: string; label: string }[] = [
  { to: '/studio', label: '作业' },
  { to: '/workbuddy', label: '人机协作' },
  { to: '/attestation', label: '确权中心' },
  { to: '/attestation/meta', label: '元函数确权' },
  { to: '/attestation/dynamic', label: '动态确权' },
  { to: '/cluster', label: '集群编排' },
  { to: '/ownership-registry', label: '权属登记' },
  { to: '/authorization-registry', label: '合约备案' },
  { to: '/use/upload', label: '交素材' }, // L1SI182-USE-U2-001：U-2 起步页（创始人裁定：入口挂私域我的·确权栏目）
  { to: '/use/agent', label: '代办登记' }, // L1SI182-USE-U2-001：机器人只跑腿五步流程（同裁定）
  { to: '/market-sim', label: '规范与沙盒链' },
  { to: '/channel/my', label: '我的通道' }, // L1SI167-CHANNEL-UI-001：四屏流水线（押金→令牌→转正→沙盒；私域）
  { to: '/terms', label: '术语检索' }, // L1SI175-A1-3：术语页进私域（登录可见；⛔ 公域匿名导航——匿名开放另候创始人一句）
]

/** 「我的」卡（批1骨架）：登录态摘要 + 快捷入口；批2块一加入私域栏目（申诉端 /me/appeal 随块三） */
function MeCard() {
  const { isAuthenticated, did } = useAuth()
  return (
    <section data-testid="me-card" className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-gray-800">我的</h3>
      {isAuthenticated ? (
        <p data-testid="me-card-did" className="mb-2 truncate text-xs text-emerald-700">🔐 {did}</p>
      ) : (
        <p className="mb-2 text-xs text-gray-500">未登录（注册即缔约 · viewer 只读）</p>
      )}
      <div className="flex gap-2 text-[11px]">
        <NavLink to="/me" className="rounded bg-gray-100 px-2 py-1 text-gray-600 hover:bg-gray-200">我的</NavLink>
        <NavLink to="/auth" className="rounded bg-gray-100 px-2 py-1 text-gray-600 hover:bg-gray-200">登录</NavLink>
        <NavLink to="/register" className="rounded bg-gray-100 px-2 py-1 text-gray-600 hover:bg-gray-200">注册</NavLink>
      </div>
      <div data-testid="me-private-nav" className="mt-3 border-t border-gray-100 pt-2">
        <p className="mb-1.5 text-[10px] font-medium tracking-wide text-gray-400">我的栏目（须登录／须角色）</p>
        <div className="flex flex-wrap gap-1.5 text-[11px]">
          {PRIVATE_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className="rounded bg-indigo-50 px-2 py-1 text-indigo-700 hover:bg-indigo-100"
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    </section>
  )
}

/** 站内 AI 助手会话框（批1骨架）：已接 /api/v1/intent（真 AI＋规则表兜底，fail-soft） */
function AssistantPanel() {
  const [input, setInput] = useState('')
  const [msgs, setMsgs] = useState<ChatMsg[]>([])
  const [busy, setBusy] = useState(false)

  async function send() {
    const q = input.trim()
    if (!q || busy) return
    setBusy(true)
    setInput('')
    setMsgs((m) => [...m, { role: 'user', text: q }])
    const res = await api.get<{ title?: string; route?: string; guide?: string[]; note?: string }>(
      `/api/v1/intent?q=${encodeURIComponent(q)}`,
    )
    if (res.ok) {
      const d = res.data
      const text = [`给你找到：${d.title ?? '首页总览'}`, ...(d.guide ?? [])].join('；')
      setMsgs((m) => [...m, { role: 'assistant', text, route: d.route }])
    } else {
      // fail-soft（ID85）：不猜测，明示降级（规则表路径零外呼仍可用）
      setMsgs((m) => [...m, { role: 'assistant', text: '意图服务暂不可用，请直接走上方导航。' }])
    }
    setBusy(false)
  }

  return (
    <section data-testid="assistant-panel" className="flex min-h-[220px] flex-col rounded-xl border border-indigo-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-indigo-900">AI 助手</h3>
      <div data-testid="assistant-msgs" className="flex-1 space-y-2 overflow-y-auto text-xs">
        {msgs.length === 0 && (
          <p className="text-gray-400">说你要做什么，例如：我要签批／查税收／创建智能体</p>
        )}
        {msgs.map((m, i) => (
          <p key={i} className={m.role === 'user' ? 'text-right text-slate-700' : 'text-left text-gray-600'}>
            {m.text}
            {m.route && (
              <NavLink to={m.route} className="ml-1 text-emerald-700 underline">直达 →</NavLink>
            )}
          </p>
        ))}
        {busy && <p className="text-gray-400">应答中（真 AI＋规则表兜底）…</p>}
      </div>
      <div className="mt-2 flex gap-1.5">
        <input
          data-testid="assistant-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void send()}
          placeholder="说意图…"
          className="flex-1 rounded-md border border-indigo-200 px-2 py-1.5 text-xs outline-none focus:border-indigo-400"
        />
        <button
          data-testid="assistant-send"
          onClick={() => void send()}
          disabled={busy}
          className="rounded-md bg-indigo-600 px-2.5 py-1.5 text-xs text-white disabled:opacity-50"
        >
          发送
        </button>
      </div>
    </section>
  )
}

/** 右栏（批1骨架）：「我的」＋ AI 助手会话框 */
export function RightRail() {
  return (
    <div className="space-y-4">
      <MeCard />
      <AssistantPanel />
    </div>
  )
}
