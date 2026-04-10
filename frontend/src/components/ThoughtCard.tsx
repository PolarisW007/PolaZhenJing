/**
 * =============================================================================
 * Module: components/ThoughtCard.tsx
 * Description: Card component for displaying a thought preview in the
 *              dashboard list.
 *              思绪卡片组件 - 用于在仪表盘列表中展示思绪预览。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, react-router-dom, lucide-react
 * =============================================================================
 */

import { Link } from 'react-router-dom'
import { Calendar, Tag as TagIcon } from 'lucide-react'
import type { Thought } from '../hooks/useThoughts'

interface Props {
  thought: Thought
}

const statusLabels: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}

export default function ThoughtCard({ thought }: Props) {
  return (
    <Link
      to={`/thought/${thought.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
          {thought.title}
        </h3>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${
            thought.status === 'draft'
              ? 'bg-yellow-100 text-yellow-800'
              : thought.status === 'published'
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-600'
          }`}
        >
          {statusLabels[thought.status] || thought.status}
        </span>
      </div>

      {/* Summary / snippet */}
      {thought.summary && (
        <p className="text-gray-500 text-sm mt-2 line-clamp-2">{thought.summary}</p>
      )}

      {/* Footer: date + tags */}
      <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <Calendar size={12} />
          {new Date(thought.created_at).toLocaleDateString()}
        </span>
        {thought.tags.length > 0 && (
          <span className="flex items-center gap-1">
            <TagIcon size={12} />
            {thought.tags.map((t) => t.name).join(', ')}
          </span>
        )}
        {thought.category && (
          <span className="text-indigo-500">{thought.category}</span>
        )}
      </div>
    </Link>
  )
}
