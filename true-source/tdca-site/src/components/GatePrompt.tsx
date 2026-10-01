import { useState } from 'react'
import { getGate, setGate } from '../lib/siteApi'

// 口令门输入：仅存 sessionStorage，口令值不落任何文件/产物
export default function GatePrompt({ onOk }: { onOk: () => void }) {
  const [v, setV] = useState(getGate())
  return (
    <div className="mx-auto max-w-sm py-24 text-center">
      <h2 className="text-xl font-bold mb-2">站点口令</h2>
      <p className="text-sm text-muted-foreground mb-4">
        请输入站点口令（向管理员索取，仅本次会话有效，不会保存到任何文件）
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          setGate(v)
          onOk()
        }}
        className="flex gap-2"
      >
        <input
          type="password"
          value={v}
          onChange={(e) => setV(e.target.value)}
          className="flex-1 rounded border px-3 py-2 text-sm"
          placeholder="站点口令"
        />
        <button className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground">进入</button>
      </form>
    </div>
  )
}
