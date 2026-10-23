// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-START-ROUTE-001 | 目标函数: L1SI167-START-ROUTE-001 四路分流判成
// 约束矩阵: 令 §五判成五条（顶部四路／三步+按钮／R-2 状态句／零内部编号）
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect } from 'vitest'
import { StartPageBody } from '@/pages/start/start'
import { parseStartMap } from '@/pages/start/parse'
import startMapYaml from '@/pages/start/start-map.yaml?raw'

const data = parseStartMap(startMapYaml)

describe('L1SI167-START-ROUTE-001 四路分流', () => {
  it('判成1/3：页顶四路卡片齐、R-2 状态句在位、六步区在其下', () => {
    render(
      <MemoryRouter initialEntries={['/start']}>
        <StartPageBody data={data} />
      </MemoryRouter>,
    )
    const routes = screen.getByTestId('start-routes')
    for (const r of ['route-r1', 'route-r2', 'route-r3', 'route-r4']) {
      expect(screen.getByTestId(r)).toBeInTheDocument()
    }
    // R-2 状态说明句（§二 诚实性要求）
    expect(routes).toHaveTextContent('通道当前为内部开通期，外部自助登记暂未开放；内部账号可经登录后登记。')
    // 六步区仍在分流区之下
    const shell = screen.getByTestId('page-shell')
    expect(shell.textContent?.indexOf('你来做甚么？')).toBeLessThan(shell.textContent?.indexOf('按六步了解 TDCA') ?? 0)
  })

  it('判成2：每路三步＋一按钮，四按钮落点正确', () => {
    render(
      <MemoryRouter initialEntries={['/start']}>
        <StartPageBody data={data} />
      </MemoryRouter>,
    )
    const want = [
      ['route-r1-btn', '去登记资产', '/ownership-registry'],
      ['route-r2-btn', '去登记智能体', '/channel/registry'],
      ['route-r3-btn', '去市场看看', '/market'],
      ['route-r4-btn', '看看规章制度', '/rules'],
    ] as const
    for (const [tid, label, href] of want) {
      const a = screen.getByTestId(tid)
      expect(a).toHaveTextContent(label)
      expect(a).toHaveAttribute('href', href)
    }
    // 每路各三个步骤
    for (const r of ['route-r1', 'route-r2', 'route-r3', 'route-r4']) {
      expect(screen.getByTestId(r).querySelectorAll('ol li').length).toBe(3)
    }
  })

  it('判成4：分流区零内部编号（GSEQ-／TDCA-E-／NCA- 命中 0）', () => {
    render(
      <MemoryRouter initialEntries={['/start']}>
        <StartPageBody data={data} />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('start-routes').textContent ?? '').not.toMatch(/GSEQ-|TDCA-E-|NCA-/)
  })
})
