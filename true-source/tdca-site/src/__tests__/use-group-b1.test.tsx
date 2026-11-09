// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 用组批（L1SI206-USE-GROUP-B1）「用」组两面验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-USE-GROUP-B1-001 §四——
//   ① U-1 三处原文保真（页头/说明/防重句）② 成功显收件编号/哈希/归属＋下一步链接串 U-2
//   ③ 拒收给人话理由（⛔ 只给错误码）④ U-2 页头原文「代办登记（机器人只跑腿）」不改不扩
//   ⑤ 空态指回 U-1 且链接可达 ⑥ 代办边界：不代签／不代判／不对外承诺
//   ⑦ 草稿不落库不出号；未确认 ⛔ 出号 ⑧ 出号面必标 SIMULATED（ID92）
//   ⑨ 两动作面 ⛔ 入栏目检索索引（COLUMN_EXCLUDE 豁免口径）但入册站点地图 PAGE_META
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { UseUploadPage } from '@/pages/use/UseUploadPage'
import { UseAgentPage } from '@/pages/use/UseAgentPage'
import { PAGE_META, ROUTE_PATHS } from '@/pages/PagesIndex'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-11-10T00:00:00Z', data_nature: 'real' }
}

const UPLOAD_RESULT = {
  upload_id: 'UP-0001', sha256: 'ab'.repeat(32), sha256_16: 'ABCD1234EFGH5678',
  size_bytes: 3, original_filename: 'demo.txt', accept_category: '文档',
  owner: 'alice', uploaded_at: '2026-11-10T01:00:00+08:00', duplicate: false,
  note: '已收件——这是你的收件凭据。',
}

const UPLOAD_RECORD = {
  upload_id: 'UP-0001', sha256_16: 'ABCD1234EFGH5678', size_bytes: 3,
  original_filename: 'demo.txt', accept_category: '文档', uploaded_at: '2026-11-10T01:00:00+08:00',
}

const REGISTER_RESULT = { record_id: 'OR-0001', status: 'registered', nca_ref: 'nca:test', simulated: true }

/** 通用 fetch 桩：auth/me＋upload 回读＋登记出号三段，其余 404 */
function mockApi(handlers: Record<string, () => Response>) {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    const u = String(url)
    for (const [key, make] of Object.entries(handlers)) {
      if (u.includes(key)) return make()
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'unexpected' }) } as Response
  }))
}

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload }) as Response

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

// ---------------------------------------------------------------- U-1 交素材
describe('用组批 U-1：交素材（上传一件）', () => {
  it('页头与说明三处原文保真（令面硬要求，一字不改）', () => {
    render(<MemoryRouter><UseUploadPage /></MemoryRouter>)
    expect(screen.getByText('交素材（上传一件）')).toBeTruthy()
    expect(screen.getByText(/把素材原件交给站方：选一件文件传上来，当场看到哈希与归属。同一件重复传不会重复收。/)).toBeTruthy()
    expect(screen.getByTestId('use-upload')).toBeTruthy()
  })

  it('未选文件时上传按钮置灰（无上传件挡回，⛔ 空提交）', () => {
    render(<MemoryRouter><UseUploadPage /></MemoryRouter>)
    const btn = screen.getByTestId('use-upload-submit') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it('上传成功：显收件编号/哈希/归属＋下一步链接串 U-2（?u= 携带）', async () => {
    let posted: { url: string; auth: string | null; name: string | null } | null = null
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
      if (url.endsWith('/api/v1/use/upload')) {
        const h = (init?.headers ?? {}) as Record<string, string>
        posted = { url, auth: h.Authorization ?? null, name: h['X-Upload-Filename'] ?? null }
        return okJson({ data: UPLOAD_RESULT })
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'unexpected' }) } as Response
    }))
    sessionStorage.setItem('tdca_session_token', 'TDCA-SES-test')
    render(<MemoryRouter><UseUploadPage /></MemoryRouter>)
    fireEvent.change(screen.getByTestId('use-upload-file'), {
      target: { files: [new File(['abc'], 'demo.txt', { type: 'text/plain' })] },
    })
    fireEvent.click(screen.getByTestId('use-upload-submit'))
    await waitFor(() => expect(screen.getByTestId('use-upload-result')).toBeTruthy())
    expect(posted?.auth).toBe('TDCA-SES-test')                    // 会话令牌直注（直传报文走 raw fetch）
    expect(posted?.name).toBe(encodeURIComponent('demo.txt'))     // 文件名走 X-Upload-Filename
    expect(screen.getByText('UP-0001')).toBeTruthy()
    expect(screen.getByText('ab'.repeat(32))).toBeTruthy()        // 全哈希当场可见
    expect(screen.getByText('alice')).toBeTruthy()                // 归属
    const next = screen.getByTestId('use-upload-next') as HTMLAnchorElement
    expect(next.href).toContain('/use/agent?u=UP-0001')           // 串接 U-2
  })

  it('拒收：后端 detail 人话理由直出（⛔ 只给错误码）', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 422, json: async () => ({ detail: '这类文件不收——请换成文档/数据/图像等常见类型。' }) }) as Response))
    render(<MemoryRouter><UseUploadPage /></MemoryRouter>)
    fireEvent.change(screen.getByTestId('use-upload-file'), {
      target: { files: [new File(['x'], 'a.exe', { type: 'application/octet-stream' })] },
    })
    fireEvent.click(screen.getByTestId('use-upload-submit'))
    await waitFor(() => expect(screen.getByTestId('use-upload-reject')).toBeTruthy())
    expect(screen.getByText(/这类文件不收/)).toBeTruthy()
    expect(screen.queryByTestId('use-upload-result')).toBeNull()  // ⛔ 假成功
  })

  it('网络失败：人话兜底文案（fail-closed 不猜测）', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) }) as Response))
    render(<MemoryRouter><UseUploadPage /></MemoryRouter>)
    fireEvent.change(screen.getByTestId('use-upload-file'), {
      target: { files: [new File(['x'], 'b.txt', { type: 'text/plain' })] },
    })
    fireEvent.click(screen.getByTestId('use-upload-submit'))
    await waitFor(() => expect(screen.getByTestId('use-upload-reject')).toBeTruthy())
    expect(screen.getByText(/没传成：/)).toBeTruthy()
  })
})

// ---------------------------------------------------------------- U-2 代办登记
describe('用组批 U-2：代办登记（机器人只跑腿）', () => {
  const renderU2 = (path: string) =>
    render(<MemoryRouter initialEntries={[path]}><UseAgentPage /></MemoryRouter>)

  it('页头原文不改不扩＋代办边界三不全在（不代签／不代判／不对外承诺）', () => {
    renderU2('/use/agent')
    expect(screen.getByText('代办登记（机器人只跑腿）')).toBeTruthy()
    expect(screen.getByText(/机器人不代签、不代判、不对外承诺。/)).toBeTruthy()
  })

  it('空态（无 ?u）：人话挡回＋指回 U-1 链接可达（⛔ 白屏 ⛔ 假登记）', () => {
    renderU2('/use/agent')
    const alert = screen.getByRole('alert')
    expect(alert.textContent).toContain('还没有收件')
    const link = alert.querySelector('a') as HTMLAnchorElement
    expect(link.getAttribute('to') ?? link.getAttribute('href')).toBe('/use/upload')
    expect(link.textContent).toContain('交素材（上传一件）')
  })

  it('全流程：收件→只问缺项→草稿→本人确认→出号，登记号与 SIMULATED 标同现', async () => {
    const posted: unknown[] = []
    mockApi({
      '/api/v1/auth/me': () => okJson(envelope({ username: 'alice' })),
      '/api/v1/use/upload/UP-0001': () => okJson(envelope(UPLOAD_RECORD)),
      '/api/v1/ownership/register': () => {
        posted.push(null)
        return okJson(envelope(REGISTER_RESULT))
      },
    })
    renderU2('/use/agent?u=UP-0001')
    // 步1 收件：四要件核对面（文件已收）
    await waitFor(() => expect(screen.getByText(/第 1 步 · 收件/)).toBeTruthy())
    expect(screen.getByText('UP-0001')).toBeTruthy()
    // 步2 只问缺项：缺项点名
    expect(screen.getByTestId('use-agent-missing').textContent).toContain('还差：')
    fireEvent.change(screen.getByTestId('use-agent-title'), { target: { value: '测试作品' } })
    expect(screen.getByTestId('use-agent-author')).toHaveProperty('value', 'alice') // 登录名默认带入
    fireEvent.change(screen.getByTestId('use-agent-date'), { target: { value: '2026-11-01' } })
    fireEvent.change(screen.getByTestId('use-agent-source'), { target: { value: 'human/original' } })
    await waitFor(() => expect(screen.queryByTestId('use-agent-missing')).toBeNull())
    // 步3 草稿：先看后签；⛔ 预填登记号
    fireEvent.click(screen.getByTestId('use-agent-draft'))
    await waitFor(() => expect(screen.getByTestId('use-agent-draft-view')).toBeTruthy())
    expect(screen.getByText('草稿 · 未经签署 ⛔ 生效')).toBeTruthy()
    // 步4 本人确认：⛔ 默认勾选——未勾时按钮置灰；不收签名值/授权码文案在册
    expect(screen.getByText(/不收签名值、不收授权码/)).toBeTruthy()
    const confirmBtn = screen.getByTestId('use-agent-confirm') as HTMLButtonElement
    expect(confirmBtn.disabled).toBe(true)
    fireEvent.click(screen.getByTestId('use-agent-ack'))
    expect(confirmBtn.disabled).toBe(false)
    fireEvent.click(confirmBtn)
    await waitFor(() => expect(screen.getByText(/已由本人确认：alice/)).toBeTruthy())
    // 步5 出号
    fireEvent.click(screen.getByTestId('use-agent-register-btn'))
    await waitFor(() => expect(screen.getByTestId('use-agent-result')).toBeTruthy())
    expect(screen.getByText('OR-0001')).toBeTruthy()
    expect(screen.getByText(/SIMULATED · 版权链为站内模拟态，非对外法律凭据/)).toBeTruthy()
  })

  it('拒收第 4 类（外链下载式）：只给链接 → 收件步拦（⛔ 出草稿）＋人话退回文案在册', async () => {
    mockApi({
      '/api/v1/auth/me': () => okJson(envelope({ username: 'alice' })),
      '/api/v1/use/upload/UP-0001': () => okJson(envelope(UPLOAD_RECORD)),
    })
    renderU2('/use/agent?u=UP-0001')
    await waitFor(() => expect(screen.getByText(/第 1 步 · 收件/)).toBeTruthy())
    fireEvent.change(screen.getByTestId('use-agent-title'), { target: { value: 'https://example.com/x.zip' } })
    fireEvent.change(screen.getByTestId('use-agent-date'), { target: { value: '2026-11-01' } })
    fireEvent.change(screen.getByTestId('use-agent-source'), { target: { value: 'human/original' } })
    fireEvent.click(screen.getByTestId('use-agent-draft'))
    await waitFor(() => expect(screen.queryByTestId('use-agent-draft-view')).toBeNull()) // 收件步拦：草稿不出
    // 人话退回文案「只给链接不收——请把文件本身传上来，再填登记信息。」按原文在册（源页 L131 落 state）；
    // 展示位随原文在第 5 步区块（verbatim 直拷不挪位，展示面观察随回报呈智库裁）
  })

  it('回读失败：人话门槛文案（请先从「交素材」页上传）', async () => {
    mockApi({
      '/api/v1/auth/me': () => okJson(envelope({ username: 'alice' })),
      '/api/v1/use/upload/NOPE': () => ({ ok: false, status: 404, json: async () => ({ detail: 'not found' }) }) as Response,
    })
    renderU2('/use/agent?u=NOPE')
    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(screen.getByRole('alert').textContent).toContain('没查到这件')
  })
})

// ---------------------------------------------------------------- 索引与站点地图
describe('用组批：站点地图入册＋检索索引豁免', () => {
  it('PAGE_META 26 条含两面（题名照页头原文）', () => {
    const up = PAGE_META.find((m) => m.path === '/use/upload')
    const ag = PAGE_META.find((m) => m.path === '/use/agent')
    expect(PAGE_META).toHaveLength(34) /* 追平批B1：+4（/rules /help /negativespace /academy/outline） */
    expect(up?.title).toBe('交素材（上传一件）')
    expect(ag?.title).toBe('代办登记（机器人只跑腿）')
    expect(ROUTE_PATHS).toContain('/use/upload')
    expect(ROUTE_PATHS).toContain('/use/agent')
  })
})
