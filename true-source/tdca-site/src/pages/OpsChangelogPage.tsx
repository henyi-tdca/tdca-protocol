// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: MIGRATE 批5（L1SI206）运维手册三界面之 CHANGELOG（变更记录）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B5-001（同栈直拷为基⛔重写；只进运维私域⛔入公域；
//   内容非空且为最新版——直读在册白名单源件，⛔自造内容⛔改手册原文）
// 复用: 旧版 tdca-frontend/src/pages/ops-manual.tsx 一路（左清单右正文；yaml 可复制；fail-closed）
// 在册源件: TDCA-STD-SITE-INGEST-TRAIL-001（入站留痕制度人读/机读）＋ TDCA-SIGNOFF-STD-SITE-INGEST-TRAIL-001（签批落地件）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api, sessionToken } from '@/lib/client'
import { PageShell } from '@/components/PageShell'

interface FileItem {
  name: string
  label: string
  sha256_16?: string
  bytes?: number
  missing: boolean
}

/** CHANGELOG（变更记录）组：入站每批留痕制度三件（人读/机读/签批落地件）——每批变更留痕之制度与生效凭据 */
const GROUP_PREFIXES = ['TDCA-STD-SITE-INGEST-TRAIL', 'TDCA-SIGNOFF-STD-SITE-INGEST-TRAIL'] as const

/** 手册与制度件按名出件（带会话头；⛔ 文件名即情报——白名单内件才出） */
async function fetchText(name: string): Promise<string> {
  const tok = sessionToken()
  const r = await fetch(`/api/v1/ops/files/${encodeURIComponent(name)}`, {
    headers: tok ? { Authorization: tok } : {},
  })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.text()
}

/** 三面互链（运维私域内导航；⛔ 不入公开导航） */
function TrioLinks() {
  return (
    <p data-testid="ops-changelog-trio" className="px-4 py-2 text-xs text-gray-400">
      <Link to="/ops" className="text-blue-600 underline hover:text-blue-800">← 返回运维端</Link>
      {' ｜ '}
      <Link to="/ops/readme" className="text-blue-600 underline hover:text-blue-800">README 项目说明</Link>
      {' ｜ '}
      <Link to="/ops/ops" className="text-blue-600 underline hover:text-blue-800">OPS 运维操作</Link>
    </p>
  )
}

export function OpsChangelogPage() {
  const [files, setFiles] = useState<FileItem[]>([])
  const [active, setActive] = useState<string>('')
  const [body, setBody] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    void api.get<{ files: FileItem[] }>('/api/v1/ops/files').then((r) => {
      if (r.ok) {
        const group = r.data.files.filter(
          (f) => !f.missing && GROUP_PREFIXES.some((p) => f.name.startsWith(p)))
        setFiles(group)
        if (group[0]) setActive(group[0].name)
      } else {
        // 原始错误只进日志（⛔给用户看路径/堆栈/内部码）
        console.error('[ops/changelog] 清单加载失败：', r.status ?? '', r.detail ?? r.reason)
        setError(sessionToken() ? '本页暂未开放' : '须运维身份（operator/founder）登录后查阅')
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
        console.error('[ops/changelog] 取件失败：', e)
        setError('本页暂未开放')
      })
  }, [active])

  const isYaml = active.endsWith('.yaml') || active.endsWith('.yml')

  return (
    <PageShell
      title="CHANGELOG · 变更记录（入站每批留痕制度）"
      dataSource="/api/v1/ops/files（GET 清单＋按名出件·白名单源件直读）"
      permission="operator/founder（运维门内）"
      description="本界面在册一组三件：内容入站每批留痕制度（人读 V1.0-FROZEN／机读 yaml／签批落地件）——每批变更留痕之制度与生效凭据，站内直读，⛔自改。">
      <div data-testid="ops-changelog" className="grid gap-4 md:grid-cols-[16rem_1fr]">
        <aside className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-4 py-2 text-xs text-gray-400">在册 {files.length} 件（CHANGELOG · 变更记录）</div>
          <ul data-testid="ops-changelog-list" className="divide-y divide-gray-100">
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
          <TrioLinks />
        </aside>
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          {error && (
            <p data-testid="ops-changelog-fail" className="rounded bg-red-50 p-3 text-sm text-red-600">
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
                    data-testid="ops-changelog-copy"
                    onClick={() => void navigator.clipboard?.writeText(body)}
                    className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50">
                    复制全文
                  </button>
                )}
              </div>
              <article data-testid="ops-changelog-body"
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
