// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B1 S1-5 · 「怎么验证」常设页（公域新增）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B1-001 S1-5——不注册 5 分钟三件自查全路径：
//   公开账本 → CI 徽章 → 形式化清单；三个端点均为匿名只读（批1可信面）
// 红线: ⛔ 不展示凭据/内部编号/日志详情；只给公开地址与看点，不给内部件号
// =============================================================================
import { PageShell } from './PageShell'

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
  return (
    <PageShell
      title="怎么验证"
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
      </div>
    </PageShell>
  )
}
