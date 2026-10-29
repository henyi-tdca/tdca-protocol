// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 手册接口化站内直读（/ops/manual——INACCOUNT-DEPLOY 块 2）
// 约束矩阵: TDCA-HANDOFF-OPS-INACCOUNT-DEPLOY-001 §三-D（左清单右正文；复用既有文档纯文本渲染；yaml 可复制）
// 复用: PageShell / api+sessionToken（照 ops-logs-list 透传惯例）；⛔ 不加 markdown 依赖（既有渲染器＝纯文本 pre-wrap）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api, sessionToken } from '@/api/client'
import { PageShell } from './PageShell'

interface FileItem {
  name: string
  label: string
  sha256_16?: string
  bytes?: number
  missing: boolean
}

/** 手册与制度件按名出件（带会话头；⛔ 文件名即情报——白名单内件才出） */
async function fetchText(name: string): Promise<string> {
  const tok = sessionToken()
  const r = await fetch(`/api/v1/ops/files/${encodeURIComponent(name)}`, {
    headers: tok ? { Authorization: tok } : {},
  })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.text()
}

export function OpsManualPage() {
  const [files, setFiles] = useState<FileItem[]>([])
  const [active, setActive] = useState<string>('')
  const [body, setBody] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    void api.get<{ files: FileItem[] }>('/api/v1/ops/files').then((r) => {
      if (r.ok) {
        setFiles(r.data.files.filter((f) => !f.missing))
        const first = r.data.files.find((f) => !f.missing)
        if (first) setActive(first.name)
      } else {
        // L1SI181-P0-FIX-002 F-3：原始错误只进日志（⛔给用户看路径/堆栈/内部码）
        console.error('[ops/manual] 手册清单加载失败：', r.status ?? '', r.code ?? '', r.rawDetail ?? r.detail ?? r.reason)
        setError('本页暂未开放')
      }
    })
  }, [])

  useEffect(() => {
    if (!active) return
    setBody('')
    setError('')
    fetchText(active)
      .then(setBody)
      .catch((e) => {
        // L1SI181-P0-FIX-002 F-3：原始错误只进日志，页面只给一句人话
        console.error('[ops/manual] 手册取件失败：', e)
        setError('本页暂未开放')
      })
  }, [active])

  const isYaml = active.endsWith('.yaml') || active.endsWith('.yml')

  return (
    <PageShell dataNature="real"
      title="运维手册与制度（点击直接阅读）"
      dataSource="/api/v1/ops/files（GET 清单＋按名出件）"
      permission="operator/founder（运维门内）"
      description="在册七件：运维手册／运维制度／日志模板／入站留痕制度——站内直读，不再输口令；新增件须登记白名单。">
      <div data-testid="ops-manual" className="grid gap-4 md:grid-cols-[16rem_1fr]">
        <aside className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-4 py-2 text-xs text-gray-400">在册 {files.length} 件（人工登记）</div>
          <ul data-testid="ops-manual-list" className="divide-y divide-gray-100">
            {files.map((f) => (
              <li key={f.name}>
                <button
                  type="button"
                  onClick={() => setActive(f.name)}
                  className={`block w-full px-4 py-2 text-left text-sm hover:bg-gray-50 ${active === f.name ? 'bg-blue-50 font-medium text-blue-700' : 'text-gray-700'}`}>
                  {f.label}
                  <span className="block truncate text-xs text-gray-400">{f.sha256_16 ?? ''}</span>
                </button>
              </li>
            ))}
            {files.length === 0 && <li className="px-4 py-3 text-sm text-gray-400">清单加载中…</li>}
          </ul>
          <p className="px-4 py-2 text-xs text-gray-400">
            <Link to="/ops" className="text-blue-600 underline hover:text-blue-800">← 返回运维端</Link>
          </p>
        </aside>
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          {error && (
            <p data-testid="ops-manual-fail" className="rounded bg-red-50 p-3 text-sm text-red-600">
              [fail-closed] 取件失败：{error}
            </p>
          )}
          {!error && !body && <p className="text-sm text-gray-400">读取中…</p>}
          {!error && body && (
            <>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-800">
                  {files.find((f) => f.name === active)?.label ?? active}
                </h3>
                {isYaml && (
                  <button
                    type="button"
                    data-testid="ops-manual-copy"
                    onClick={() => void navigator.clipboard?.writeText(body)}
                    className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50">
                    复制全文
                  </button>
                )}
              </div>
              <article data-testid="ops-manual-body"
                className="whitespace-pre-wrap text-sm leading-6 text-gray-700">
                {body}
              </article>
              <footer className="mt-6 border-t border-gray-100 pt-2 text-xs text-gray-400">
                件名：{active} · 本站只读，不跳转外部
              </footer>
            </>
          )}
        </section>
      </div>
    </PageShell>
  )
}
