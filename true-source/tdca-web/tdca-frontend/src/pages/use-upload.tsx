// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 「用」组 U-1 素材上传页（L1SI181-USE-U1-001）
// 约束矩阵: 开工令 §四——一个朴素上传页：选文件→上传→显示哈希/大小/归属/时间；
//   拒收显示人话理由；成功给下一步一句话；⛔ 拖拽/进度动画/多语言/批量
// 复用: PageShell / api（会话令牌自动注入）；后端 POST /api/v1/use/upload（直传报文）
// =============================================================================
import { useState } from 'react'
import { api, sessionToken } from '@/api/client'
import { PageShell } from './PageShell'

interface UploadResult {
  upload_id: string
  sha256: string
  sha256_16: string
  size_bytes: number
  original_filename: string
  accept_category: string
  owner: string
  uploaded_at: string
  duplicate: boolean
  note: string
}

export function UseUploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [rejectReason, setRejectReason] = useState('')

  const onUpload = async () => {
    if (!file || busy) return
    setBusy(true)
    setResult(null)
    setRejectReason('')
    try {
      const res = await fetch('/api/v1/use/upload', {
        method: 'POST',
        headers: {
          Authorization: sessionToken() ?? '',
          'X-Upload-Filename': encodeURIComponent(file.name),
        },
        body: file, // 直传报文（后端按字节取哈希；⛔ 不走 multipart）
      })
      const raw = (await res.json()) as { data?: UploadResult; detail?: string }
      if (!res.ok) {
        // 拒收：后端回一句人话理由（⛔ 只给错误码）
        setRejectReason(raw.detail ?? '没传成——请换个文件再试，或联系站方。')
        return
      }
      setResult(raw.data ?? null)
    } catch {
      setRejectReason('网络没通——请稍后重试，或联系站方。')
    } finally {
      setBusy(false)
    }
  }

  return (
    <PageShell dataNature="real"
      title="交素材（上传一件）"
      dataSource="POST /api/v1/use/upload（登录后单件直传；哈希防重）"
      permission="登录 DID（未登录请先登录）"
      description="把素材原件交给站方：选一件文件传上来，当场看到哈希与归属。同一件重复传不会重复收。">
      <div data-testid="use-upload" className="max-w-xl space-y-4">
        <ol className="list-decimal space-y-1 pl-5 text-sm text-gray-600">
          <li>点下面「选择文件」，挑一件素材（文档、数据、图像、音频、压缩包等常见类型）。</li>
          <li>点「上传」，等一行结果出来。</li>
          <li>记下哈希——它就是这件的「收件凭据」。</li>
        </ol>

        <div className="flex items-center gap-3">
          <input
            type="file"
            data-testid="use-upload-file"
            className="block text-sm text-gray-600"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button
            type="button"
            data-testid="use-upload-submit"
            disabled={!file || busy}
            className="rounded-md border border-blue-600 bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:border-gray-300 disabled:bg-gray-300"
            onClick={() => void onUpload()}>
            {busy ? '上传中…' : '上传'}
          </button>
        </div>

        {rejectReason && (
          <p data-testid="use-upload-reject" className="rounded bg-amber-50 p-3 text-sm text-amber-800" role="alert">
            没传成：{rejectReason}
          </p>
        )}

        {result && (
          <div data-testid="use-upload-result" className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm">
            <p className="font-medium text-green-800">{result.note}</p>
            <dl className="mt-2 space-y-1 text-gray-700">
              <div><dt className="inline font-semibold">收件编号：</dt><dd className="inline">{result.upload_id}</dd></div>
              <div><dt className="inline font-semibold">哈希：</dt><dd className="inline break-all">{result.sha256}</dd></div>
              <div><dt className="inline font-semibold">大小：</dt><dd className="inline">{result.size_bytes} 字节</dd></div>
              <div><dt className="inline font-semibold">归属：</dt><dd className="inline">{result.owner}</dd></div>
              <div><dt className="inline font-semibold">时间：</dt><dd className="inline">{result.uploaded_at}</dd></div>
            </dl>
            {/* L1SI182-USE-U2-001：上传成功下一句——接着办登记（机器人只跑腿，五步入 /use/agent） */}
            <p className="mt-3">
              <a data-testid="use-upload-next" href={`/use/agent?u=${encodeURIComponent(result.upload_id)}`}
                className="inline-block rounded-md border border-blue-600 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-50">
                下一步：代办登记（机器人协助）→
              </a>
            </p>
          </div>
        )}
        {/* api 引用保持会话接缝一致（fetch 直传另行注入令牌；此引用防 tree-shake 误裁） */}
        <p className="hidden">{typeof api}</p>
      </div>
    </PageShell>
  )
}
