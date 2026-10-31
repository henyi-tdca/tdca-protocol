// L1SI182-BATCH-002 §二/§三：收录开面表与 nginx map $uri $seo_robots 同源锁定
import { describe, expect, it } from 'vitest'
import { isSeoOpen, SEO_OPEN_FACES } from '@/app/seo-robots'

describe('L1SI182-BATCH-002 收录开面表（与 deploy/nginx/default.conf map $uri $seo_robots 同源；L1SI183-SITEOBS-001 任务B：/attestation 登录页剔出后共 9 路）', () => {
  it('开放面恰为 9 路（登录页 /attestation 已剔出；/agents 需登录使用仍收录），不多不少', () => {
    expect([...SEO_OPEN_FACES].sort()).toEqual(
      [
        '/',
        '/about',
        '/academy',
        '/agents',
        '/audit',
        '/docs/papers',
        '/docs/regulation',
        '/docs/whitepapers',
        '/library',
      ].sort(),
    )
  })

  it('尾斜杠等价于无斜杠（/about/ ≡ /about）', () => {
    expect(isSeoOpen('/')).toBe(true)
    expect(isSeoOpen('/about/')).toBe(true)
    expect(isSeoOpen('/docs/regulation/')).toBe(true)
  })

  it('单件页/详情页/子路径一律谢绝（开放面子路径不继承）', () => {
    expect(isSeoOpen('/attestation/meta')).toBe(false)
    expect(isSeoOpen('/attestation/dynamic')).toBe(false)
    expect(isSeoOpen('/attestation/history')).toBe(false)
    expect(isSeoOpen('/agents/xyz')).toBe(false)
    expect(isSeoOpen('/docs/regulation/some-doc')).toBe(false)
    expect(isSeoOpen('/docs')).toBe(false)
    expect(isSeoOpen('/docs/unknown-family')).toBe(false)
  })

  it('谢绝面 14 条维持 noindex（含 S-1 裁出的 /notifier、/governance；本批不开的 /announcements、/nca-guide）', () => {
    for (const p of [
      '/auth',
      '/register',
      '/me',
      '/ownership',
      '/market',
      '/sandbox',
      '/tax',
      '/studio',
      '/notifier',
      '/governance',
      '/announcements',
      '/nca-guide',
      '/use/upload',
      '/use/agent',
    ]) {
      expect(isSeoOpen(p)).toBe(false)
    }
  })
})
