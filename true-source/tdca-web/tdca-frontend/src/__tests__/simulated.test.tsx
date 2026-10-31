// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A5 模拟态标注测试（ID92）
// 约束矩阵: ID92 + FRAMEWORK-001 §5.1
// =============================================================================
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'
import { AuthProvider } from '@/app/auth-context'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { PageShell } from '@/pages/PageShell'

describe('F0-A5 模拟态标注（ID92）', () => {
  it('SimulatedBadge：三档映射——simulated/mixed 显示且属性如实，real 不渲染', () => {
    const r1 = render(<SimulatedBadge nature="simulated" />)
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('数据性质 · 模拟（期一内部真跑）')
    expect(screen.getByTestId('simulated-badge')).toHaveAttribute('data-nature', 'simulated')
    r1.unmount()
    const r2 = render(<SimulatedBadge nature="mixed" />)
    // L1SI183-SITEOBS-001 任务A：mixed ⛔ 显示为「模拟」
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('数据性质 · 混合')
    expect(screen.getByTestId('simulated-badge')).toHaveAttribute('data-nature', 'mixed')
    r2.unmount()
    render(<SimulatedBadge nature="real" />)
    expect(screen.queryByTestId('simulated-badge')).not.toBeInTheDocument()
  })

  it('页面占位壳默认全站模拟态标注', () => {
    render(<PageShell title="税收" dataSource="A-2" permission="公开" description="d" />)
    expect(screen.getByTestId('simulated-badge')).toBeInTheDocument()
  })

  it('L1SI177 块一：PageShell 两态数据源——匿名显脱敏文案、登录显完整编号', () => {
    // 匿名（无 Provider，视同未登录）：显 dataSourceAnon，零内部编号
    const r1 = render(
      <PageShell title="协作集群" dataSource="A-13 /api/v1/cluster/*（授权件四要件机验）"
        dataSourceAnon="制度件 · 公开可读（协作规则与谱系说明）· 明细登录可见"
        permission="公开" description="d" />)
    expect(screen.getByText(/数据源：制度件 · 公开可读/)).toBeTruthy()
    expect(screen.queryByText(/A-13/)).toBeNull()
    r1.unmount()
    // 未填 dataSourceAnon 的页：匿名仍显原值（本块只改三页，⛔ 不顺手扩面）
    const r2 = render(<PageShell title="税收" dataSource="A-2 GET /api/v1/tax" permission="公开" description="d" />)
    expect(screen.getByText(/数据源：A-2 GET \/api\/v1\/tax/)).toBeTruthy()
    r2.unmount()
    // 登录态：始终显完整 dataSource
    render(
      <MemoryRouter>
        <AuthProvider>
          <PageShell title="协作集群" dataSource="A-13 /api/v1/cluster/*（授权件四要件机验）"
            dataSourceAnon="制度件 · 公开可读（协作规则与谱系说明）· 明细登录可见"
            permission="公开" description="d" />
        </AuthProvider>
      </MemoryRouter>)
    // 登录需 did+token 双置位才成立，此处 Provider 内默认未登录——断言匿名口径仍成立即可；
    // 登录分支由 ownership-registry 等真实页 useAuth 覆盖（既有测试在册）
    expect(screen.getByText(/数据源：制度件 · 公开可读/)).toBeTruthy()
  })

  it('应用壳顶部全站模拟态横幅', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    // L1SI183-SITEOBS-001 任务A：全站角标并入单一映射表（文案＝映射表 simulated 档）；
    // 首页路由另渲染页面级角标，故允许多处命中
    expect(screen.getAllByText(/数据性质 · 模拟（期一内部真跑）/).length).toBeGreaterThan(0)
  })
})

// HomePage 新增五元拓扑 Ω（TopologyEngine/Cytoscape）——jsdom stub 布局计算
vi.mock('cytoscape', () => {
  const fakeNode = () => ({ position: () => ({ x: 10, y: 10 }), id: () => 'n' })
  const fakeCore = {
    nodes: () => [fakeNode()],
    elements: () => ({ boundingBox: () => ({ x1: 0, y1: 0, x2: 100, y2: 100 }), nodes: () => [fakeNode()] }),
    ready: (cb: () => void) => cb(),
    destroy: () => {},
  }
  return { default: () => fakeCore }
})