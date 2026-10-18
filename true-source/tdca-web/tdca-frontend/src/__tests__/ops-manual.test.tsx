// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 手册接口化前端测试（/ops/manual 左清单右正文）
// 约束矩阵: TDCA-HANDOFF-OPS-INACCOUNT-DEPLOY-001 §三-D（站内直读；yaml 可复制；fail-closed）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { OpsManualPage } from '@/pages/ops-manual'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-10-17T00:00:00Z', data_nature: 'real' }
}

const FILES = [
  { name: 'manual-a.md', label: '运维手册（人读）', sha256_16: 'AAAAAAAAAAAAAAAA', bytes: 100, missing: false },
  { name: 'spec.yaml', label: '入站留痕制度（机读）', sha256_16: 'BBBBBBBBBBBBBBBB', bytes: 50, missing: false },
  { name: 'gone.md', label: '缺失件', missing: true },
]

function mockAll() {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const u = String(url)
    if (u.includes('/api/v1/ops/files') && !u.includes('/files/manual') && !u.includes('/files/spec')) {
      return { ok: true, status: 200, json: async () => envelope({ total: 3, files: FILES }) } as Response
    }
    if (u.includes('/api/v1/ops/files/manual-a.md')) {
      return { ok: true, status: 200, text: async () => '# 运维手册\n值班守检七项。' } as Response
    }
    if (u.includes('/api/v1/ops/files/spec.yaml')) {
      return { ok: true, status: 200, text: async () => 'version: V1.0' } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('手册接口化 · /ops/manual', () => {
  it('清单在册件全列、缺失件不列；默认开首件正文', async () => {
    mockAll()
    render(<MemoryRouter><OpsManualPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-manual-list')).toBeInTheDocument())
    expect(screen.getByText('运维手册（人读）')).toBeInTheDocument()
    expect(screen.getByText('入站留痕制度（机读）')).toBeInTheDocument()
    expect(screen.queryByText('缺失件')).not.toBeInTheDocument()   // missing 不渲染
    await waitFor(() => expect(screen.getByTestId('ops-manual-body')).toHaveTextContent('值班守检七项'))
  })

  it('点选 yaml 件出正文＋复制钮；md 件无复制钮', async () => {
    mockAll()
    render(<MemoryRouter><OpsManualPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-manual-body')).toBeInTheDocument())
    fireEvent.click(screen.getByText('入站留痕制度（机读）'))
    await waitFor(() => expect(screen.getByTestId('ops-manual-body')).toHaveTextContent('version: V1.0'))
    expect(screen.getByTestId('ops-manual-copy')).toBeInTheDocument()
  })

  it('取件失败 fail-closed 明示', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      ({ ok: false, status: 403, json: async () => ({ detail: 'forbidden' }) }) as Response))
    render(<MemoryRouter><OpsManualPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-manual-fail')).toBeInTheDocument())
  })
})
