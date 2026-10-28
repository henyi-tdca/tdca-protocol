// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 批3 C块 — 首页公告条（一行高）
// 约束矩阵: L1SI177 SITE-FIND-CODE-001 §一.C（首页一条，一行高；空态不渲染、不占首屏；
//          后端不可用／无公告 → 整条不渲染，fail-closed）
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { Link } from 'react-router'
import { useApiGet } from '@/shared/useApi'

interface NoticeBoard {
  count: number
  announcements: {
    announcement_id: string
    title: string
    published_at: string
    withdrawn_at?: string | null
  }[]
  note: string
}

/**
 * 首页公告条：页头下方一条（h-9＝一行高）。取最新一条未撤回公告；
 * 无公告／后端不可用 → 渲染 null（空态呈现，不挤动首屏）。
 */
export function HomeNoticeBar() {
  const { status, data } = useApiGet<NoticeBoard>('/api/v1/announcements/list')
  if (status !== 'ok' || !data) return null
  const latest = (data.announcements ?? []).find((a) => !a.withdrawn_at)
  if (!latest) return null
  return (
    <div
      data-testid="home-notice"
      className="mb-3 flex h-9 items-center gap-2 overflow-hidden whitespace-nowrap rounded-lg border border-amber-200 bg-amber-50 px-3 text-[13px]"
    >
      <span className="shrink-0 rounded bg-amber-100 px-1.5 py-px text-xs font-medium text-amber-700">公告</span>
      <Link to="/announcements" className="min-w-0 flex-1 truncate text-gray-800 hover:underline">
        {latest.title}
      </Link>
      <span className="shrink-0 text-xs text-amber-700">{latest.published_at.slice(0, 10)}</span>
      <Link to="/announcements" className="shrink-0 text-xs text-blue-700 hover:underline">
        查看
      </Link>
    </div>
  )
}
