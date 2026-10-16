// =============================================================================
// TDCA 制度水印
// 来源: tdca-site/src/components/AccountCredentialPanel.tsx（批 3 移植·凭证批呈现件）
// 目标函数: 账户凭证四分面＋授权行权两段要素呈现
// 口径：通俗、零编号、不显示任何令牌值；未落实者如实标「待建」
// =============================================================================
import { authCode, hufToken, identityToken, sessionToken } from '@/api/client'
import { useAuth } from '@/app/auth-context'

interface Quadrant {
  key: string
  face: string
  token: string
  plain: string
  stateful: string
  has: boolean
  note?: string
}

export function AccountCredentialPanel() {
  const { did } = useAuth()
  const quadrants: Quadrant[] = [
    {
      key: 'access', face: '账户读写', token: '访问令牌', plain: '进站＋读写我自己的账户',
      stateful: '有状态（随会话，关窗即焚）', has: sessionToken() !== null,
    },
    {
      key: 'identity', face: '账户管理', token: '身份令牌', plain: '管我的账户',
      stateful: '有状态', has: identityToken() !== null,
      note: '须强核身 · 现状待建（谁能取得属明示项，本站不代定）',
    },
    {
      key: 'execution', face: '事务执行', token: '写操作钥匙（待建执行令牌之临时替代）', plain: '去办事（写操作与签批）',
      stateful: '静态兜底（随浏览器存留）', has: hufToken() !== null,
      note: '由人类签发 · AI 无权代行',
    },
    {
      key: 'authcode', face: '资产使用', token: '授权码', plain: '用资产',
      stateful: '有状态（随会话）', has: authCode() !== null,
      note: '属资产线，不等于授权本身 · 现状待建',
    },
  ]
  return (
    <section data-testid="cred-quadrants" className="mt-8 space-y-4 rounded-xl border border-gray-200 bg-gray-50 p-4">
      <header>
        <h2 className="text-sm font-semibold text-gray-800">我的账户 · 四把钥匙</h2>
        <p className="text-xs text-gray-500">
          一看即知是哪把、能干什么。层级如实：账户读写 ⊂ 账户管理（拿到身份者内含读写之能，反之不成立）；
          事务执行与资产使用互不蕴含、可并存。两线分面：身份与钥匙线 ≠ 资产线，存证亦不混同。
          通知机钥匙是身份之根锚，不在四把之列。
        </p>
      </header>
      <div className="grid gap-3 sm:grid-cols-2">
        {quadrants.map((q) => (
          <div key={q.key} data-testid={`quad-${q.key}`} className="rounded-lg border border-gray-200 bg-white p-3">
            <h3 className="text-xs font-semibold text-gray-800">{q.face} · {q.token}</h3>
            <p className="mt-1 text-xs text-gray-600">{q.plain}</p>
            <p className="mt-1 text-xs text-gray-500">状态：{q.stateful} · 当前{q.has ? '在位' : '未持有'}</p>
            <p className="mt-1 text-xs text-gray-500" data-testid={`quad-${q.key}-note`}>
              {q.note ? q.note : '用途如上一句；令牌值一律不显示。'}
            </p>
          </div>
        ))}
      </div>
      <div data-testid="authz-action-elements" className="rounded-lg border border-gray-200 bg-white p-3">
        <h3 className="text-xs font-semibold text-gray-800">授权与行权 · 两段要素怎么看</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-xs text-gray-600">
          <li>授权件必现两段：谁＝授权的法律主体（本人，人类签署、不得代签）；干什么＝授权件载明的事项。</li>
          <li>行权记录必现两段：谁＝行权者（执行令牌由人类签发）；干什么＝记录载明的事务。</li>
          <li>当前身份（谁）：{did ?? '未登录'}。当前可办事务（干什么）：写操作与签批，走「事务执行」面，触发时须人类最终签批。</li>
        </ul>
      </div>
    </section>
  )
}
