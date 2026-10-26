// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项二 · 官方资产区验收
// 约束矩阵: AMEND-1（产物＝付费橱窗）＋ AMEND-2（工具九类·官智与用户皆可用）
//   ＋ AMEND-3（工具免费＋配置调用计费两层并行）＋ B5-AMEND-1（调用未开放·⛔ 零支付）
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect } from 'vitest'
import App from '@/App'

describe('B5 项二 · 官方资产区（公域新增）', () => {
  it('/official-assets 渲染：栏目在位、权限公开、工具在上产物在下', () => {
    render(
      <MemoryRouter initialEntries={['/official-assets']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-shell')).toBeInTheDocument()
    expect(screen.getByTestId('official-assets-page')).toBeInTheDocument()
    expect(screen.getByText(/官方资产区（官方工具 · 官方产物）/)).toBeInTheDocument()
    expect(screen.getByText('权限：公开')).toBeInTheDocument()
    // 工具在上（九类清单抽查；免费标记在位）
    const tools = screen.getByTestId('official-tools')
    expect(tools).toHaveTextContent('智能合约')
    expect(tools).toHaveTextContent('编译器')
    expect(tools).toHaveTextContent('反函数求解器')
    expect(tools).toHaveTextContent('skill（技能）')
    expect(tools).toHaveTextContent('免费')
    // 产物在下（付费标记在位）
    const products = screen.getByTestId('official-products')
    expect(products).toHaveTextContent('观测包')
    expect(products).toHaveTextContent('治理包')
    expect(products).toHaveTextContent('付费')
    // 计价明示在位
    expect(products).toHaveTextContent(/0\.01 元/)
  })

  it('调用入口为未开放态（disabled），本期无任何支付入口（B5-AMEND-1）', () => {
    render(
      <MemoryRouter initialEntries={['/official-assets']}>
        <App />
      </MemoryRouter>,
    )
    const callBtn = screen.getByTestId('product-call-disabled')
    expect(callBtn).toBeInTheDocument()
    expect(callBtn).toBeDisabled()
    // ⛔ 零支付集成：凡标「支付／购买／收款」的按钮必须不可点（页壳其他按钮不在此口径）
    const body = document.body.textContent ?? ''
    for (const btn of screen.queryAllByRole('button')) {
      const label = btn.textContent ?? ''
      if (/支付|购买|收款/.test(label)) {
        expect(btn).toBeDisabled()
      }
    }
    expect(body).not.toMatch(/扫码支付|支付宝|微信支付/)
  })

  it('三层收益结构在位（工具免费／产物付费／配置调用计费·与调度税两层并行）', () => {
    render(
      <MemoryRouter initialEntries={['/official-assets']}>
        <App />
      </MemoryRouter>,
    )
    const rev = screen.getByTestId('revenue-structure')
    expect(rev).toHaveTextContent('免费')
    expect(rev).toHaveTextContent('付费')
    expect(rev).toHaveTextContent('计费')
    expect(rev).toHaveTextContent(/两层/)
  })

  it('⛔ 无内部编号／凭据样式（S-3 守检）', () => {
    render(
      <MemoryRouter initialEntries={['/official-assets']}>
        <App />
      </MemoryRouter>,
    )
    const body = document.body.textContent ?? ''
    expect(body).not.toMatch(/GSEQ-\d/)
    expect(body).not.toMatch(/L1SI1\d\d/)
    expect(body).not.toMatch(/HANDOFF-[A-Z]|WITNESS-|TDCA-RULING/)
    expect(body).not.toMatch(/ghp_[A-Za-z0-9]|PRIVATE KEY|AKID[A-Za-z0-9]/)
  })

  it('公共导航「服务」栏含官方工具入口（官方资产区拆基础/增值两行，同页 /official-assets）', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    expect(nav).toHaveTextContent('官方工具')
    expect(nav).toHaveTextContent('官方产物与增值')
  })
})
