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
        <p className="mt-6 text-muted-foreground">该族暂无入库文档（weekly 族源目录未建，留空在案）。</p>
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
        内部试运行版 · 白皮书 / 论文 / 公约条例 / COP 库四族内容已入库，点开即读
      </p>
      <p className="mt-2 rounded-md border bg-muted/50 px-4 py-2 text-xs text-muted-foreground">
        分工（SITE-THREE-FIXES-001）：文档库＝对外公约条例与操作文档；协议本体文献（白皮书 · 论文与实证 · 产物库 · 制度规范）请走「知识库」（/library，原名文库，路由不变）。
      </p>
      <p className="mt-3 rounded-md border bg-muted/50 px-4 py-3 text-sm">
        <strong>受邀进入：</strong>建设期站点凭邀请码进入。邀请码凭人工发放——按 TDCA 管理方 指令由系统生成，由 TDCA 管理方 转交受邀者；到期失效，不回收。
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
  const { data, error } = useLoaded(
    () => siteGet<{ title: string; body_md: string; source_path: string; synced_at: string }>(`/docs/${family}/${slug}`),
    [family, slug],
  )
  if (error) return <div className="py-24 text-center text-destructive">加载失败：{error}</div>
  if (!data) return <div className="py-24 text-center text-muted-foreground">加载中…</div>
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <Link to={`/docs/${family}`} className="text-sm text-muted-foreground">← 返回列表</Link>
      <article className="prose prose-neutral mt-4 max-w-none dark:prose-invert">
        <Markdown>{data.body_md}</Markdown>
      </article>
      <footer className="mt-12 border-t pt-4 text-xs text-muted-foreground">
        源路径：{data.source_path} · 入库：{data.synced_at}
      </footer>
    </div>
  )
}
