// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-C1 自助验链四区块测试（并入 /verify）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-C1-001 §四/§七——
//   原三件自查区块一字不动（S-1）；C3 只显白名单（S-2 防线）；C3 两分支；
//   页面零编号零价格；免责与限速原样在位
// =============================================================================
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { VerifyPage } from '@/pages/verify'

function envelope(payload: unknown) {
  return { ok: true, status: 200, json: async () => ({ nca_watermark: 'sha256:test', data_nature: 'simulated', data: payload }) } as Response
}

const SPEC = {
  entry: { record: 'GET /api/v1/selfcheck/nca/{nca_id}', anchor: 'GET /api/v1/selfcheck/anchor' },
  rec_hash_spec: "rec_hash = sha256('nca_id|prev_nca|action|actor|artifact_path|sha256_8|handshake_id|data_provenance|ts') → 十六进制大写前 16 位（空值按空串计；actor 计入哈希但不出原值，以 actor_hash 脱敏供给）",
  anchor_digest_spec: "anchor_digest = sha256('date|row_count|sorted(leaf_hashes).join(\",\")') → 十六进制大写前 16 位（口径写死在当日锚件 canonicalization 字段）",
  fields_whitelist: [
    'nca_id', 'action', 'ts', 'artifact_filename_sha256_16', 'artifact_ext',
    'sha256_8', 'rec_hash', 'prev_hash', 'detached', 'detach_reason', 'actor_hash',
  ],
  not_returned: [
    'actor（原值，自然人标识一律不出）', 'handshake_id', 'chain_id', 'side', '凭据', '内部编号', '负空间词面',
    'artifact_filename（台账件名原值，035-A2 令脱敏）',
  ],
  artifact_filename_note: '台账件名原值不入响应；以 artifact_filename_sha256_16 供给（sha256(件名 UTF-8) 前 16 位大写），artifact_ext 为扩展名',
  rate_limit: '60/min/IP（内存滑窗，单实例口径）',
  sha256_8_note: 'sha256_8 系 artifact_path 之哈希，非记录哈希（如实标注）',
  page_disclaimer: '本查询可证：该条记录存在于台账，且其内容与写入时一致；台账当日形态与公开锚一致。历史各日是否被改写，取决于每日锚是否连续可核。',
}

const ANCHOR = {
  anchor: {
    date: '2026-10-19', row_count: 179, anchor_digest: '528AD76993BB89FC',
    leaf_count: 69, detached_count: 49, detached_digest: '569A67F47BD050AF', schema_version: 2,
  },
  canonicalization: "anchor_digest=sha256('date|row_count|sorted(leaf_hashes).join(,)' 的UTF-8字节)前16位大写；detached_digest=sha256('detached_count|sorted(detached_heads).join(,)' 的UTF-8字节)前16位大写",
  page_disclaimer: SPEC.page_disclaimer,
}

const HISTORY = {
  events: [
    { event_id: 'EVT-CASE002-01', type: 'dispatch_tax', ts: '2026-08-20T15:50:20.486926+00:00' },
    { event_id: 'EVT-CASE002-02', type: 'royalty', ts: '2026-08-20T15:55:20.486926+00:00' },
  ],
  total: 2,
  note: '账本事件（事件溯源，O(n) 可审计）',
}

const RECORD = {
  nca_id: 'NCA-DEMO-0001',
  action: 'deliver',
  ts: '2026-10-25T08:00:00+00:00',
  artifact_filename_sha256_16: 'AB12CD34EF56AB12',
  artifact_ext: '.md',
  sha256_8: '89ABCDEF',
  rec_hash: '0123456789ABCDEF',
  prev_hash: 'FEDCBA9876543210',
  detached: false,
  actor_hash: 'A1B2C3D4E5F60718',
  // 以下字段在白名单外，⛔ 不得渲染（S-2 防线）
  actor: 'NATURAL-PERSON-NAME',
  handshake_id: 'HS-DEMO-1',
  chain_id: 'CHAIN-DEMO-1',
  artifact_filename: 'TDCA-INTERNAL-FILENAME.md',
}

function mockAll() {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const u = String(url)
    if (u.includes('/selfcheck/spec')) return envelope(SPEC)
    if (u.includes('/selfcheck/anchor')) return envelope(ANCHOR)
    if (u.includes('/tax/nca-history')) return envelope(HISTORY)
    if (u.includes('/selfcheck/nca/NCA-DEMO-0001')) return envelope(RECORD)
    if (u.includes('/selfcheck/nca/NOPE-000')) {
      return { ok: false, status: 404, json: async () => ({ detail: 'NOT_FOUND: 该 nca_id 不存在于台账（统一 404）', code: 'TDCA-E-ASSET-STATE-001' }) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'nf' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('L1SI175-C1 自助验链四区块（并入 /verify）', () => {
  it('S-1 守护：原三件自查区块与口径区块一字不动', async () => {
    mockAll()
    render(<MemoryRouter><VerifyPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('verify-spec')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByTestId('verify-step-一')).toBeTruthy()
    expect(screen.getByTestId('verify-step-二')).toBeTruthy()
    expect(screen.getByTestId('verify-step-三')).toBeTruthy()
    expect(screen.getByTestId('verify-note')).toBeTruthy()
    expect(screen.getAllByText(/5 分钟三件自查/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/体验期免费使用，收费标准另定/).length).toBeGreaterThanOrEqual(1)
  })

  it('C1 校验规格：公式/白名单/不返回/双注记/免责/限速全齐（原文照排）', async () => {
    mockAll()
    render(<MemoryRouter><VerifyPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('verify-spec')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByText(/rec_hash = sha256/)).toBeTruthy()
    expect(screen.getByText(/anchor_digest = sha256/)).toBeTruthy()
    expect(screen.getByTestId('spec-whitelist').textContent).toContain('actor_hash')
    expect(screen.getByText(/actor（原值，自然人标识一律不出）/)).toBeTruthy()
    expect(screen.getByText(/sha256_8 系 artifact_path 之哈希/)).toBeTruthy()
    expect(screen.getAllByText(/60\/min\/IP/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/本查询可证：该条记录存在于台账/).length).toBeGreaterThanOrEqual(1)
  })

  it('C2 锚点核验：digest/计数/canonicalization ＋ 怎么自己算一句 ＋ 免责', async () => {
    mockAll()
    render(<MemoryRouter><VerifyPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('verify-anchor-block')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByTestId('anchor-digest').textContent).toBe('528AD76993BB89FC')
    expect(screen.getByText('179')).toBeTruthy()
    expect(screen.getByTestId('anchor-canonicalization').textContent).toContain('UTF-8字节')
    expect(screen.getByText(/怎么自己算：取当日台账全部叶哈希/)).toBeTruthy()
    expect(screen.getAllByText(/本查询可证：该条记录存在于台账/).length).toBeGreaterThanOrEqual(1)
  })

  it('C3 命中分支：只显白名单字段，actor/handshake_id/chain_id/件名原值零渲染', async () => {
    mockAll()
    render(<MemoryRouter><VerifyPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('verify-spec')).toBeTruthy(), { timeout: 3000 })
    fireEvent.change(screen.getByTestId('c3-input'), { target: { value: 'NCA-DEMO-0001' } })
    fireEvent.click(screen.getByTestId('c3-query'))
    await waitFor(() => expect(screen.getByTestId('c3-record')).toBeTruthy(), { timeout: 3000 })
    const text = document.body.textContent ?? ''
    expect(text).toContain('NCA-DEMO-0001')
    expect(text).toContain('AB12CD34EF56AB12')
    expect(text).toContain('A1B2C3D4E5F60718')
    // 白名单外：⛔ 出
    expect(text.includes('NATURAL-PERSON-NAME')).toBe(false)
    expect(text.includes('HS-DEMO-1')).toBe(false)
    expect(text.includes('CHAIN-DEMO-1')).toBe(false)
    expect(text.includes('TDCA-INTERNAL-FILENAME')).toBe(false)
  })

  it('C3 未找到分支：人话 ＋ 错误码 TDCA-E-ASSET-STATE-001', async () => {
    mockAll()
    render(<MemoryRouter><VerifyPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('verify-spec')).toBeTruthy(), { timeout: 3000 })
    fireEvent.change(screen.getByTestId('c3-input'), { target: { value: 'NOPE-000' } })
    fireEvent.click(screen.getByTestId('c3-query'))
    await waitFor(() => expect(screen.getByTestId('c3-not-found')).toBeTruthy(), { timeout: 3000 })
    expect(screen.getByText(/未找到：该 nca_id 不存在于台账/)).toBeTruthy()
    expect(screen.getByText('TDCA-E-ASSET-STATE-001')).toBeTruthy()
  })

  it('C4 税事件时间轴：按时间倒序、event_id 整串、type 在', async () => {
    mockAll()
    render(<MemoryRouter><VerifyPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('tax-event-list')).toBeTruthy(), { timeout: 3000 })
    const items = screen.getAllByTestId('tax-event')
    expect(items.length).toBe(2)
    expect(items[0].textContent).toContain('EVT-CASE002-02')
    expect(items[1].textContent).toContain('EVT-CASE002-01')
    expect(screen.getByText('dispatch_tax')).toBeTruthy()
    expect(screen.getByText('royalty')).toBeTruthy()
  })

  it('页面零价格字样（¥/￥/元/价格/档位/付费 均不出）', async () => {
    mockAll()
    const { container } = render(<MemoryRouter><VerifyPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('verify-spec')).toBeTruthy(), { timeout: 3000 })
    const text = container.textContent ?? ''
    for (const bad of ['¥', '￥', '元', '价格', '档位', '付费']) {
      if (text.includes(bad)) throw new Error(`命中价格字样: ${bad}`)
      expect(text.includes(bad)).toBe(false)
    }
  })
})
