// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-F2-001 | 目标函数: L1SI188-NAV-FIX-004 项4 登录墙三要素测试
// 约束矩阵: NAV-FIX-004 §一——只改文案；鉴权行为零变化（未登录仍重定向 /auth，内容仍不可读）
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal('fetch', vi.fn(async () => {
    throw new Error('network down') // 登录墙断言不依赖后端
  }))
})

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('NAV-FIX-004 项4：登录墙三要素（六栏逐栏文案）', () => {
  it('受保护主栏匿名态 → 登录墙含栏目说明＋登录后可见＋就地登录入口', () => {
    renderAt('/studio')
    expect(screen.getByTestId('login-wall')).toBeInTheDocument()
    expect(screen.getByTestId('login-wall-column')).toHaveTextContent('工作台（作业）')
    expect(screen.getByTestId('login-wall-what')).toHaveTextContent('全生命周期')
    expect(screen.getByTestId('login-wall-visible')).toHaveTextContent('登录后可见')
    expect(screen.getByTestId('login-wall-goto-login')).toHaveAttribute('href', '#auth-account-form')
  })

  it('六栏文案两两不同（⛔ 不再同一句模板）', () => {
    const texts = ['/me', '/studio', '/review', '/agents', '/attestation', '/governance'].map((p) => {
      const r = renderAt(p)
      const t = screen.getByTestId('login-wall').textContent ?? ''
      r.unmount()
      return t
    })
    expect(new Set(texts).size).toBe(6)
  })

  it('子路归并：/attestation/meta 与 /attestation/dynamic 命中确权中心栏', () => {
    const r1 = renderAt('/attestation/meta')
    expect(screen.getByTestId('login-wall-column')).toHaveTextContent('确权中心')
    r1.unmount()
    const r2 = renderAt('/attestation/dynamic')
    expect(screen.getByTestId('login-wall-column')).toHaveTextContent('确权中心')
    r2.unmount()
  })

  it('非六栏受护路由（/use/upload）与直接进 /auth → 不渲染登录墙（原通用口径）', () => {
    const r1 = renderAt('/use/upload')
    expect(screen.queryByTestId('login-wall')).toBeNull()
    r1.unmount()
    const r2 = renderAt('/auth')
    expect(screen.queryByTestId('login-wall')).toBeNull()
    r2.unmount()
  })

  it('鉴权行为零变化：未登录访问 /studio 仍落在登录页（auth-form 渲染），受保护内容不出现', () => {
    renderAt('/studio')
    expect(screen.getByTestId('auth-form')).toBeInTheDocument()
    expect(screen.queryByTestId('studio-lifecycle')).toBeNull()
  })
})
