// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 追平批B4（L1SI206-PARITY-B4）验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-PARITY-B4-001 §四验收——
//   ① /verify 匿名态可点可读（三件自查区块渲染·不登录亦走完全程入口）
//   ② 两旧链重定向实测（/assets → /five-orders；/ops/manual → /ops/readme，⛔ 只看代码）
//   ③ 索引三产物机算自洽（/verify 入册；两旧链重定向 ⛔ 入栏目索引）
//   ④ 375px 四字段逐面过（见测量回报；本件为 jsdom 路由级实测）
//   ⑤ vitest/tsc/build 终值（见回报 -229）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'
import { PAGE_META, ROUTE_PATHS } from '@/pages/PagesIndex'

// 路由级实测走整 App（AuthProvider＋SiteLayout 俱在）；fetch/api 不外呼
beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals(); window.history.pushState({}, '', '/') })

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('追平批B4：/verify 怎么验证 · 5 分钟三件自查（公开面·匿名可达）', () => {
  it('匿名态直开：三件自查三件在架（公开账本/机验徽章/形式化清单）', async () => {
    renderAt('/verify')
    await waitFor(() => expect(screen.getByTestId('verify-page')).toBeTruthy())
    expect(screen.getByTestId('verify-intro')).toBeTruthy()
    // 三件自查（一/二/三）逐件渲染——匿名不注册亦可见入口
    expect(screen.getByTestId('verify-step-一')).toBeTruthy()
    expect(screen.getByTestId('verify-step-二')).toBeTruthy()
    expect(screen.getByTestId('verify-step-三')).toBeTruthy()
    // 自助验链四区块挂架（spec/anchor/selfcheck 区块在；失败 fail-closed 人话兜底，不白屏）
    expect(screen.getByTestId('verify-spec')).toBeTruthy()
    expect(screen.getByTestId('verify-anchor-block')).toBeTruthy()
    expect(screen.getByTestId('verify-selfcheck')).toBeTruthy()
  })
})

describe('追平批B4：两旧链重定向（重定向实测·⛔ 只看代码）', () => {
  it('/assets → 落在五序资产总览（导轨＋资产页俱在）', async () => {
    renderAt('/assets')
    await waitFor(() => expect(screen.getByTestId('assets-page')).toBeTruthy())
    expect(screen.getByTestId('main-chain-guide')).toBeTruthy()
  })

  it('/ops/manual → 落在运维 readme（等价裁示 GSEQ-7743）', async () => {
    renderAt('/ops/manual')
    await waitFor(() => expect(screen.getByTestId('ops-readme')).toBeTruthy())
  })
})

describe('追平批B4：索引入册（/verify 入册·两旧链重定向 ⛔ 入册）', () => {
  it('PAGE_META 35→36（+1 /verify）；两旧链 ⛔ 入册', () => {
    expect(PAGE_META).toHaveLength(38) /* SMALL2-001：+2（/me/compile /me/privacy 入册） */
    expect(PAGE_META.find((m) => m.path === '/verify')?.title).toBe('怎么验证 · 5 分钟三件自查')
    expect(ROUTE_PATHS).toContain('/verify')
    expect(ROUTE_PATHS).not.toContain('/assets')
    expect(ROUTE_PATHS).not.toContain('/ops/manual')
  })
})

// jsdom 无 canvas：Ω 区打桩（照旧例；全 App 渲染过首页 Ω）
vi.mock('@/lib/TopologyEngine', () => ({
  TopologyEngine: () => null,
  hashAgentId: (id: string) => 'hash-' + id,
}))
