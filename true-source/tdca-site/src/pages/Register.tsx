// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-M4REG-001 | 目标函数: /register 注册页（M4 应用侧补注册，GSEQ-0663）
// 约束矩阵: TDCA-HANDOFF-KIMI-M4-REGISTER-001 §二.2 + ID92 + fail-closed
// 预期分配: RegisterPage（用户名/密码/确认密码 + 强度提示 → 注册成功自动登录入 /me）
// 制度锚点: 人类账号注册=人机面（agent_card 机机面不受影响，身份凭证不互换）
// =============================================================================
import { useState } from 'react'
import { Link } from 'react-router'
import { PageShell } from '@/components/PageShell'
import { AnchorSelectSection } from '@/components/IdentityMark'
import { useAuth } from '@/lib/auth-context'
import { api, setSessionToken } from '@/lib/client'
import { CONTRACT_EN_TEXT, CONTRACT_ID, CONTRACT_VERSION, CONTRACT_ZH_TEXT } from '@/lib/register-contract'

const USERNAME_RE = /^[A-Za-z0-9_-]{3,32}$/

/** 密码强度（与后端 fail-closed 口径一致：≥8 位且含字母+数字；更长+符号为强） */
function passwordStrength(pw: string): { level: '弱' | '中' | '强'; ok: boolean; hint: string } {
  const hasAlpha = /[A-Za-z]/.test(pw)
  const hasDigit = /\d/.test(pw)
  const ok = pw.length >= 8 && hasAlpha && hasDigit
  if (!pw) return { level: '弱', ok: false, hint: '至少 8 位，须同时包含字母与数字' }
  if (!ok) return { level: '弱', ok: false, hint: '未达标：至少 8 位且含字母+数字' }
  const strong = pw.length >= 12 && /[^A-Za-z0-9]/.test(pw)
  return strong
    ? { level: '强', ok, hint: '强度：强（长度 ≥12 且含符号）' }
    : { level: '中', ok, hint: '强度：中（可用；更长并含符号更佳）' }
}

/** M4 注册页：注册成功即签发 TDCA-SES 会话并进入个人后台 */
export function RegisterPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [agreed, setAgreed] = useState(false)
  const [anchorKind, setAnchorKind] = useState('realname-phone')   // 'none'=暂不选择（可后补）
  const [showEn, setShowEn] = useState(false)   // 英文读本内嵌展开（2026-10-16：删 GitHub 外链，与中文同待遇）
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const strength = passwordStrength(password)
  const usernameOk = USERNAME_RE.test(username.trim())

  async function submit() {
    setMsg(null)
    if (!agreed) {
      setMsg(`注册即缔约：请先阅读并勾选同意《TDCA 缔约注册协议》（${CONTRACT_VERSION}）`)
      return
    }
    const name = username.trim()
    if (!USERNAME_RE.test(name)) {
      setMsg('用户名须为 3~32 位字母/数字/下划线/连字符')
      return
    }
    if (!strength.ok) {
      setMsg('密码未达标：至少 8 位且同时包含字母与数字')
      return
    }
    if (password !== confirm) {
      setMsg('两次输入的密码不一致')
      return
    }
    setBusy(true)
    try {
      const res = await api.post<{ token: string; role: string; nca_id: string }>(
        '/api/v1/auth/register',
        {
          username: name, password, agree_contract: true, contract_version: CONTRACT_VERSION,
          // 批 2：所选锚随注册落存证；「暂不选择」不传 anchor_kind（后端默认记名级·待补）
          ...(anchorKind !== 'none' ? { anchor_kind: anchorKind } : {}),
        },
      )
      if (res.ok) {
        setSessionToken(res.data.token)
        login('TDID-H-0001', res.data.token) // 人机面：注册即人类账号身份
        // 整页重载：保证登录后各页取数新鲜（同 auth.tsx 口径）
        window.location.assign('/#/me')
      } else if (res.status === 409) {
        setMsg('该用户名已被注册，请换一个')
      } else if (res.status === 429) {
        setMsg('注册过于频繁，请稍后再试（每 IP 每小时限 5 次）')
      } else {
        setMsg(`注册未成功（${res.status ?? res.reason}）——请核对用户名与密码规则后重试`)
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <PageShell
      title="注册（人类账号）"
      dataSource="M4 POST /api/v1/auth/register（users 表 + NCA 落链 + 2h 会话）"
      permission="公开"
      description="注册即获得 viewer 只读账号（人机面身份；智能体接入走 agent_card 机机面，凭证不互换）。注册存证自动落 NCA 链。"
    >
      <div data-testid="register-form" className="max-w-md space-y-3 rounded border border-gray-200 bg-white p-4">
        <div className="text-xs font-semibold text-gray-700">创建你的 TDCA 账号（默认 viewer 角色）</div>
        {/* 注册即缔约（GSEQ-0669）：人读版协议展示 → 同意勾选（必选）→ 表单 */}
        <div data-testid="register-contract" className="rounded border border-slate-200 bg-slate-50">
          <div className="flex items-center justify-between border-b border-slate-200 px-3 py-1.5">
            <span className="text-xs font-semibold text-slate-700">《TDCA 缔约注册协议》{CONTRACT_VERSION}</span>
            <button
              type="button"
              data-testid="register-contract-en-toggle"
              onClick={() => setShowEn((v) => !v)}
              aria-expanded={showEn}
            >
              English 版 {showEn ? '▴' : '▾'}
            </button>
          </div>
          <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap px-3 py-2 font-sans text-[11px] leading-relaxed text-slate-600">
            {CONTRACT_ZH_TEXT}
          </pre>
          {showEn && (
            <pre
              data-testid="register-contract-en"
              className="max-h-48 overflow-y-auto whitespace-pre-wrap border-t border-slate-200 px-3 py-2 font-sans text-[11px] leading-relaxed text-slate-600"
            >
              {CONTRACT_EN_TEXT}
            </pre>
          )}
        </div>
        <label data-testid="register-agree-wrap" className="flex items-start gap-2 rounded border border-emerald-200 bg-emerald-50 px-3 py-2">
          <input
            data-testid="register-agree"
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="mt-0.5"
          />
          <span className="text-xs text-emerald-900">
            我已阅读并同意《TDCA 缔约注册协议》（{CONTRACT_ID} {CONTRACT_VERSION}）——注册即缔约，缔约存证将落 NCA 链
          </span>
        </label>
        <div>
          <input
            data-testid="register-username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="用户名（3~32 位字母/数字/-/_）"
            className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
          />
          {username && !usernameOk && (
            <div className="mt-1 text-xs text-red-700">用户名格式不符：3~32 位，仅限字母/数字/下划线/连字符</div>
          )}
        </div>
        <div>
          <input
            data-testid="register-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="密码"
            className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
          />
          {password && (
            <div
              data-testid="register-strength"
              className={`mt-1 text-xs ${strength.ok ? (strength.level === '强' ? 'text-emerald-700' : 'text-amber-700') : 'text-red-700'}`}
            >
              {strength.hint}
            </div>
          )}
        </div>
        <input
          data-testid="register-confirm"
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="确认密码"
          className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
        {confirm && password !== confirm && (
          <div className="text-xs text-red-700">两次输入的密码不一致</div>
        )}
        <AnchorSelectSection value={anchorKind} onChange={setAnchorKind} />
        {msg && <div data-testid="register-msg" className="text-xs text-red-700">{msg}</div>}
        {!agreed && (
          <div data-testid="register-agree-hint" className="text-xs text-amber-700">
            注册即缔约：请先勾选上方「我已阅读并同意」后再提交
          </div>
        )}
        <button
          data-testid="register-submit"
          disabled={busy || !agreed}
          className="w-full rounded bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
          onClick={submit}
        >
          {busy ? '注册中…' : '注册并登录（→ 我的智能体）'}
        </button>
        <div className="pt-1 text-xs text-gray-500">
          已有账号？<Link to="/auth" className="font-medium text-emerald-700 underline">去登录 →</Link>
        </div>
      </div>
    </PageShell>
  )
}
