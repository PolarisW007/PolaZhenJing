/**
 * =============================================================================
 * Module: components/ShareDialog.tsx
 * Description: Modal dialog for sharing a thought to social platforms.
 *              Fetches share URLs from the API and offers copy-to-clipboard.
 *              分享对话框 - 将思绪分享到社交平台，获取分享URL并支持复制到剪贴板。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, lucide-react, api/client
 * =============================================================================
 */

import { useEffect, useState } from 'react'
import { Copy, ExternalLink, X } from 'lucide-react'
import client from '../api/client'

interface Props {
  thoughtId: string
  onClose: () => void
}

interface ShareData {
  url: string
  platforms: {
    x: string
    weibo: string
    xiaohongshu: string
  }
  share_text: string
}

export default function ShareDialog({ thoughtId, onClose }: Props) {
  const [data, setData] = useState<ShareData | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    client
      .get(`/api/share/${thoughtId}`)
      .then((res) => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [thoughtId])

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-1 rounded-lg hover:bg-gray-100"
        >
          <X size={18} className="text-gray-400" />
        </button>

        <h3 className="text-lg font-semibold text-gray-900 mb-4">分享思绪</h3>

        {loading && (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600" />
          </div>
        )}

        {data && (
          <div className="space-y-4">
            {/* URL */}
            <div>
              <label className="text-xs text-gray-500 mb-1 block">公开链接</label>
              <div className="flex items-center gap-2">
                <input
                  readOnly
                  value={data.url}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50"
                />
                <button
                  onClick={() => copyToClipboard(data.url)}
                  className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100"
                >
                  <Copy size={14} />
                </button>
              </div>
            </div>

            {/* Platform buttons */}
            <div className="space-y-2">
              <label className="text-xs text-gray-500">分享到平台</label>
              <div className="flex gap-2">
                <a
                  href={data.platforms.x}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-black text-white rounded-lg text-sm hover:bg-gray-800 transition"
                >
                  <ExternalLink size={14} /> X / Twitter
                </a>
                <a
                  href={data.platforms.weibo}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition"
                >
                  <ExternalLink size={14} /> 微博
                </a>
              </div>
            </div>

            {/* Xiaohongshu (copy text) */}
            <div>
              <label className="text-xs text-gray-500 mb-1 block">小红书（复制粘贴）</label>
              <div className="relative">
                <textarea
                  readOnly
                  value={data.platforms.xiaohongshu}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50 resize-none"
                />
                <button
                  onClick={() => copyToClipboard(data.platforms.xiaohongshu)}
                  className="absolute top-2 right-2 p-1 border border-gray-300 rounded bg-white hover:bg-gray-100"
                >
                  <Copy size={12} />
                </button>
              </div>
            </div>

            {/* Copy share text */}
            <button
              onClick={() => copyToClipboard(data.share_text)}
              className="w-full flex items-center justify-center gap-2 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 transition"
            >
              <Copy size={14} />
              {copied ? '已复制！' : '复制全部分享文本'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
