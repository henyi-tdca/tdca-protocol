// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI208 SEG2-B2-REFIRE-001 A/B 块挂载验证
// 约束矩阵: REFIRE-001 块 A 判据（①匿名不显数据 ②六步逐步可点可停 ③私料⛔入检索 ④⛔整包索取）
//           ＋块 B 判据（①四档逐档可见默认 L1 ②档位不足三选项 ③六项逐项有值——六项读数在 MeNcaPage
//           面测，本件测四档/三选项/三守/四类分治/删除可验证）
//           AMEND-1 §三~§六、§八（六步六态·默认 M-2）；AMEND-2 §三~§七（默认 L1·L3 二次确认·告知三选项）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { MeCompilePage } from '@/pages/MeCompilePage'
import { MePrivacyPage } from '@/pages/MePrivacyPage'
import { MeNcaPage } from '@/pages/MeNcaPage'
import { AuthProvider } from '@/lib/auth-context'

// jsdom 无 canvas：拓扑引擎打桩（批5/批6/b7 先例）
vi.mock('@/lib/TopologyEngine', () => ({
  TopologyEngine: () => null,
  hashAgentId: (s: string) => `h-${s}`,
}))

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-11-11T00:00:00Z', data_nature: 'real' }
}

function mockAuthed() {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.includes('/api/v1/auth/me')) {
      return { ok: true, status: 200, json: async () => envelope({ username: 'tester' }) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

function mockAnon() {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 401, json: async () => ({ detail: 'unauthorized' }) }) as Response))
}

function renderCompile() {
  return render(<MemoryRouter><AuthProvider><MeCompilePage /></AuthProvider></MemoryRouter>)
}

function renderPrivacy() {
  return render(<MemoryRouter><AuthProvider><MePrivacyPage /></AuthProvider></MemoryRouter>)
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('REFIRE A块：区 2A 编译转化面（AMEND-1）', () => {
  it('六步流水线逐步在册（1 编译意图 → 6 创建与发布），每步显工具/产出/门', async () => {
    mockAuthed()
    renderCompile()
    await waitFor(() => expect(screen.getByTestId('compile-steps')).toBeTruthy())
    const keys = ['intent', 'objective', 'functional', 'negative', 'contract', 'publish']
    const names = ['编译意图', '求解目标函数', '函数化表达', '定义负空间', '合约与思维协议', '创建与发布']
    keys.forEach((k, i) => {
      expect(screen.getByTestId(`compile-step-${k}`).textContent).toContain(names[i])
    })
    // 逐步可点：第 1 步默认展开（工具/产出/确认勾在页）；展开第 2 步 ⟹ 其确认勾出现
    const step1 = screen.getByTestId('compile-step-intent')
    expect(within(step1).getByTestId('compile-confirm-intent')).toBeTruthy()
    expect(step1.textContent).toContain('SKILL 执行官')
    expect(step1.textContent).toContain('意图单')
    expect(step1.textContent).toContain('负空间预检')
    // 工具内嵌既有入口（货架与下载件，⛔下载再上传之外链）
    expect(step1.querySelector('a[href="/toolshelf"]')).toBeTruthy()
    const step2 = screen.getByTestId('compile-step-objective')
    fireEvent.click(within(step2).getByRole('button'))
    expect(within(step2).getByTestId('compile-confirm-objective')).toBeTruthy()
    expect(step2.textContent).toContain('反函数求解器')
    expect(step2.querySelector('a[href="/downloads/tdca-inverse-solver-v1.0.zip"]')).toBeTruthy()
  })

  it('默认 M-2 向导档；六态全列；逐步确认推进状态（可停可回退）', async () => {
    mockAuthed()
    renderCompile()
    await waitFor(() => expect(screen.getByTestId('compile-modes')).toBeTruthy())
    // 默认 M-2（向导）
    expect(screen.getByTestId('compile-mode-M-2').className).toContain('border-emerald-500')
    // 六态全列
    for (const s of ['DRAFT', 'COMPILING', 'NEG_PASS', 'SANDBOX_PASS', 'PUBLISHED', 'SUSPENDED']) {
      expect(screen.getByTestId(`compile-state-${s}`)).toBeTruthy()
    }
    expect(screen.getByTestId('compile-states').textContent).toContain('当前：DRAFT')
    // 勾选第 1 步 ⟹ 状态推进 COMPILING（逐步可点）；再取消 ⟹ 回退 DRAFT（可回退）
    // （第 1 步默认展开，确认勾直接可见可点）
    const step1 = screen.getByTestId('compile-step-intent')
    const cb = within(step1).getByTestId('compile-confirm-intent')
    fireEvent.click(cb)
    expect(screen.getByTestId('compile-states').textContent).toContain('当前：COMPILING')
    fireEvent.click(cb)
    expect(screen.getByTestId('compile-states').textContent).toContain('当前：DRAFT')
  })

  it('私料边界四条在页（私域内使用／⛔入仓／逐次授权留痕）＋责任澄清', async () => {
    mockAuthed()
    renderCompile()
    await waitFor(() => expect(screen.getByTestId('compile-private-rules')).toBeTruthy())
    const t = screen.getByTestId('compile-private-rules').textContent ?? ''
    expect(t).toContain('私域内使用')
    expect(t).toContain('⛔ 入仓')
    expect(t).toContain('逐次授权')
    expect(t).toContain('⛔ 默认全量读取')
    // 责任澄清（⛔ 代签；商业判断之责）
    expect(screen.getByTestId('compile-modes').textContent).toContain('⛔ 代签')
    expect(screen.getByTestId('compile-modes').textContent).toContain('⛔ 负「商业判断」之责')
  })

  it('⛔ 整包索取：面无文件上传控件', async () => {
    mockAuthed()
    const { container } = renderCompile()
    await waitFor(() => expect(screen.getByTestId('compile-steps')).toBeTruthy())
    expect(container.querySelector('input[type="file"]')).toBeNull()
  })

  it('匿名不显数据：401 ⟹ PrivateGate 引导登录零数据渲染（判据①）', async () => {
    mockAnon()
    renderCompile()
    await waitFor(() => expect(screen.getByTestId('private-gate-denied')).toBeTruthy())
    expect(screen.queryByTestId('compile-steps')).toBeNull()
    expect(screen.queryByTestId('compile-private-rules')).toBeNull()
  })
})

describe('REFIRE B块：数据开放四档与冲突告知（AMEND-2）', () => {
  it('四档逐档可见且默认 L1（判据 B①）', async () => {
    mockAuthed()
    renderPrivacy()
    await waitFor(() => expect(screen.getByTestId('privacy-tiers')).toBeTruthy())
    for (const t of ['L0', 'L1', 'L2', 'L3']) {
      expect(screen.getByTestId(`tier-${t}`)).toBeTruthy()
      expect(screen.getByTestId(`tier-pick-${t}`)).toBeTruthy()
    }
    expect(screen.getByTestId('tier-current').textContent).toContain('当前档：L1')
    expect(screen.getByTestId('tier-L1').className).toContain('border-emerald-500')
  })

  it('L3 未二次确认不可申明；勾选后可申明并留痕（⛔ 预勾选）', async () => {
    mockAuthed()
    renderPrivacy()
    await waitFor(() => expect(screen.getByTestId('privacy-tiers')).toBeTruthy())
    const l3pick = screen.getByTestId('tier-pick-L3') as HTMLButtonElement
    expect(l3pick.disabled).toBe(true)
    fireEvent.click(screen.getByTestId('tier-l3-confirm'))
    expect((screen.getByTestId('tier-pick-L3') as HTMLButtonElement).disabled).toBe(false)
    fireEvent.click(screen.getByTestId('tier-pick-L3'))
    expect(screen.getByTestId('tier-current').textContent).toContain('当前档：L3')
    expect(localStorage.getItem('me.data-tier')).toBe('L3')
  })

  it('冲突告知三选项 A/B/C 逐字在页、可点选并记录（判据 B②）', async () => {
    mockAuthed()
    renderPrivacy()
    await waitFor(() => expect(screen.getByTestId('privacy-conflict')).toBeTruthy())
    // 告知文案照 AMEND-2 §五：⛔ 静默读取＋三选项
    const copy = screen.getByTestId('conflict-copy').textContent ?? ''
    expect(copy).toContain('仅就本次提权')
    expect(copy).toContain('不办此项')
    expect(copy).toContain('改')
    expect(copy).toContain('⛔ 我们不会在你未选择时读取或使用')
    fireEvent.click(screen.getByTestId('conflict-choose-a'))
    expect(screen.getByTestId('conflict-result').textContent).toContain('已选 A')
    fireEvent.click(screen.getByTestId('conflict-choose-b'))
    expect(screen.getByTestId('conflict-result').textContent).toContain('已选 B')
    fireEvent.click(screen.getByTestId('conflict-choose-c'))
    expect(screen.getByTestId('conflict-result').textContent).toContain('已选 C')
    expect(screen.getByTestId('conflict-records').textContent?.match(/选/g)?.length).toBeGreaterThanOrEqual(3)
  })

  it('合规三守与四类分治在页（每档适用＋默认 L0 处理项）', async () => {
    mockAuthed()
    renderPrivacy()
    await waitFor(() => expect(screen.getByTestId('privacy-guards')).toBeTruthy())
    const g = screen.getByTestId('privacy-guards').textContent ?? ''
    expect(g).toContain('合法合规')
    expect(g).toContain('脱敏')
    expect(g).toContain('保密')
    const k = screen.getByTestId('privacy-kinds').textContent ?? ''
    for (const kind of ['知识资产', '业务数据', '个人敏感信息', '第三方权属内容']) {
      expect(k).toContain(kind)
    }
    expect(k).toContain('默认 L0 处理')
  })

  it('撤回与删除可验证：删除 ⟹ 回落 L1、记录清零、读数明示', async () => {
    mockAuthed()
    renderPrivacy()
    await waitFor(() => expect(screen.getByTestId('privacy-withdraw')).toBeTruthy())
    fireEvent.click(screen.getByTestId('conflict-choose-a'))
    fireEvent.click(screen.getByTestId('privacy-delete-verify'))
    const r = screen.getByTestId('privacy-verify-result').textContent ?? ''
    expect(r).toContain('删除可验证')
    expect(screen.getByTestId('tier-current').textContent).toContain('当前档：L1')
    expect(localStorage.getItem('me.data-tier')).toBeNull()
    expect(localStorage.getItem('me.tier-notices')).toBeNull()
  })

  it('匿名不显数据：401 ⟹ PrivateGate 引导登录零数据渲染', async () => {
    mockAnon()
    renderPrivacy()
    await waitFor(() => expect(screen.getByTestId('private-gate-denied')).toBeTruthy())
    expect(screen.queryByTestId('privacy-tiers')).toBeNull()
    expect(screen.queryByTestId('privacy-conflict')).toBeNull()
  })
})

describe('REFIRE B2块：NCA 权限边界举证（AMEND-3 §三/§四）', () => {
  const NCA_PAYLOAD = {
    total: 2, page: 1, limit: 20,
    items: [
      { nca_id: 'NCA-TEST-0001', action: 'service.compile', artifact_path: 'docs/a.md', sha256_8: 'abcd1234', ts: '2026-11-11T01:00:00+00:00' },
      { nca_id: 'NCA-TEST-0002', action: 'service.read', artifact_path: null, sha256_8: null, ts: '2026-11-11T02:00:00+00:00' },
    ],
  }

  function mockNca() {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.includes('/api/v1/me/nca')) {
        return { ok: true, status: 200, json: async () => envelope(NCA_PAYLOAD) } as Response
      }
      if (url.includes('/api/v1/auth/me')) {
        return { ok: true, status: 200, json: async () => envelope({ username: 'tester' }) } as Response
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
    }))
  }

  it('六项逐项有值或「本期无」；三时点齐；越界四步在页（判据 B③）', async () => {
    mockNca()
    render(<MemoryRouter><AuthProvider><MeNcaPage /></AuthProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('nca-boundary-proof')).toBeTruthy())
    // 逐项映射读数：③事由 ④对象/时间窗 ⑥指纹有值；①主体 ②授权依据 ⑤比对结论明标「本期无」
    const row1 = screen.getByTestId('nca-proof-NCA-TEST-0001')
    expect(row1.textContent).toContain('service.compile')
    expect(row1.textContent).toContain('docs/a.md')
    expect(row1.textContent).toContain('2026-11-11 01:00:00')
    expect(row1.textContent).toContain('abcd1234')
    expect(row1.textContent).toContain('本期无')
    // 空值行以「—」明示（⛔ 留空）
    const row2 = screen.getByTestId('nca-proof-NCA-TEST-0002')
    expect(row2.textContent).toContain('—')
    expect(row2.textContent).toContain('本期无')
    // 六项表头齐
    const six = screen.getByTestId('nca-proof-six').textContent ?? ''
    for (const h of ['①主体', '②授权依据', '③触发事由', '④访问范围', '⑤比对结论', '⑥对象指纹']) {
      expect(six).toContain(h)
    }
    // 三时点卡
    const moments = screen.getByTestId('nca-proof-moments').textContent ?? ''
    expect(moments).toContain('授权时')
    expect(moments).toContain('执行时')
    expect(moments).toContain('结束时')
    expect(moments).toContain('本期无')
    // 越界四步
    const proof = screen.getByTestId('nca-boundary-proof').textContent ?? ''
    expect(proof).toContain('即时中止')
    expect(proof).toContain('越界事实')
    expect(proof).toContain('告知用户')
    expect(proof).toContain('报运维并登记')
    // 原文 ⛔ 入证口径
    expect(proof).toContain('原文 ⛔ 入证')
  })
})
