// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI188-NAV-FIX-004 项2 · /channel 智能体通道总入口
// 约束矩阵: NAV-FIX-004 §一——内容照在册「智能体通道六步」，⛔ 新写内容、⛔ 添加对外承诺
// 在册出处（引用来源）：
//   ① 六步硬序＝《智能体定义条例》第 19 条（TDCA-REG-AGENT-DEFINITION-001 人读版，
//      六环节字样：加载 TDCA 协议／持根节点执行令牌／负空间审查／沙盒验证／正空间执行事务／NCA 存证；
//      原文「⛔ 六步不可跳过、⛔ 不可互替」；该件 V1.0-PENDING-SIGNATURE，本页仅照在册表述呈现）
//   ② 「登记」为六步之外的前置＝同条例第 9 条（登记方为创建；未登记者不判创建、不受制度保护，运行而不登记判幽灵态）
//   ③ 六个子页入口＝既有 /channel/* 五路极简入口＋登记实页（App.tsx 既有路由，本页只指不建）
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from './PageShell'

/** 六步硬序（照在册表述，逐字引自条例第 19 条环节名） */
const SIX_STEPS = [
  { no: '①', name: '加载 TDCA 协议', note: '通道准入之唯一验证对象' },
  { no: '②', name: '持根节点执行令牌', note: '' },
  { no: '③', name: '负空间审查', note: '' },
  { no: '④', name: '沙盒验证', note: '执行行为合 TDCA 机制要求' },
  { no: '⑤', name: '正空间执行事务', note: '' },
  { no: '⑥', name: 'NCA 存证', note: '全程' },
] as const

/** 六个子页入口（既有路由，本页只指不建） */
const SUB_ENTRIES = [
  { to: '/channel/registry', label: '自助登记', note: '智能体自助登记入口（登记前先答分流首问）' },
  { to: '/channel/my', label: '我的通道', note: '「我的通道」四屏流水线（须登录）' },
  { to: '/agents', label: '能力与观测', note: '官方智能体观测橱窗' },
  { to: '/agent-shelf', label: '智能体货架', note: '组二 10 件呈现（呈现≠注册）' },
  { to: '/market', label: '配置权市场', note: '使用权／配置权可流转市场' },
  { to: '/toolshelf', label: '工具货架', note: '官方工具展示面' },
  // NAV-FIX-005 顺手①：两条旧路子路由站内零入链，纳入清单并照实标注「跳转等同」
  { to: '/channel/agents', label: '能力直达（旧路）', note: '旧路跳转，等同「能力与观测」/agents' },
  { to: '/channel/tools', label: '工具直达（旧路）', note: '旧路跳转，等同「工具货架」/toolshelf' },
] as const

/** 智能体通道总入口（NAV-FIX-004 项2）：六步照在册＋六子页入口 */
export function ChannelPortalPage() {
  return (
    <PageShell dataNature="real"
      title="智能体通道"
      dataSource="在册《智能体定义条例》第 19 条（六步硬序）＋既有 /channel/* 路由"
      permission="公开"
      description="智能体经站点通道接入的总入口：先登记（前置），再按六步硬序走通；六步不可跳过、不可互替。"
    >
      <div data-testid="channel-portal" className="space-y-6">
        {/* 前置：登记（条例第 9 条口径照录） */}
        <section data-testid="channel-preregister" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-800">前置 · 登记</h3>
          <p className="text-xs text-gray-600">
            登记方为创建：未登记者不判创建、不受制度保护；运行而不登记者判幽灵态。
            登记入口见下方「自助登记」。
          </p>
        </section>

        {/* 六步硬序（照在册表述） */}
        <section data-testid="channel-six-steps">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">六步硬序（照在册，不可跳过、不可互替）</h3>
          <ol className="divide-y divide-gray-100 rounded-lg border border-gray-200">
            {SIX_STEPS.map((s) => (
              <li key={s.no} data-testid={`channel-step-${s.no}`} className="flex items-baseline gap-2 px-4 py-2.5">
                <span className="text-sm font-medium text-blue-700">{s.no}</span>
                <span className="text-sm font-medium text-gray-800">{s.name}</span>
                {s.note && <span className="text-xs text-gray-500">（{s.note}）</span>}
              </li>
            ))}
          </ol>
        </section>

        {/* 六个子页入口 */}
        <section data-testid="channel-subentries">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">子页入口</h3>
          <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
            {SUB_ENTRIES.map((e) => (
              <li key={e.to + e.label}>
                <Link to={e.to} data-testid={`channel-entry-${e.label}`}
                  className="block px-4 py-3 hover:bg-gray-50">
                  <span className="text-sm font-medium text-blue-700 underline hover:text-blue-900">{e.label}</span>
                  <span className="ml-2 text-xs text-gray-500">{e.note} → {e.to}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </PageShell>
  )
}
