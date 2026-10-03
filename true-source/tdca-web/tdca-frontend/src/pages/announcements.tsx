// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 公告栏（对外公告区）
// 约束矩阵: 创始人 2026-10-04 明示「对外公告，要有公告栏」
// 口径: 本次只建【公告栏功能】；公告内容须创始人逐次明示后才可发布——
//       ⛔ 不自行拟稿、⛔ 不先行发布、⛔ 不预置示例公告冒充正式公告；
//       对外纪律：零内部编号、零凭据值、零人名、零自然人敏感信息。
// =============================================================================
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface AnnouncementView {
  announcement_id: string
  title: string
  body: string
  published_at: string
}

interface BoardData {
  count: number
  announcements: AnnouncementView[]
  note: string
}

/** 公告栏：对外公告区（公开可读；初始空栏为常态） */
export function AnnouncementsPage() {
  const { status, data, nature } = useApiGet<BoardData>('/api/v1/announcements/list')

  return (
    <PageShell
      title="公告栏"
      dataSource="A-23 GET /api/v1/announcements/list（公开读）"
      permission="公开"
      description="站点对外公告区：公告内容经创始人明示后由运营发布；空栏为常态，不预置内容。"
    >
      <div className="space-y-4">
        {status === 'loading' && <p className="text-sm text-gray-400">加载中…</p>}
        {status === 'fail' && (
          <p className="rounded bg-red-50 p-3 text-sm text-red-600" data-testid="ann-fail-closed">
            [fail-closed] 公告栏后端不可用，拒绝渲染
          </p>
        )}
        {status === 'ok' && data && (
          <section data-testid="ann-list" className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <SimulatedBadge nature={nature ?? 'simulated'} />
              <span>{data.note}</span>
            </div>
            {data.count === 0 ? (
              <p className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-500"
                 data-testid="ann-empty">
                暂无公告。
              </p>
            ) : (
              data.announcements.map((a) => (
                <article key={a.announcement_id}
                         className="rounded-lg border border-gray-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-gray-900">{a.title}</h3>
                  <p className="mt-0.5 text-xs text-gray-400">{a.published_at}</p>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700">{a.body}</p>
                </article>
              ))
            )}
          </section>
        )}
      </div>
    </PageShell>
  )
}
