// TDCA DID 角色类型小件（FRONTEND-MERGE 批2）
// 界分：仅搬类型与角色标签常量；DIDProvider 属应用壳（AppShell），不在本批
export type DIDRole = 'H' | 'M' | 'L'

const ROLE_LABEL: Record<DIDRole, string> = {
  H: '人类（Human）',
  M: '智能体（Machine）',
  L: '学习体（Learner）',
}

export const ROLE_LABELS = ROLE_LABEL
