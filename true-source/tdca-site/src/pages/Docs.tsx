import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import Markdown from 'react-markdown'
import { siteGet, getGate, setGate, GateRequired, FAMILIES } from '../lib/siteApi'

function GatePrompt({ onOk }: { onOk: () => void }) {
  const [v, setV] = useState(getGate())
  return (
    <div className="mx-auto max-w-sm py-24 text-center">
      <h2 className="text-xl font-bold mb-2">口令门</h2>
      <p className="text-sm text-muted-foreground mb-4">请输入内部访问口令（仅本次会话有效）</p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          setGate(v)
          onOk()
        }}
        className="flex gap-2"
      >
        <input
          type="password"
          value={v}
          onChange={(e) => setV(e.target.value)}
          className="flex-1 rounded border px-3 py-2 text-sm"
          placeholder="x-tdca-site-gate"
        />
        <button className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground">进入</button>
      </form>
    </div>
  )
}

function useGated<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [needGate, setNeedGate] = useState(false)
  const [error, setError] = useState<string>('')
  const load = () => {
    fn().then(setData).catch((e) => {
      if (e instanceof GateRequired) setNeedGate(true)
      else setError(String(e))
    })
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, deps)
  return { data, needGate, error, retry: () => { setNeedGate(false); setError(''); load() } }
}

export function DocsIndex() {
  const { family } = useParams()
  const fam = FAMILIES.find((f) => f.key === family)
  const { data, needGate, error, retry } = useGated(
    () => siteGet<{ items: { slug: string; title: string; synced_at: string }[] }>(`/docs/${family}`),
    [family],
  )
  if (needGate) return <GatePrompt onOk={retry} />
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
      <p className="mt-3 rounded-md border bg-muted/50 px-4 py-3 text-sm">
        <strong>怎么进（两步）：</strong>① 浏览器弹出账号密码框时，填管理员发你的站点账号密码；
        ② 若页面提示输入口令，向管理员索取后填上即可。无需注册，看完直接关。
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
  const { data, needGate, error, retry } = useGated(
    () => siteGet<{ title: string; body_md: string; source_path: string; synced_at: string }>(`/docs/${family}/${slug}`),
    [family, slug],
  )
  if (needGate) return <GatePrompt onOk={retry} />
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
