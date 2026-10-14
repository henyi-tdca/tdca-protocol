// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 页面接线测试（所有权市场，拆自 pages-f1）
// 约束矩阵: FRAMEWORK-001 §四 + A-2 契约
// 拆搬说明：旧 pages-f1.test.tsx 按页拆为 8 件，本件为所有权市场 1 用例，字句未改。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OwnershipPage } from '@/pages/OwnershipPage'

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

describe('F1 橱窗层页面接线 · 所有权市场', () => {
  it('所有权市场：确权路径向导五步 + 登记簿只读（无编辑路径）', () => {
    render(<OwnershipPage />)
    expect(screen.getByTestId('ownership-attest-path')).toBeInTheDocument()
    expect(screen.getByText('提交至法定交易中心')).toBeInTheDocument()
    expect(screen.getByText('进入 L2 配置权市场')).toBeInTheDocument()
    const registry = screen.getByText('所有权登记簿（公开查询）')
    expect(registry).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
