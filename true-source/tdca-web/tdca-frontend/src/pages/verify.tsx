// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B1 S1-5 · 「怎么验证」常设页（公域新增）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B1-001 S1-5——不注册 5 分钟三件自查全路径：
//   公开账本 → CI 徽章 → 形式化清单；三个端点均为匿名只读（批1可信面）
// 红线: ⛔ 不展示凭据/内部编号/日志详情；只给公开地址与看点，不给内部件号
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

// ── 1.6-C 自助验链四区块（TDCA-HANDOFF-EXEC-L1SI175-C1-001）──
// 纯只读面追加：spec／anchor／nca-history 三源并行拉取，C3 单条查按需触发；
// C3 只显 fields_whitelist（运行时以 spec 负载为准），404 显人话＋错误码；
// EVT- 族登记待核：event_id 整串可显，⛔ 再拆 CASE 段；四区块各带 disclaimer 原样＋限速。
interface SpecData {
  entry: { record: string; anchor: string }
  rec_hash_spec: string
  anchor_digest_spec: string
  fields_whitelist: string[]
  not_returned: string[]
  artifact_filename_note: string
  rate_limit: string
  sha256_8_note: string
  page_disclaimer: string
}

interface AnchorData {
  anchor: {
    date: string
    row_count: number
    anchor_digest: string
    leaf_count: number
    detached_count: number
    detached_digest: string
    schema_version: number
  }
  canonicalization: string
  page_disclaimer: string
}

interface TaxEvent {
  event_id: string
  type: string
  ts: string
}

interface VerifyStep {
  no: string
  title: string
  page: string
  pageLabel: string
  endpoint: string
  look: string
}

/** 三件自查（全路径照 S1-5：公开账本 → 徽章 → 形式化清单） */
const STEPS: VerifyStep[] = [
  {
    no: '一',
    title: '查公开账本',
    page: '/audit',
    pageLabel: '审计透明页',
    endpoint: 'GET /api/v1/audit/ledger-public',
    look: '看存证链公开账本是否可查：每一笔记账带哈希，前后相衔，任何人可独立核验。',
  },
  {
    no: '二',
    title: '看机验徽章',
    page: '/formal',
    pageLabel: '形式化页',
    endpoint: 'GET /api/v1/ci/badge',
    look: '看最近一回机验状态一行绿/红（PASS/FAIL）；徽章只报状态，不含日志详情。',
  },
  {
    no: '三',
    title: '对形式化清单',
    page: '/formal',
    pageLabel: '形式化页',
    endpoint: 'GET /api/v1/formal/conclusion/catalog',
    look: '看已入站结论清单：每条只含结论文字与数据性质（形式化已证／模拟／评估），可逐条对读。',
  },
]

export function VerifyPage() {
  // 1.6-C 四区块数据源（纯只读；失败 fail-closed，不猜测）
  const [spec, setSpec] = useState<SpecData | null>(null)
  const [anchor, setAnchor] = useState<AnchorData | null>(null)
  const [events, setEvents] = useState<TaxEvent[] | null>(null)
  const [cFail, setCFail] = useState('')
  // C3 单条自助查（按需触发，尊重 60/min/IP 限速）
  const [qid, setQid] = useState('')
  const [querying, setQuerying] = useState(false)
  const [record, setRecord] = useState<Record<string, unknown> | null>(null)
  const [notFound, setNotFound] = useState('')
  const [qError, setQError] = useState('')

  useEffect(() => {
    let alive = true
    ;(async () => {
      const [r1, r2, r3] = await Promise.all([
        api.get<SpecData>('/api/v1/selfcheck/spec'),
        api.get<AnchorData>('/api/v1/selfcheck/anchor'),
        api.get<{ events: TaxEvent[] }>('/api/v1/tax/nca-history'),
      ])
      if (!alive) return
      const errs = [r1, r2, r3].filter((r) => !r.ok)
      if (errs.length > 0) {
        setCFail(errs.map((r) => (r as { status?: number }).status ?? 'fail').join('/'))
      }
      // 各源独立落态：单源失败不拖垮其余区块（区块内自显 fail-closed）
      if (r1.ok) setSpec(r1.data)
      if (r2.ok) setAnchor(r2.data)
      if (r3.ok) setEvents(r3.data.events)
    })()
    return () => { alive = false }
  }, [])

  /** C3：只显 fields_whitelist 内字段（运行时以 spec 负载为准） */
  async function queryOne(id: string) {
    const clean = id.trim()
    if (!clean) return
    setQuerying(true)
    setRecord(null)
    setNotFound('')
    setQError('')
    const r = await api.get<Record<string, unknown>>(`/api/v1/selfcheck/nca/${encodeURIComponent(clean)}`)
    setQuerying(false)
    if (r.ok) {
      setRecord(r.data)
      return
    }
    if (r.status === 404) {
      setNotFound(r.code ?? 'TDCA-E-ASSET-STATE-001')
      return
    }
    setQError(r.detail ?? '查询暂不可用')
  }

  return (
    <PageShell
      title="怎么验证 · 5 分钟三件自查"
      dataSource="匿名只读三件：ledger-public ／ ci/badge ／ formal/conclusion/catalog"
      permission="公开"
      description="不注册、不登录，5 分钟三件自查：公开账本 → 机验徽章 → 形式化清单。三个端点都是匿名只读，任何第三方可复算。体验期免费使用，收费标准另定。"
    >
      <div data-testid="verify-page" className="space-y-6">
        <section data-testid="verify-intro">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">三件自查（全程匿名，约 5 分钟）</h3>
          <ol className="space-y-4">
            {STEPS.map((s) => (
              <li key={s.no} data-testid={`verify-step-${s.no}`} className="rounded-lg border border-gray-200 p-4">
                <div className="mb-1 text-sm font-semibold text-gray-800">
                  第{s.no}件 · {s.title}
                </div>
                <div className="space-y-1 text-xs leading-relaxed text-gray-600">
                  <p>
                    页面：<span className="text-gray-800">{s.page}</span>（{s.pageLabel}）
                  </p>
                  <p>
                    端点：<code className="rounded bg-gray-100 px-1">{s.endpoint}</code>
                  </p>
                  <p>看点：{s.look}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section data-testid="verify-note" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">口径</h3>
          <ul className="space-y-1.5 text-xs leading-relaxed text-gray-600">
            <li>三件全部匿名可读——验证不需要信任本站，只需要复算公开面。</li>
            <li>徽章＝最近一回手动机验结果（非自动门禁）；账本与清单以在册仓库为唯一权威源。</li>
            <li>工具货架公开目录（/api/v1/toolshelf/catalog）与文献族公开目录（/api/v1/library/paper/catalog）同属匿名面，可一并走查。</li>
          </ul>
        </section>

        {/* ===== 1.6-C 自助验链四区块（追加区：上方三件自查与口径区块一字未动）===== */}
        {cFail && (
          <p data-testid="c1-fail-closed" className="rounded bg-red-50 p-3 text-xs text-red-600">
            [fail-closed] 部分验链数据源暂不可用（{cFail}）：下方区块以实际取回者为准，未取回区块明示。
          </p>
        )}

        {/* C1 校验规格：spec 原文照排 */}
        <section data-testid="verify-spec" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">校验规格（原文照排）</h3>
          {spec ? (
            <div className="space-y-3 text-xs leading-relaxed text-gray-600">
              <div>
                <div className="mb-1 font-semibold text-gray-700">记录哈希公式</div>
                <pre data-testid="spec-rec-hash" className="overflow-x-auto rounded bg-gray-100 p-2 text-[11px]">{spec.rec_hash_spec}</pre>
              </div>
              <div>
                <div className="mb-1 font-semibold text-gray-700">锚点摘要公式</div>
                <pre data-testid="spec-anchor-spec" className="overflow-x-auto rounded bg-gray-100 p-2 text-[11px]">{spec.anchor_digest_spec}</pre>
              </div>
              <div>
                <div className="mb-1 font-semibold text-gray-700">响应字段白名单（只显这些）</div>
                <p data-testid="spec-whitelist" className="rounded bg-gray-50 p-2 font-mono text-[11px] break-all">{spec.fields_whitelist.join(' ／ ')}</p>
              </div>
              <div>
                <div className="mb-1 font-semibold text-gray-700">不返回（明确不出）</div>
                <ul className="list-inside list-disc space-y-0.5">
                  {spec.not_returned.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
              <ul className="list-inside list-disc space-y-0.5">
                <li>{spec.sha256_8_note}</li>
                <li>{spec.artifact_filename_note}</li>
              </ul>
              <footer className="space-y-1 border-t border-gray-100 pt-2 text-[11px] text-gray-500">
                <p>能证什么：{spec.page_disclaimer}</p>
                <p>限速：{spec.rate_limit}</p>
              </footer>
            </div>
          ) : (
            <p className="text-xs text-gray-400">{cFail ? '[fail-closed] 规格数据暂不可得' : '加载中…'}</p>
          )}
        </section>

        {/* C2 锚点核验：anchor 原值 + 一句怎么自己算 */}
        <section data-testid="verify-anchor-block" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">锚点核验</h3>
          {anchor ? (
            <div className="space-y-3 text-xs leading-relaxed text-gray-600">
              <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <div className="rounded bg-gray-50 p-2">
                  <dt className="text-[10px] text-gray-400">锚日期</dt>
                  <dd className="font-mono text-gray-800">{anchor.anchor.date}</dd>
                </div>
                <div className="rounded bg-gray-50 p-2">
                  <dt className="text-[10px] text-gray-400">台账行数</dt>
                  <dd className="font-mono text-gray-800">{anchor.anchor.row_count}</dd>
                </div>
                <div className="rounded bg-gray-50 p-2">
                  <dt className="text-[10px] text-gray-400">叶哈希数</dt>
                  <dd className="font-mono text-gray-800">{anchor.anchor.leaf_count}</dd>
                </div>
                <div className="rounded bg-gray-50 p-2">
                  <dt className="text-[10px] text-gray-400">摘除叶数</dt>
                  <dd className="font-mono text-gray-800">{anchor.anchor.detached_count}</dd>
                </div>
                <div className="col-span-2 rounded bg-gray-50 p-2">
                  <dt className="text-[10px] text-gray-400">anchor_digest</dt>
                  <dd data-testid="anchor-digest" className="break-all font-mono text-gray-800">{anchor.anchor.anchor_digest}</dd>
                </div>
                <div className="col-span-2 rounded bg-gray-50 p-2">
                  <dt className="text-[10px] text-gray-400">detached_digest</dt>
                  <dd className="break-all font-mono text-gray-800">{anchor.anchor.detached_digest}</dd>
                </div>
              </dl>
              <div>
                <div className="mb-1 font-semibold text-gray-700">canonicalization（口径写死）</div>
                <pre data-testid="anchor-canonicalization" className="overflow-x-auto rounded bg-gray-100 p-2 text-[11px]">{anchor.canonicalization}</pre>
              </div>
              <p className="rounded bg-blue-50 p-2 text-blue-700">
                怎么自己算：取当日台账全部叶哈希按字典序排序，与 date、row_count 按上方「锚点摘要公式」拼接求 SHA-256，取十六进制大写前 16 位，与此处 anchor_digest 对读——一致即「当日台账形态与公开锚一致」。
              </p>
              <footer className="space-y-1 border-t border-gray-100 pt-2 text-[11px] text-gray-500">
                <p>能证什么：{anchor.page_disclaimer}</p>
                <p>限速：{spec?.rate_limit}</p>
              </footer>
            </div>
          ) : (
            <p className="text-xs text-gray-400">{cFail ? '[fail-closed] 锚点数据暂不可得' : '加载中…'}</p>
          )}
        </section>

        {/* C3 单条自助查：只显 fields_whitelist；404 显人话＋错误码 */}
        <section data-testid="verify-selfcheck" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">单条自助查（台账记录）</h3>
          <p className="mb-2 text-xs text-gray-500">
            端点：GET /api/v1/selfcheck/nca/｛nca_id｝；只显字段白名单内字段，其余一律不出。
          </p>
          <div className="mb-3 flex gap-2">
            <input
              data-testid="c3-input"
              value={qid}
              onChange={(e) => setQid(e.target.value)}
              placeholder="输入 nca_id"
              className="flex-1 rounded border border-gray-300 px-2 py-1.5 font-mono text-xs"
            />
            <button
              data-testid="c3-query"
              onClick={() => queryOne(qid)}
              disabled={querying || !qid.trim()}
              className="rounded bg-gray-800 px-3 py-1.5 text-xs text-white disabled:opacity-40"
            >
              {querying ? '查询中…' : '查询'}
            </button>
          </div>
          {notFound && (
            <p data-testid="c3-not-found" className="rounded border border-dashed border-gray-300 bg-gray-50 p-3 text-xs text-gray-600">
              未找到：该 nca_id 不存在于台账（请核对查询键后再试）。错误码：
              <code className="rounded bg-gray-100 px-1">{notFound}</code>
            </p>
          )}
          {qError && (
            <p data-testid="c3-error" className="rounded bg-red-50 p-3 text-xs text-red-600">
              [fail-closed] 查询暂不可用：{qError}
            </p>
          )}
          {record && spec && (
            <dl data-testid="c3-record" className="space-y-1.5">
              {spec.fields_whitelist.map((k) =>
                record[k] !== undefined && record[k] !== null ? (
                  <div key={k} className="flex gap-2 text-xs">
                    <dt className="w-44 shrink-0 font-mono text-gray-500">{k}</dt>
                    <dd className="break-all font-mono text-gray-800">{String(record[k])}</dd>
                  </div>
                ) : null,
              )}
            </dl>
          )}
          <footer className="mt-3 space-y-1 border-t border-gray-100 pt-2 text-[11px] text-gray-500">
            <p>能证什么：{spec?.page_disclaimer ?? '（规格未取回，免责声明暂不可得）'}</p>
            <p>限速：{spec?.rate_limit ?? '（规格未取回）'}</p>
          </footer>
        </section>

        {/* C4 税事件时间轴：event_id 整串可显（EVT- 族登记待核），⛔ 拆 CASE 段；按时间倒序 */}
        <section data-testid="verify-events" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">税事件时间轴（倒序）</h3>
          {events && events.length > 0 ? (
            <ol data-testid="tax-event-list" className="space-y-2">
              {[...events]
                .sort((a, b) => b.ts.localeCompare(a.ts))
                .map((e) => (
                  <li key={e.event_id} data-testid="tax-event" className="flex flex-wrap items-baseline gap-x-3 text-xs">
                    <span className="font-mono text-gray-400">{e.ts}</span>
                    <span className="font-mono text-gray-800">{e.event_id}</span>
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600">{e.type}</span>
                  </li>
                ))}
            </ol>
          ) : (
            <p className="text-xs text-gray-400">{events ? '暂无税事件' : cFail ? '[fail-closed] 税事件数据暂不可得' : '加载中…'}</p>
          )}
          <footer className="mt-3 space-y-1 border-t border-gray-100 pt-2 text-[11px] text-gray-500">
            <p>能证什么：{spec?.page_disclaimer ?? '（规格未取回，免责声明暂不可得）'}</p>
            <p>限速：{spec?.rate_limit ?? '（规格未取回）'}</p>
          </footer>
        </section>
      </div>
    </PageShell>
  )
}
