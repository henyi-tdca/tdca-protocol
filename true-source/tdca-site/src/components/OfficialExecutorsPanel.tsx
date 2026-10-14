// 官方执行体目录＋制度执行/资产使用分野＋令牌身份前置判据（执行体批呈现件）
// 口径：官方集群＝制度之执行体（不与普通用户、履约方混述）；零编号；不显任何值
interface Executor {
  key: string
  name: string
  role: string
  can: string
}

const EXECUTORS: Executor[] = [
  { key: 'trainer', name: '培训导师', role: '制度里的执教面（学术交流与考核测评）', can: '学术交流、考核测评、学习路径' },
  { key: 'executor', name: '执行官', role: '制度里的执行面（任务执行与交付闭环）', can: '任务执行、交付闭环' },
  { key: 'auditor', name: '审查官', role: '制度里的监督面（代码审查与合规审计）', can: '代码审查、合规审计' },
  { key: 'service', name: '服务官', role: '制度里的服务面（行业顾问与落地匹配）', can: '行业顾问、落地匹配' },
  { key: 'genie', name: '效用精灵', role: '制度里的度量面（正和满意解与效用计量）', can: '正和满意解、效用计量' },
]

export function OfficialExecutorsPanel() {
  return (
    <section data-testid="executors-directory" className="mt-8 space-y-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
      <header>
        <h2 className="text-sm font-semibold text-gray-800">官方执行体目录</h2>
        <p className="text-xs text-gray-500">
          官方集群不是普通用户，是制度自己的执行体（手脚）。每把三句话：是制度里的哪个角色、能干什么、怎么用。
          确权状态以观测页状态灯为准。
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {EXECUTORS.map((e) => (
          <div key={e.key} data-testid={`executor-${e.key}`} className="rounded-lg border border-gray-200 bg-white p-3">
            <h3 className="text-xs font-semibold text-gray-800">{e.name} · 官方执行体</h3>
            <p className="mt-1 text-xs text-gray-600">我是{e.role}。</p>
            <p className="mt-1 text-xs text-gray-600">我能干：{e.can}。</p>
            <p className="mt-1 text-xs text-gray-500">
              怎么用：在线＝站内直接使用；离线＝本地部署（如实标注「本地部署」，离线能力是否对外另候明示）。
            </p>
          </div>
        ))}
      </div>

      <div data-testid="load-activates" className="rounded-lg border border-gray-200 bg-white p-3">
        <h3 className="text-xs font-semibold text-gray-800">加载协议 ＝ 权限激活</h3>
        <p className="mt-1 text-xs text-gray-600">
          官方执行体加载协议，即激活全部调用权限（权限面以制度职责为界），不必逐次签发；
          但一旦碰上「用别人的资产」，仍须走资产授权（授权码）。
        </p>
      </div>

      <div data-testid="separation" className="grid gap-3 sm:grid-cols-2">
        <div data-testid="sep-institutional" className="rounded-lg border border-gray-200 bg-white p-3">
          <h3 className="text-xs font-semibold text-gray-800">制度执行 · 不逐次授权</h3>
          <p className="mt-1 text-xs text-gray-600">
            办制度的事（巡检、测评、审查、执行、计量）：加载协议即有权，权限以制度职责为界。
          </p>
        </div>
        <div data-testid="sep-asset" className="rounded-lg border border-gray-200 bg-white p-3">
          <h3 className="text-xs font-semibold text-gray-800">资产使用 · 仍须授权</h3>
          <p className="mt-1 text-xs text-gray-600">
            碰他人资产：仍须资产授权（授权码）。授权码属资产线，不等于授权本身。
          </p>
        </div>
      </div>
      <p className="text-xs text-gray-500">
        与「我的账户 · 四把钥匙」同一套口径共轴：四把钥匙管身份与办事，授权码管资产；两线分面、存证不混。
      </p>

      <div data-testid="identity-precursor" className="rounded-lg border border-gray-200 bg-white p-3">
        <h3 className="text-xs font-semibold text-gray-800">令牌身份前置 · 三条判据</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-xs text-gray-600">
          <li>先定身份、再发令牌：令牌签发须挂「身份确定」前置，身份未定不发令牌。</li>
          <li>令牌不得越其锚：令牌层级与锚档对应；现时之锚＝记名级（实名注册＋手机号锚定）⟹ 高权无限制面不发。</li>
          <li>固锚级待建：通知机现为模拟态，固锚级尚未落地——如实标「待建」，不对外声称。</li>
        </ul>
        <p className="mt-2 text-xs text-gray-500">
          人类环节不隐：执行令牌由人类签发，授权件由法律主体本人签署（不得代签）。
        </p>
      </div>
    </section>
  )
}
