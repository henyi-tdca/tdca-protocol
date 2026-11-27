// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /ownership L1 所有权市场（确权向导 + 登记簿）
// 约束矩阵: REV-002 §三（L1 法定确权层，ID43）+ §8C（确权路径向导 + 登记簿只读）
// 预期分配: 确权向导五步 + 登记簿（公开只读，模拟态 ID92）
// =============================================================================
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { ReadOnlyStream } from '@/shared/guards'

const ATTEST_PATH = [
  { step: 1, title: '提交至法定交易中心', desc: '国家可信版权链 / 交易所（外部接口）' },
  { step: 2, title: '交易中心审核', desc: '法律合规 + 原创性审查' },
  { step: 3, title: '生成所有权证书', desc: '链上哈希存证（NCA 水印）' },
  { step: 4, title: '证书与 TDCA DID 绑定', desc: '所有权人身份锚定' },
  { step: 5, title: '进入 L2 配置权市场', desc: '所有权确权后，配置权方可流转' },
]

const REGISTRY = [
  { asset: 'AST-001', owner: 'TDID-H-0001', date: '2026-08-01', authority: '国家可信版权链', status: 'CERTIFIED' },
  { asset: 'AST-002', owner: 'TDID-H-0002', date: '2026-08-05', authority: '交易所（模拟）', status: 'CERTIFIED' },
  { asset: 'AST-003', owner: 'TDID-H-0003', date: '2026-08-10', authority: '国家可信版权链', status: 'PENDING' },
]

/** L1 所有权市场：所有权不得在协议网络内流转（ID43），确权须经法定交易中心 */
export function OwnershipPage() {
  return (
    <PageShell
      title="所有权市场（L1 法定确权层）"
      dataSource="法定交易中心接口（外部）+ 登记簿只读"
      permission="公开读 / 确权操作须 HUF"
      description="所有权不得在协议网络内流转：确权路径向导 / 转让 / 登记簿公开查询。"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          层级关系（不可越级/不可混淆）：所有权 ⊃ 配置权 ⊃ 效用计量 <SimulatedBadge nature="simulated" />
        </div>

        {/* 确权路径向导（REV-002 §8C.2 五步） */}
        <section data-testid="ownership-attest-path" className="rounded-lg border border-blue-200 bg-blue-50/50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-blue-800">确权路径向导（法定交易中心接口）</h3>
          <ol className="space-y-1.5">
            {ATTEST_PATH.map((s) => (
              <li key={s.step} className="flex items-start gap-2 text-sm">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white">
                  {s.step}
                </span>
                <span>
                  <span className="font-medium text-gray-800">{s.title}</span>
                  <span className="ml-2 text-xs text-gray-500">{s.desc}</span>
                </span>
              </li>
            ))}
          </ol>
        </section>

        {/* 接入适配包（只读 · 自助下载）——TDCA-HANDOFF-EXEC-L1SI234-ADAPTPUB-001 §三 文案逐字；⛔改确权向导 ⛔改登记簿 */}
        <section data-testid="ownership-adapt-pack" className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-emerald-800">接入适配包（只读 · 自助下载）</h3>
          <p className="mb-2 text-sm text-gray-700">
            拟与本网络对接的平台，可在此下载六份适配材料并按之自查改造；机读字段规格随附。不能完成适配者不得接入。
          </p>
          <div className="space-y-2 text-sm">
            <div>
              <div className="mb-1 text-xs font-semibold text-gray-500">人读材料 6 件</div>
              <ul className="space-y-0.5">
                {[
                  '版权确权规则一致性清单.md',
                  '登记规则对照表.md',
                  '登记信息模板包.md',
                  '接入方制度最小集清单.md',
                  '字段级schema包.md',
                  '交易信息公开范围与回传数据字典.md',
                ].map((name) => (
                  <li key={name}>
                    <a className="text-blue-700 underline" href={`/api/public/docs/adapt/${encodeURIComponent(name)}`}>
                      {name.replace(/\.md$/, '')}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="mb-1 text-xs font-semibold text-gray-500">机器可校验规格与样例 12 件</div>
              <ul className="space-y-0.5">
                {[
                  'd1-consistency.json',
                  'd2-rules.json',
                  'd3-fields.json',
                  'd3-example-ok.json',
                  'd3-example-reject.json',
                  'd5-aggregate.schema.json',
                  'd5-detail.schema.json',
                  'd5-registration.schema.json',
                  'd5-relay.schema.json',
                  'd5-trade-info.schema.json',
                  'd6-public-fields.json',
                  'd6-relay-dict.json',
                ].map((name) => (
                  <li key={name}>
                    <a className="text-blue-700 underline" href={`/api/public/docs/adapt/${encodeURIComponent(name)}`}>
                      {name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* 所有权登记簿（公开只读，BV-3） */}
        <ReadOnlyStream
          title="所有权登记簿（公开查询）"
          data={REGISTRY}
          nature="simulated"
        />
      </div>
    </PageShell>
  )
}
