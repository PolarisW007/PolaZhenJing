/**
 * =============================================================================
 * Module: components/AIAssistant.tsx
 * Description: Panel for AI-powered text operations – polish, summarise,
 *              suggest tags, and expand thought.
 *              AI助手面板 - 支持AI文本操作：润色、摘要、标签建议和扩展思绪。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, lucide-react, api/client
 * =============================================================================
 */

import { useState } from 'react'
import { Sparkles, Wand2, FileText, Tags, Expand } from 'lucide-react'
import client from '../api/client'

interface Props {
  content: string
  onApplyText: (text: string) => void
  onApplySummary: (summary: string) => void
}

export default function AIAssistant({ content, onApplyText, onApplySummary }: Props) {
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeAction, setActiveAction] = useState<string | null>(null)

  const callAI = async (endpoint: string, action: string) => {
    if (!content.trim()) {
      setError('请先写一些内容')
      return
    }
    setLoading(true)
    setError(null)
    setActiveAction(action)
    try {
      const res = await client.post(`/api/ai/${endpoint}`, { text: content })
      if (endpoint === 'suggest-tags') {
        setResult(res.data.tags.join(', '))
      } else {
        setResult(res.data.result)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'AI请求失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-purple-50 border border-purple-200 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={18} className="text-purple-600" />
        <h3 className="text-sm font-semibold text-purple-900">AI 助手</h3>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => callAI('polish', 'polish')}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-purple-300 rounded-lg text-sm text-purple-700 hover:bg-purple-100 disabled:opacity-50 transition"
        >
          <Wand2 size={14} /> 润色
        </button>
        <button
          onClick={() => callAI('summarize', 'summarize')}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-purple-300 rounded-lg text-sm text-purple-700 hover:bg-purple-100 disabled:opacity-50 transition"
        >
          <FileText size={14} /> 摘要
        </button>
        <button
          onClick={() => callAI('suggest-tags', 'tags')}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-purple-300 rounded-lg text-sm text-purple-700 hover:bg-purple-100 disabled:opacity-50 transition"
        >
          <Tags size={14} /> 建议标签
        </button>
        <button
          onClick={() => callAI('expand', 'expand')}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-purple-300 rounded-lg text-sm text-purple-700 hover:bg-purple-100 disabled:opacity-50 transition"
        >
          <Expand size={14} /> 扩展
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center gap-2 text-sm text-purple-600">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600" />
          处理中...
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="text-sm text-red-600 mb-3">{error}</div>
      )}

      {/* Result */}
      {result && !loading && (
        <div className="mt-3">
          <div className="bg-white border border-purple-200 rounded-lg p-3 text-sm text-gray-700 max-h-60 overflow-y-auto whitespace-pre-wrap">
            {result}
          </div>
          <div className="flex gap-2 mt-2">
            {(activeAction === 'polish' || activeAction === 'expand') && (
              <button
                onClick={() => {
                  onApplyText(result)
                  setResult('')
                }}
                className="px-3 py-1 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-700 transition"
              >
                应用为内容
              </button>
            )}
            {activeAction === 'summarize' && (
              <button
                onClick={() => {
                  onApplySummary(result)
                  setResult('')
                }}
                className="px-3 py-1 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-700 transition"
              >
                应用为摘要
              </button>
            )}
            <button
              onClick={() => {
                navigator.clipboard.writeText(result)
              }}
              className="px-3 py-1 border border-gray-300 text-gray-600 text-xs rounded-lg hover:bg-gray-100 transition"
            >
              复制
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
