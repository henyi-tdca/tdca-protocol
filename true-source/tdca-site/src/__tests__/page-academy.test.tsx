// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（知识学院，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + A-6 契约 + G-1
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为知识学院 1 用例，字句未改。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { AcademyPage } from '@/pages/AcademyPage'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-12T00:00:00Z', data_nature: 'simulated' }
}

function mockApi(pathPart: string, payload: unknown, fail = false) {
  const fn = vi.fn(async (url: string, _init?: RequestInit) => {
    if (fail) throw new Error('network down')
    if (!url.includes(pathPart)) throw new Error(`unexpected url ${url}`)
    return { ok: true, status: 200, json: async () => envelope(payload) } as Response
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

beforeEach(() => {
  localStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('F1 橱窗层页面接线 · 知识学院', () => {
  it('知识学院：A-6 术语渲染 + 检索过滤（G-1）', async () => {
    mockApi('/api/v1/knowledge/terms', {
      terms: [
        { term: '配置权', id: 'ID76', def: '不拥有参数，只拥有场景化调用权' },
        { term: 'MOU', id: 'ID79', def: '最低可见效用' },
      ],
      total: 2,
      note: 'G-1 子集',
    })
    render(<AcademyPage />)
    await waitFor(() => expect(screen.getByTestId('academy-terms')).toBeInTheDocument())
    expect(screen.getByText('配置权')).toBeInTheDocument()
    fireEvent.change(screen.getByTestId('academy-search'), { target: { value: 'MOU' } })
    expect(screen.queryByText('配置权')).not.toBeInTheDocument()
    expect(screen.getByText('MOU')).toBeInTheDocument()
  })
})
