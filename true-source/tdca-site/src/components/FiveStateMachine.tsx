// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI207 MYSPACE-PHASE1-001 §一.6 — 五态状态机展示
// 约束矩阵: MYSPACE-PHASE1-001 §一.6（暂用五态 DRAFT／NEG_PASS／SANDBOX_PASS／PUBLISHED／SUSPENDED；
//          COMPILING 待二批令）；§二-H-3 私域不简化规则——依据明文引令载口径
// 口径: 纯展示件，零业务逻辑；「当前态」由调用方按实据传入，无据 ⟹ 全置灰并明示未入管，
//       ⛔ 臆造当前态
// =============================================================================

const FIVE_STATES = [
  { key: 'DRAFT', label: '草稿', hint: '拟制中，未进任何校验' },
  { key: 'NEG_PASS', label: '负空间通过', hint: '负空间判据逐项过' },
  { key: 'SANDBOX_PASS', label: '沙盒通过', hint: '沙盒演练达标出盒' },
  { key: 'PUBLISHED', label: '已发布', hint: '对外在架生效' },
  { key: 'SUSPENDED', label: '已停用', hint: '在架但暂停服务' },
] as const

/** 五态状态机（横条展示）。current 无实据时传 null/undefined —— 全置灰＋未入管注记。 */
export function FiveStateMachine({ current }: { current?: string | null }) {
  const known = FIVE_STATES.some((s) => s.key === current)
  return (
    <div data-testid="five-state-machine" className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-2 text-xs font-semibold text-gray-600">
        状态机（五态暂用口径）
        <span className="ml-2 font-normal text-gray-400">依据：MYSPACE-PHASE1-001 §一.6；COMPILING 态随二批令加</span>
      </div>
      <ol className="flex flex-wrap items-center gap-1">
        {FIVE_STATES.map((s, i) => {
          const active = known && s.key === current
          return (
            <li key={s.key} className="flex items-center gap-1">
              <span
                data-testid={`fsm-${s.key}`}
                title={s.hint}
                className={
                  active
                    ? 'rounded-md border border-emerald-500 bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-800'
                    : 'rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-[11px] text-gray-400'
                }
              >
                {s.label}
                <span className="ml-1 font-mono text-[10px]">{s.key}</span>
              </span>
              {i < FIVE_STATES.length - 1 && <span className="text-[10px] text-gray-300">→</span>}
            </li>
          )
        })}
      </ol>
      {!known && (
        <p data-testid="fsm-not-in-pipeline" className="mt-2 text-[11px] text-amber-700">
          该件未入编译管线：一期骨架只展示状态机形态，当前态待区 2A 编译流水线（二批令）接入后按实据标注，本站不臆造。
        </p>
      )}
    </div>
  )
}
