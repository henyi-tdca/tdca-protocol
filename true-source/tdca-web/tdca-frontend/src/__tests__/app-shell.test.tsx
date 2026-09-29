// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A1 应用壳测试（DID 三身份 / HUF Banner / 通知机栏 / 层级指示器）
// 约束矩阵: FRAMEWORK-001 §三
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'

function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
})

describe('F0-A1 应用壳', () => {
  it('DID 上下文：H/M/L 三身份切换生效', () => {
    const r = renderApp()
    expect(screen.getByTestId('did-value')).toHaveTextContent('TDID-H-')
    fireEvent.click(screen.getByTestId('did-switcher').querySelector('[data-role="M"]')!)
    expect(screen.getByTestId('did-value')).toHaveTextContent('TDID-M-')
    fireEvent.click(screen.getByTestId('did-switcher').querySelector('[data-role="L"]')!)
    expect(screen.getByTestId('did-value')).toHaveTextContent('TDID-L-')
    r.unmount()
  })

  it('HUF 常驻 Banner：打开模态 → 取消即中止（签批状态不置位）', () => {
    const r = renderApp()
    expect(screen.getByTestId('huf-banner')).toHaveTextContent('HUF 人类最终签批权')
    fireEvent.click(screen.getByTestId('huf-banner-open'))
    expect(screen.getByTestId('huf-modal')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('huf-cancel'))
    expect(screen.queryByTestId('huf-modal')).not.toBeInTheDocument()
    expect(screen.getByTestId('huf-banner-open')).toHaveTextContent('发起签批')
    r.unmount()
  })

  it('HUF 签批确认 → 状态置为已存证', () => {
    renderApp()
    fireEvent.click(screen.getByTestId('huf-banner-open'))
    fireEvent.click(screen.getByTestId('huf-confirm'))
    expect(screen.getByTestId('huf-banner-open')).toHaveTextContent('已签批存证')
  })

  it('通知机状态栏渲染（WS 不可用 → 模拟态降级）', () => {
    renderApp()
    const bar = screen.getByTestId('notifier-bar')
    expect(bar).toBeInTheDocument()
    expect(bar.textContent).toContain('SIMULATED')
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