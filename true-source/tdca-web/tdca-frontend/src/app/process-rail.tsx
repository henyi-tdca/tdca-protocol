// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批1 — 左栏流程栏骨架（随页面上下文切换）
// 约束矩阵: TDCA-HANDOFF-SITE-PHASE2-REVAMP-001 §二.1／§四批1（骨架占位，正式内容批3移植）
// =============================================================================
import { NavLink, useLocation } from 'react-router'

export interface RailStep {
  label: string
  hint?: string
}

/** 路由前缀 → 该环节流程（批1骨架占位：条目为版式示例，正式流程条批3自 tdca-site 移植） */
const RAIL_BY_CONTEXT: { prefix: string; title: string; steps: RailStep[] }[] = [
  {
    prefix: '/studio',
    title: '创建智能体流程',
    steps: [
      { label: '① 说清楚意图' },
      { label: '② 确认六要素' },
      { label: '③ HUF 签署负责' },
      { label: '④ 沙盒试用' },
      { label: '⑤ 出盒终裁' },
    ],
  },
  {
    prefix: '/workbuddy',
    title: 'WorkBuddy 作业流程',
    steps: [
      { label: '① 创建工作流' },
      { label: '② 执行并观察' },
      { label: '③ 硬件签名（模拟线）' },
      { label: '④ WORM 日志核验' },
    ],
  },
  {
    prefix: '/agent-channel',
    title: '智能体通道六步',
    steps: [
      { label: '⓪ 登记注册' },
      { label: '① 加载协议' },
      { label: '② 申领令牌' },
      { label: '③ 负空间审查' },
      { label: '④ 沙盒验证' },
      { label: '⑤ 交易执行' },
    ],
  },
]

const DEFAULT_RAIL: { title: string; steps: RailStep[] } = {
  title: '站点导览',
  steps: [
    { label: '橱窗：公开可读面' },
    { label: '观测：集群与通知机' },
    { label: '作业：Studio／WorkBuddy' },
    { label: '确权：签批与历史' },
  ],
}

/** 左栏流程栏（批1骨架）：随当前路由切换流程条目；小屏由壳层折叠 */
export function ProcessRail() {
  const { pathname } = useLocation()
  const ctx = RAIL_BY_CONTEXT.find((c) => pathname.startsWith(c.prefix))
  const title = ctx?.title ?? DEFAULT_RAIL.title
  const steps = ctx?.steps ?? DEFAULT_RAIL.steps
  return (
    <aside data-testid="process-rail" className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 data-testid="process-rail-title" className="mb-2 text-sm font-semibold text-gray-800">
        流程 · {title}
      </h3>
      <ol className="space-y-1.5">
        {steps.map((s, i) => (
          <li key={i} className="rounded bg-gray-50 px-2 py-1.5 text-xs text-gray-600">
            {s.label}
          </li>
        ))}
      </ol>
      <p className="mt-3 text-[10px] text-gray-400">F0 骨架占位（批3 移植 tdca-site 操作进阶流程栏）</p>
      <div className="mt-2 border-t border-gray-100 pt-2 text-[10px] text-gray-400">
        <NavLink to="/" className="underline hover:text-slate-700">回首页</NavLink>
      </div>
    </aside>
  )
}
