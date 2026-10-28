// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI178 公域披露页（匿名可查 · 含版本历史）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI178-SITE-PRIVATE-ZONE-002 §二.3——匿名可查（⛔ 须登录才可看＝不合令）；
//   含版本历史（旧版可读）；按节点／按空间两维筛选；所列条目均为虚构样例（标数据性质）；
//   ⛔ 不展示内部编号形态 · ⛔ 不展示实现细节 · ⛔ 不含凭据 · ⛔ 不含自然人敏感信息
// =============================================================================
import { useState } from 'react'
import { PageShell } from './PageShell'

interface HistoryEntry {
  ver: string
  invalid: boolean
  range: string
  text: string
  reason: string
}

interface DisclosureItem {
  node: string
  space: string
  name: string
  scope: string
  version: string
  summary: string
  history: HistoryEntry[]
}

/** 披露条目（虚构样例，不指向真实在册件） */
const ITEMS: DisclosureItem[] = [
  {
    node: '示例节点·青屿',
    space: '负空间',
    name: '否决动作留痕判据',
    scope: '示例节点·青屿域内一切否决类动作',
    version: '2026-10-21 起 · 第 2 版',
    summary: '凡否决动作必留痕：留痕含动作人、时点、依据三项，缺一不可。',
    history: [
      { ver: '第 1 版', invalid: true, range: '2026-09-30~2026-10-20', text: '否决必留痕（字段未细化）。', reason: '被第 2 版替代。' },
    ],
  },
  {
    node: '示例节点·青屿',
    space: '沙盒出盒',
    name: '沙盒出盒门槛（三次演练）',
    scope: '示例节点·青屿沙盒演练成果出盒',
    version: '2026-10-27 起 · 现行版',
    summary: '出盒须三次演练通过并附演练留痕与复核签字。',
    history: [
      { ver: '早期版', invalid: true, range: '2026-10-01~2026-10-26', text: '一次演练通过即可出盒。', reason: '门槛收紧，被现行版替代。' },
    ],
  },
  {
    node: '示例节点·白鹿',
    space: '正空间',
    name: '域内知识库分层上架约定（披露节选）',
    scope: '示例节点·白鹿域内知识上架',
    version: '2026-10-15 起 · 第 5 版（披露节选）',
    summary: '知识分公开层／域内层两级；域内层未经披露不上对外面。',
    history: [],
  },
]

function DisclosureCard({ item }: { item: DisclosureItem }) {
  const [open, setOpen] = useState(false)
  return (
    <article data-testid={`disclosure-card-${item.name}`} className="rounded-xl border border-gray-200 bg-white p-5">
      <h3 className="mb-2.5 text-base font-semibold text-gray-900">
        {item.name}{' '}
        <span className="rounded bg-sky-100 px-2 py-0.5 text-xs text-sky-800">{item.space}</span>
      </h3>
      <dl className="grid grid-cols-[110px_1fr] gap-1.5 text-[13px]">
        <dt className="text-gray-500">规则名称</dt>
        <dd>{item.name}</dd>
        <dt className="text-gray-500">所属空间</dt>
        <dd>{item.space}</dd>
        <dt className="text-gray-500">适用范围</dt>
        <dd>{item.scope}</dd>
        <dt className="text-gray-500">生效时间/版本</dt>
        <dd>
          {item.version} <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-700">现行有效</span>
        </dd>
        <dt className="text-gray-500">判据摘要</dt>
        <dd>{item.summary}</dd>
      </dl>
      {item.history.length > 0 && (
        <>
          <button data-testid={`disclosure-hist-toggle-${item.name}`} onClick={() => setOpen((v) => !v)}
                  className="mt-2 cursor-pointer text-[13px] text-teal-700">
            {open ? '▾' : '▸'} 版本历史（旧版可读）
          </button>
          {open && (
            <div data-testid={`disclosure-hist-${item.name}`} className="mt-2.5 border-t border-dashed border-gray-200 pt-2.5">
              {item.history.map((h) => (
                <div key={h.ver} className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-3 text-[13px] opacity-90">
                  {h.ver} <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-700">已失效</span> · {h.range}
                  <br />
                  {h.text}
                  <br />
                  <small className="text-gray-500">失效原因：{h.reason}</small>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </article>
  )
}

export function NodeDisclosurePage() {
  const [node, setNode] = useState('')
  const [space, setSpace] = useState('')
  const shown = ITEMS.filter((i) => (!node || i.node === node) && (!space || i.space === space))

  return (
    <PageShell
      title="规则披露公示 · 按节点查阅"
      dataSource="纯前端样例态（虚构示例条目）；零接口调用"
      permission="公开（匿名可读）"
      description="私域条目的对外披露面：匿名可查、无需登录，含版本历史。公示才公信——未披露条目不构成对外依据。"
    >
      <div data-testid="disclosure-page" className="space-y-5">
        {/* 页头（照样张乙：匿名可查标识） */}
        <div data-testid="disclosure-header" className="rounded-lg bg-teal-700 px-5 py-4 text-white">
          <div className="text-lg font-bold">规则披露公示 · 按节点查阅</div>
          <span className="mt-1.5 inline-block rounded-full bg-teal-100 px-3 py-0.5 text-xs text-teal-800">
            匿名可查 · 无需登录 · 公示才公信
          </span>
        </div>

        {/* 两维筛选（按节点／按空间） */}
        <div data-testid="disclosure-filters" className="flex flex-wrap items-end gap-3.5 rounded-lg border border-gray-200 bg-white p-3.5">
          <div>
            <label className="mb-1 block text-xs text-gray-500" htmlFor="pz-f-node">按节点名筛选</label>
            <select id="pz-f-node" value={node} onChange={(e) => setNode(e.target.value)}
                    className="min-w-[180px] rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]">
              <option value="">全部节点</option>
              <option>示例节点·青屿</option>
              <option>示例节点·白鹿</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-500" htmlFor="pz-f-space">按空间筛选</label>
            <select id="pz-f-space" value={space} onChange={(e) => setSpace(e.target.value)}
                    className="min-w-[180px] rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]">
              <option value="">全部空间</option>
              <option>负空间</option>
              <option>沙盒出盒</option>
              <option>正空间</option>
            </select>
          </div>
        </div>

        {/* 披露条目（样例态） */}
        <div data-testid="disclosure-list" className="space-y-4">
          {shown.map((i) => (
            <DisclosureCard key={i.name} item={i} />
          ))}
          {shown.length === 0 && (
            <p className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-400">
              当前筛选条件下暂无披露条目
            </p>
          )}
        </div>

        <footer data-testid="disclosure-footer" className="pb-6 text-xs leading-relaxed text-gray-400">
          本页所列条目均为虚构示例，仅示意披露页形态，不指向真实在册件。
          <br />
          禁项自查：⛔ 不展示内部编号形态 · ⛔ 不展示实现细节 · ⛔ 不含凭据 · ⛔ 不含自然人敏感信息。
        </footer>
      </div>
    </PageShell>
  )
}
