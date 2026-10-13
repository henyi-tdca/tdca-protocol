// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 + 20261009-ANN | 目标函数: 公告发布栏前端测试（operator 显隐＋发布回流）
// 约束矩阵: 2026-10-09 开工令（发布面施工：仅 operator 可见；不预置内容）
// 并轨注记: 随面迁入新版树（FRONTEND-MERGE 批1）；⚠️ 新版树暂未配 vitest 运行器，随搬备跑·如实标注「暂不可跑」
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { AnnouncementsPage } from '@/pages/Announcements'

function envelope(payload: unknown, nature = 'real') {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-10-09T00:00:00Z', data_nature: nature }
}

const LIST_EMPTY = { count: 0, announcements: [], note: '公告栏（对外公告区）' }

function mockAll(role: string | null) {
  vi.stubGlobal('fetch', vi.fn(async (url: string, opts?: RequestInit) => {
    const u = String(url)
    if (opts?.method === 'POST' && u.includes('/api/v1/announcements/publish')) {
      return { ok: true, status: 201, json: async () => envelope({ announcement_id: 'AN-test123ab', title: '站点建设进展', nca_ref: 'NCA-ANN-test' }) } as Response
    }
    if (u.includes('/api/v1/me/dashboard')) {
      if (role === null) return { ok: false, status: 401, json: async () => ({ detail: '未登录' }) } as Response
      return { ok: true, status: 200, json: async () => envelope({ session: { role } }) } as Response
    }
    if (u.includes('/api/v1/announcements/list')) {
      return { ok: true, status: 200, json: async () => envelope(LIST_EMPTY) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('公告发布栏（2026-10-09 开工令）', () => {
  it('operator → 渲染发布栏；发布成功显示公告号与存证号', async () => {
    mockAll('operator')
    render(<MemoryRouter><AnnouncementsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ann-publish')).toBeTruthy())
    fireEvent.change(screen.getByTestId('ann-title'), { target: { value: '站点建设进展' } })
    fireEvent.change(screen.getByTestId('ann-body'), { target: { value: '首条公告正文' } })
    fireEvent.click(screen.getByTestId('ann-publish-btn'))
    await waitFor(() => expect(screen.getByTestId('ann-msg').textContent).toContain('AN-test123ab'))
    expect(screen.getByTestId('ann-msg').textContent).toContain('NCA-ANN-test')
  })

  it('founder → 渲染发布栏', async () => {
    mockAll('founder')
    render(<MemoryRouter><AnnouncementsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ann-publish')).toBeTruthy())
  })

  it('viewer → 不渲染发布栏（公开列表照常）', async () => {
    mockAll('viewer')
    render(<MemoryRouter><AnnouncementsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ann-empty')).toBeTruthy())
    expect(screen.queryByTestId('ann-publish')).toBeNull()
  })

  it('未登录 → 不渲染发布栏（公开列表照常）', async () => {
    mockAll(null)
    render(<MemoryRouter><AnnouncementsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ann-empty')).toBeTruthy())
    expect(screen.queryByTestId('ann-publish')).toBeNull()
  })

  it('空标题或空正文 → 不发请求，提示补全', async () => {
    mockAll('operator')
    render(<MemoryRouter><AnnouncementsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ann-publish')).toBeTruthy())
    fireEvent.change(screen.getByTestId('ann-body'), { target: { value: '只有正文' } })
    fireEvent.click(screen.getByTestId('ann-publish-btn'))
    await waitFor(() => expect(screen.getByTestId('ann-msg').textContent).toContain('不得为空'))
    const calls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls
    expect(calls.some((c) => c[1]?.method === 'POST')).toBe(false)
  })
})
