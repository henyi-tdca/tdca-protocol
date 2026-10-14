// 批 5 执行体自证：官方执行体目录、加载即激活、两分清分野、身份前置三判据
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '../App'

// jsdom 无 canvas：拓扑引擎（cytoscape）打桩；本批断言不涉及拓扑
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

describe('批 5：官方执行体目录面', () => {
  it('目录就位：五执行体卡齐，逐体三句（角色/能干/怎么用）', () => {
    renderAt('/agents')
    expect(screen.getByTestId('executors-directory')).toBeInTheDocument()
    const names = ['trainer', 'executor', 'auditor', 'service', 'genie']
    for (const k of names) {
      const card = screen.getByTestId(`executor-${k}`).textContent ?? ''
      expect(card).toContain('我是')
      expect(card).toContain('我能干')
      expect(card).toContain('怎么用')
      expect(card).toContain('在线')
    }
  })

  it('遮蔽 M-1：公开面不见离线能力表述（离线/本地部署零出现）', () => {
    renderAt('/agents')
    const dir = screen.getByTestId('executors-directory').textContent ?? ''
    expect(dir).not.toContain('离线')
    expect(dir).not.toContain('本地部署')
  })

  it('执行体不是用户：明示官方集群＝制度自己的执行体', () => {
    renderAt('/agents')
    expect(screen.getByTestId('executors-directory').textContent).toContain('不是普通用户')
    expect(screen.getByTestId('executors-directory').textContent).toContain('制度自己的执行体')
  })

  it('加载协议＝权限激活：不必逐次签发，权限以制度职责为界', () => {
    renderAt('/agents')
    const el = screen.getByTestId('load-activates').textContent ?? ''
    expect(el).toContain('加载协议')
    expect(el).toContain('激活')
    expect(el).toContain('不必逐次签发')
    expect(el).toContain('制度职责')
  })

  it('两分清：制度执行不逐次授权／资产使用仍须授权（授权码）', () => {
    renderAt('/agents')
    expect(screen.getByTestId('sep-institutional').textContent).toContain('不逐次授权')
    const asset = screen.getByTestId('sep-asset').textContent ?? ''
    expect(asset).toContain('仍须授权')
    expect(asset).toContain('授权码')
    expect(asset).toContain('不等于授权本身')
    expect(screen.getByTestId('executors-directory').textContent).toContain('四把钥匙')
  })

  it('身份前置判据齐：先定身份／不得越其锚（记名级·不发高权面）；遮蔽 M-2（不见固锚级/模拟态实体状态）', () => {
    renderAt('/agents')
    const el = screen.getByTestId('identity-precursor').textContent ?? ''
    expect(el).toContain('先定身份')
    expect(el).toContain('身份确定')
    expect(el).toContain('不得越其锚')
    expect(el).toContain('记名级')
    expect(el).toContain('高权无限制面不发')
    expect(el).not.toContain('固锚级')
    expect(el).not.toContain('通知机现为模拟态')
    expect(el).not.toContain('不对外声称')
    expect(el).toContain('由人类签发')
    expect(el).toContain('不得代签')
    expect(el).toContain('不得分发任务')
  })

  it('批 4 措辞更正＋名称纪律：事务执行面标「静态兜底（随浏览器存留）」与「写操作钥匙（待建执行令牌之临时替代）」', () => {
    renderAt('/me')
    const quad = screen.getByTestId('quad-execution').textContent ?? ''
    expect(quad).toContain('静态兜底')
    expect(quad).toContain('随浏览器存留')
    expect(quad).toContain('写操作钥匙')
    expect(quad).toContain('待建执行令牌之临时替代')
  })
})
