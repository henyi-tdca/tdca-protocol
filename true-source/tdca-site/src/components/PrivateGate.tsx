// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI206-MIGRATE-B3 私域面门槛（API 401/403 把守）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B3-001 §二-A／§四-3——私域权限由接口层
//   401/403 fail-closed 把守；前端隐藏 ⛔ 作据（照 /channel/my 先例，MIGRATE 批2 并轨注记③）
// 用法: 私域面载入先探 GET /api/v1/auth/me——
//   unauthorized/forbidden → 渲染「请先登录」人话提示，私域内容零渲染；
//   fail_closed（站点不可达/水印缺失）→ fail-closed 提示，⛔ 瞎猜数据；
//   ok → 渲染私域内容本体。
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/lib/client'

export type PrivateGateState = 'loading' | 'denied' | 'unavailable' | 'ok'

export function usePrivateGate(): PrivateGateState {
  const [state, setState] = useState<PrivateGateState>('loading')
  useEffect(() => {
    let alive = true
    void api.get<{ username?: string }>('/api/v1/auth/me').then((r) => {
      if (!alive) return
      if (r.ok) setState('ok')
      else if (r.reason === 'unauthorized' || r.reason === 'forbidden') setState('denied')
      else setState('unavailable')
    })
    return () => { alive = false }
  }, [])
  return state
}

/** 私域门槛未过时的统一提示（零数据渲染） */
export function PrivateGateNotice({ state }: { state: PrivateGateState }) {
  if (state === 'denied') {
    return (
      <div data-testid="private-gate-denied" className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
        这是私域面：谁的数据谁可见。请先登录（右上角登录入口）后再来看这一页——未登录态本站接口一律 401/403 拒答，本页不渲染任何私域内容。
      </div>
    )
  }
  if (state === 'unavailable') {
    return (
      <div data-testid="private-gate-unavailable" className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
        站点暂时连不上（fail-closed）——稍后再试，本页不会瞎猜私域数据。
      </div>
    )
  }
  return <p data-testid="private-gate-loading" className="text-sm text-gray-400">身份核验中…</p>
}
