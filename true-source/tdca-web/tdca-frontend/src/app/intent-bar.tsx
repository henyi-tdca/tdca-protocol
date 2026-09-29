// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M4 | 目标函数: 全局意图导航条（自然语言 → 功能页直达 + 操作指引）
// 约束矩阵: 创始人 2026-08-21 04:12 指令（主站全局入口）；接缝式新增，不改既有页面逻辑
// 制度锚点: ID91（走 api.get 水印校验）/ ID85（失败 fail-soft 提示，不猜测路由）
// =============================================================================
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { api } from '@/api/client'

interface IntentData {
  matched: boolean
  route: string
  title: string
  action: string
  guide: string[]
  alternatives: { route: string; title: string }[]
}

/** 全局意图导航条：顶栏输入大白话 → 下拉给出直达路由 + 分步操作指引 */
export function IntentBar() {
  const [q, setQ] = useState('')
  const [result, setResult] = useState<IntentData | null>(null)
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()
  const boxRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(ev: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(ev.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  async function ask() {
    const query = q.trim()
    if (!query) return
    setBusy(true)
    const res = await api.get<IntentData>(`/api/v1/intent?q=${encodeURIComponent(query)}`)
    setBusy(false)
    if (res.ok) {
      setResult(res.data)
      setOpen(true)
    }
    // res.ok=false：fail-soft，不弹窗不猜测（ID85）
  }

  function go(route: string) {
    setOpen(false)
    setQ('')
    navigate(route)
  }

  return (
    <div ref={boxRef} data-testid="intent-bar" className="relative">
      <div className="flex items-center overflow-hidden rounded-full border border-gray-300 bg-white focus-within:border-slate-500">
        <input
          data-testid="intent-input"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') ask() }}
          placeholder="说意图直达，如：我要签批"
          className="w-44 px-3 py-1 text-xs outline-none"
        />
        <button
          data-testid="intent-go"
          onClick={ask}
          className="bg-slate-800 px-2.5 py-1 text-xs text-white hover:bg-slate-700"
        >
          {busy ? '…' : '直达'}
        </button>
      </div>
      {open && result && (
        <div
          data-testid="intent-result"
          className="absolute right-0 z-50 mt-1 w-80 rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">{result.title}</span>
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
              {result.action}
            </span>
          </div>
          <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs leading-5 text-gray-600">
            {result.guide.map((step, i) => <li key={i}>{step}</li>)}
          </ol>
          <button
            data-testid="intent-jump"
            onClick={() => go(result.route)}
            className="mt-2 w-full rounded bg-slate-800 py-1.5 text-xs font-medium text-white hover:bg-slate-700"
          >
            直达「{result.title}」→
          </button>
          {result.alternatives.length > 0 && (
            <div className="mt-2 text-[11px] text-gray-400">
              相关入口：
              {result.alternatives.map((a) => (
                <button
                  key={a.route}
                  onClick={() => go(a.route)}
                  className="ml-1 text-slate-600 underline hover:text-slate-900"
                >
                  {a.title}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
