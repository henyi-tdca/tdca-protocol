// 单摘自旧版 shared/guards/index.tsx（ID93 通知机四角色：Operator/Gov/Fin/Med 四灯）
// 连带 NotifierRoleState 类型＋NotifierRolesProps＋文件级常量 ROLE_LABELS；以内容定界
// 界面与文案逐字未改

// ---------------------------------------------------------------------------
// ID93 通知机四角色：Operator/Gov/Fin/Med 四灯
// ---------------------------------------------------------------------------
export interface NotifierRoleState {
  operator: boolean
  gov: boolean
  fin: boolean
  med: boolean
}
export interface NotifierRolesProps {
  roles: NotifierRoleState
  sceneCount?: number
}
const ROLE_LABELS: { key: keyof NotifierRoleState; label: string }[] = [
  { key: 'operator', label: 'Operator' },
  { key: 'gov', label: 'Gov' },
  { key: 'fin', label: 'Fin' },
  { key: 'med', label: 'Med' },
]
export function NotifierRoles({ roles, sceneCount = 0 }: NotifierRolesProps) {
  return (
    <div data-testid="notifier-roles" className="flex items-center gap-3">
      {ROLE_LABELS.map(({ key, label }) => (
        <span key={key} data-role={key} data-active={roles[key]} className="flex items-center gap-1">
          <span className={`h-2.5 w-2.5 rounded-full ${roles[key] ? 'bg-emerald-500' : 'bg-gray-300'}`} />
          <span className="text-xs text-gray-700">{label}</span>
        </span>
      ))}
      <span className="text-xs text-gray-400">场景 {sceneCount}</span>
    </div>
  )
}
