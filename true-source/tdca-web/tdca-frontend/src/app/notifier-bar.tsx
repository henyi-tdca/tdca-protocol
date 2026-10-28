// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-1 通知机状态栏（四角色灯 + WS notifier 通道）
// 约束矩阵: FRAMEWORK-001 §五.2（WS 四通道）/ ID93（四角色）/ ID92（模拟态降级）
// 预期分配: NotifierBar（WS 订阅 + 秒级刷新指示 + 消息计数；不可用时模拟态降级）
// =============================================================================
import { useEffect, useRef, useState } from 'react'
import { api } from '@/api/client'
import { NotifierRoles, type NotifierRoleState } from '@/shared/guards'

export interface NotifierBarProps {
  roles?: NotifierRoleState
}

const DEFAULT_ROLES: NotifierRoleState = { operator: true, gov: true, fin: true, med: true }

/** 通知机状态栏：WS notifier 通道实时订阅（B-5），不可用则模拟态降级（ID92） */
export function NotifierBar({ roles = DEFAULT_ROLES }: NotifierBarProps) {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [messageCount, setMessageCount] = useState(0)
  const [lastMsg, setLastMsg] = useState<string>('')

  useEffect(() => {
    let cancelled = false
    let closeFn: (() => void) | null = null
    try {
      closeFn = api.ws('notifier', {
        onStatus: (s) => {
          if (cancelled) return
          if (s === 'open') setConnected(true)
          if (s === 'close' || s === 'error') setConnected(false)
        },
        onMessage: (msg) => {
          if (cancelled) return
          setMessageCount((c) => c + 1)
          setLastMsg(typeof msg === 'string' ? msg : JSON.stringify(msg).slice(0, 80))
        },
      })
    } catch {
      setConnected(false)
    }
    return () => {
      cancelled = true
      closeFn?.()
    }
  }, [])

  return (
    <div data-testid="notifier-bar" data-connected={connected} className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-gray-200 bg-white px-3 py-1.5">
      <span className="text-xs font-medium text-gray-600">通知机</span>
      <NotifierRoles roles={roles} />
      <span className="text-xs text-gray-400" data-testid="notifier-msg-count">
        {connected ? `消息 ${messageCount}` : 'WS 未连接 [SIMULATED]'}
      </span>
      {lastMsg && <span className="max-w-40 truncate text-[10px] text-gray-400">最近：{lastMsg}</span>}
    </div>
  )
}
