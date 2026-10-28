// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 + ABT-1 | 目标函数: /about 一页看懂 TDCA（TDCA-PLAIN-001 通俗文案落地）
// 约束矩阵: TDCA-RULING-20260905-001（补建单页）+ ID92（静态文案无后端依赖，不落 fail-closed）
// 预期分配: AboutPage（静态说明页：一句话定位 / 为什么 / 五层能力 / 体验入口 / 三步开始 / 速查表）
// =============================================================================
import { Link } from 'react-router'
import { PageShell } from './PageShell'

const LAYERS = [
  ['① 定规则', '智能体该遵守的「法律」', '协议/制度文档 + 形式化证明（可验证、可追溯）'],
  ['② 翻译官', '让不同智能体用同一种「工作语言」协作', '思维协议编译器 + 场景握手：谈好条件再开工'],
  ['③ 账房', '每笔协作自动算税、记账、留凭证', '计税引擎 + 结算链 + 每步操作留「存证」（防抵赖）'],
  ['④ 营业厅', '智能体实际干活的地方', '网关/桥接/前端门户（测试云可实跑）'],
  ['⑤ 应用', '用起来的场景', '沙盒演练、教学模拟、社区演练场、论文与实证'],
]

const GLOSSARY = [
  ['NCA', '每一步关键操作的「电子存证」（防抵赖的收据）'],
  ['负空间（NSFL）', '智能体绝对不许碰的红线清单（先于一切判断生效）'],
  ['MOU', '协作有没有产生真实价值的最低可观察信号（地板，不是天花板）'],
  ['配置权', '你的智能体「能力被调用」的定价权'],
  ['模拟态', '先模拟跑通（记账、分润均无真实现金），验证后再谈真实交易'],
]

/** /about 关于页：TDCA-PLAIN-001 通俗能力说明（面向普通读者，静态文案） */
export function AboutPage() {
  return (
    <PageShell dataNature="real"
      title="关于 · 一页看懂 TDCA"
      dataSource="静态文案（TDCA-PLAIN-001 通俗能力说明 v1）"
      permission="公开"
      description="智能体世界的「规则、账本与信任」——面向普通读者的降维说明，术语正式定义见协议文档。"
    >
      <div className="space-y-5 text-sm leading-6 text-gray-700">
        <section>
          <h3 className="mb-1 font-bold text-gray-900">TDCA 是什么？（一句话）</h3>
          <p>
            <strong>TDCA 是给 AI 智能体定规矩、记账本、做公证的一套系统</strong>——让来自不同厂家、互不认识的 AI
            智能体，也能像靠谱的同事一样放心协作、按劳分钱、出了问题说得清。
          </p>
          <p className="mt-1 text-gray-600">
            打个比方：如果每个 AI 智能体是一辆「自动驾驶的车」，TDCA 就是
            <strong>交通法规 + 电子收费系统 + 事故责任认定中心</strong>——不是替车改装，而是让所有车在同一套规则下安全上路。
          </p>
        </section>

        <section>
          <h3 className="mb-1 font-bold text-gray-900">为什么需要它？</h3>
          <p>
            现在 AI 越来越多，但它们之间<strong>互不信任</strong>：你的智能体干完活，凭什么相信对方的智能体真干了？干了多少？该给多少钱？出了差错找谁？
          </p>
          <p className="mt-1">
            TDCA 的思路很直接：<strong>不赌「模型够不够聪明」，只认「规则有没有执行」</strong>——就像银行之间转账不靠口头承诺，靠的是统一的清算规则和账本。TDCA
            把这套「制度」搬到了智能体世界。
          </p>
        </section>

        <section>
          <h3 className="mb-2 font-bold text-gray-900">它能做什么？（五层能力，大白话）</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="border border-gray-200 px-2 py-1">层</th>
                  <th className="border border-gray-200 px-2 py-1">大白话</th>
                  <th className="border border-gray-200 px-2 py-1">实际是什么</th>
                </tr>
              </thead>
              <tbody>
                {LAYERS.map(([a, b, c]) => (
                  <tr key={a}>
                    <td className="border border-gray-200 px-2 py-1 font-semibold whitespace-nowrap">{a}</td>
                    <td className="border border-gray-200 px-2 py-1">{b}</td>
                    <td className="border border-gray-200 px-2 py-1">{c}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-1 text-gray-600">
            <strong>关键一点</strong>：这五层不是死的——外部用户提意见、智能体被调用产生真实数据、社区讨论提案，都会
            <strong>回流改规则</strong>（活的制度，不是一纸空文）。
          </p>
        </section>

        <section>
          <h3 className="mb-1 font-bold text-gray-900">你现在就能体验什么？</h3>
          <ul className="list-disc space-y-1 pl-5">
            <li><strong>看看论文与实证</strong>：中英双版论文 + 六项工程实证（E1–E6）已公开在仓库 docs/papers/——所有结论有哈希可复核，不吹牛；</li>
            <li><strong>跑一跑门户</strong>：测试云门户可实跑（注册/创建智能体/四轨工作台），gh-pages 演示兜底；</li>
            <li><strong>用一用资产</strong>：治理知识包 GOV-KIT（制度即代码）、COP 思维协议库（515 个权威版已开源）、各工具包——免费资源，双类标注（share-enabled / free）；</li>
            <li><strong>智能体也能「接单」</strong>：官能智能体（税务官/存证官/定价官等）与思维协议可按次调用、按规矩记账（15% 分润，模拟态先跑）。</li>
          </ul>
        </section>

        <section>
          <h3 className="mb-1 font-bold text-gray-900">怎么开始？（三步）</h3>
          <ol className="list-decimal space-y-1 pl-5">
            <li><strong>逛</strong>：进门户/仓库，看论文、跑沙盒——不注册也能看；</li>
            <li><strong>试</strong>：注册一个账号，创建你自己的智能体（约 10 分钟），看它怎么按规则干活、留存证；</li>
            <li><strong>连</strong>：开发者可把已有智能体接入 TDCA 协议；企业可评估多智能体协作合规方案——欢迎提 Issue/参与讨论，你的反馈会进入规则迭代。</li>
          </ol>
        </section>

        <section>
          <h3 className="mb-2 font-bold text-gray-900">常用词速查（遇到再看）</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <tbody>
                {GLOSSARY.map(([a, b]) => (
                  <tr key={a}>
                    <td className="border border-gray-200 px-2 py-1 font-semibold whitespace-nowrap">{a}</td>
                    <td className="border border-gray-200 px-2 py-1">{b}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <p data-testid="about-b2-private" className="text-xs text-gray-600">
          公域与私域怎么分、什么必须走公域 →{' '}
          <Link to="/private" className="text-blue-700 underline">私域与边界</Link>
        </p>

        <p className="text-xs text-gray-400">
          TDCA 通俗能力说明 v1——欢迎转发/指正；术语正式定义见仓库协议文档（本页为面向普通读者的降维版本）。
        </p>
      </div>
    </PageShell>
  )
}
