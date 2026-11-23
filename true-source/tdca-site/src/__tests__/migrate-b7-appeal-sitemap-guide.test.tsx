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

describe('MIGRATE 批7：站点地图 ≡ 真源清单（prerender-routes.mjs SITEMAP_ROUTES 机取，/ops* 私域不入）', () => {
  // ALPHA-ALL-001 A-2（2026-11-15）：sitemap 已收敛至 57 条恒定（PR538 回写为准），旧
  // 「静态路由数−/ops*−受护面」公式随路由新增漂移失效（机算 70 ≠ 实 57）；改机取生成器
  // 真源清单对账，⛔手编塞条目。/docs/* 三族为 nginx 直出文档面（⛔React 路由）。
  // SITEA-RESIDUAL-001 余项2：/authorization/panel（RequireAuth 受护面）已移出 sitemap 与预渲染。
  const prerenderSrc = readFileSync(repoRoot + 'true-source/tdca-site/scripts/prerender-routes.mjs', 'utf-8')
  const CANONICAL_SITEMAP = (() => {
    const m = prerenderSrc.match(/const SITEMAP_ROUTES = \[([\s\S]*?)\]/)
    if (!m) throw new Error('SITEMAP_ROUTES 真源未找到')
    return [...m[1].matchAll(/'([^']+)'/g)].map((x) => x[1])
  })()

  it('条目数≡真源清单数（机取机算，⛔手编塞条目；61 条口径＝57+1+3−1+1）', () => {
    // L1SI218-ALIAS301-001 项2（GSEQ-8493）：/acceptance 公示面入预渲染，57→58
    // SITEA-RESIDUAL-001 余项1（GSEQ-8809）：/register /formal /market-sim 三公开页补入，58→61
    // SITEA-RESIDUAL-001 余项2：/authorization/panel（受护面）移出，61→60
    // DUALCH-021 上批：/dual-channel 公示面入预渲染，60→61（存量口径未跟上批，B1-001 顺手修）
    expect(CANONICAL_SITEMAP).toHaveLength(61)
    expect(SITEMAP_ENTRIES).toHaveLength(CANONICAL_SITEMAP.length)
    expect(new Set(SITEMAP_ENTRIES)).toEqual(new Set(CANONICAL_SITEMAP))
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

  it('旧树残留清尽：sitemap 条目全部在真源清单内（/docs/* nginx 直出族登记照实）', () => {
    for (const e of SITEMAP_ENTRIES) {
      expect(CANONICAL_SITEMAP).toContain(e)
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
