/**
 * =============================================================================
 * Component: ResearchCard
 * Description: Card component for displaying a research report in list views.
 *              研究报告列表卡片组件。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, react-router-dom, lucide-react
 * =============================================================================
 */

import { Link } from 'react-router-dom'
import { BookOpen, CheckCircle, Clock, Loader2, XCircle } from 'lucide-react'
import type { ResearchItem } from '../hooks/useResearch'

const STATUS_MAP: Record<
  string,
  { label: string; color: string; icon: typeof Clock }
> = {
  pending: { label: '待生成', color: 'text-yellow-600 bg-yellow-50', icon: Clock },
  generating: { label: '生成中', color: 'text-blue-600 bg-blue-50', icon: Loader2 },
  completed: { label: '已完成', color: 'text-green-600 bg-green-50', icon: CheckCircle },
  failed: { label: '失败', color: 'text-red-600 bg-red-50', icon: XCircle },
}

export default function ResearchCard({ research }: { research: ResearchItem }) {
  const status = STATUS_MAP[research.status] || STATUS_MAP.pending
  const StatusIcon = status.icon
  const date = new Date(research.created_at).toLocaleDateString('zh-CN')

  return (
    <Link
      to={`/research/${research.id}`}
      className="block bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="mt-0.5 p-2 bg-purple-50 rounded-lg shrink-0">
            <BookOpen size={16} className="text-purple-600" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-gray-900 truncate">
              {research.title || research.query.slice(0, 60)}
            </h3>
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">
              {research.summary || research.query}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 ml-3 shrink-0">
          <span
            className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${status.color}`}
          >
            <StatusIcon size={12} className={research.status === 'generating' ? 'animate-spin' : ''} />
            {status.label}
          </span>
          <span className="text-xs text-gray-400">{date}</span>
        </div>
      </div>
    </Link>
  )
}
