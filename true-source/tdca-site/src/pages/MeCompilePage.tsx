// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI208 SEG2-B2-REFIRE-001 块 A — 区 2A 编译转化面
//           （TDCA-AMEND-DESIGN-L1SI207-MY-SPACE-001-AMEND-1，GSEQ-7828）
// 约束矩阵: §三 六步流水线（件内表 6 行为准，标题「五步」为笔误照复令以六步施工）；
//           §四 私料边界四条；§五 三档辅助（默认 M-2）；§六 责任澄清；
//           §八 六态 DRAFT→COMPILING→NEG_PASS→SANDBOX_PASS→PUBLISHED→SUSPENDED；
//           产物一律经 负空间检查→沙盒验证→正空间，⛔跳步；工具一律内嵌（⛔下载再上传）；
//           ⛔整包索取；H-5 ⛔部署（本面为前端骨架，产物登记本会话，接账候后续令）
// 口径（如实）: 本面为编译流水线骨架与向导：逐步可点可停、逐步确认；产出（意图单／目标函数式／
//   函数化资产／负空间声明／合约条款＋协议绑定／发布单元）以会话内草稿呈现，⛔预置真实发布。
// =============================================================================
import { useState } from 'react'
import { PageShell } from '@/components/PageShell'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'

interface ToolRef {
  name: string
  href: string
  note: string
}

interface Step {
  no: number
  key: string
  name: string
  userDoes: string
  tools: ToolRef[]
  output: string
  gate: string
}

const STEPS: Step[] = [
  {
    no: 1, key: 'intent', name: '编译意图',
    userDoes: '说清「我想达成什么」（自然语言；可附私有语料，私料只在私域内使用、逐次授权）',
    tools: [
      { name: 'SKILL 执行官', href: '/toolshelf', note: '会话受理＋意图解析（货架在架）' },
    ],
    output: '意图单（目标·约束·期望形态）', gate: '负空间预检',
  },
  {
    no: 2, key: 'objective', name: '求解目标函数',
    userDoes: '确认目标函数与权重',
    tools: [
      { name: '反函数求解器（inverse-solver）', href: '/downloads/tdca-inverse-solver-v1.0.zip', note: '给定目标效用反推配置方案＋ f⁻ 定标框架' },
    ],
    output: '目标函数式＋求解说明', gate: '—',
  },
  {
    no: 3, key: 'functional', name: '函数化表达',
    userDoes: '提供私有知识库／数据库；确认七要素（私料只作编译输入、不因使用而搬迁）',
    tools: [
      { name: '编译器族（COP／NSFL／KG／函数编译器）', href: '/toolshelf', note: '函数七要素规范，产出含七要素 docstring' },
    ],
    output: '函数化资产（含七要素 docstring）', gate: '体例与零编号',
  },
  {
    no: 4, key: 'negative', name: '定义负空间',
    userDoes: '勾选并补充「我不会做／不允许做」',
    tools: [
      { name: 'NSFL 负空间函数语言', href: '/toolshelf', note: '负空间栏＋负空间检查' },
    ],
    output: '负空间声明', gate: '负空间检查',
  },
  {
    no: 5, key: 'contract', name: '合约与思维协议',
    userDoes: '确认协作原则、条款、授权范围；确认智能体行为范式',
    tools: [
      { name: '智能合约模板（契约模板 3 件／六要素）', href: '/downloads/tdca-templates-v1.0.zip', note: '＋授权件四要件' },
      { name: '思维协议库（cop-library 290 件）', href: '/library/cop-library', note: '协议绑定，赋予智能体符合 TDCA 的行为范式' },
    ],
    output: '合约条款＋思维协议绑定＋授权件', gate: '沙盒验证',
  },
  {
    no: 6, key: 'publish', name: '创建与发布',
    userDoes: '点发布并确认（发布前六道门已序过，⛔跳步）',
    tools: [
      { name: 'SKILL 执行官', href: '/toolshelf', note: '编排＋三段门（负空间检查→沙盒验证→正空间）' },
    ],
    output: '公域可见之协作单元', gate: '正空间',
  },
]

const STATES = ['DRAFT', 'COMPILING', 'NEG_PASS', 'SANDBOX_PASS', 'PUBLISHED', 'SUSPENDED'] as const

const MODES = [
  { key: 'M-1', name: '自助', desc: '会写函数式、懂负空间；用户自办，工具只校验' },
  { key: 'M-2', name: '向导（默认）', desc: '只答问题、只做确认；工具与智能体逐步代做，用户逐步确认' },
  { key: 'M-3', name: '代劳', desc: '只给目标与语料、最后签署；SKILL 执行官全程代办，仅在须本人签署处出面' },
]

const PRIVATE_RULES = [
  '私有知识库／数据库／聊天记录只在私域内使用；⛔ 入公域、⛔ 入仓（业务数据不入仓）',
  '只作编译输入；输出限于编译产物（函数化表达·负空间声明·条款·协议绑定）',
  '私料不因使用而搬迁；可随时停止授权并删除接入',
  '助手与工具对其之访问须用户逐次授权（⛔ 默认全量读取）；每次编译留痕',
]

function stateAt(doneCount: number): (typeof STATES)[number] {
  if (doneCount <= 0) return 'DRAFT'
  if (doneCount <= 2) return 'COMPILING'
  if (doneCount === 3) return 'NEG_PASS'
  if (doneCount <= 5) return 'SANDBOX_PASS'
  return 'PUBLISHED'
}

export function MeCompilePage() {
  const gate = usePrivateGate()
  const [mode, setMode] = useState('M-2')
  const [done, setDone] = useState<boolean[]>(STEPS.map(() => false))
  const [open, setOpen] = useState<number>(0)
  const doneCount = done.filter(Boolean).length
  const current = stateAt(doneCount)

  if (gate !== 'ok') {
    return (
      <PageShell title="编译转化" dataSource="—" permission="须登录（谁的事谁可见）"
                 description="区 2A：把「我的知识与意图」编译成「可在公域可信协作的形态」的车间。">
        <PrivateGateNotice state={gate} />
      </PageShell>
    )
  }

  return (
    <PageShell title="编译转化（区 2A）" dataSource="会话内草稿（骨架期，⛔入账）" permission="须登录"
               description="六步流水线：意图→目标函数→函数化→负空间→合约与协议→创建与发布。产物一律经 负空间检查→沙盒验证→正空间，⛔跳步。">
      <div className="space-y-4">
        {/* 三档辅助（默认 M-2） */}
        <section data-testid="compile-modes" className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">辅助模式（默认：向导）</h3>
          <div className="grid gap-2 sm:grid-cols-3">
            {MODES.map((m) => (
              <button key={m.key} type="button" data-testid={`compile-mode-${m.key}`}
                      onClick={() => setMode(m.key)}
                      className={`rounded-md border p-3 text-left text-xs ${mode === m.key ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 bg-white hover:border-emerald-300'}`}>
                <div className="font-medium text-gray-800">{m.name}</div>
                <div className="mt-1 text-gray-500">{m.desc}</div>
              </button>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-gray-400">硬线：⛔ 代签；每一步可回退与重跑；产物责任仍在用户（目标与语料之来源），官方工具负「规范符合性」之责，⛔ 负「商业判断」之责。</p>
        </section>

        {/* 六态状态机 */}
        <section data-testid="compile-states" className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">状态（六态）</h3>
          <ol className="flex flex-wrap gap-1.5">
            {STATES.map((s) => (
              <li key={s} data-testid={`compile-state-${s}`}
                  className={`rounded px-2 py-1 text-[11px] font-mono ${s === current ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-500'}`}>
                {s}
              </li>
            ))}
          </ol>
          <p className="mt-2 text-[11px] text-gray-400">当前：{current}（随逐步确认推进；逐步可点可停，任一步可回退重跑）</p>
        </section>

        {/* 六步流水线 */}
        <section data-testid="compile-steps" className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">六步流水线（每步显示所用工具与产出，⛔黑箱）</h3>
          <ol className="space-y-2">
            {STEPS.map((st, i) => (
              <li key={st.key} data-testid={`compile-step-${st.key}`} className="rounded-md border border-gray-200 bg-white">
                <button type="button" onClick={() => setOpen(open === i ? -1 : i)}
                        className="flex w-full items-center justify-between px-3 py-2 text-left text-sm">
                  <span>
                    <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-[11px] text-emerald-700">{st.no}</span>
                    <span className="font-medium text-gray-800">{st.name}</span>
                    <span className="ml-2 text-[11px] text-gray-400">门：{st.gate}</span>
                  </span>
                  <span className="text-[11px] text-gray-400">{open === i ? '收起' : '展开'}</span>
                </button>
                {open === i && (
                  <div className="border-t border-gray-100 px-3 py-2 text-xs text-gray-600">
                    <p><span className="text-gray-400">用户做什么：</span>{st.userDoes}</p>
                    <div className="mt-1">
                      <span className="text-gray-400">官方工具（内嵌，⛔下载再上传）：</span>
                      <ul className="mt-0.5 space-y-0.5">
                        {st.tools.map((t) => (
                          <li key={t.name}>· <a href={t.href} className="text-blue-700 underline hover:bg-blue-50">{t.name}</a>——{t.note}</li>
                        ))}
                      </ul>
                    </div>
                    <p className="mt-1"><span className="text-gray-400">产出：</span>{st.output}</p>
                    <label className="mt-2 flex items-center gap-2">
                      <input type="checkbox" data-testid={`compile-confirm-${st.key}`}
                             checked={done[i]}
                             onChange={(e) => setDone((prev) => prev.map((v, j) => (j === i ? e.target.checked : v)))} />
                      <span>{mode === 'M-1' ? '本步自检完成' : mode === 'M-3' ? '本步已由 SKILL 执行官代办，本人确认' : '本步工具代做已完成，我逐步确认'}</span>
                    </label>
                  </div>
                )}
              </li>
            ))}
          </ol>
        </section>

        {/* 私料边界 */}
        <section data-testid="compile-private-rules" className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">私有语料接入与边界（要紧）</h3>
          <ul className="list-inside list-disc space-y-1 text-xs text-gray-700">
            {PRIVATE_RULES.map((r) => <li key={r}>{r}</li>)}
          </ul>
        </section>
      </div>
    </PageShell>
  )
}
