// SITE-001（L1SI226）T-2：/docs 四路 title 同步表（SPA 客户端导航时逐字对齐预渲染 title）
// 值照线上 dist 预渲染实读（scripts/prerender-routes.mjs 之 SUPPLEMENT／PagesIndex PAGE_META 同源），
// ⛔ 只此四路，不顺带波及任何其他路由；本令不动预渲染脚本。
export const DOCS_ROUTE_TITLES: Record<string, string> = {
  '/docs': '文档库',
  '/docs/papers': '论文族文档',
  '/docs/regulation': '条例族文档',
  '/docs/whitepapers': '白皮书族文档',
}
