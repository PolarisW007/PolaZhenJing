/**
 * =============================================================================
 * Module: pages/ThoughtEditor.tsx
 * Description: Markdown editor page for creating and editing thoughts.
 *              Includes title, content, category, tags, and status fields,
 *              plus AI assistant and share buttons.
 *              Markdown编辑器页面 - 用于创建和编辑思绪，包含标题、内容、分类、
 *              标签和状态字段，以及AI助手和分享按钮。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, react-router-dom, api/client
 * =============================================================================
 */

import { type FormEvent, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Save, Send, Sparkles } from 'lucide-react'
import client from '../api/client'
import TagSelector from '../components/TagSelector'
import AIAssistant from '../components/AIAssistant'
import ShareDialog from '../components/ShareDialog'

export default function ThoughtEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew = !id

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [summary, setSummary] = useState('')
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('draft')
  const [tagIds, setTagIds] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [showAI, setShowAI] = useState(false)
  const [showShare, setShowShare] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load existing thought
  useEffect(() => {
    if (!id) return
    client
      .get(`/api/thoughts/${id}`)
      .then((res) => {
        setTitle(res.data.title)
        setContent(res.data.content)
        setSummary(res.data.summary || '')
        setCategory(res.data.category || '')
        setStatus(res.data.status)
        setTagIds(res.data.tags.map((t: any) => t.id))
      })
      .catch(() => setError('加载思绪失败'))
  }, [id])

  const handleSave = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload = {
        title,
        content,
        summary: summary || null,
        category: category || null,
        status,
        tag_ids: tagIds,
      }
      if (isNew) {
        const res = await client.post('/api/thoughts', payload)
        navigate(`/thought/${res.data.id}`, { replace: true })
      } else {
        await client.patch(`/api/thoughts/${id}`, payload)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handlePublish = async () => {
    if (!id) return
    try {
      await client.post(`/api/publish/${id}`)
      setShowShare(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || '发布失败')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-900 transition text-sm"
          >
            <ArrowLeft size={16} />
            返回
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAI(!showAI)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-purple-300 text-purple-600 text-sm hover:bg-purple-50 transition"
            >
              <Sparkles size={14} />
              AI 助手
            </button>
            {!isNew && status === 'published' && (
              <button
                onClick={handlePublish}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm hover:bg-green-700 transition"
              >
                <Send size={14} />
                发布到站点
              </button>
            )}
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1 px-4 py-1.5 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              <Save size={14} />
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {error && (
          <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-5">
          {/* Title */}
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="思绪标题..."
            className="w-full text-2xl font-bold border-0 border-b-2 border-gray-200 bg-transparent pb-2 focus:border-indigo-500 outline-none"
          />

          {/* Content (markdown) */}
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="用 Markdown 写下你的思绪..."
            rows={16}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm resize-y focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          />

          {/* Metadata row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">摘要</label>
              <input
                type="text"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="简短摘要..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="如：技术、生活、灵感"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="draft">草稿</option>
                <option value="published">已发布</option>
                <option value="archived">已归档</option>
              </select>
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">标签</label>
            <TagSelector selected={tagIds} onChange={setTagIds} />
          </div>
        </form>

        {/* AI Assistant panel */}
        {showAI && (
          <div className="mt-6">
            <AIAssistant
              content={content}
              onApplyText={(text) => setContent(text)}
              onApplySummary={(s) => setSummary(s)}
            />
          </div>
        )}

        {/* Share dialog */}
        {showShare && id && (
          <ShareDialog thoughtId={id} onClose={() => setShowShare(false)} />
        )}
      </main>
    </div>
  )
}
