// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块三 — 申诉端 /me/appeal 薄占位
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块三（申诉端占位：无令载细则，⛔ 不编造受理表单/渠道）
// 口径: 只说明受理面在建＋链帮助页；受理渠道随制度入站开通后再补
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from './PageShell'

/** 申诉端（薄占位）：受理通道随制度入站开通；⛔ 不预置受理表单与渠道 */
export function MeAppealPage() {
  return (
    <PageShell dataNature="real"
      title="申诉"
      dataSource="—（受理面在建）"
      permission="须登录（谁的事谁可见）"
      description="对惩罚处置（冻结／降权／吊销）的申诉受理面。受理通道随制度入站开通，开通前不在此预置表单与渠道。"
    >
      <section data-testid="me-appeal-placeholder" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-sm text-gray-600">
        <p className="mb-2">
          申诉受理通道<strong>在建中</strong>：受理范围、材料要件与办理时限以制度入站件为准，本站不预置、不代拟。
        </p>
        <p>
          通用操作指引可先查 <Link to="/help" className="text-blue-700 underline hover:text-blue-900">帮助与联系</Link>；
          惩罚三态（冻结／降权／吊销）的现行口径见个人后台与制度公开面。
        </p>
      </section>
    </PageShell>
  )
}
