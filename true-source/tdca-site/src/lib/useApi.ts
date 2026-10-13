// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 数据获取 hook（api.get + NCA 水印结果状态）
// 约束矩阵: FRAMEWORK-001 §5.1（NCA 水印校验 + fail-closed + ID92）
// 预期分配: useApiGet<T>（status: loading/ok/fail + data/nature/reason）
// =============================================================================
import { useEffect, useState } from 'react'
import { api, type GetOptions } from '@/lib/client'

export interface UseApiState<T> {
  status: 'loading' | 'ok' | 'fail'
  data: T | null
  nature: 'real' | 'simulated' | null
  reason?: string
}

/** 统一数据获取：NCA 水印缺失/后端不可用 → fail 状态（fail-closed，页面渲染降级提示） */
export function useApiGet<T>(path: string, opts?: GetOptions): UseApiState<T> {
  const [state, setState] = useState<UseApiState<T>>({ status: 'loading', data: null, nature: null })

  useEffect(() => {
    let cancelled = false
    setState({ status: 'loading', data: null, nature: null })
    api
      .get<T>(path, opts)
      .then((res) => {
        if (cancelled) return
        if (res.ok) {
          setState({ status: 'ok', data: res.data, nature: res.nature })
        } else {
          setState({ status: 'fail', data: null, nature: null, reason: res.reason })
        }
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'fail', data: null, nature: null, reason: 'fail_closed' })
      })
    return () => {
      cancelled = true
    }
  }, [path, opts?.tolerateMissingWatermark])

  return state
}
