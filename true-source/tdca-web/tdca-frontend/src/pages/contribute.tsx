// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B2 S2-5 · 「我要贡献」提权入口（批2前三包）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B2-001 S2-5——三台阶（viewer→贡献者→节点方）；
//   每台阶写什么件／走哪条路（指向既有登记端点）／什么算成；
//   ⛔ 承诺时限 ⛔ 承诺必过；必写「机器人不代签、不代判，产出皆草稿／建议」
// 实测: ownership/register、authorization/register、agent-channel/register 三端点
//   GET 405（路由在）、POST 401／422（须登录体）——可直接指路，提交须登录
// 红线: 页面零内部编号零价格字样
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from './PageShell'

interface Tier {
  name: string
  tagline: string
  items: string
  road: { label: string; href: string }[]
  done: string
  pending?: string
}

const TIERS: Tier[] = [
  {
    name: '第一阶 · viewer（注册即有）',
    tagline: '站上注册的每一位读者，起步就在这一阶。',
    items: '一件都不用额外准备：注册账号本身即第一阶的凭据。',
    road: [
      { label: '站内注册页（注册即 viewer 只读账号）', href: '/register' },
    ],
    done: '注册成功即站稳第一阶：可以浏览公域全部公开面，也可以读私域对你开放的只读面。',
  },
  {
    name: '第二阶 · 贡献者（交素材，得登记号）',
    tagline: '把素材交给站方登记，拿到属于你的登记号。',
    items: '素材原件 ＋ 一段登记自述。自述可以用「三问向导」生成（新手指引页内），照实回答、真实性由你本人负责。',
    road: [
      { label: '权属登记页（登记「这是谁的」）', href: '/ownership-registry' },
      { label: '合约备案页（登记「允许谁用、什么条件」）', href: '/authorization-registry' },
      { label: '三问向导（先生成登记自述草稿）', href: '/start/three-questions' },
    ],
    done: '登记被受理、取得登记号，即算站上第二阶。登记端点已在站内路由（提交须登录态）；不承诺时限，也不承诺必过——受理与否以登记簿为准。',
    pending: '素材上传通道：建设中。真因：上传接口待建（批 2 后段，待后端就绪）——当前请先备好素材原件与自述草稿。',
  },
  {
    name: '第三阶 · 节点方（起你的私域节点）',
    tagline: '不只交素材，还把自己的场景私域跑起来。',
    items: '本地部署包 ＋ 两权登记（权属、授权各一件）＋ 通道登记。先读「私域与边界」页弄清公域与私域的分工，再起节点。',
    road: [
      { label: '私域与边界（先读这页再决定）', href: '/private' },
      { label: '智能体通道登记入口（通道登记端点已在站内路由）', href: '/channel/registry' },
      { label: '权属登记页', href: '/ownership-registry' },
      { label: '合约备案页', href: '/authorization-registry' },
    ],
    done: '节点在你一侧跑起来、两权落进登记簿，即算第三阶。同前：不承诺时限，不承诺必过。',
    pending: '本地部署包：建设中。真因：「私域可带走」属批 4 段，待后端就绪——可先完成两权登记与通道登记。',
  },
]

export function ContributePage() {
  return (
    <PageShell dataNature="real"
      title="我要贡献 · 三级台阶"
      dataSource="纯前端指路页（零接口调用）；所指向的登记端点已在站内路由"
      permission="公开"
      description="从读者到贡献者到节点方，每一阶写什么件、走哪条路、什么算成，都写在这一页。只指路，不代办。"
    >
      <div data-testid="contribute-page" className="space-y-6">
        <p data-testid="contribute-duty" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs leading-relaxed text-amber-800">
          机器人不代签、不代判，产出皆草稿／建议。本页不承诺任何时限，也不承诺必过——每一步的受理与否，都以登记簿与签批为准。
        </p>

        <ol className="space-y-4">
          {TIERS.map((t) => (
            <li key={t.name} data-testid="contribute-tier" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-1 text-sm font-semibold text-gray-900">{t.name}</h3>
              <p className="mb-3 text-xs text-gray-500">{t.tagline}</p>
              <div className="space-y-2 text-xs leading-relaxed text-gray-600">
                <p>
                  <span className="font-semibold text-gray-700">要什么件：</span>
                  {t.items}
                </p>
                <div>
                  <span className="font-semibold text-gray-700">走哪条路：</span>
                  <ul className="mt-1 list-inside list-disc space-y-0.5">
                    {t.road.map((r) => (
                      <li key={r.href}>
                        <Link data-testid="contribute-road" to={r.href} className="text-blue-700 underline underline-offset-2">
                          {r.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
                <p>
                  <span className="font-semibold text-gray-700">什么算成：</span>
                  {t.done}
                </p>
                {t.pending && (
                  <p data-testid="contribute-pending" className="rounded bg-gray-50 p-2 text-amber-700">
                    {t.pending}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>

        <section data-testid="contribute-note" className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4">
          <h3 className="mb-1 text-sm font-semibold text-gray-900">一句话口径</h3>
          <p className="text-xs leading-relaxed text-gray-600">
            台阶只描述路径，不代替你走。呈请、登记、签批每一步都须本人（或本人的法律主体）完成；站上任何智能体产出皆草稿／建议，不构成判定，也不构成承诺。
          </p>
        </section>
      </div>
    </PageShell>
  )
}
