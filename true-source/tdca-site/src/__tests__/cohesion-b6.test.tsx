// 批 6 咬合收口自证：三项明示呈现更新就位
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '../App'

// jsdom 无 canvas：拓扑引擎打桩（同批 5 先例）
vi.mock('@/lib/TopologyEngine', () => ({
  TopologyEngine: () => null,
  hashAgentId: (s: string) => `h-${s}`,
}))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('批 6：三项明示呈现更新', () => {
  it('签发链三层一句：人类签发初始／经一并许可向下一序列签发子任务令牌／无许可不得签发分发', () => {
    renderAt('/agents')
    const el = screen.getByTestId('identity-precursor').textContent ?? ''
    expect(el).toContain('初始任务由人类签发')
    expect(el).toContain('一并许可')
    expect(el).toContain('下一序列任务执行体')
    expect(el).toContain('子任务执行令牌')
    expect(el).toContain('无许可不得签发')
    expect(el).toContain('不得分发任务')
    expect(el).toContain('不得代签')
  })

  it('离线能力现时不对外：与通知机实体可部署同一时点一并对外', () => {
    renderAt('/agents')
    const dir = screen.getByTestId('executors-directory').textContent ?? ''
    expect(dir).toContain('现时不对外')
    expect(dir).toContain('通知机实体可部署')
    expect(dir).toContain('本地部署')
  })

  it('分野层次写清：制度规则 ⊃ 资产用权管理；制度执行＝规则落地动作；不是两套并列', () => {
    renderAt('/agents')
    const dir = screen.getByTestId('executors-directory').textContent ?? ''
    expect(dir).toContain('制度规则（全体）⊃ 资产使用权限管理')
    expect(dir).toContain('规则约束的落地动作')
    expect(dir).toContain('不是两套并列')
    expect(dir).toContain('四把钥匙')
  })

  it('环 9 与分野共轴不矛盾：人类签发初始层仍可见', () => {
    renderAt('/process')
    expect(screen.getByTestId('ring-9').textContent).toContain('人类签发')
  })
})
