// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项一 · 负空间栏（公域新增）
// 约束矩阵: TDCA-SPEC-SITE-CONTENT-ZONES-001（八区语义·负空间＝管什么不能做）
//   ＋ AMEND-1（负空间单开一栏·三空间不可缺）
// 红线: 只讲原则与类别，⛔ 不列具体禁项词表（在册「不公开四条」含负空间词面）
// =============================================================================
import { PageShell } from './PageShell'

/** 三空间（原则级说明，照在册 TruthSpace 口径；⛔ 不涉内部编号） */
const THREE_SPACES = [
  { name: '正空间', desc: '成立、可证、可为——经制度确认可以做的事。' },
  { name: '负空间', desc: '不可为、不可算计——制度明令不可做的事。' },
  { name: '未裁决', desc: '待定——尚无定论的事，先入沙盒试行，不作正空间对待。' },
]

/** 管理机制（类别级，⛔ 不含禁项词面） */
const MECHANISMS = [
  { name: '负空间函数语言（NSFL）', desc: '判定规则写成机器可执行的语言，人与智能体同一标准、同一判定结果。' },
  { name: '负空间熔断', desc: '一旦触发即停：当前动作立即中止，无任何绕过通道。' },
  { name: '拒绝清单', desc: '被否决的事项入清单留痕，只增不改——拒绝本身也受制度约束。' },
  { name: '公共负空间维护', desc: '负空间由公共机制维护，人人可查其生效，不设私下豁免。' },
]

export function NegativeSpacePage() {
  return (
    <PageShell dataNature="real"
      title="负空间 · 什么不能做"
      dataSource="静态文案（站内审定口径）"
      permission="公开"
      description="TDCA 三空间之一：负空间管「什么不能做」——本栏只讲原则与类别，是拒绝清单面向公众的说明面。"
    >
      <div data-testid="negativespace-page" className="space-y-6">
        <section>
          <h3 className="mb-2 text-sm font-semibold text-gray-900">这一栏管什么</h3>
          <p className="text-sm leading-relaxed text-gray-600">
            负空间是 TDCA 三空间不可缺少的一部分，管的是「什么不能做」：不可为、禁项、以及被否决事项（拒绝清单）的对外说明。
            与正空间相对——正空间讲「可以做什么」，负空间讲「不可做什么」；两者加上「未裁决」，构成完整的三空间。
          </p>
        </section>

        <section>
          <h3 className="mb-2 text-sm font-semibold text-gray-900">三空间（原则）</h3>
          <div className="grid gap-3 sm:grid-cols-3">
            {THREE_SPACES.map((s) => (
              <div key={s.name} className="rounded-lg border border-gray-200 bg-gray-50/60 p-3">
                <div className="text-sm font-medium text-gray-900">{s.name}</div>
                <p className="mt-1 text-xs leading-relaxed text-gray-600">{s.desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-500">三者两两互斥：同一件事不能既「可为」又「不可为」，「未裁决」事项也不按「可为」对待。</p>
        </section>

        <section>
          <h3 className="mb-2 text-sm font-semibold text-gray-900">怎么管（机制 · 类别级）</h3>
          <ul className="space-y-2">
            {MECHANISMS.map((m) => (
              <li key={m.name} className="rounded-lg border border-gray-200 p-3">
                <span className="text-sm font-medium text-gray-900">{m.name}</span>
                <span className="ml-2 text-xs text-gray-600">{m.desc}</span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h3 className="mb-2 text-sm font-semibold text-gray-900">对用户与智能体的一句话</h3>
          <p className="text-sm leading-relaxed text-gray-600">
            缔约、调用、内容入站之前，一律先过负空间判定；触负即拒（fail-closed），人与智能体同一标准、不留例外。
            「不确定能不能做」的事，去沙盒——沙盒就是「不确定的事在哪里做」的地方。
          </p>
        </section>

        <section data-testid="negativespace-redline" className="rounded-lg border border-amber-200 bg-amber-50/60 p-3">
          <p className="text-xs leading-relaxed text-amber-800">
            本栏口径：只讲原则与类别。具体禁项的词面属不公开面——本栏不列、公开页面不转载；判定时以制度内的机器可读负空间为准。
          </p>
        </section>
      </div>
    </PageShell>
  )
}
