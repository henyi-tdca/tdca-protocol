// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: VISUAL-001 可视化增强测试（/sandbox NSFL 三层防线，拆自 visual）
// 约束矩阵: TDCA-FRONTEND-VISUAL-001
// 拆搬说明：旧 visual.test.tsx 按场景拆为 5 件，本件为 P2-3 用例，字句未改；
//   共享脚手架（envelope/fetch 桩）逐字随件。页 import 适配新树 named export。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { SandboxPage } from '@/pages/SandboxPage'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-13T00:00:00Z', data_nature: 'simulated' }
}

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const s = String(url)
    if (s.includes('/api/v1/sandbox/sea-status')) {
      return {
        ok: true,
        status: 200,
        json: async () => envelope({
          sea: [
            { requirement: '任务书六要素', status: 'GREEN', note: 'FROZEN' },
            { requirement: '激活系数>1.2 门槛', status: 'AMBER', note: '待真实数据' },
          ],
          all_green: false,
          note: '模拟态',
        }),
      } as Response
    }
    throw new Error('unexpected url')
  }))
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('VISUAL-001 可视化增强 · /sandbox', () => {
  it('P2-3 /sandbox：NSFL 三层防线状态机（编译期 → 运行期 → 发布期）', async () => {
    render(<SandboxPage />)
    await waitFor(() => expect(screen.getByTestId('nsfl-layers')).toBeInTheDocument())
    expect(screen.getByText('编译期 · C1-C6')).toBeInTheDocument()
    expect(screen.getByText('运行期 · L1 / R5-R8')).toBeInTheDocument()
    expect(screen.getByText('发布期 · Layer-8')).toBeInTheDocument()
    expect(screen.getByTestId('nsfl-flow-0')).toHaveTextContent('→')
  })
})
