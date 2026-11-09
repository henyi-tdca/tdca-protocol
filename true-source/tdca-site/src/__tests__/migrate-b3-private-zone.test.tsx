// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI206-MIGRATE-B3 私域三空间与公域披露页自测
// 约束矩阵: L1SI178 §五自测——三栏可切换／披露强制（未披露「启用」disabled＋原因旁注）／
//   六槽只读（无输入控件）／流程条五步写死／披露页匿名可查／零编号五式扫描为 0／样例态标注
//   ＋ MIGRATE-B3-001 §四-3：私域面未登录由接口 401/403 把守（前端隐藏 ⛔ 作据）
// 并轨注记: MIGRATE 批3 自旧树 __tests__/pz-private-zone.test.tsx 迁移适配——
//   ① 导入路径换新版（@/pages/MeNode、NodeDisclosure）；路由注册断言换 ROUTE_PATHS；
//   ② 私域三空间页接门禁（auth/me ok 剧本渲染内容；401 剧本验零渲染——新增）；
//   ③ 披露页（公域）与零编号扫描断言一字未动。
// =============================================================================
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

// —— 门禁剧本 ——
let meScript: { ok: boolean } = { ok: true }
vi.mock('@/lib/client', () => ({
  api: {
    get: vi.fn(async (path: string) => {
      if (path.includes('/auth/me')) {
        return meScript.ok
          ? { ok: true, data: { username: 'founder' }, watermark: 'w', nature: 'real' }
          : { ok: false, reason: 'unauthorized', status: 401 }
      }
      return { ok: false, reason: 'http_error' }
    }),
    post: vi.fn(async () => ({ ok: false, reason: 'http_error' })),
  },
  loadDraft: () => null,
  saveDraft: () => undefined,
  clearDraft: () => undefined,
}))

import { MeNodePage } from '@/pages/MeNode'
import { NodeDisclosurePage, validateShape } from '@/pages/NodeDisclosure'
import { ROUTE_PATHS } from '@/pages/PagesIndex'

const BANNED = [/GSEQ-/, /T-/, /COP-/, /A-/, /base_protocol/]

describe('MIGRATE-B3 路由注册', () => {
  it('/me/node 与 /disclosure 入 ROUTE_PATHS（新树 PAGE_META 在册）', () => {
    expect(ROUTE_PATHS).toContain('/me/node')
    expect(ROUTE_PATHS).toContain('/disclosure')
  })
})

describe('私域三空间页：入口＋流程条＋三栏切换（门禁 ok 剧本）', () => {
  it('入口两链在（三栏锚＋公域披露页 /disclosure）', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    expect(await screen.findByTestId('me-node-entry-spaces')).toBeTruthy()
    expect(screen.getByTestId('me-node-entry-disclosure').getAttribute('href')).toBe('/disclosure')
  })

  it('流程条五步写死（私域改动 → … → 域内生效）', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const flow = (await screen.findByTestId('me-node-flow')).textContent ?? ''
    expect(flow).toContain('流程写死')
    expect(flow).toContain('私域改动')
    expect(flow).toContain('生成待披露条目')
    expect(flow).toContain('披露（落存证，可追谁在何时披露哪一版）')
    expect(flow).toContain('回写版本号')
    expect(flow).toContain('域内生效')
  })

  it('三栏可切换：负空间 → 沙盒出盒 → 正空间', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    expect(await screen.findByTestId('me-node-panel-neg')).toBeTruthy()
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

describe('私域三空间页：披露强制与六项硬核只读（门禁 ok 剧本）', () => {
  it('未披露条目「启用」disabled＋原因旁注「须先披露（不披露不可启用）」', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const btn = (await screen.findByTestId('me-node-enable-blocked')) as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    expect(btn.textContent).toBe('启用')
    const neg = screen.getByTestId('me-node-panel-neg').textContent ?? ''
    expect(neg).toContain('未披露')
    expect(neg).toContain('须先披露（不披露不可启用）')
  })

  it('六项硬核六槽齐（H1~H6）· 三栏共同展示', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const hc = await screen.findByTestId('me-node-hardcore')
    for (const id of ['H1', 'H2', 'H3', 'H4', 'H5', 'H6']) {
      expect(hc.querySelector(`[data-testid="me-node-hc-${id}"]`)).not.toBeNull()
    }
    expect(hc.textContent).toContain('只读锁定')
    expect(hc.textContent).toContain('人类签名权不可绕过')
    expect(hc.textContent).toContain('数据性质必标')
  })

  it('六槽只读：hardcore 区内无 input／select／contenteditable', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    const hc = await screen.findByTestId('me-node-hardcore')
    expect(hc.querySelectorAll('input').length).toBe(0)
    expect(hc.querySelectorAll('select').length).toBe(0)
    expect(hc.querySelectorAll('[contenteditable]').length).toBe(0)
  })

  it('样例态标数据性质（虚构样例角标在）', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    await screen.findByTestId('me-node-header')
    expect(screen.getAllByTestId('simulated-badge').length).toBeGreaterThanOrEqual(3)
    expect(screen.getByTestId('me-node-header').textContent).toContain('示例节点·青屿（虚构样例）')
  })
})

describe('私域三空间页：门禁 401 剧本（批3 §四-3：API 层把守，前端隐藏 ⛔ 作据）', () => {
  it('未登录 ⟹ 人话提示在、三空间／六项硬核零渲染', async () => {
    meScript = { ok: false }
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    expect(await screen.findByTestId('private-gate-denied')).toBeTruthy()
    expect(screen.queryByTestId('me-node-spaces')).toBeNull()
    expect(screen.queryByTestId('me-node-hardcore')).toBeNull()
    expect(screen.queryByTestId('me-node-entry')).toBeNull()
    // 页壳在（公开面可达），私域样例数据不露
    expect(screen.getByTestId('me-node-page')).toBeTruthy()
  })
})

describe('公域披露登记簿：公域可查＋登记约定＋三式查', () => {
  it('匿名只读标识在，登记约定三硬句齐', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    expect(screen.getByTestId('disclosure-header').textContent).toContain('匿名可查 · 只读 · 只登记不审批')
    const contract = screen.getByTestId('disclosure-contract').textContent ?? ''
    expect(contract).toContain('披露')
    expect(contract).toContain('改变规则效力边界')
    expect(contract).toContain('只登记、不审批')
    expect(contract).toContain('只增不改')
    expect(contract).toContain('全文不入本簿')
  })

  it('空簿如实：无在册记录文案在，无形状不合', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    expect(screen.queryByTestId('disclosure-shape-error')).toBeNull()
    expect(screen.getByTestId('disclosure-list').textContent).toContain('登记簿现无在册记录')
  })

  it('三式查输入具在（节点／类型／生效日），空簿查询仍如实', () => {
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    expect(screen.getByTestId('disclosure-q-node')).toBeTruthy()
    expect(screen.getByTestId('disclosure-q-type')).toBeTruthy()
    expect(screen.getByTestId('disclosure-q-date')).toBeTruthy()
    fireEvent.change(screen.getByTestId('disclosure-q-node'), { target: { value: 'node-a' } })
    expect(screen.getByTestId('disclosure-list').textContent).toContain('登记簿现无在册记录')
  })

  it('形状闸 fail-closed：digest 非 16 位大写 ⟹ 拒渲染', () => {
    expect(validateShape({ contract: 'nd/1.0', records: [] })).toBeNull()
    const bad = {
      contract: 'nd/1.0',
      records: [{
        record_no: 'R-1', recorded_at: '2026-11-05T10:00:00+08:00', node_id: 'n1',
        rule_type: 't1', rule_digest: 'xyz', rule_ref: 'ref', effective_at: '2026-11-05T00:00:00+08:00',
        supersedes: null, status: 'ACTIVE' as const,
      }],
    }
    expect(validateShape(bad)).toContain('rule_digest')
    expect(validateShape({ contract: 'nd/2.0', records: [] })).toContain('contract')
    const badStatus = { ...bad, records: [{ ...bad.records[0], rule_digest: '0123456789ABCDEF', status: 'OK' as never }] }
    expect(validateShape(badStatus)).toContain('status')
  })
})

describe('零编号五式扫描（渲染 DOM 级 · 应为 0）', () => {
  it('私域三空间页渲染文本五式零命中（门禁 ok 剧本）', async () => {
    meScript = { ok: true }
    const { container } = render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    await screen.findByTestId('me-node-header')
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

  it('零本地存：两页渲染无 localStorage 写入', async () => {
    meScript = { ok: true }
    const spy = Object.getOwnPropertyDescriptor(Storage.prototype, 'setItem')
    let wrote = false
    Object.defineProperty(Storage.prototype, 'setItem', {
      configurable: true,
      value: () => { wrote = true },
    })
    render(<MemoryRouter><MeNodePage /></MemoryRouter>)
    render(<MemoryRouter><NodeDisclosurePage /></MemoryRouter>)
    await screen.findByTestId('me-node-header')
    if (spy) Object.defineProperty(Storage.prototype, 'setItem', spy)
    expect(wrote).toBe(false)
  })
})
