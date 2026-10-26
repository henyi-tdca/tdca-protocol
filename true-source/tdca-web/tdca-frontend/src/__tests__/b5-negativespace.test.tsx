// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项一 · 负空间栏验收
// 约束矩阵: 交办令验收六条（公域栏在位／不露私域／⛔ 无禁项词表与内部编号）
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect } from 'vitest'
import App from '@/App'

describe('B5 项一 · 负空间栏（公域新增）', () => {
  it('/negativespace 渲染：栏目在位、权限公开、三空间与机制面齐全', () => {
    render(
      <MemoryRouter initialEntries={['/negativespace']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-shell')).toBeInTheDocument()
    expect(screen.getByTestId('negativespace-page')).toBeInTheDocument()
    expect(screen.getByText(/负空间 · 什么不能做/)).toBeInTheDocument()
    expect(screen.getByText('权限：公开')).toBeInTheDocument()
    // 三空间与机制（原则与类别级）
    expect(screen.getByText('正空间')).toBeInTheDocument()
    expect(screen.getByText('负空间函数语言（NSFL）')).toBeInTheDocument()
    expect(screen.getAllByText(/拒绝清单/).length).toBeGreaterThan(0)
    // 红线声明在位（只讲原则与类别）
    expect(screen.getByTestId('negativespace-redline')).toHaveTextContent(/不列/)
  })

  it('⛔ 无内部编号／凭据样式／禁项词表（S-3 守检）', () => {
    render(
      <MemoryRouter initialEntries={['/negativespace']}>
        <App />
      </MemoryRouter>,
    )
    const body = document.body.textContent ?? ''
    expect(body).not.toMatch(/GSEQ-\d/)
    expect(body).not.toMatch(/L1SI1\d\d/)
    expect(body).not.toMatch(/HANDOFF-[A-Z]|WITNESS-|TDCA-RULING/)
    expect(body).not.toMatch(/ghp_[A-Za-z0-9]|PRIVATE KEY|AKID[A-Za-z0-9]/)
  })

  it('公共导航「了解 TDCA」栏含负空间入口', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    expect(nav).toHaveTextContent('负空间')
  })
})
