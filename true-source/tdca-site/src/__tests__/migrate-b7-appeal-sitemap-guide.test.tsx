// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: MIGRATE 批7（L1SI206）申诉面＋站点地图＋主链导轨挂载验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B7-001 §三
//   ① 申诉面 me-appeal 直拷渲染（薄占位口径，⛔不预置受理表单）
//   ② sitemap 条目≡静态路由数（/ops* 私域不入；零内部编号机扫）
//   ③ 主链导轨挂主链在册实路由（⛔全站；/five-orders 新版无路由⛔挂，照实登记）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { readFileSync } from 'node:fs'
import App from '../App'
import { MeAppealPage } from '@/pages/MeAppealPage'
import { MePage } from '@/pages/MeConsole'
import { AuthProvider } from '@/lib/auth-context'

// jsdom 无 canvas：拓扑引擎打桩（批5/批6 先例）
vi.mock('@/lib/TopologyEngine', () => ({
  TopologyEngine: () => null,
  hashAgentId: (s: string) => `h-${s}`,
}))

// vitest 进程 cwd＝包根（true-source/tdca-site），仓根＝上两级（批3既有测试同式取盘）
const repoRoot = process.cwd().replace(/\\/g, '/').replace(/\/true-source\/tdca-site\/?$/, '/')
const appSrc = readFileSync(repoRoot + 'true-source/tdca-site/src/App.tsx', 'utf-8')
const sitemap = readFileSync(repoRoot + 'deploy/ops-files/public-static/sitemap.xml', 'utf-8')

/** 静态路由表（机取：含 ':' 动态参或 '*' 通配不入图） */
const ROUTES = [...appSrc.matchAll(/<Route path="([^"]+)"/g)]
  .map((m) => m[1])
  .filter((p) => !p.includes(':') && p !== '*')
const SITEMAP_ENTRIES = [...sitemap.matchAll(/<loc>https:\/\/tdca\.com\.cn([^<]*)<\/loc>/g)].map((m) => m[1] || '/')

/** 编号形态禁则（照 build-search-index.mjs FORBIDDEN 表逐字同源，机扫 sitemap） */
const FORBIDDEN = [/\bCOP-\d+\b/gi, /\bGSEQ-\d+\b/g, /(^|[^A-Z0-9])A-\d+(?![0-9])/g, /\bT-\d{3}\b/g, /base_protocol/gi,
  /\bTDCA-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}\b/g, /\bPUB-CORPUS-\d+\b/g]

function envelope(payload: unknown, nature = 'real') {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-11-09T00:00:00Z', data_nature: nature }
}

const ME_PAYLOAD = {
  session: { username: 'tester', role: 'viewer', expires_at: '2026-11-09T13:30:00+00:00' },
  pending_count: 0,
  my_agents: [],
  my_pending_sign: [],
  my_decided: [],
  my_sandbox: [],
  my_governance: [],
  my_assets: [],
  my_grants: [],
  my_ownership: [],
  my_config_records: [],
  my_points: { balance: 0, data_provenance: 'simulated', note: 't' },
  my_nca: [],
  note: 'test',
}

function mockByUrl(routes: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    for (const [part, payload] of Object.entries(routes)) {
      if (url.includes(part)) return { ok: true, status: 200, json: async () => envelope(payload) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

async function renderAt(path: string) {
  const __r = render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
  await waitFor(() => { expect(screen.queryByTestId('route-loading')).not.toBeInTheDocument() })
  return __r
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('MIGRATE 批7：申诉面（MYSPACE-PHASE1-001 §一.4 补齐口径，2026-11-11 更替薄占位）', () => {
  it('受理面渲染：最小必填登记表单在页＋口径逐字（事由/对象/诉求必填，附件选填不整包索取）', async () => {
    // PrivateGate 探针放行（登录态）后渲染表单本体
    mockByUrl({ '/api/v1/auth/me': { username: 'tester' } })
    render(<MemoryRouter><MeAppealPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-appeal-form')).toBeTruthy())
    expect(screen.getByTestId('me-appeal-reason')).toBeTruthy()
    expect(screen.getByTestId('me-appeal-target')).toBeTruthy()
    expect(screen.getByTestId('me-appeal-claim')).toBeTruthy()
    expect(screen.getByTestId('me-appeal-attachment')).toBeTruthy()
    // 最小必填标注（照 GSEQ-7831 最小集）＋站内登记口径如实
    expect(screen.getByTestId('me-appeal-form').textContent).toContain('最小必填：事由／对象／诉求')
    expect(screen.getByTestId('me-appeal-form').textContent).toContain('不入账、不产生存证号')
    // 三态状态机展示（已提交/受理中/已裁定）
    expect(screen.getByTestId('me-appeal-states').textContent).toContain('已提交')
    expect(screen.getByTestId('me-appeal-states').textContent).toContain('已裁定')
  })

  it('匿名不可见：未登录（401）⟹ 引导登录＋零数据渲染（§一.5 口径，PrivateGate 把守）', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 401, json: async () => ({ detail: 'unauthorized' }) }) as Response))
    await renderAt('/me/appeal')
    await waitFor(() => expect(screen.getByTestId('private-gate-denied')).toBeTruthy())
    expect(screen.queryByTestId('me-appeal-form')).toBeNull()
  })

  it('个人面入口可寻：me 登录态见申诉入口，提交路径与旧版同（/me/appeal）', async () => {
    mockByUrl({ '/api/v1/me/dashboard': ME_PAYLOAD })
    render(<MemoryRouter><AuthProvider><MePage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-comm-appeal-entry')).toBeTruthy())
    expect(screen.getByTestId('me-comm-appeal-entry').getAttribute('href')).toBe('/me/appeal')
  })
})

describe('MIGRATE 批7：站点地图 ≡ 静态路由数（/ops* 私域不入）', () => {
  it('条目数≡静态路由数−/ops*−受护面（机取机算，⛔手编塞条目）', () => {
    // 追平批B3：/authorization/panel 为受护面（PARITY-B3-001 §三「⛔ 入公域栏目索引」），
    // 与 /ops* 私域同口径零入图；公式随批更正，⛔ 手编塞条目
    // 追平批B4（PARITY-B4-001 §三）：/assets 为重定向旧链（→/five-orders），重定向⛔入图；
    // /ops/manual 已被 /ops* 私域规则滤除（等价裁示 GSEQ-7743：→/ops/readme）
    // MYSPACE-PHASE1-001（L1SI207 §一.5）：/me/asset /me/registry /me/config /me/nca 为私域新建面
    // （匿名 PrivateGate 引导登录），照 /authorization/panel 受护面同口径零入图
    // SEG2-BATCH2-001（L1SI208 REFIRE A/B 块）：/me/compile 区 2A 编译向导＋/me/privacy 数据四档
    // 同为私域新建面（匿名 PrivateGate 零数据渲染），照同口径零入图；公开站点地图册亦不入
    // （照 MYSPACE 受护面先例：/pages PAGE_META 不收匿名引导登录之私域面，发现性由 /me 控制台实链卡承担）
    const PROTECTED_FROM_SITEMAP = ['/authorization/panel', '/assets', '/me/asset', '/me/registry', '/me/config', '/me/nca', '/me/compile', '/me/privacy']
    const ops = ROUTES.filter((p) => p === '/ops' || p.startsWith('/ops/'))
    const expected = ROUTES.filter((p) => !ops.includes(p) && !PROTECTED_FROM_SITEMAP.includes(p))
    expect(ops.length).toBeGreaterThan(0)
    expect(SITEMAP_ENTRIES).toHaveLength(expected.length)
    expect(new Set(SITEMAP_ENTRIES)).toEqual(new Set(expected))
  })

  it('/ops* 三私域（实测四条 /ops、/ops/changelog、/ops/ops、/ops/readme）零入图', () => {
    for (const p of ['/ops', '/ops/changelog', '/ops/ops', '/ops/readme']) {
      expect(SITEMAP_ENTRIES).not.toContain(p)
    }
  })

  it('零内部编号机扫（FORBIDDEN 表逐词过 sitemap 全文）', () => {
    for (const re of FORBIDDEN) {
      re.lastIndex = 0
      expect(re.test(sitemap)).toBe(false)
    }
  })

  it('旧树残留清尽：sitemap 条目全部在新版路由表内', () => {
    for (const e of SITEMAP_ENTRIES) {
      expect(ROUTES).toContain(e)
    }
  })
})

describe('MIGRATE 批7：主链导轨挂载（仅主链在册实路由七页）', () => {
  it.each([
    ['/', '门户首页'],
    ['/channel', '智能体通道'],
    ['/agents', '智能体集群观测'],
    ['/attestation', '确权中心总览'],
    ['/authorization-registry', '合约备案'],
    ['/market', '配置权市场'],
    ['/audit', '审计透明'],
  ])('导轨挂在 %s（主链环节在页）', async (path) => {
    await renderAt(path)
    expect(screen.getByTestId('main-chain-guide')).toBeTruthy()
  })

  it('非主链页不挂导轨（⛔全站：/about、/search 对照）', async () => {
    for (const path of ['/about', '/search']) {
      const { container, unmount } = await renderAt(path)
      expect(container.querySelector('[data-testid="main-chain-guide"]')).toBeNull()
      unmount()
    }
  })

  it('/five-orders 追平批B2 已入册：路由＋sitemap 均在架（导轨第八环挂载与否候令，本批未动）', () => {
    // 追平批B2（L1SI206-PARITY-B2）：照 PARITY-FILL 令 #1 迁入五序资产总览，旧「无此路由」口径随之作废
    expect(ROUTES).toContain('/five-orders')
    expect(SITEMAP_ENTRIES).toContain('/five-orders')
  })
})
