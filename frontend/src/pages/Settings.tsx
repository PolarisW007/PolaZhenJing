/**
 * =============================================================================
 * Module: pages/Settings.tsx
 * Description: Settings page for configuring AI provider, API keys, and
 *              site preferences.
 *              设置页面 - 用于配置AI提供商、API密钥和站点偏好。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, lucide-react, stores/authStore
 * =============================================================================
 */

import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Info } from 'lucide-react'
import useAuthStore from '../stores/authStore'

export default function Settings() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-900 transition text-sm"
          >
            <ArrowLeft size={16} />
            返回
          </button>
          <h1 className="text-lg font-semibold text-gray-900">设置</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {/* Profile */}
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">个人资料</h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500">用户名</span>
              <p className="font-medium">{user?.username}</p>
            </div>
            <div>
              <span className="text-gray-500">邮箱</span>
              <p className="font-medium">{user?.email}</p>
            </div>
            <div>
              <span className="text-gray-500">显示名称</span>
              <p className="font-medium">{user?.display_name || '—'}</p>
            </div>
            <div>
              <span className="text-gray-500">角色</span>
              <p className="font-medium">{user?.is_superuser ? '管理员' : '普通用户'}</p>
            </div>
          </div>
        </section>

        {/* AI Configuration Info */}
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">AI 提供商</h2>
          <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-lg p-3">
            <Info size={16} className="text-blue-500 mt-0.5 shrink-0" />
            <p className="text-sm text-blue-700">
              AI提供商通过环境变量配置：
              <code className="bg-blue-100 px-1 rounded mx-1">AI_PROVIDER</code>、
              <code className="bg-blue-100 px-1 rounded mx-1">OPENAI_API_KEY</code>、
              <code className="bg-blue-100 px-1 rounded mx-1">OPENAI_BASE_URL</code>。
              修改 <code className="bg-blue-100 px-1 rounded">.env</code> 文件或
              Docker Compose 环境变量来切换提供商。
            </p>
          </div>
        </section>

        {/* Site Configuration Info */}
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">站点与发布</h2>
          <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-lg p-3">
            <Info size={16} className="text-blue-500 mt-0.5 shrink-0" />
            <p className="text-sm text-blue-700">
              已发布的思绪会导出为 Markdown 文件到 MkDocs 站点。
              静态站点通过 GitHub Actions 构建并部署到 GitHub Pages。
              设置 <code className="bg-blue-100 px-1 rounded mx-1">SITE_BASE_URL</code> 为
              你的 GitHub Pages 地址。
            </p>
          </div>
        </section>
      </main>
    </div>
  )
}
