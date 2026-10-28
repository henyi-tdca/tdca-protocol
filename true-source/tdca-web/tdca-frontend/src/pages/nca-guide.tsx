// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项三 · 存证（NCA）说明栏（公域新增）
// 约束矩阵: TDCA-RULING-NCA-FORMAT-UNIVERSAL-001（NCA 格式制度须明示·贯彻每一场景·
//   官方与用户一致·人类与智能体一致）＋ TDCA-NCA-STD-001（在册格式标准）
// 红线: ⛔ 栏内不展示任何实际凭据或内部编号（S-3）——只讲格式标准与义务，不列真实存证件
// =============================================================================
import { PageShell } from './PageShell'

/** 十三项统一字段（照在册 TDCA-NCA-STD-001 明示要点） */
const FIELDS_13 = [
  { k: 'nca_id', d: '存证编号' },
  { k: 'side', d: '所属侧（权属／配置权等）' },
  { k: 'timestamp', d: '时间戳' },
  { k: 'chain_space', d: '链上空间' },
  { k: 'chain_id', d: '链标识' },
  { k: 'chain_ref', d: '链上引用' },
  { k: 'prev_nca', d: '前序存证指针（带链）' },
  { k: 'operation_type', d: '操作类型' },
  { k: 'actor', d: '行为主体' },
  { k: 'artifacts', d: '工件清单（含 sha256_16 摘要）' },
  { k: 'data_provenance', d: '数据来源' },
  { k: 'profit_sharing', d: '分润口径' },
  { k: 'compliance', d: '合规项' },
]

/** 义务块六键（裁定 R-2：NCA 制度合一版） */
const OBLIGATION_6 = [
  { k: 'function_call_id', d: '对应调用编号' },
  { k: 'state_hashes', d: '状态哈希' },
  { k: 'config_right', d: '配置权凭据' },
  { k: 'audit_trail', d: '审计轨迹' },
  { k: 'human_signature', d: '人类签名' },
  { k: 'negative_space_check', d: '负空间检查' },
]

/** 合规六条（现行） */
const COMPLIANCE_6 = [
  '只赋能不改码',
  '不复制上游代码',
  '算力零提及',
  '不声称上游背书',
  '无存证不执行',
  '分润模拟态',
]

export function NcaGuidePage() {
  return (
    <PageShell dataNature="real"
      title="存证（NCA）说明"
      dataSource="静态文案（站内审定口径，依在册 NCA 格式标准）"
      permission="公开"
      description="本站唯一存证格式＝NCA 格式：每一个场景都要存，官方与用户一个样，人类与智能体一个样——本栏讲为什么要存、怎么存、谁都要存。"
    >
      <div data-testid="nca-guide-page" className="space-y-6">
        {/* ── 为什么要存证 ── */}
        <section data-testid="nca-why">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">为什么要存证</h3>
          <ul className="space-y-1.5 text-xs leading-relaxed text-gray-600">
            <li><strong className="text-gray-800">无存证不执行</strong>——每一次操作皆须先落存证，未落存证的操作不成立、不执行。</li>
            <li><strong className="text-gray-800">可观测</strong>——存证链公开可查，任何人可独立核验发生过什么（制度即公开）。</li>
            <li><strong className="text-gray-800">可问责</strong>——谁调的、凭什么、出什么、留什么痕，四问皆有链上答案。</li>
            <li><strong className="text-gray-800">可回溯</strong>——每一次协作＝一次调用，调用必留痕，痕与痕前后相衔成链。</li>
          </ul>
        </section>

        {/* ── 怎么存（格式标准明示）── */}
        <section data-testid="nca-how">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">怎么存（格式标准）</h3>
          <p className="mb-3 text-xs text-gray-500">
            全站唯一标准＝NCA 存证格式（在册格式标准现行版）。存证一律带链：以链标识、前序存证指针与自身摘要前后相衔，任何一环可独立校验。
          </p>

          <div className="mb-3">
            <h4 className="mb-1.5 text-xs font-medium text-gray-700">十三项统一字段</h4>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {FIELDS_13.map((f) => (
                <div key={f.k} className="rounded border border-gray-200 bg-white px-2.5 py-1.5">
                  <code className="text-[11px] font-medium text-slate-700">{f.k}</code>
                  <span className="ml-2 text-[11px] text-gray-500">{f.d}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mb-3">
            <h4 className="mb-1.5 text-xs font-medium text-gray-700">义务块六键（每一次执行皆须齐备）</h4>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {OBLIGATION_6.map((f) => (
                <div key={f.k} className="rounded border border-gray-200 bg-white px-2.5 py-1.5">
                  <code className="text-[11px] font-medium text-slate-700">{f.k}</code>
                  <span className="ml-2 text-[11px] text-gray-500">{f.d}</span>
                </div>
              ))}
            </div>
            <p className="mt-1.5 text-[11px] text-gray-400">
              其中负空间检查块含检查版本／是否触发／触发缘由三键；人类签名块含状态／签署人／签署时点三键——涉及人类签批的操作，签名块不可缺。
            </p>
          </div>

          <div>
            <h4 className="mb-1.5 text-xs font-medium text-gray-700">合规六条（现行）</h4>
            <ol className="list-decimal space-y-1 pl-5 text-xs text-gray-600">
              {COMPLIANCE_6.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ol>
          </div>
        </section>

        {/* ── 谁都要存（三一律）── */}
        <section data-testid="nca-who">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">谁都要存（三个一律）</h3>
          <ul className="space-y-1.5 text-xs leading-relaxed text-gray-600">
            <li><strong className="text-gray-800">场景一律</strong>——每一次操作皆留 NCA，无一例外；与「无存证不执行」同一句。</li>
            <li><strong className="text-gray-800">主体一律</strong>——官方（运营方）与用户无差别适用，同一格式、同一标准。</li>
            <li><strong className="text-gray-800">形态一律</strong>——人类用户与智能体无差别适用；智能体之调用尤须落痕——智能体互调即协作，协作必留痕。</li>
          </ul>
        </section>

        <section className="rounded-lg border border-gray-200 bg-gray-50/60 p-3">
          <p className="text-xs leading-relaxed text-gray-500">
            边界：本栏为制度说明面——只讲格式标准、义务与适用口径；真实存证件与链上数据经审计透明等既有在册入口公开可查，本栏不陈列具体存证内容。
          </p>
        </section>
      </div>
    </PageShell>
  )
}
