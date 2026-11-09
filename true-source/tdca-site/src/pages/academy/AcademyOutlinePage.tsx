// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 商学院栏目——教材目录（纲要）（/academy/outline）
// 约束矩阵: TDCA-HANDOFF-EXEC-EDU-PORTAL-001（「站点只入目录」）
//          §三 原文照贴·零内部编号·价格留白 ｜ §九 ⛔ 不改一字
// 追平批B1（L1SI206-PARITY-B1）：旧版 biz-school.tsx 页二直拷（接缝＝markdown 渲染器同拷＋outline.md ?raw 原字节）
// 内容件: outline.md（旧版 academy/outline.md 原字节随批，⛔ 不经手改写）
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from '@/components/PageShell'
import { MarkdownDoc } from './markdown'
// ⭐ 原文照贴：?raw 原字节进包（⛔ 不经手改写）
import outlineMd from './outline.md?raw'

/** 页二：教材目录（纲要）（/academy/outline）——只放目录，⛔ 不含正文 */
export function AcademyOutlinePage() {
  return (
    <PageShell
      title="教材目录（纲要）"
      dataSource="静态文案（照贴）"
      permission="公开"
      description="商学院教材目录（纲要）：五卷 35 册编排，正文不入站。"
    >
      <div data-testid="biz-school-outline">
        <div className="mb-4 text-sm">
          <Link to="/academy" className="text-blue-700 underline hover:text-blue-900">
            ← 返回商学院
          </Link>
        </div>
        <MarkdownDoc md={outlineMd} />
      </div>
    </PageShell>
  )
}
