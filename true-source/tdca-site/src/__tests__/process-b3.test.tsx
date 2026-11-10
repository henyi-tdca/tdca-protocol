// 批 3 内容自证：协作流程汇总页就位、14 环四能文案、左轴直链
import { describe, expect, it } from 'vitest'
import { render, screen, waitFor} from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '../App'

async function renderAt(path: string) {
  const __r = render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
  await waitFor(() => { expect(screen.queryByTestId('route-loading')).not.toBeInTheDocument() })
  return __r
}

describe('批 3：协作流程汇总页（/process）', () => {
  it('页面就位：process-overview 容器存在', async () => {
    await renderAt('/process')
    expect(screen.getByTestId('process-overview')).toBeInTheDocument()
  })

  it('14 环全就位：ring-1 至 ring-14 的 testid 齐', async () => {
    await renderAt('/process')
    for (let i = 1; i <= 14; i += 1) {
      expect(screen.getByTestId(`ring-${i}`)).toBeInTheDocument()
    }
  })

  it('环 1 四能文案齐：是什么／如何行动／规则／后果', async () => {
    await renderAt('/process')
    const ring1 = screen.getByTestId('ring-1').textContent ?? ''
    expect(ring1).toContain('是什么')
    expect(ring1).toContain('如何行动')
    expect(ring1).toContain('规则')
    expect(ring1).toContain('后果')
  })

  it('环 7 签约含「不得代签」规则原文', async () => {
    await renderAt('/process')
    const ring7 = screen.getByTestId('ring-7').textContent ?? ''
    expect(ring7).toContain('签约')
    expect(ring7).toContain('不得代签')
  })

  it('左轴环节名直达本节：首个环链接 href=/process#ring-1', async () => {
    await renderAt('/about')
    const nav = screen.getByTestId('process-nav')
    const firstRingLink = nav.querySelector('a[href="/process#ring-1"]')
    expect(firstRingLink).not.toBeNull()
  })
})
