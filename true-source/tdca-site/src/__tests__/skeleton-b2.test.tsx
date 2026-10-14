// 批 2 骨架自证：两轴落位、频道首页就位、/ops 管理员入口归位
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '../App'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('批 2 骨架：全局壳与两轴', () => {
  it('任一页顶部有频道横轴、左侧有协作流程竖列', () => {
    renderAt('/about')
    expect(screen.getByTestId('app-nav')).toBeInTheDocument()
    const nav = screen.getByTestId('process-nav')
    expect(nav).toBeInTheDocument()
    expect(screen.getByText('门户')).toBeInTheDocument()
    expect(screen.getByText('工具与运维')).toBeInTheDocument()
    expect(nav.textContent).toContain('争议裁决')
  })

  it('全局细横条二件保留（意图直达＋登录状态）', () => {
    renderAt('/about')
    expect(screen.getByTestId('intent-bar')).toBeInTheDocument()
    expect(screen.getByTestId('auth-login-link')).toBeInTheDocument()
  })

  it('管理员入口归位：在顶部横轴右端，指向 /ops（不加门）', () => {
    renderAt('/about')
    const admin = screen.getByTestId('nav-admin')
    expect(admin).toHaveAttribute('href', '/ops')
  })

  it('频道首页五路就位：以门户为例（一句话＋入口卡片＋协作环节）', () => {
    renderAt('/channel/portal')
    expect(screen.getByTestId('channel-home')).toBeInTheDocument()
    expect(screen.getByText('公告栏')).toBeInTheDocument()
    expect(screen.getByText(/相关协作环节：/)).toBeInTheDocument()
  })

  it('工具与运维频道首页不含运维端入口（已归管理员空间）', () => {
    renderAt('/channel/tools')
    expect(screen.queryByText('运维端')).not.toBeInTheDocument()
    expect(screen.getByText('沙盒')).toBeInTheDocument()
  })
})
