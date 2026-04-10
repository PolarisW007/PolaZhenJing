/**
 * =============================================================================
 * Module: pages/Dashboard.tsx
 * Description: Main dashboard page – lists thoughts with search, filter,
 *              and pagination. Acts as the home page for authenticated users.
 *              主仪表盘页面 - 展示思绪列表，支持搜索、筛选和分页。登录用户的首页。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, react-router-dom, lucide-react, hooks/useThoughts
 * =============================================================================
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BookOpen, LogOut, PenSquare, Search, Settings } from 'lucide-react'
import useAuthStore from '../stores/authStore'
import { useThoughts } from '../hooks/useThoughts'
import ThoughtCard from '../components/ThoughtCard'
import { useResearchList } from '../hooks/useResearch'
import ResearchCard from '../components/ResearchCard'

export default function Dashboard() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)

  const { thoughts, total, loading, error } = useThoughts({
    search: search || undefined,
    status: statusFilter || undefined,
    page,
    pageSize: 20,
  })

  const { researches, loading: researchLoading } = useResearchList(1, 5)

  const totalPages = Math.ceil(total / 20)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav bar */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">PolaZhenjing</h1>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">
              {user?.display_name || user?.username}
            </span>
            <Link
              to="/settings"
              className="p-2 rounded-lg hover:bg-gray-100 transition"
              title="设置"
            >
              <Settings size={18} className="text-gray-500" />
            </Link>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg hover:bg-gray-100 transition"
              title="退出登录"
            >
              <LogOut size={18} className="text-gray-500" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* Toolbar: search + filters + new button */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-6">
          <div className="relative flex-1 w-full">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              placeholder="搜索思绪..."
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            <option value="">所有状态</option>
            <option value="draft">草稿</option>
            <option value="published">已发布</option>
            <option value="archived">已归档</option>
          </select>

          <Link
            to="/thought/new"
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition text-sm font-medium shrink-0"
          >
            <PenSquare size={16} />
            新建思绪
          </Link>
          <Link
            to="/research/new"
            className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition text-sm font-medium shrink-0"
          >
            <BookOpen size={16} />
            深度研究
          </Link>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          </div>
        )}

        {/* Thought list */}
        {!loading && thoughts.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">还没有思绪</p>
            <p className="text-sm mt-1">点击“新建思绪”开始写作</p>
          </div>
        )}

        <div className="space-y-3">
          {thoughts.map((t) => (
            <ThoughtCard key={t.id} thought={t} />
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-2 mt-8">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 rounded border text-sm disabled:opacity-40"
            >
              上一页
            </button>
            <span className="text-sm text-gray-500">
              第 {page} 页 / 共 {totalPages} 页
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 rounded border text-sm disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        )}

        {/* Research Reports Section */}
        {!researchLoading && researches.length > 0 && (
          <div className="mt-10">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-800">深度研究报告</h2>
              <Link
                to="/research/new"
                className="text-sm text-purple-600 hover:text-purple-700"
              >
                查看全部
              </Link>
            </div>
            <div className="space-y-2">
              {researches.map((r) => (
                <ResearchCard key={r.id} research={r} />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
