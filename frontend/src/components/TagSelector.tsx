/**
 * =============================================================================
 * Module: components/TagSelector.tsx
 * Description: Multi-select tag picker component. Displays existing tags as
 *              chips and allows toggling selection.
 *              多选标签选择器组件 - 以芯片形式展示现有标签，支持切换选中状态。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react, hooks/useThoughts
 * =============================================================================
 */

import { useTags } from '../hooks/useThoughts'

interface Props {
  selected: string[]
  onChange: (ids: string[]) => void
}

export default function TagSelector({ selected, onChange }: Props) {
  const { tags, loading } = useTags()

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id))
    } else {
      onChange([...selected, id])
    }
  }

  if (loading) {
    return <div className="text-sm text-gray-400">加载标签中...</div>
  }

  if (tags.length === 0) {
    return <div className="text-sm text-gray-400">还没有标签</div>
  }

  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag) => (
        <button
          key={tag.id}
          type="button"
          onClick={() => toggle(tag.id)}
          className={`px-3 py-1 rounded-full text-sm border transition ${
            selected.includes(tag.id)
              ? 'bg-indigo-100 border-indigo-400 text-indigo-700'
              : 'bg-white border-gray-300 text-gray-600 hover:border-gray-400'
          }`}
        >
          {tag.name}
        </button>
      ))}
    </div>
  )
}
