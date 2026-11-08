// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-REGPAGE-001 | 目标函数: 公域登记查询页验收（REGISTRY-PAGE-001）
// 约束矩阵: 验收五条之前三条——匿名数据面（mock 等价于匿名 GET）／三组字与双向两行 DOM 逐字／
//           四条扫描对渲染文本零命中（内部编号／凭据密钥／自然人敏感信息／负空间词面）。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { RegistrationsPage } from '@/pages/RegistrationsPage'

const PROVABLE = '本登记可证：内容于登记时点之字节与哈希、时间戳、提交主体标识、链上序号与前序衔接（第三方可复算）。'
const NOT_PROVABLE = '本登记不可证：权利是否成立、作品是否独创、是否不侵害第三人权利、能否对抗第三人。'
const LABELS = [
  '建设期内部登记',
  '法定确权另行申请，正式实行时由国家可信版权链办理',
  '获取方式 ≠ 已获授权',
  '未登记者视为不存在',
]

const LIST = {
  face: '内部权属登记（建设期）',
  count: 3,
  items: [
    { record_id: 'OR-G7-AAAA0001', title: '甲条例（V1.0）', family: 'regulation', content_sha256_16: 'AAAA0001BBBB0002', registered_at: '2026-11-08T17:10:22+08:00', nca_ref: 'NCA-WEB-000000000001', status: 'registered' },
    { record_id: 'OR-G7-AAAA0002', title: '乙素材件', family: 'cop-library', content_sha256_16: 'AAAA0002BBBB0003', registered_at: '2026-11-08T17:10:23+08:00', nca_ref: 'NCA-WEB-000000000002', status: 'registered' },
    { record_id: 'OR-G7-AAAA0003', title: '丙白皮书', family: 'whitepaper', content_sha256_16: 'AAAA0003BBBB0004', registered_at: '2026-11-08T17:10:24+08:00', nca_ref: 'NCA-WEB-000000000003', status: 'registered' },
  ],
  labels: LABELS,
  proof_boundary: { provable: PROVABLE, not_provable: NOT_PROVABLE },
}

const DETAIL = {
  face: '内部权属登记（建设期）',
  family: 'regulation',
  fields: {
    ownership_info: {
      登记题名: '甲条例（V1.0）',
      登记记录号: 'OR-G7-AAAA0001',
      内容哈希短值: 'AAAA0001BBBB0002',
      字节数: '10914',
      登记时间戳: '2026-11-08T17:10:22+08:00',
      链上序号: 'NCA-WEB-000000000001',
      来源路径: 'docs/regulations/甲条例（V1.0）.md',
    },
    authorization_info: '本登记不含对外授权信息；授权凭据只记存在（备注位丙栏）。',
    authorization_status: '无对外授权记录（未登记者视为不存在）。',
    access_method: '站内公开阅读（制度栏／文库对应族面）；获取方式 ≠ 已获授权',
  },
  note_section: '【甲·权利束与保留束】……【乙·内容承诺值】……【丙·授权凭据】已获签署方书面授权（授权书 2026-11-08 生效，原件由签署方保管）。【丁·证据要素】……',
  record_meta: { 提交主体标识: 'tdca-official-genesis', 表达形式: 'text', 法域归口: 'copyright', 登记状态: 'registered', updated_at: '2026-11-08T17:10:22+08:00' },
  labels: LABELS,
  proof_boundary: { provable: PROVABLE, not_provable: NOT_PROVABLE },
}

const EVIDENCE = {
  用途声明: '本导出仅供向法定机构提交与内部留档，⛔ 公开发布；不含签名值与姓名。',
  栏一_件名与路径: { '件名（净名）': '甲条例（V1.0）', 路径: 'docs/regulations/甲条例（V1.0）.md' },
  栏二_内容哈希与字节: { 'sha256 全值': 'AAAA0001BBBB0002CCCC0003DDDD0004EEEE0005FFFF0006AAAA0001BBBB0002CCCC0003DDDD0004', 'sha256 短值': 'AAAA0001BBBB0002', 字节数: 10914 },
  栏三_登记时间戳与记录号: { 登记时间戳: '2026-11-08T17:10:22+08:00', 登记记录号: 'OR-G7-AAAA0001' },
  栏四_链段: { 当条链号: 'NCA-WEB-000000000001', 前序衔接: 'NCA-WEB-000000000000', 链记录时间: '2026-11-08T17:10:22+08:00', 当条自哈希: 'AAAA0001BBBB0002', 前序哈希: 'BBBB0002CCCC0003' },
}

function mockFetch() {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    if (url.endsWith('/api/public/registrations')) return jsonResp(LIST)
    if (url.includes('/evidence')) return jsonResp(EVIDENCE)
    if (url.includes('/api/public/registrations/')) return jsonResp(DETAIL)
    return jsonResp({}, 404)
  }))
}

function jsonResp(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

beforeEach(() => {
  localStorage.clear()
  mockFetch()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('RegistrationsPage（REGISTRY-PAGE-001 验收）', () => {
  it('列表渲染：三组字与双向两行 DOM 逐字在页', async () => {
    render(<RegistrationsPage />)
    await waitFor(() => expect(screen.getByTestId('reg-list')).toBeTruthy())
    for (const t of LABELS) expect(screen.getAllByText(t).length).toBeGreaterThan(0)
    expect(screen.getByTestId('boundary-provable').textContent).toBe(PROVABLE)
    expect(screen.getByTestId('boundary-not-provable').textContent).toBe(NOT_PROVABLE)
    // 页内计数为功能读数（实拉·实显），非公告式文案
    expect(screen.getByTestId('reg-count').textContent).toContain('实拉 3 条')
  })

  it('检索与族筛选可定位记录号', async () => {
    render(<RegistrationsPage />)
    await waitFor(() => expect(screen.getByTestId('reg-list')).toBeTruthy())
    fireEvent.change(screen.getByTestId('reg-search'), { target: { value: '乙素材' } })
    await waitFor(() => {
      expect(screen.queryByTestId('reg-item-OR-G7-AAAA0001')).toBeNull()
      expect(screen.getByTestId('reg-item-OR-G7-AAAA0002')).toBeTruthy()
    })
    fireEvent.change(screen.getByTestId('reg-family'), { target: { value: 'whitepaper' } })
    await waitFor(() => expect(screen.getByTestId('reg-count').textContent).toContain('实显 0 条'))
  })

  it('详情：四字段＋备注节；证据包四栏＋用途声明在页', async () => {
    render(<RegistrationsPage />)
    await waitFor(() => expect(screen.getByTestId('reg-list')).toBeTruthy())
    fireEvent.click(screen.getByTestId('reg-item-OR-G7-AAAA0001'))
    await waitFor(() => expect(screen.getByTestId('reg-detail')).toBeTruthy())
    expect(screen.getByTestId('reg-auth-status').textContent).toBe('无对外授权记录（未登记者视为不存在）。')
    expect(screen.getByTestId('reg-access-method').textContent).toContain('获取方式 ≠ 已获授权')
    expect(screen.getByTestId('reg-note').textContent).toContain('【甲·权利束与保留束】')
    fireEvent.click(screen.getByTestId('reg-evidence-btn'))
    await waitFor(() => expect(screen.getByTestId('reg-evidence')).toBeTruthy())
    expect(screen.getByTestId('reg-evidence-purpose').textContent).toBe(EVIDENCE.用途声明)
    expect(screen.getByTestId('reg-evidence').textContent).toContain('栏一 · 件名与路径')
  })

  it('四条扫描对渲染文本零命中', async () => {
    const { container } = render(<RegistrationsPage />)
    await waitFor(() => expect(screen.getByTestId('reg-list')).toBeTruthy())
    const html = container.textContent ?? ''
    const scans: [string, RegExp][] = [
      ['内部编号式', /TDCA-[A-Z0-9-]*\d{3,}/],
      ['负空间词面', /确权登记|已确权/],
      ['自然人敏感信息', /\b\d{17}[\dXx]\b|\b1[3-9]\d{9}\b/],
      ['凭据形态', /-----BEGIN|AKIA[0-9A-Z]{16}/],
    ]
    for (const [name, pat] of scans) {
      expect(pat.findall ? 0 : (html.match(pat) ?? []).length, `扫描[${name}]须0命中`).toBe(0)
    }
    // 遮蔽形保留：来源路径遮蔽样（详情含隐去形时不展开）
    fireEvent.click(screen.getByTestId('reg-item-OR-G7-AAAA0001'))
    await waitFor(() => expect(screen.getByTestId('reg-detail')).toBeTruthy())
    expect(container.textContent).not.toMatch(/TDCA-[A-Z0-9-]*\d{3,}/)
  })
})
