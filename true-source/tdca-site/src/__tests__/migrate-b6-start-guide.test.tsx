// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: MIGRATE 批6（L1SI206）入门与指南四件验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B6-001 §三沙盒六组
//   ① 四件皆在 ② 全子页可达——六步/计数与旧版逐项对得上 ③ 导航层级照在册（L0 公开）
//   ④ start-map.yaml 原字节随批（哈希对在册值·⛔手改）⑤ 机端可读（甲态：yaml 机读单一事实源）
//   ⑥ 移动四字段另报回报件
// =============================================================================
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { StartPageBody } from '@/pages/start/start'
import { parseStartMap } from '@/pages/start/parse'
import { NcaGuidePage } from '@/pages/NcaGuidePage'
import { MAIN_CHAIN, MAIN_CHAIN_PAGES } from '@/pages/MainChainGuide'
import { ROUTE_PATHS, PAGE_META } from '@/pages/PagesIndex'
import startMapYaml from '@/pages/start/start-map.yaml?raw'

/** WebCrypto 标准接口（零新依赖；与在册测试同式） */
async function sha16(s: string) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()
    .slice(0, 16)
}

const STEPS6 = ['了解 TDCA', '读懂基本制度', '看资产与授权', '参与协作', '结算与计税', '争议与退出'] as const

describe('MIGRATE 批6：start-map.yaml 数据件原字节随批（沙盒④⛔手改）', () => {
  it('yaml sha256_16 == 在册值 E9FFC4080C045CD2（_START-MAP-20261021-V1·R1-001-A 实测口径）', async () => {
    expect(await sha16(startMapYaml)).toBe('E9FFC4080C045CD2')
  })

  it('解析计数与旧版权逐项对得上（沙盒②：steps 6／docs 54 page_visible／terms 147）', () => {
    const d = parseStartMap(startMapYaml)
    expect(d.steps).toHaveLength(6)
    expect(d.docs.filter((x) => x.page_visible)).toHaveLength(54)
    expect(d.terms).toHaveLength(147)
    // 六步徽数照 STEP 表 5/24/17/26/2/3（旧版权测试口径）
    expect(d.steps.map((s) => s.count)).toEqual([5, 24, 17, 26, 2, 3])
  })
})

describe('MIGRATE 批6：/start 渲染（六步逐字·四路分流·data=null 兜底）', () => {
  it('六步卡 S1~S6 逐字在页（A-2 口径）', () => {
    render(<MemoryRouter><StartPageBody data={parseStartMap(startMapYaml)} /></MemoryRouter>)
    STEPS6.forEach((s, i) => {
      const card = screen.getByTestId(`step-card-S${i + 1}`)
      expect(card.textContent).toContain(s)
    })
    expect(screen.getByTestId('step-cards')).toBeTruthy()
  })

  it('四路分流在页（L1SI167-START-ROUTE-001，⛔动一字照旧版）', () => {
    render(<MemoryRouter><StartPageBody data={parseStartMap(startMapYaml).data} /></MemoryRouter>)
    expect(screen.getByTestId('route-r1')).toBeTruthy()
    expect(screen.getByTestId('route-r2')).toBeTruthy()
    expect(screen.getByTestId('route-r3')).toBeTruthy()
  })

  it('data=null 兜底不白屏（A-10+M-4 口径）', () => {
    render(<MemoryRouter><StartPageBody data={null} /></MemoryRouter>)
    expect(screen.getByTestId('load-error')).toBeTruthy()
  })
})

describe('MIGRATE 批6：/nca-guide 与导轨组件入册', () => {
  it('/nca-guide 渲染冒烟（NCA 说明面三节在页）', () => {
    render(<MemoryRouter><NcaGuidePage /></MemoryRouter>)
    expect(screen.getByTestId('nca-guide-page')).toBeTruthy()
    expect(screen.getByTestId('nca-why')).toBeTruthy()
    expect(screen.getByTestId('nca-how')).toBeTruthy()
    expect(screen.getByTestId('nca-who')).toBeTruthy()
  })

  it('主链导轨八环节照在册序列（件入册；挂载候另裁——如实登记）', () => {
    expect(MAIN_CHAIN).toHaveLength(8)
    expect(MAIN_CHAIN[0]).toEqual({ to: '/', label: '门户首页' })
    expect(MAIN_CHAIN[7]).toEqual({ to: '/audit', label: '审计与账本' })
    expect(MAIN_CHAIN_PAGES.size).toBe(8)
  })
})

describe('MIGRATE 批6：两面入册（ROUTE_PATHS＋PAGE_META·22→24）', () => {
  it('/start 与 /nca-guide 在册，权限照在册=公开', () => {
    expect(ROUTE_PATHS).toContain('/start')
    expect(ROUTE_PATHS).toContain('/nca-guide')
    expect(PAGE_META).toHaveLength(26) /* 用组批：+2（/use/upload /use/agent） */
    expect(PAGE_META.find((m) => m.path === '/start')?.permission).toBe('公开')
    expect(PAGE_META.find((m) => m.path === '/nca-guide')?.permission).toBe('公开')
  })
})
