/**
 * =============================================================================
 * Page: DeepResearch
 * Description: Deep Research report generation page with SSE progress streaming.
 *              Users input a research question, AI generates a structured HTML report.
 *              深度研究报告生成页面 - 用户输入研究问题，AI生成结构化HTML报告。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, react-router-dom, lucide-react, hooks/useResearch
 * =============================================================================
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  BookOpen,
  Check,
  Download,
  ExternalLink,
  FileSearch,
  Loader2,
  Search,
  Send,
  Sparkles,
  Wand2,
} from 'lucide-react'
import client from '../api/client'
import { type SSEEvent, useResearchSSE } from '../hooks/useResearch'

// Step configuration for progress display
const STEP_CONFIG: Record<string, { icon: typeof Sparkles; label: string }> = {
  outline: { icon: BookOpen, label: '分析问题 & 生成大纲' },
  search: { icon: Search, label: '搜索相关资料' },
  section: { icon: FileSearch, label: '生成报告章节' },
  compile: { icon: Wand2, label: '编译完整报告' },
  render: { icon: Sparkles, label: '渲染HTML报告' },
  complete: { icon: Check, label: '完成' },
}

type Phase = 'input' | 'generating' | 'done' | 'error'

export default function DeepResearch() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [phase, setPhase] = useState<Phase>(id ? 'done' : 'input')
  const [query, setQuery] = useState('')
  const [title, setTitle] = useState('')
  const [researchId, setResearchId] = useState<string | null>(id || null)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [messages, setMessages] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [htmlContent, setHtmlContent] = useState<string | null>(null)
  const [reportTitle, setReportTitle] = useState('')
  const [generating, setGenerating] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)
  // Guard: skip the load-existing effect when we just initiated generation locally
  const localGenerationRef = useRef(false)
  // Ref to always have the latest researchId for callbacks
  const researchIdRef = useRef(researchId)

  // Keep ref in sync
  useEffect(() => {
    researchIdRef.current = researchId
  }, [researchId])

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load existing research if ID provided (skip if we just triggered generation)
  useEffect(() => {
    if (!id) return
    if (localGenerationRef.current) {
      localGenerationRef.current = false
      return
    }
    client
      .get(`/api/research/${id}`)
      .then((res) => {
        setReportTitle(res.data.title)
        setQuery(res.data.query)
        if (res.data.html_content) {
          setHtmlContent(res.data.html_content)
          setPhase('done')
        } else if (res.data.status === 'generating') {
          setPhase('generating')
          setGenerating(true)
          setResearchId(res.data.id)
        } else if (res.data.status === 'pending') {
          setPhase('input')
        } else if (res.data.status === 'failed') {
          setPhase('error')
          setError('上次生成失败，请重试')
        }
      })
      .catch(() => setError('加载研究报告失败'))
  }, [id])

  // SSE event handler
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    setProgress(event.progress)
    setCurrentStep(event.step)
    setMessages((prev) => [...prev, event.message])

    if (event.status === 'error') {
      setPhase('error')
      setError(event.message)
      setGenerating(false)
    }

    if (event.data?.title) {
      setReportTitle(event.data.title as string)
    }
  }, [])

  const handleSSEDone = useCallback(() => {
    setGenerating(false)
    // Fetch the completed research to get HTML (use ref for latest id)
    const rid = researchIdRef.current
    if (rid) {
      client.get(`/api/research/${rid}`).then((res) => {
        if (res.data.html_content) {
          setHtmlContent(res.data.html_content)
          setReportTitle(res.data.title)
          setPhase('done')
        } else if (res.data.status === 'failed') {
          setPhase('error')
          setError(res.data.summary || '生成失败，请重试')
        }
      }).catch(() => {
        setPhase('error')
        setError('获取报告失败，请刷新页面')
      })
    }
  }, []) // no deps needed, uses ref

  // SSE hook - only activate when generating
  const sseId = generating ? researchId : null
  useResearchSSE(sseId, handleSSEEvent, handleSSEDone)

  // Smart Describe: optimize query via AI 聪明描述
  const handleOptimize = async () => {
    if (!query.trim()) return
    setOptimizing(true)
    setError(null)
    try {
      const res = await client.post('/api/research/optimize-query', {
        query: query.trim(),
        title: title.trim() || null,
      })
      setQuery(res.data.optimized_query)
      if (res.data.optimized_title) {
        setTitle(res.data.optimized_title)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'AI优化失败，请重试')
    } finally {
      setOptimizing(false)
    }
  }

  // Create research and start generation
  const handleGenerate = async () => {
    if (!query.trim() || submitting) return
    setSubmitting(true)
    setError(null)
    setMessages([])
    setProgress(0)

    try {
      // Step 1: Create research record
      const res = await client.post('/api/research', {
        query: query.trim(),
        title: title.trim() || null,
      })
      const newId = res.data.id
      setResearchId(newId)
      setPhase('generating')
      setGenerating(true)

      // Mark that we initiated generation locally so the load-existing effect is skipped
      localGenerationRef.current = true
      // Update URL without triggering a full reload
      navigate(`/research/${newId}`, { replace: true })
    } catch (err: any) {
      const detail = err.response?.data?.detail
      // If duplicate detected, redirect to existing research
      if (err.response?.status === 409 && err.response?.data?.existing_id) {
        navigate(`/research/${err.response.data.existing_id}`, { replace: true })
        return
      }
      setError(detail || '创建研究失败')
    } finally {
      setSubmitting(false)
    }
  }

  // Retry failed generation
  const handleRetry = () => {
    if (!researchId) return
    setError(null)
    setMessages([])
    setProgress(0)
    setPhase('generating')
    setGenerating(true)
  }

  // Download HTML
  const handleDownload = () => {
    if (!htmlContent) return
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${reportTitle || 'research-report'}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Open in new tab
  const handleOpenNewTab = () => {
    if (!researchId) return
    window.open(`/api/research/${researchId}/html`, '_blank')
  }

  // Write HTML to iframe
  useEffect(() => {
    if (htmlContent && iframeRef.current) {
      const doc = iframeRef.current.contentDocument
      if (doc) {
        doc.open()
        doc.write(htmlContent)
        doc.close()
      }
    }
  }, [htmlContent])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="p-2 rounded-lg hover:bg-gray-100 transition"
            >
              <ArrowLeft size={18} className="text-gray-500" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles size={20} className="text-purple-600" />
              <h1 className="text-lg font-bold text-gray-900">深度研究</h1>
            </div>
          </div>
          {phase === 'done' && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition"
              >
                <Download size={14} /> 下载 HTML
              </button>
              <button
                onClick={handleOpenNewTab}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition"
              >
                <ExternalLink size={14} /> 新窗口打开
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* ── Input Phase ───────────────────────────────────────────── */}
        {phase === 'input' && (
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                AI 深度研究报告生成
              </h2>
              <p className="text-gray-500">
                输入您的研究问题，AI将为您生成一篇结构化的深度研究报告
              </p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                标题（可选）
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="如不填写，将自动生成..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-sm mb-4"
              />

              <label className="block text-sm font-medium text-gray-700 mb-2">
                研究问题 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={'例如：详细阐述下模型预训练和后训练的概念，核心的训练方法，分别解决什么问题，这几年都经历了哪些核心阶段和节点，有什么重要的Paper（给一个带Paper链接的列表），目前阶段的问题和下一阶段的核心进展会在哪些方面，给我做一个普及'}
                rows={6}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-sm resize-none"
              />

              <div className="flex justify-end mt-4 gap-3">
                <button
                  onClick={handleOptimize}
                  disabled={!query.trim() || optimizing}
                  className="flex items-center gap-2 bg-white border border-purple-300 text-purple-600 px-5 py-2.5 rounded-lg hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium"
                >
                  {optimizing ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Wand2 size={16} />
                  )}
                  {optimizing ? '优化中...' : '聪明描述'}
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={!query.trim() || submitting}
                  className="flex items-center gap-2 bg-purple-600 text-white px-6 py-2.5 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium"
                >
                  {submitting ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Send size={16} />
                  )}
                  {submitting ? '提交中...' : '生成研报'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Generating Phase ──────────────────────────────────────── */}
        {phase === 'generating' && (
          <div className="max-w-3xl mx-auto">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              {/* Progress bar */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {reportTitle || '正在生成研究报告...'}
                  </span>
                  <span className="text-sm text-purple-600 font-semibold">
                    {progress}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-purple-600 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Step indicators */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
                {Object.entries(STEP_CONFIG).map(([key, { icon: Icon, label }]) => {
                  const isActive = currentStep === key
                  const isDone =
                    Object.keys(STEP_CONFIG).indexOf(key) <
                    Object.keys(STEP_CONFIG).indexOf(currentStep)
                  return (
                    <div
                      key={key}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${
                        isActive
                          ? 'bg-purple-100 text-purple-700 border border-purple-300'
                          : isDone
                            ? 'bg-green-50 text-green-700 border border-green-200'
                            : 'bg-gray-50 text-gray-400 border border-gray-200'
                      }`}
                    >
                      {isActive ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : isDone ? (
                        <Check size={14} />
                      ) : (
                        <Icon size={14} />
                      )}
                      {label}
                    </div>
                  )
                })}
              </div>

              {/* Message log */}
              <div className="bg-gray-50 rounded-lg p-4 max-h-60 overflow-y-auto">
                <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  生成日志
                </h4>
                {messages.map((msg, i) => (
                  <div key={i} className="text-xs text-gray-600 py-0.5">
                    <span className="text-gray-400 mr-2">
                      [{String(i + 1).padStart(2, '0')}]
                    </span>
                    {msg}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
        )}

        {/* ── Error Phase ──────────────────────────────────────────── */}
        {phase === 'error' && (
          <div className="max-w-3xl mx-auto">
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <p className="text-red-600 mb-4">{error || '生成过程中出现错误'}</p>
              <div className="flex justify-center gap-3">
                <button
                  onClick={handleRetry}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition"
                >
                  重试
                </button>
                <button
                  onClick={() => {
                    setPhase('input')
                    setError(null)
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-100 transition"
                >
                  返回
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Done Phase: HTML Preview ─────────────────────────────── */}
        {phase === 'done' && htmlContent && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-700">
                {reportTitle || '研究报告预览'}
              </h3>
              <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                已完成
              </span>
            </div>
            <iframe
              ref={iframeRef}
              title="Research Report Preview"
              className="w-full border-0"
              style={{ height: '80vh' }}
            />
          </div>
        )}

        {/* ── Error message for non-phase errors ──────────────────── */}
        {error && phase === 'input' && (
          <div className="max-w-3xl mx-auto mt-4">
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
