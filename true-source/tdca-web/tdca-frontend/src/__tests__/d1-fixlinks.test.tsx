// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-D1 修「带走」断链测试（改指 selfcheck/spec）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-D1-001 §四/§六——
//   另两条路一字不动（S-1）；openapi.json 与 /docs 失效指向撤下或改说明；
//   页面零编号零价格
// =============================================================================
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { HelpPage } from '@/pages/help'

function mockHelpDocs() {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (String(url).includes('/api/site/docs/help')) {
      return { ok: false, status: 404, json: async () => ({ detail: 'nf' }) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'nf' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); mockHelpDocs() })
afterEach(() => { vi.unstubAllGlobals() })

describe('L1SI175-D1 修「带走」断链（改指 /api/v1/selfcheck/spec）', () => {
  it('S-1 守护：另两条路（验证／贡献）一字未动', async () => {
    render(<MemoryRouter><HelpPage /></MemoryRouter>)
    const verify = screen.getByTestId('help-path-verify')
    expect(verify.textContent).toContain('想验证')
    expect(verify.textContent).toContain('不注册，5 分钟三件自查：公开账本 → 机验徽章 → 形式化清单，全匿名只读。')
    expect(verify.textContent).toContain('/verify（怎么验证）')
    const contribute = screen.getByTestId('help-path-contribute')
    expect(contribute.textContent).toContain('想贡献')
    expect(contribute.textContent).toContain('智能体自助登记入口：登记前先答分流首问，在册流程站内办结。')
    expect(contribute.textContent).toContain('/channel/registry（自助登记）')
  })

  it('「带走」改指 selfcheck/spec：新链接在、openapi.json 失效指向撤下', async () => {
    render(<MemoryRouter><HelpPage /></MemoryRouter>)
    const takeaway = screen.getByTestId('help-path-takeaway')
    expect(takeaway.textContent).toContain('想带走')
    expect(takeaway.textContent).toContain('机器可读校验规格')
    const link = takeaway.querySelector('a[href="/api/v1/selfcheck/spec"]')
    expect(link).not.toBeNull()
    // ⛔ 失效指向：openapi.json 不再是链接；/docs 不再是站内路由链接
    expect(takeaway.querySelector('a[href="/openapi.json"]')).toBeNull()
    expect(takeaway.querySelector('a[href="/docs"]')).toBeNull()
    // 改为说明：两处字样以说明形态保留
    expect(takeaway.textContent).toContain('暂未开放，恢复后另行标注')
  })

  it('帮助族 404 走如实空栏（fail-soft 不受影响）', async () => {
    render(<MemoryRouter><HelpPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('help-list').textContent).toContain('帮助族暂无入库文档'), { timeout: 3000 })
  })

  it('页面零编号零价格（¥/￥/元/价格/档位/付费/EIOS-/S-数字 均不出）', async () => {
    const { container } = render(<MemoryRouter><HelpPage /></MemoryRouter>)
    const text = container.textContent ?? ''
    for (const bad of ['¥', '￥', '元', '价格', '档位', '付费', 'EIOS-']) {
      if (text.includes(bad)) throw new Error(`命中禁样: ${bad}`)
      expect(text.includes(bad)).toBe(false)
    }
    expect(text.match(/S-\d/g) ?? []).toEqual([])
  })
})
