// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 商学院栏目两页（介绍 /academy ＋ 教材目录 /academy/outline）
// 约束矩阵: TDCA-HANDOFF-EXEC-EDU-PORTAL-001（创始人逐字「可以安排该栏目内容进站的任务了」＋「站点只入目录」）
//          §三 原文照贴·零内部编号·价格留白 ｜ §九 ⛔ 不改一字
// 内容件: biz-intro.md（TDCA-EDU-BIZ-INTRO-001-EXT V1.1 · sha256_16 9C9E83BACC40E70F）
//         outline.md（TDCA-EDU-OUTLINE-001-EXT V1.2 · sha256_16 3C5F8F33511F53AB）
// =============================================================================
import { Link } from 'react-router'
import { MarkdownDoc } from './markdown'
// ⭐ 原文照贴：?raw 原字节进包（⛔ 不经手改写；哈希核验见 __tests__/biz-school.test.tsx）
import introMd from './biz-intro.md?raw'
import outlineMd from './outline.md?raw'

/** 页一：商学院介绍（/academy）——标题档位照附 A「一、一句话」节同序呈现 */
export function BizSchoolIntroPage() {
  return (
    <section data-testid="biz-school-intro" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h1 className="text-xl font-bold text-gray-900">TDCA 商学院</h1>
      <div className="mt-1 mb-4 flex flex-wrap gap-3 text-sm">
        <Link to="/academy/outline" className="text-blue-700 underline hover:text-blue-900">
          教材目录（纲要）→
        </Link>
      </div>
      <MarkdownDoc md={introMd} />
    </section>
  )
}

/** 页二：教材目录（纲要）（/academy/outline）——只放目录，⛔ 不含正文 */
export function BizSchoolOutlinePage() {
  return (
    <section data-testid="biz-school-outline" className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h1 className="text-xl font-bold text-gray-900">教材目录（纲要）</h1>
      <div className="mt-1 mb-4 flex flex-wrap gap-3 text-sm">
        <Link to="/academy" className="text-blue-700 underline hover:text-blue-900">
          ← 返回商学院介绍
        </Link>
      </div>
      <MarkdownDoc md={outlineMd} />
    </section>
  )
}
