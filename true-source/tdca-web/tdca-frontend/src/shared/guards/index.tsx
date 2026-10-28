// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 六约束模块（guards/）——制度约束前端化
// 约束矩阵: TDCA-TASK-FRONTEND-001（FROZEN）§三 F0-4 + FRAMEWORK-001 §六
// 制度锚点: BV-3（只读流）/ F-4（熔断三色灯）/ ID79（MOU 不可降）/ HUF（签批模态）
//          / ID93（通知机四角色）/ G-1（术语 + 最小化合）
// 预期分配: ReadOnlyStream / FuseIndicator / MouReadout / HufModal / NotifierRoles / TermGuard / CompoundCheck
// =============================================================================
import { scanTermDrift } from '@/shared/terms'

export type FuseState = 'CLOSED' | 'SUSPENDED' | 'BLOCKED'

const FUSE_META: Record<FuseState, { label: string; dot: string; desc: string }> = {
  CLOSED: { label: 'CLOSED 运行', dot: 'bg-emerald-500', desc: '熔断器闭合，规则流正常运行' },
  SUSPENDED: { label: 'SUSPENDED 挂起', dot: 'bg-amber-500', desc: '疑似负空间逼近，规则流挂起待审' },
  BLOCKED: { label: 'BLOCKED 阻断', dot: 'bg-red-600', desc: '触碰法律/伦理红线（LEGAL 绝对熔断，无替代路径）' },
}

// ---------------------------------------------------------------------------
// BV-3 只读流：数据只读渲染，无编辑路径，无本地缓存修改
// ---------------------------------------------------------------------------
export interface ReadOnlyStreamProps {
  title: string
  data: unknown
  nature?: 'real' | 'simulated'
}
export function ReadOnlyStream({ title, data, nature = 'simulated' }: ReadOnlyStreamProps) {
  return (
    <div data-testid="readonly-stream" className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{title}</span>
        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
          BV-3 只读 · {nature === 'simulated' ? 'SIMULATED' : 'REAL'}
        </span>
      </div>
      <pre className="max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-700">
        {JSON.stringify(data, null, 2)}
      </pre>
      <p className="mt-1 text-[10px] text-gray-400">只读流：无编辑路径 · 无本地缓存修改</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// F-4 熔断三色灯：绿=CLOSED / 金=SUSPENDED / 红=BLOCKED
// ---------------------------------------------------------------------------
export interface FuseIndicatorProps {
  state: FuseState
  label?: string
}
export function FuseIndicator({ state, label }: FuseIndicatorProps) {
  const meta = FUSE_META[state]
  return (
    <div data-testid="fuse-indicator" data-state={state} className="flex items-center gap-2">
      <span data-testid="fuse-dot" className={`h-3 w-3 rounded-full ${meta.dot}`} />
      <span className="text-sm font-medium text-gray-800">{label ?? meta.label}</span>
      <span className="text-xs text-gray-500">{meta.desc}</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// MOU 不可降（ID79）：金色高亮 + 税额硬下限校验
// ---------------------------------------------------------------------------
export interface MouReadoutProps {
  label: string
  amount: number
  minThreshold?: number
}
export function MouReadout({ label, amount, minThreshold = 0 }: MouReadoutProps) {
  const violated = amount < minThreshold
  return (
    <div data-testid="mou-readout" data-violated={violated} className="flex items-center gap-2">
      <span className="text-sm text-gray-600">{label}</span>
      <span className={`rounded px-2 py-0.5 text-sm font-semibold ${violated ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
        ¥{amount.toFixed(2)}
      </span>
      {violated && (
        <span className="text-xs font-medium text-red-600" data-testid="mou-violation">
          MOU 硬下限违反（&lt; {minThreshold}）——结算拒绝
        </span>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// HUF 签批模态：AI 无权替代 + 取消即中止
// ---------------------------------------------------------------------------
export interface HufModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  title?: string
  description?: string
}
export function HufModal({ open, onOpenChange, onConfirm, title = 'HUF 人类最终签批', description }: HufModalProps) {
  if (!open) return null
  return (
    <div
      data-testid="huf-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="w-full max-w-md rounded-lg border border-amber-300 bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-1 text-base font-bold text-gray-900">{title}</h3>
        <p className="mb-3 text-sm text-gray-600">
          {description ?? '本操作涉及制度级决策（治理/创建/签批/确权）。AI 无权替代人类最终签批权（HUF）。'}
        </p>
        <div className="flex justify-end gap-2">
          <button
            data-testid="huf-cancel"
            className="rounded border border-blue-600 bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            onClick={() => onOpenChange(false)}
          >
            取消（中止操作）
          </button>
          <button
            data-testid="huf-confirm"
            className="rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700"
            onClick={() => {
              onOpenChange(false)
              onConfirm()
            }}
          >
            确认签批 · NCA 存证
          </button>
        </div>
      </div>
    </div>
  )
}

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

// ---------------------------------------------------------------------------
// G-1 术语守卫：扫描渲染文本中的漂移词（ID93/G-1）
// ---------------------------------------------------------------------------
export interface TermGuardProps {
  text: string
}
export function TermGuard({ text }: TermGuardProps) {
  const hits = scanTermDrift(text)
  if (hits.length === 0) return null
  return (
    <div data-testid="term-guard" className="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">
      术语漂移：{hits.map((h) => `「${h.phrase}」${h.reason}`).join('；')}
    </div>
  )
}

// ---------------------------------------------------------------------------
// G-1 最小化合（ID90）：配置权调用前三条件，任一失败阻断
// ---------------------------------------------------------------------------
export interface CompoundCondition {
  id: string
  label: string
  met: boolean
}
export interface CompoundCheckProps {
  conditions: CompoundCondition[]
}
export function CompoundCheck({ conditions }: CompoundCheckProps) {
  const allMet = conditions.every((c) => c.met)
  return (
    <div data-testid="compound-check" data-blocked={!allMet} className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-2 text-sm font-medium text-gray-800">最小化合 · 调用前三条件</div>
      <ul className="space-y-1">
        {conditions.map((c) => (
          <li key={c.id} data-condition={c.id} className="flex items-center gap-2 text-xs">
            <span className={`h-2 w-2 rounded-full ${c.met ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className={c.met ? 'text-gray-700' : 'text-red-600'}>{c.label}</span>
          </li>
        ))}
      </ul>
      {!allMet && (
        <p className="mt-2 text-xs font-medium text-red-600" data-testid="compound-blocked">
          条件未全满足——配置权调用阻断
        </p>
      )}
    </div>
  )
}
