// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项三 · 存证（NCA）说明栏验收
// 约束矩阵: RULING-NCA-FORMAT-UNIVERSAL-001（明示·每场景·官方与用户一致·人机一致）
//   ＋ 交办令项三（为什么存/怎么存/谁都要存；⛔ 栏内不展实际凭据或内部编号）
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect } from 'vitest'
import App from '@/App'

describe('B5 项三 · 存证（NCA）说明栏（公域新增）', () => {
  it('/nca-guide 渲染：栏目在位、权限公开、为什么存在位', () => {
    render(
      <MemoryRouter initialEntries={['/nca-guide']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-shell')).toBeInTheDocument()
    expect(screen.getByTestId('nca-guide-page')).toBeInTheDocument()
    expect(screen.getByText('存证（NCA）说明')).toBeInTheDocument()
    expect(screen.getByText('权限：公开')).toBeInTheDocument()
    // 为什么存：无存证不执行＋可观测＋可问责＋可回溯
    const why = screen.getByTestId('nca-why')
    expect(why).toHaveTextContent('无存证不执行')
    expect(why).toHaveTextContent('可观测')
    expect(why).toHaveTextContent('可问责')
    expect(why).toHaveTextContent('可回溯')
  })

  it('怎么存：十三字段／义务块六键／合规六条明示齐', () => {
    render(
      <MemoryRouter initialEntries={['/nca-guide']}>
        <App />
      </MemoryRouter>,
    )
    const how = screen.getByTestId('nca-how')
    // 十三字段抽查
    for (const k of ['nca_id', 'chain_id', 'prev_nca', 'operation_type', 'actor', 'artifacts', 'data_provenance', 'profit_sharing', 'compliance']) {
      expect(how).toHaveTextContent(k)
    }
    // 义务块六键
    for (const k of ['function_call_id', 'state_hashes', 'config_right', 'audit_trail', 'human_signature', 'negative_space_check']) {
      expect(how).toHaveTextContent(k)
    }
    // 合规六条
    for (const c of ['只赋能不改码', '不复制上游代码', '算力零提及', '不声称上游背书', '无存证不执行', '分润模拟态']) {
      expect(how).toHaveTextContent(c)
    }
    // 带链说明在位
    expect(how).toHaveTextContent(/带链/)
  })

  it('谁都要存：三一律（场景／主体／形态；官方与用户一致、人类与智能体一致）', () => {
    render(
      <MemoryRouter initialEntries={['/nca-guide']}>
        <App />
      </MemoryRouter>,
    )
    const who = screen.getByTestId('nca-who')
    expect(who).toHaveTextContent('场景一律')
    expect(who).toHaveTextContent('主体一律')
    expect(who).toHaveTextContent('形态一律')
    expect(who).toHaveTextContent(/智能体互调即协作/)
  })

  it('⛔ 无内部编号／凭据样式（S-3 守检）', () => {
    render(
      <MemoryRouter initialEntries={['/nca-guide']}>
        <App />
      </MemoryRouter>,
    )
    const body = document.body.textContent ?? ''
    expect(body).not.toMatch(/GSEQ-\d/)
    expect(body).not.toMatch(/L1SI1\d\d/)
    expect(body).not.toMatch(/HANDOFF-[A-Z]|WITNESS-|TDCA-RULING|TDCA-NCA-STD/)
    expect(body).not.toMatch(/ghp_[A-Za-z0-9]|PRIVATE KEY|AKID[A-Za-z0-9]/)
  })

  it('公共导航「NCA 与透明」栏含存证说明入口（纯中文标签）', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('app-nav')
    expect(nav).toHaveTextContent('存证说明')
  })
})
