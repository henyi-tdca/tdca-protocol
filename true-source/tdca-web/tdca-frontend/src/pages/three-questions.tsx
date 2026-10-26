// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B2 S2-3 · 三问向导（批2前三包）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B2-001 S2-3——三问（原创／AI 参与／场景）人答；
//   系统只汇总、⛔ 代判（无「是否原创」判定、无通过／不通过结论）；
//   提交后端未通：不出提交按钮，标「暂存本页，提交功能在建」＋真因
// 红线: 必写「你的回答会作为登记自述，真实性由你本人负责」；页面零内部编号零价格字样
// =============================================================================
import { useState } from 'react'
import { PageShell } from './PageShell'

interface Question {
  key: string
  title: string
  hint: string
  choices: string[]
  /** 自述模板里引用答案的方式 */
  speak: (choice: string, note: string) => string
}

const QUESTIONS: Question[] = [
  {
    key: 'origin',
    title: '第一问：这是你自己原创的吗？',
    hint: '按实情选一项，可在补充里说明来源或合作情况。',
    choices: ['是，完全由我本人创作', '部分借助了现成素材（补充里注明来源）', '其他情况（补充里说明）'],
    speak: (c) => `关于原创性：${c}`,
  },
  {
    key: 'ai',
    title: '第二问：创作过程中是否用过 AI 工具？',
    hint: '用过或没用过都照实选；用过的话，补充里可以写用在哪个环节。',
    choices: ['没用过', '用过（补充里说明用在哪个环节）'],
    speak: (c, n) => {
      const base = `关于 AI 工具使用情况：${c}`
      return n ? `${base}；补充说明：${n}` : base
    },
  },
  {
    key: 'scene',
    title: '第三问：它用在什么场景？',
    hint: '选最接近的一项，补充里可以写具体场景。',
    choices: ['个人学习或研究', '工作或商业场景', '公开发布或分享'],
    speak: (c, n) => {
      const base = `关于使用场景：${c}`
      return n ? `${base}；补充说明：${n}` : base
    },
  },
]

interface Answer {
  choice: string
  note: string
}

export function ThreeQuestionsPage() {
  const [step, setStep] = useState(0)
  const [draft, setDraft] = useState<Answer[]>(QUESTIONS.map(() => ({ choice: '', note: '' })))
  const [copied, setCopied] = useState(false)
  const q = QUESTIONS[step]
  const a = draft[step]
  const answeredAll = draft.every((d) => d.choice !== '')

  function pick(choice: string) {
    setCopied(false)
    setDraft((prev) => prev.map((d, i) => (i === step ? { ...d, choice } : d)))
  }

  function note(text: string) {
    setCopied(false)
    setDraft((prev) => prev.map((d, i) => (i === step ? { ...d, note: text } : d)))
  }

  /** 只汇总、不判定：三问答案成文，⛔ 任何原创性结论 */
  const statement = answeredAll
    ? [
        '【登记自述 · 草稿】',
        ...QUESTIONS.map((qq, i) => {
          const d = draft[i]
          const noteText = d.note.trim()
          const spoken = qq.speak(d.choice, noteText)
          // 第一问的 speak 不含补充，手动并入
          return qq.key === 'origin' && noteText ? `${spoken}；补充说明：${noteText}` : spoken
        }),
      ].join('\n')
    : ''

  async function copyStatement() {
    if (!statement) return
    try {
      await navigator.clipboard.writeText(statement)
      setCopied(true)
    } catch {
      // 剪贴板不可用时静默：自述文字仍在页面上，可手动全选复制
      setCopied(false)
    }
  }

  return (
    <PageShell
      title="三问向导 · 贡献前自述"
      dataSource="纯前端表单（本页零接口调用）；提交功能待后端就绪"
      permission="公开"
      description="交素材前的三问：原创吗？用过 AI 吗？用在什么场景？系统只替你汇成一段自述文字，不作任何判定。"
    >
      <div data-testid="threeq-page" className="space-y-6">
        <p data-testid="threeq-duty" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs leading-relaxed text-amber-800">
          你的回答会作为登记自述，真实性由你本人负责。本向导只汇总、不判定——系统不判断「是否原创」，也不给「通过／不通过」结论。
        </p>

        <section data-testid="threeq-wizard" className="rounded-lg border border-gray-200 p-4">
          <ol data-testid="threeq-progress" className="mb-3 flex flex-wrap gap-2">
            {QUESTIONS.map((qq, i) => (
              <li
                key={qq.key}
                className={`rounded px-2 py-1 text-[11px] ${i === step ? 'bg-gray-800 text-white' : i < step ? 'bg-gray-200 text-gray-600' : 'bg-gray-50 text-gray-400'}`}
              >
                {i + 1}. {qq.title.replace(/第[一二三]问：/, '')}
              </li>
            ))}
          </ol>
          <div className="mb-1 text-[11px] text-gray-400">第 {step + 1} ／ {QUESTIONS.length} 问</div>
          <h3 className="mb-2 text-sm font-semibold text-gray-900">{q.title}</h3>
          <p className="mb-3 text-xs text-gray-500">{q.hint}</p>
          <div className="mb-3 space-y-2">
            {q.choices.map((c) => (
              <label key={c} className="flex cursor-pointer items-start gap-2 rounded border border-gray-200 p-2.5 text-xs text-gray-700 hover:border-gray-400">
                <input
                  data-testid={`threeq-choice-${step}`}
                  type="radio"
                  name={`q-${step}`}
                  checked={a.choice === c}
                  onChange={() => pick(c)}
                  className="mt-0.5"
                />
                <span>{c}</span>
              </label>
            ))}
          </div>
          <input
            data-testid="threeq-note"
            value={a.note}
            onChange={(e) => note(e.target.value)}
            placeholder="一句补充（可选）"
            className="mb-3 w-full rounded border border-gray-300 px-2 py-1.5 text-xs"
          />
          <div className="flex gap-2">
            <button
              data-testid="threeq-prev"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0}
              className="rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-600 disabled:opacity-40"
            >
              上一问
            </button>
            <button
              data-testid="threeq-next"
              onClick={() => setStep((s) => Math.min(QUESTIONS.length - 1, s + 1))}
              disabled={step === QUESTIONS.length - 1}
              className="rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-600 disabled:opacity-40"
            >
              下一问
            </button>
            <button
              data-testid="threeq-back"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              className="rounded border border-dashed border-gray-300 px-3 py-1.5 text-xs text-gray-400"
            >
              回退修改
            </button>
          </div>
        </section>

        <section data-testid="threeq-result" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">汇出的自述文字（草稿，可复制）</h3>
          {statement ? (
            <>
              <pre data-testid="threeq-statement" className="mb-3 overflow-x-auto whitespace-pre-wrap rounded bg-gray-100 p-3 text-xs leading-relaxed text-gray-800">{statement}</pre>
              <button
                data-testid="threeq-copy"
                onClick={copyStatement}
                className="rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
              >
                {copied ? '已复制' : '复制自述'}
              </button>
            </>
          ) : (
            <p className="text-xs text-gray-400">三问都作答后，这里会生成一段自述文字。</p>
          )}
        </section>

        <section data-testid="threeq-pending" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-900">提交功能：<span className="text-amber-600">建设中</span></h3>
          <p className="text-xs leading-relaxed text-gray-600">
            暂存本页，提交功能在建。真因：上传与登记提交接口待建（批 2 后段，待后端就绪）——本页只出草稿与复制，不替你提交、也不替你判定。
          </p>
        </section>
      </div>
    </PageShell>
  )
}
