// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 /ownership L1 所有权市场（确权向导 + 登记簿）
// 约束矩阵: REV-002 §三（L1 法定确权层，ID43）+ §8C（确权路径向导 + 登记簿只读）
// 预期分配: 确权向导五步 + 登记簿（公开只读，模拟态 ID92）
// =============================================================================
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { ReadOnlyStream } from '@/lib/read-only-stream'

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
