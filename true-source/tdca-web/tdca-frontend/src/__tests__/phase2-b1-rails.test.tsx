// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批1 — 三栏骨架测试（左流程栏／右我的+助手）
// =============================================================================
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ProcessRail } from '@/app/process-rail'
import { RightRail } from '@/app/right-rail'
import { AuthProvider } from '@/app/auth-context'

vi.mock('@/api/client', () => ({
  api: { get: vi.fn() },
}))

import { api } from '@/api/client'

describe('二期改版批1：三栏骨架', () => {
  it('左栏流程栏随路由上下文切换（studio → 创建流程）', () => {
    render(
      <MemoryRouter initialEntries={['/studio']}>
        <ProcessRail />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('process-rail-title').textContent).toContain('创建智能体流程')
    expect(screen.getByTestId('process-rail').textContent).toContain('HUF 签署负责')
  })

  it('左栏流程栏未知路由回落默认导览', () => {
    render(
      <MemoryRouter initialEntries={['/something-new']}>
        <ProcessRail />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('process-rail-title').textContent).toContain('站点导览')
  })

  it('右栏含「我的」卡与 AI 助手会话框', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <RightRail />
        </AuthProvider>
      </MemoryRouter>,
    )
    expect(screen.getByTestId('me-card')).toBeTruthy()
    expect(screen.getByTestId('assistant-panel')).toBeTruthy()
    expect(screen.getByTestId('assistant-input')).toBeTruthy()
  })

  it('助手框发问→命中时给出直达与步骤（真 AI／规则表由端点裁决）', async () => {
    ;(api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: { matched: true, title: '治理中心', route: '/governance', guide: ['HUF 签批表单（需登录）'] },
    })
    render(
      <MemoryRouter>
        <AuthProvider>
          <RightRail />
        </AuthProvider>
      </MemoryRouter>,
    )
    fireEvent.change(screen.getByTestId('assistant-input'), { target: { value: '我要签批' } })
    fireEvent.click(screen.getByTestId('assistant-send'))
    await waitFor(() => expect(screen.getByTestId('assistant-msgs').textContent).toContain('治理中心'))
    expect(screen.getByTestId('assistant-msgs').textContent).toContain('直达')
  })

  it('助手框失败 fail-soft：不猜测，明示不可用', async () => {
    ;(api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: false })
    render(
      <MemoryRouter>
        <AuthProvider>
          <RightRail />
        </AuthProvider>
      </MemoryRouter>,
    )
    fireEvent.change(screen.getByTestId('assistant-input'), { target: { value: '随便问' } })
    fireEvent.click(screen.getByTestId('assistant-send'))
    await waitFor(() =>
      expect(screen.getByTestId('assistant-msgs').textContent).toContain('意图服务暂不可用'),
    )
  })
})
