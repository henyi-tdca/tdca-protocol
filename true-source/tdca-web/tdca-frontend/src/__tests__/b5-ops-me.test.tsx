// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项四 · 运维「我的」验收
// 约束矩阵: DESIGN-OPS-ME-001（两套「我的」独立）＋ 交办令项四（六栏只读占位；
//   申诉受理只读；⛔ 不复用用户 /me 组件、不共路由 S-6）
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect } from 'vitest'
import App from '@/App'

describe('B5 项四 · 运维「我的」（/ops/me 只读六栏）', () => {
  it('/ops/me 渲染：栏目在位、六栏只读占位齐', () => {
    render(
      <MemoryRouter initialEntries={['/ops/me']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-shell')).toBeInTheDocument()
    expect(screen.getByTestId('ops-me-page')).toBeInTheDocument()
    expect(screen.getByText('运维我的（站与服务的）')).toBeInTheDocument()
    // 六栏在位（testid 逐一断言）
    for (const key of ['ops-me-site', 'ops-me-service', 'ops-me-governance', 'ops-me-audit', 'ops-me-emergency', 'ops-me-account']) {
      expect(screen.getByTestId(key)).toBeInTheDocument()
    }
    // 申诉受理为只读口径
    expect(screen.getByTestId('ops-me-service')).toHaveTextContent(/申诉受理（只读队列）/)
    // 只读占位声明：无任何可点操作按钮（页壳 HUF 横幅除外）
    const page = screen.getByTestId('ops-me-page')
    expect(page.querySelectorAll('button').length).toBe(0)
    expect(page.querySelectorAll('input').length).toBe(0)
  })

  it('站务栏内容口径（公域维护核对面）', () => {
    render(
      <MemoryRouter initialEntries={['/ops/me']}>
        <App />
      </MemoryRouter>,
    )
    const site = screen.getByTestId('ops-me-site')
    for (const t of ['公域内容在位核对', '公开面守检', '入口与白名单核对']) {
      expect(site).toHaveTextContent(t)
    }
  })

  it('S-6 零复用：与用户 /me 不共路由、内容不重叠', () => {
    render(
      <MemoryRouter initialEntries={['/ops/me']}>
        <App />
      </MemoryRouter>,
    )
    const page = screen.getByTestId('ops-me-page')
    // ⛔ 不混入用户「我的」的私有资产/业务栏目
    for (const banned of ['我的智能体', '配置权资产', '确权办理', '人机协作', '签批待办']) {
      expect(page).not.toHaveTextContent(banned)
    }
  })

  it('⛔ 无内部编号／凭据样式（S-3 守检）', () => {
    render(
      <MemoryRouter initialEntries={['/ops/me']}>
        <App />
      </MemoryRouter>,
    )
    const body = document.body.textContent ?? ''
    expect(body).not.toMatch(/GSEQ-\d/)
    expect(body).not.toMatch(/L1SI1\d\d/)
    expect(body).not.toMatch(/HANDOFF-[A-Z]|WITNESS-|TDCA-RULING|TDCA-DESIGN/)
    expect(body).not.toMatch(/ghp_[A-Za-z0-9]|PRIVATE KEY|AKID[A-Za-z0-9]/)
  })

  it('/ops 运维端含「运维我的」入口链接', () => {
    render(
      <MemoryRouter initialEntries={['/ops']}>
        <App />
      </MemoryRouter>,
    )
    const entry = screen.getByTestId('ops-me-entry')
    expect(entry).toBeInTheDocument()
    expect(entry).toHaveAttribute('href', '/ops/me')
  })
})
