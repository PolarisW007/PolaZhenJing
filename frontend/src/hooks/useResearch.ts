/**
 * =============================================================================
 * Hook: useResearch
 * Description: Custom hook for fetching research list and SSE event handling.
 *              研究列表获取和SSE事件处理的自定义Hook。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, axios client
 * =============================================================================
 */

import { useCallback, useEffect, useState } from 'react'
import client from '../api/client'

export interface ResearchItem {
  id: string
  title: string
  query: string
  summary: string | null
  status: string
  created_at: string
  updated_at: string
}

interface UseResearchListResult {
  researches: ResearchItem[]
  total: number
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useResearchList(page = 1, pageSize = 20): UseResearchListResult {
  const [researches, setResearches] = useState<ResearchItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(() => {
    setLoading(true)
    client
      .get('/api/research', { params: { page, page_size: pageSize } })
      .then((res) => {
        setResearches(res.data.items)
        setTotal(res.data.total)
        setError(null)
      })
      .catch((err) => setError(err.response?.data?.detail || '加载研究列表失败'))
      .finally(() => setLoading(false))
  }, [page, pageSize])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { researches, total, loading, error, refresh: fetch }
}

export interface SSEEvent {
  step: string
  status: string
  message: string
  progress: number
  data?: Record<string, unknown>
}

export function useResearchSSE(
  researchId: string | null,
  onEvent: (event: SSEEvent) => void,
  onDone: () => void,
) {
  useEffect(() => {
    if (!researchId) return

    const token = localStorage.getItem('access_token')
    // EventSource doesn't support custom headers, so we use fetch with ReadableStream
    const controller = new AbortController()

    const startStream = async () => {
      try {
        const resp = await fetch(`/api/research/${researchId}/generate`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        })

        if (!resp.ok || !resp.body) {
          onEvent({
            step: 'error',
            status: 'error',
            message: `HTTP ${resp.status}: ${resp.statusText}`,
            progress: 0,
          })
          return
        }

        const reader = resp.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event: SSEEvent = JSON.parse(line.slice(6))
                onEvent(event)
                if (
                  event.step === 'stream_end' ||
                  event.step === 'complete' ||
                  event.status === 'error'
                ) {
                  onDone()
                }
              } catch {
                // skip malformed lines
              }
            }
          }
        }
        onDone()
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        onEvent({
          step: 'error',
          status: 'error',
          message: '连接中断',
          progress: 0,
        })
        onDone()
      }
    }

    startStream()

    return () => controller.abort()
  }, [researchId]) // eslint-disable-line react-hooks/exhaustive-deps
}
