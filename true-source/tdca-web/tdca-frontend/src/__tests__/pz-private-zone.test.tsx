// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI178 私域三空间与公域披露页测试
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI178-SITE-PRIVATE-ZONE-002 §五自测与§七回报——
//   三栏可切换／披露强制（未披露「启用」disabled＋原因旁注）／六槽只读（无输入控件）／
//   流程条五步写死／披露页匿名可查含版本历史／零编号五式扫描为 0／样例态标数据性质
// =============================================================================
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { MeNodePage } from '@/pages/me-node'
import { NodeDisclosurePage } from '@/pages/node-disclosure'
import { PAGE_COMPONENTS, ROUTE_PATHS } from '@/pages/pages'

const BANNED = [/GSEQ-/, /T-/, /COP-/, /A-/, /base_protocol/]

describe('L1SI178 路由注册（甲案）', () => {
  it('/me/node 与 /disclosure 入 ROUTE_PATHS 且组件映射齐', () => {
    expect(ROUTE_PATHS).toContain('/me/node')
    expect(ROUTE_PATHS).toContain('/disclosure')
    expect(PAGE_COMPONENTS['/me/node']).toBeTruthy()
    expect(PAGE_COMPONENTS['/disclosure']).toBeTruthy()
  })
})

describe('私域三空间页：入口＋流程条＋三栏切换', () => {
  it('入口两链在（三栏锚＋公域披露页 /disclosure）', () => {
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    expect(screen.getByTestId('me-node-entry-spaces')).toBeTruthy()
    expect(screen.getByTestId('me-node-entry-disclosure').getAttribute('href')).toBe('/disclosure')
  })

  it('流程条五步写死（私域改动 → … → 域内生效）', () => {
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const flow = screen.getByTestId('me-node-flow').textContent ?? ''
    expect(flow).toContain('流程写死')
    expect(flow).toContain('私域改动')
    expect(flow).toContain('生成待披露条目')
    expect(flow).toContain('披露（落存证，可追谁在何时披露哪一版）')
    expect(flow).toContain('回写版本号')
    expect(flow).toContain('域内生效')
  })

  it('三栏可切换：负空间 → 沙盒出盒 → 正空间', () => {
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    expect(screen.getByTestId('me-node-panel-neg')).toBeTruthy()
    expect(screen.queryByTestId('me-node-panel-sandbox')).toBeNull()
    fireEvent.click(screen.getByTestId('me-node-tab-sandbox'))
    expect(screen.getByTestId('me-node-panel-sandbox')).toBeTruthy()
    expect(screen.queryByTestId('me-node-panel-neg')).toBeNull()
    fireEvent.click(screen.getByTestId('me-node-tab-pos'))
    expect(screen.getByTestId('me-node-panel-pos')).toBeTruthy()
    const pos = screen.getByTestId('me-node-panel-pos').textContent ?? ''
    expect(pos).toContain('本栏内容「仅域内生效」——未经披露，不构成对外依据。')
  })
})

describe('私域三空间页：披露强制与六项硬核只读', () => {
  it('未披露条目「启用」disabled＋原因旁注「须先披露（不披露不可启用）」', () => {
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const btn = screen.getByTestId('me-node-enable-blocked') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    expect(btn.textContent).toBe('启用')
    const neg = screen.getByTestId('me-node-panel-neg').textContent ?? ''
    expect(neg).toContain('未披露')
    expect(neg).toContain('须先披露（不披露不可启用）')
  })

  it('六项硬核六槽齐（H1~H6）· 三栏共同展示', () => {
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const hc = screen.getByTestId('me-node-hardcore')
    for (const id of ['H1', 'H2', 'H3', 'H4', 'H5', 'H6']) {
      expect(hc.querySelector(`[data-testid="me-node-hc-${id}"]`)).not.toBeNull()
    }
    expect(hc.textContent).toContain('只读锁定')
    expect(hc.textContent).toContain('人类签名权不可绕过')
    expect(hc.textContent).toContain('数据性质必标')
  })

  it('六槽只读：hardcore 区内无 input／select／contenteditable', () => {
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const hc = screen.getByTestId('me-node-hardcore')
    expect(hc.querySelectorAll('input').length).toBe(0)
    expect(hc.querySelectorAll('select').length).toBe(0)
    expect(hc.querySelectorAll('[contenteditable]').length).toBe(0)
  })

  it('样例态标数据性质（虚构样例角标在）', () => {
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    expect(screen.getAllByTestId('simulated-badge').length).toBeGreaterThanOrEqual(3)
    expect(screen.getByTestId('me-node-header').textContent).toContain('示例节点·青屿（虚构样例）')
  })
})

describe('公域披露页：匿名可查＋版本历史＋筛选', () => {
  it('匿名标识在，条目含三空间', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    expect(screen.getByTestId('disclosure-header').textContent).toContain('匿名可查 · 无需登录 · 公示才公信')
    const list = screen.getByTestId('disclosure-list').textContent ?? ''
    expect(list).toContain('否决动作留痕判据')
    expect(list).toContain('沙盒出盒门槛（三次演练）')
    expect(list).toContain('域内知识库分层上架约定（披露节选）')
  })

  it('版本历史默认收起 → 点开可见旧版（含失效原因）', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    expect(screen.queryByTestId('disclosure-hist-否决动作留痕判据')).toBeNull()
    fireEvent.click(screen.getByTestId('disclosure-hist-toggle-否决动作留痕判据'))
    const hist = screen.getByTestId('disclosure-hist-否决动作留痕判据').textContent ?? ''
    expect(hist).toContain('第 1 版')
    expect(hist).toContain('已失效')
    expect(hist).toContain('被第 2 版替代。')
  })

  it('按节点／按空间两维筛选生效', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('按节点名筛选'), { target: { value: '示例节点·白鹿' } })
    expect(screen.getByTestId('disclosure-list').textContent).toContain('域内知识库分层上架约定（披露节选）')
    expect(screen.queryByTestId('disclosure-card-否决动作留痕判据')).toBeNull()
    fireEvent.change(screen.getByLabelText('按空间筛选'), { target: { value: '负空间' } })
    expect(screen.getByTestId('disclosure-list').textContent).toContain('当前筛选条件下暂无披露条目')
  })
})

describe('零编号五式扫描（渲染 DOM 级 · 应为 0）', () => {
  it('私域三空间页渲染文本五式零命中', () => {
    const { container } = render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const text = container.textContent ?? ''
    for (const re of BANNED) {
      expect(text.match(re) ?? [], String(re)).toEqual([])
    }
  })

  it('公域披露页渲染文本五式零命中', () => {
    const { container } = render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    const text = container.textContent ?? ''
    for (const re of BANNED) {
      expect(text.match(re) ?? [], String(re)).toEqual([])
    }
  })

  it('零本地存：两页渲染无 localStorage 写入', () => {
    const spy = Object.getOwnPropertyDescriptor(Storage.prototype, 'setItem')
    let wrote = false
    Object.defineProperty(Storage.prototype, 'setItem', {
      configurable: true,
      value: () => { wrote = true },
    })
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    if (spy) Object.defineProperty(Storage.prototype, 'setItem', spy)
    expect(wrote).toBe(false)
  })
})
