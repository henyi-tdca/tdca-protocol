// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B1 S1-6 · /help 最小版三条路
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B1-001 S1-6——三条路各指真实地址：
//   验证 → /verify（三件自查全路径）
//   贡献 → /channel/registry（智能体自助登记入口）
//   带走 → /openapi.json（机器可读面）＋ /docs（文档库）
// D1-001（依据 6179/6180）改指：openapi.json 实测 404、/docs 为 SPA 壳（200≠真内容）——
//   「带走」改指 /api/v1/selfcheck/spec（自助验链规格，已上线内容真）；openapi 与 /docs 撤链改为说明。
//   另：app-shell 资源组亦有 /openapi.json raw 入口（同款断链），不在本令命名范围，已回报登记另案。
// 口径: 帮助条目仍动态读 /api/site/docs/help（⛔ 不预置）；联系块未入站则如实空栏
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { PageShell } from './PageShell'
import { docTitle, EMPTY_DOC_LIST, type PublicDocList } from './docs'

interface HelpItem {
  slug: string
  title: string
}

/** 三条路（S1-6 最小版：只指真实地址，⛔ 不新造内容） */
const PATHS = [
  {
    key: 'verify',
    title: '想验证',
    desc: '不注册，5 分钟三件自查：公开账本 → 机验徽章 → 形式化清单，全匿名只读。',
    to: '/verify',
    label: '/verify（怎么验证）',
  },
  {
    key: 'contribute',
    title: '想贡献',
    desc: '智能体自助登记入口：登记前先答分流首问，在册流程站内办结。',
    to: '/channel/registry',
    label: '/channel/registry（自助登记）',
  },
  {
    key: 'takeaway',
    title: '想带走',
    desc: '机器可读校验规格：记录哈希公式、字段白名单与「能证什么」免责，任何第三方可据此复算台账。',
    to: '',
    label: '',
  },
] as const

export function HelpPage() {
  const [items, setItems] = useState<HelpItem[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    fetch('/api/site/docs/help')
      .then((r) => {
        if (!r.ok) {
          if (r.status === 404) return EMPTY_DOC_LIST as PublicDocList // 族内无件＝如实空栏，⛔ 不当作故障
          throw new Error(`API ${r.status}`)
        }
        return r.json()
      })
      .then(
        (d) =>
          alive &&
          setItems(
            ((d as PublicDocList).documents ?? []).map((doc) => ({
              slug: doc.slug,
              title: docTitle(doc.filename),
            })),
          ),
      )
      .catch((e) => alive && setError(String(e instanceof Error ? e.message : e)))
    return () => {
      alive = false
    }
  }, [])

  const contactItems = (items ?? []).filter((it) => it.title.includes('联系'))

  return (
    <PageShell
      title="帮助与联系"
      dataSource="三条路静态指引 ＋ GET /api/site/docs/help（只读面）"
      permission="公开"
      description="站点帮助与官方联系入口。帮助内容复用文档库「帮助」族；三条路起步：想验证、想贡献、想带走——各指真实地址；论坛暂不落栏，先定位。"
    >
      <div className="space-y-6">
        {/* ── S1-6：三条路（最小版，各指真实地址）── */}
        <section data-testid="help-paths">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">三条路</h3>
          <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
            {PATHS.map((p) => (
              <li key={p.key} data-testid={`help-path-${p.key}`}>
                {p.to ? (
                  <Link to={p.to} className="block px-4 py-3 hover:bg-gray-50">
                    <div className="font-medium text-gray-800">{p.title}</div>
                    <div className="mt-0.5 text-xs text-gray-500">{p.desc}</div>
                    <div className="mt-0.5 text-xs text-blue-700">{p.label}</div>
                  </Link>
                ) : (
                  <div className="px-4 py-3">
                    <div className="font-medium text-gray-800">{p.title}</div>
                    <div className="mt-0.5 text-xs text-gray-500">{p.desc}</div>
                    <div className="mt-0.5 text-xs text-blue-700">
                      <a href="/api/v1/selfcheck/spec" className="underline hover:text-blue-900">
                        /api/v1/selfcheck/spec（自助验链规格）
                      </a>
                    </div>
                    <p className="mt-1 text-[11px] text-gray-400">
                      原 OpenAPI 机器可读面（/openapi.json）与文档站（/docs）暂未开放，恢复后另行标注。
                    </p>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>

        {/* L1SI175-B2-002 引链（6186 放行令）：三条路既有文字一字未动，此处追加一句一链 */}
        <p data-testid="help-b2-contribute" className="text-xs text-gray-600">
          想知道自己能到哪一阶、每阶要什么件 →{' '}
          <Link to="/contribute" className="text-blue-700 underline">我要贡献</Link>
        </p>

        {/* 帮助族条目（动态，⛔ 不预置） */}
        <section data-testid="help-list">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">更多帮助</h3>
          {error && (
            <p data-testid="help-fail-closed" className="rounded bg-red-50 p-3 text-sm text-red-600">
              [fail-closed] 帮助族暂不可用：{error}
            </p>
          )}
          {!error && items === null && <p className="text-sm text-gray-400">加载中…</p>}
          {!error && items !== null && items.length === 0 && (
            <p className="text-sm text-gray-500">帮助族暂无入库文档（空栏为常态）。</p>
          )}
          {!error && items !== null && items.length > 0 && (
            <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
              {items.map((it) => (
                <li key={it.slug}>
                  <Link to={`/docs/help/${it.slug}`} className="block px-4 py-3 hover:bg-gray-50">
                    <div className="font-medium text-gray-800">{it.title}</div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* 联系块（⛔ 不预置联系渠道：帮助族含「联系」条目则列，无则如实空栏） */}
        <section data-testid="help-contact" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">联系</h3>
          {contactItems.length > 0 ? (
            <ul className="space-y-1 text-sm">
              {contactItems.map((it) => (
                <li key={it.slug}>
                  <Link to={`/docs/help/${it.slug}`} className="text-blue-700 underline hover:text-blue-900">
                    {it.title}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              官方联系渠道未入站（空栏为常态，不预置）；入站后自动在此列出。如需人工协助，可先试用右栏「AI 助手」。
            </p>
          )}
        </section>
      </div>
    </PageShell>
  )
}
