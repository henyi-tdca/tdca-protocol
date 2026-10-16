// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块一 — 「帮助与联系」薄占位页
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块一（顶栏六入口之第六入口）
//          ⛔ 不新造内容：帮助正文随文档库「帮助」族入站（块二），本页仅占位指路
// =============================================================================
import { PageShell } from './PageShell'

/** 帮助与联系（块一薄占位）：不留死链；帮助族内容块二入站后本页换发为正式版 */
export function HelpPage() {
  return (
    <PageShell
      title="帮助与联系"
      dataSource="静态占位（帮助族入站前）"
      permission="公开"
      description="站点帮助与官方联系入口。"
    >
      <div className="space-y-3 text-sm text-gray-600">
        <p className="flex items-center gap-2">
          <span className="rounded bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700">在建中</span>
          帮助内容随文档库「帮助」族入站（块二施工），联系块同批补入。
        </p>
        <p>
          论坛栏目暂不建、先定位（照终定稿 §二块一）；如需人工协助，请先从右栏「AI 助手」提问，
          或走「确权中心 · 申诉端」（块三，登录后于「我的」内可用）。
        </p>
      </div>
    </PageShell>
  )
}
