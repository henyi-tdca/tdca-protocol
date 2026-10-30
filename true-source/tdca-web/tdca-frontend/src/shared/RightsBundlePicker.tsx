// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 权利束＋保留束过渡选择器（BUNDLE-001）
// 口径: 十三项法定名逐字（⛔ 自造译名/简称）；note 以 #RB 前缀＋单行 JSON 承载；
//       stage=transition 标过渡（日后立字段从前缀回填）；⛔ 建字段/迁移/改表
// =============================================================================
import { useEffect, useState } from 'react'

export const RB_THIRTEEN = [
  '复制权', '发行权', '出租权', '展览权', '表演权', '放映权', '广播权',
  '信息网络传播权', '摄制权', '改编权', '翻译权', '汇编权', '其他权利',
] as const
const RB_BASIS = '著作权法第10条(五)~(十七)'
export const RB_STAGE = 'transition'
export const RB_NOTICE =
  '权利束暂以备注记录，后续将转为正式字段；现有记录届时自动迁移。'

export function buildRbNote(granted: string[], retained: string[],
                            freeText: string): string {
  const core = `#RB${JSON.stringify(
    { granted, retained, basis: RB_BASIS, stage: RB_STAGE })}`
  const tail = freeText.trim()
  return tail ? `${core} ${tail}` : core
}

interface PickerProps {
  onChange: (note: string, active: boolean) => void
  resetKey: number
}

/** 十三项多选（转出／保留双列）；保留默认自动补全＝十三项 − 转出（可手改）。 */
export function RightsBundlePicker({ onChange, resetKey }: PickerProps) {
  const [granted, setGranted] = useState<string[]>([])
  const [retained, setRetained] = useState<string[]>([])
  const [autoRetained, setAutoRetained] = useState(true)
  const [freeText, setFreeText] = useState('')

  useEffect(() => {
    setGranted([]); setRetained([]); setAutoRetained(true); setFreeText('')
  }, [resetKey])

  const active = granted.length > 0 || retained.length > 0
  const needOtherNote =
    active && (granted.includes('其他权利') || retained.includes('其他权利'))
      && !freeText.trim()

  useEffect(() => {
    onChange(buildRbNote(granted, retained, freeText), active)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [granted, retained, freeText, active])

  const toggleGranted = (name: string) => {
    const next = granted.includes(name)
      ? granted.filter((x) => x !== name)
      : [...granted, name]
    setGranted(next)
    if (autoRetained) {
      setRetained(RB_THIRTEEN.filter((x) => !next.includes(x)))
    }
  }
  const toggleRetained = (name: string) => {
    setAutoRetained(false)
    setRetained(retained.includes(name)
      ? retained.filter((x) => x !== name)
      : [...retained, name])
  }

  return (
    <fieldset data-testid="rb-picker" className="text-sm">
      <legend>权利束＋保留束（过渡方案）</legend>
      <p className="text-xs text-amber-700">{RB_NOTICE}</p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <div>
          <p className="font-medium">转出束（granted）</p>
          {RB_THIRTEEN.map((name) => (
            <label key={`g-${name}`} className="block">
              <input type="checkbox" checked={granted.includes(name)}
                onChange={() => toggleGranted(name)} /> {name}
            </label>
          ))}
        </div>
        <div>
          <p className="font-medium">保留束（retained，默认＝十三项 − 转出，可手改）</p>
          {RB_THIRTEEN.map((name) => (
            <label key={`r-${name}`} className="block">
              <input type="checkbox" checked={retained.includes(name)}
                onChange={() => toggleRetained(name)} /> {name}
            </label>
          ))}
        </div>
      </div>
      <input placeholder="人话备注·选填（选「其他权利」时此处须附一句说明）"
        value={freeText} onChange={(e) => setFreeText(e.target.value)} />
      {needOtherNote && (
        <p role="alert" className="text-xs text-red-600">
          选「其他权利」须附一句说明（写在备注里），否则提交会被拒收。
        </p>
      )}
    </fieldset>
  )
}
