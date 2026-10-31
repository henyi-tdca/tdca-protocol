// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 路由级 meta robots 注入（开放面移除 tag，其余 noindex,nofollow）
// 约束矩阵: L1SI182-BATCH-002 §二/§三——本表与 deploy/nginx/default.conf 的 map $uri $seo_robots
//   同一张开面清单（⛔两套）：内容页 6 ＋ 目录 3 处（白皮书/论文二合一）；/announcements、/nca-guide 本批不开；
//   /notifier、/governance 经智库裁定移出开放面（S-1 停手回报两处不符之裁），维持谢绝。
// =============================================================================
import { useEffect } from 'react'
import { useLocation } from 'react-router'

/** 收录开放面（L1SI183-SITEOBS-001 任务B：9 路；/attestation 为登录页已剔出；/agents 需登录使用仍收录） */
export const SEO_OPEN_FACES = [
  '/',
  '/about',
  '/audit',
  '/agents', // 需登录使用（裁定注明）
  '/academy',
  '/docs/regulation',
  '/library',
  '/docs/whitepapers',
  '/docs/papers',
] as const

const NOINDEX = 'noindex, nofollow'

/** 开放面判定：尾斜杠等价（/about/ ≡ /about）；子路径（单件页、详情页）一律谢绝 */
export function isSeoOpen(pathname: string): boolean {
  const norm = pathname.length > 1 && pathname.endsWith('/') ? pathname.slice(0, -1) : pathname
  return (SEO_OPEN_FACES as readonly string[]).includes(norm)
}

/** 路由级 meta robots 注入：开放面移除 meta（响应头同面不头发），谢绝面置 noindex,nofollow */
export function SeoRobots() {
  const { pathname } = useLocation()
  useEffect(() => {
    const tag = document.head.querySelector<HTMLMetaElement>('meta[name="robots"]')
    if (isSeoOpen(pathname)) {
      tag?.remove()
      return
    }
    if (tag) {
      tag.content = NOINDEX
    } else {
      const el = document.createElement('meta')
      el.name = 'robots'
      el.content = NOINDEX
      document.head.appendChild(el)
    }
  }, [pathname])
  return null
}
