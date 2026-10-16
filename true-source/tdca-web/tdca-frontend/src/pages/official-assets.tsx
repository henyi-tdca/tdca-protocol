// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项二 · 官方资产区（公域新增）
// 约束矩阵: CONTENT-ZONES-001 AMEND-1（产物库＝官方资产·付费·橱窗）
//   ＋ AMEND-2（官方工具清单·官方开发·官智与用户皆可用）
//   ＋ AMEND-3（工具不收费·协议层免费＋资产配置收费同源）
//   ＋ B5-AMEND-1（调用计价 0.01 元/次·未通支付渠道前暂不开放调用→展示＋未开放态，⛔ 不做支付集成）
// 呈现: 同区并陈 —— 工具在上 ‧ 产物在下
// =============================================================================
import { PageShell } from './PageShell'

/** 官方工具（照 AMEND-2 逐字清单；官方开发·官方智能体与用户皆可用·免费） */
const OFFICIAL_TOOLS = [
  { name: '智能合约', desc: '合约模板类，官方开发' },
  { name: '表单等模板', desc: '常用业务表单模板' },
  { name: '编译器', desc: '制度件与工件编译' },
  { name: '适配器', desc: '外部系统对接适配' },
  { name: '生成器', desc: '如存证（NCA）生成器等' },
  { name: '校准器', desc: '参数与口径校准' },
  { name: '连接器', desc: '节点与通道连接' },
  { name: '反函数求解器', desc: '逆问题求解工具' },
  { name: 'skill（技能）', desc: '可复用技能件' },
]

/** 官方产物／资产（照 AMEND-1：增值服务产物·取用付费·橱窗陈列） */
const OFFICIAL_PRODUCTS = [
  { name: '观测包', desc: '运行观测与指标之产物包' },
  { name: '治理包', desc: '治理操作与审计之产物包' },
]

export function OfficialAssetsPage() {
  return (
    <PageShell
      title="官方资产区（官方工具 · 官方产物）"
      dataSource="静态文案（站内审定口径）＋ 文库产物库只读面"
      permission="公开"
      description="官方资源同区并陈：工具在上（免费可用）、产物在下（付费取用）。一句话——工具随便用，产物要买，用起来官方才受益（配置调用计费）。"
    >
      <div data-testid="official-assets-page" className="space-y-6">
        {/* ── 工具在上 ── */}
        <section data-testid="official-tools">
          <div className="mb-2 flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900">官方工具（免费）</h3>
            <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">免费</span>
          </div>
          <p className="mb-3 text-xs text-gray-500">
            均为官方开发；官方智能体可以用，用户也可以用（双向可用）。使用前提照在册流程：配置类调用须凭有效授权件，参数与门槛按在册。
          </p>
          <div className="grid gap-2 sm:grid-cols-3">
            {OFFICIAL_TOOLS.map((t) => (
              <div key={t.name} className="rounded-lg border border-gray-200 bg-white p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{t.name}</span>
                  <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] text-emerald-600">免费</span>
                </div>
                <p className="mt-1 text-xs text-gray-500">{t.desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-400">工具上架与取用入口：工具货架（/toolshelf）。清单非穷举，同类官方开发之工具皆入。</p>
        </section>

        {/* ── 产物在下 ── */}
        <section data-testid="official-products">
          <div className="mb-2 flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900">官方产物／资产（取用付费）</h3>
            <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">付费</span>
          </div>
          <p className="mb-3 text-xs text-gray-500">
            官方产物＝官方资产，系增值服务之产物（产物库现有 622 件，可在文库产物库公开浏览）。取用须授权；
            计价已明示：<strong className="text-gray-700">调用一次 0.01 元</strong>。
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {OFFICIAL_PRODUCTS.map((p) => (
              <div key={p.name} className="rounded-lg border border-gray-200 bg-white p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{p.name}</span>
                  <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[10px] text-amber-600">付费</span>
                </div>
                <p className="mt-1 text-xs text-gray-500">{p.desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3">
            <p className="text-xs text-gray-600">
              取用入口：<button type="button" disabled data-testid="product-call-disabled"
                className="cursor-not-allowed rounded bg-gray-200 px-2 py-1 text-[11px] text-gray-400">
                调用产物（暂未开放）
              </button>
              <span className="ml-2 text-[11px] text-gray-400">未开通真实支付渠道前暂不开放调用（届时按 0.01 元/次接入）；本期无任何支付入口。</span>
            </p>
          </div>
        </section>

        {/* ── 三层收益结构（照 AMEND-3）── */}
        <section data-testid="revenue-structure">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">取用分层（三层收益结构）</h3>
          <ul className="space-y-1.5 text-xs text-gray-600">
            <li><strong className="text-gray-800">官方工具</strong>——免费（让人用：官方智能体与用户皆可用）。</li>
            <li><strong className="text-gray-800">官方产物</strong>——付费（增值服务产物，取用须授权）。</li>
            <li><strong className="text-gray-800">配置调用</strong>——计费：产物被配置调用时按调用计价（0.01 元/次），官方之间接受益；与配置权调度税分属两层、并行各收。</li>
          </ul>
        </section>

        <section className="rounded-lg border border-gray-200 bg-gray-50/60 p-3">
          <p className="text-xs leading-relaxed text-gray-500">
            边界：本区为橱窗与说明面——陈列、口径与取用意欲；实际取用与调用走工具货架／文库等既有在册入口，不在本区另行集成收款或计费。
          </p>
        </section>
      </div>
    </PageShell>
  )
}
