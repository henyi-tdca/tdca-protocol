import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import Markdown from 'react-markdown'
import { siteGet, FAMILIES } from '../lib/siteApi'

function useLoaded<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string>('')
  const load = () => {
    setError('')
    fn().then(setData).catch((e) => {
      setData(null)
      setError(String(e instanceof Error ? e.message : e))
    })
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, deps)
  return { data, error, retry: () => { load() } }
}

export function DocsIndex() {
  const { family } = useParams()
  const fam = FAMILIES.find((f) => f.key === family)
  const { data, error } = useLoaded(
    () => siteGet<{ items: { slug: string; title: string; synced_at: string }[] }>(`/docs/${family}`),
    [family],
  )
  if (error) return <div className="py-24 text-center text-destructive">加载失败：{error}</div>
  if (!data) return <div className="py-24 text-center text-muted-foreground">加载中…</div>
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <Link to="/docs" className="text-sm text-muted-foreground">← 全部文档</Link>
      <h1 className="mt-2 text-2xl font-bold">{fam?.label ?? family}（{data.items.length} 件）</h1>
      {data.items.length === 0 ? (
        <p className="mt-6 text-muted-foreground">该族暂无入库文档。</p>
      ) : (
        <ul className="mt-6 divide-y rounded-lg border">
          {data.items.map((d) => (
            <li key={d.slug}>
              <Link to={`/docs/${family}/${d.slug}`} className="block px-4 py-3 hover:bg-muted">
                <div className="font-medium">{d.title}</div>
                <div className="text-xs text-muted-foreground">{d.slug} · {d.synced_at}</div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function DocsHome() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-2xl font-bold">文档库</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        内部试运行版 · 制度 / 帮助二族内容已入库，点开即读
      </p>
      <div className="mt-4 rounded-md border bg-muted/50 px-4 py-3 text-sm">
        <strong>怎么用</strong>
        <p className="mt-1 text-muted-foreground">
          ① 先在下方各族中点开要找的那一类；② 族内按标题浏览，点开即读全文；③ 读完可用浏览器返回，回到族内继续看；④ 需要全站检索，用页顶搜索。
        </p>
      </div>
      <p className="mt-2 rounded-md border bg-muted/50 px-4 py-2 text-xs text-muted-foreground">
        分工（在册口径）：文档库＝制度／条例／指引／章程／规则／办法／说明／示例／帮助；理论／白皮书／术语／知识图谱／思维协议／文献请走「知识库」（/library，原名文库，路由不变）。
      </p>
      <p className="mt-3 rounded-md border bg-muted/50 px-4 py-3 text-sm">
        <strong>受邀进入：</strong>建设期站点凭邀请码进入。邀请码凭人工发放——按 TDCA 管理方 指令由系统生成，由 TDCA 管理方 转交受邀者；到期失效，不回收。
      </p>
      <div className="mt-6 rounded-md border px-4 py-3 text-sm">
        <strong>五族说明</strong>
        <ul className="mt-1 space-y-1 text-muted-foreground">
          <li><strong>白皮书</strong>：制度与技术的总体主张与论证。</li>
          <li><strong>论文</strong>：专题论文与研究稿。</li>
          <li><strong>制度规范</strong>：生效中的条例、办法、协议与登记规则。</li>
          <li><strong>素材库</strong>：思维协议与工程素材的公开集。</li>
          <li><strong>周刊</strong>：按周发布的动态与观察。</li>
        </ul>
      </div>
      <p className="mt-4 rounded-md border bg-muted/50 px-4 py-3 text-sm">
        <strong>想了解「是什么」</strong>（概念、理论与术语），请到「知识库」；<strong>想查「怎么做」</strong>（制度、办法与操作规则），留在本页。
      </p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {FAMILIES.map((f) => (
          <Link key={f.key} to={`/docs/${f.key}`} className="rounded-lg border p-5 hover:bg-muted">
            <div className="font-bold">{f.label}</div>
            <div className="mt-1 text-sm text-muted-foreground">{f.desc}</div>
            <div className="mt-3 text-xs text-muted-foreground">进入 →</div>
          </Link>
        ))}
      </div>
    </div>
  )
}

export function DocDetail() {
  const { family, slug } = useParams()
  const fam = FAMILIES.find((f) => f.key === family)
  const { data, error } = useLoaded(
    () => siteGet<{ title: string; body_md: string; source_path: string; synced_at: string }>(`/docs/${family}/${slug}`),
    [family, slug],
  )
  if (error) return <div className="py-24 text-center text-destructive">加载失败：{error}</div>
  if (!data) return <div className="py-24 text-center text-muted-foreground">加载中…</div>
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <nav aria-label="面包屑" className="text-sm text-muted-foreground">
        文档库 ›{' '}
        <Link to={`/docs/${family}`} className="hover:underline">{fam?.label ?? family}</Link>
        {' '}› {data.title}
      </nav>
      <article className="prose prose-neutral mt-4 max-w-none dark:prose-invert">
        <Markdown>{data.body_md}</Markdown>
      </article>
      <footer className="mt-12 border-t pt-4 text-xs text-muted-foreground">
        源路径：{data.source_path} · 入库：{data.synced_at}
      </footer>
    </div>
  )
}
