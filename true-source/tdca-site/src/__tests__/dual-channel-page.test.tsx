// DUALCH-021 双通道等价对照页测试（四例必绿）
// ① 一表可读：十二行六列（功能域／人／机／共用后端／等价型／缺侧理由）
// ② 丙型显式「仅人」徽标＋理由在页（运维手册；⛔混排不区分）
// ③ 页首通俗说明在页；页零内部编号（GSEQ-／NCA- 件号不渲染；institution_ref 不得出现在 DOM）
// ④ 数据不可用 → 降级提示（fail-closed，不猜测数据）
import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, afterEach } from 'vitest'

const MANIFEST = [
  { domain: '验收结论查询', human_path: '/acceptance', machine_path: '/api/v1/acceptance/verdicts', shared_backend: true, equivalence_type: '乙', single_side_reason: 'n/a', updated_at: '2026-11-23T21:00:00+08:00' },
  { domain: '节点网络', human_path: '/node-net', machine_path: '/docs/regulation/x.yaml（机读条例）', shared_backend: true, equivalence_type: '甲', single_side_reason: 'n/a', updated_at: '2026-11-23T21:00:00+08:00' },
  { domain: '运维手册', human_path: '/ops-manual', machine_path: 'none', shared_backend: false, equivalence_type: '丙', single_side_reason: '仅人——手册人读定稿；非公开机通道（不造公开机读镜像）', updated_at: '2026-11-23T21:00:00+08:00' },
]

vi.mock('@/lib/client', () => ({
  api: {
    get: vi.fn((path: string) => {
      if ((globalThis as any).__dc_fail) return Promise.resolve({ ok: false, reason: 'fail_closed' })
      if (path === '/api/v1/dual-channel') return Promise.resolve({ ok: true, data: MANIFEST, nature: 'real' })
      return Promise.resolve({ ok: false, reason: 'http_error' })
    }),
  },
}))

import { DualChannelPage } from '../pages/DualChannelPage'

afterEach(() => {
  ;(globalThis as any).__dc_fail = false
  vi.clearAllMocks()
})

describe('DualChannelPage（DUALCH-021 验收）', () => {
  it('一表可读：表头六列齐＋数据行渲染', async () => {
    render(<DualChannelPage />)
    await waitFor(() => expect(screen.getByTestId('dc-table')).toBeTruthy())
    for (const h of ['功能域', '人怎么走', '机怎么走', '共用后端', '等价型', '缺侧理由']) {
      expect(screen.getAllByText(h).length).toBeGreaterThan(0)
    }
    expect(screen.getAllByTestId('dc-row').length).toBe(3)
    expect(screen.getAllByText('/acceptance').length).toBeGreaterThan(0)
  })

  it('丙型显式「仅人」徽标＋理由在页', async () => {
    render(<DualChannelPage />)
    await waitFor(() => expect(screen.getByTestId('dc-table')).toBeTruthy())
    expect(screen.getAllByTestId('dc-side-badge').length).toBe(1)
    expect(screen.getByTestId('dc-side-badge').textContent).toBe('仅人')
    expect(screen.getAllByText(/仅人——手册人读定稿/).length).toBeGreaterThan(0)
    expect(screen.getAllByText('丙·单通道').length).toBe(1)
    expect(screen.getAllByText('甲·全共享同源').length).toBe(1)
    expect(screen.getAllByText('乙·双通道各有').length).toBe(1)
  })

  it('页首通俗说明在页；DOM 零内部编号', async () => {
    render(<DualChannelPage />)
    await waitFor(() => expect(screen.getByTestId('dc-lede')).toBeTruthy())
    expect(screen.getByTestId('dc-lede').textContent).toContain('本表说明同一件事人与智能体各自怎么做')
    const dom = document.body.innerHTML
    expect(dom).not.toContain('GSEQ-')
    expect(dom).not.toContain('institution_ref')
    expect(dom).not.toContain('TDCA-STD-')
    expect(dom).not.toContain('SITEDEP')
  })

  it('数据不可用 → 降级提示（fail-closed）', async () => {
    ;(globalThis as any).__dc_fail = true
    render(<DualChannelPage />)
    await waitFor(() => expect(screen.getByTestId('dc-fail')).toBeTruthy())
    expect(screen.getByTestId('dc-fail').textContent).toContain('不猜测')
    expect(screen.queryByTestId('dc-table')).toBeNull()
  })
})
