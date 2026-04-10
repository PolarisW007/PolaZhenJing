/**
 * =============================================================================
 * Module: hooks/useThoughts.ts
 * Description: Custom hook for fetching and managing thoughts data.
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, api/client
 * =============================================================================
 */

import { useCallback, useEffect, useState } from 'react'
import client from '../api/client'

export interface Tag {
  id: string
  name: string
  slug: string
  color: string | null
  created_at: string
}

export interface Thought {
  id: string
  title: string
  slug: string
  content: string
  summary: string | null
  category: string | null
  status: string
  author_id: string
  tags: Tag[]
  created_at: string
  updated_at: string
}

interface UseThoughtsOptions {
  search?: string
  category?: string
  tag?: string
  status?: string
  page?: number
  pageSize?: number
}

export function useThoughts(options: UseThoughtsOptions = {}) {
  const [thoughts, setThoughts] = useState<Thought[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (options.search) params.set('search', options.search)
      if (options.category) params.set('category', options.category)
      if (options.tag) params.set('tag', options.tag)
      if (options.status) params.set('status', options.status)
      params.set('page', String(options.page || 1))
      params.set('page_size', String(options.pageSize || 20))

      const res = await client.get(`/api/thoughts?${params}`)
      setThoughts(res.data.items)
      setTotal(res.data.total)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch thoughts')
    } finally {
      setLoading(false)
    }
  }, [options.search, options.category, options.tag, options.status, options.page, options.pageSize])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { thoughts, total, loading, error, refresh: fetch }
}

export function useTags() {
  const [tags, setTags] = useState<(Tag & { thought_count: number })[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    client
      .get('/api/tags')
      .then((res) => setTags(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return { tags, loading }
}
