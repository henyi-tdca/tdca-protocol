// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-1 统一 DID 上下文（H/M/L 三身份入口）
// 约束矩阵: TDCA-TASK-FRONTEND-001（FROZEN）+ DESIGN-PHILOSOPHY-001（单 DID 上下文）
// 预期分配: DIDProvider + useDID（role/did/switchRole，localStorage 持久化）
// =============================================================================
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

export type DIDRole = 'H' | 'M' | 'L'

export interface DIDState {
  role: DIDRole
  did: string
  switchRole: (role: DIDRole) => void
}

const ROLE_LABEL: Record<DIDRole, string> = {
  H: '人类（Human）',
  M: '智能体（Machine）',
  L: '学习体（Learner）',
}

export const ROLE_LABELS = ROLE_LABEL

const DIDContext = createContext<DIDState | null>(null)

function defaultDid(role: DIDRole): string {
  if (role === 'H') return 'TDID-H-0001'
  if (role === 'M') return 'TDID-M-0001'
  return 'TDID-L-0001'
}

export function DIDProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<DIDRole>(() => {
    const r = localStorage.getItem('tdca_did_role')
    return r === 'M' || r === 'L' ? r : 'H'
  })
  const [did, setDid] = useState<string>(() => {
    const r = localStorage.getItem('tdca_did_role')
    return defaultDid(r === 'M' || r === 'L' ? (r as DIDRole) : 'H')
  })

  const value = useMemo<DIDState>(
    () => ({
      role,
      did,
      switchRole: (next) => {
        setRole(next)
        const nextDid = defaultDid(next)
        setDid(nextDid)
        localStorage.setItem('tdca_did_role', next)
        localStorage.setItem('tdca_did', nextDid)
      },
    }),
    [role, did],
  )

  return <DIDContext.Provider value={value}>{children}</DIDContext.Provider>
}

export function useDID(): DIDState {
  const ctx = useContext(DIDContext)
  if (!ctx) throw new Error('useDID 必须在 DIDProvider 内使用')
  return ctx
}
