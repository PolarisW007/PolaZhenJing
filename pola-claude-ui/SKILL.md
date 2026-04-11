---
name: pola-claude-ui
description: "Harness Books 暖色书卷风 UI 设计系统，温暖米色背景 + 棕色文字 + 衬线标题 + 侧边栏导航，适用于技术文档站、电子书阅读、知识库、博客长文"
user-invocable: true
triggers:
  - pattern: "/claudeui|/书卷风|/文档站|/暖色文档|/harness|/书籍UI|/知识库UI|/阅读风格|Claude UI|Harness Books"
---

# PolaClaudeUI — Harness Books 暖色书卷设计系统

> **参考来源**：https://harness-books.agentway.dev/book2-comparing/
> **适用场景**：技术文档站、电子书阅读页、知识库、博客长文、在线教程、API 文档
> **技术栈**：Next.js + TailwindCSS（或纯 CSS）
> **风格标签**：Warm Scholarly · Earthy Brown · Serif Headlines · Sidebar Navigation · Book-like Layout

---

## 一、设计语言核心原则

### 1.1 色彩系统

```css
/* ========== 背景层次 ========== */
--bg-page:         #FFFCF5;           /* rgb(255,252,245) 页面根背景，温暖米色 */
--bg-sidebar:      #F5F0E6;           /* rgb(245,240,230) 侧边栏背景，略深米色 */
--bg-sidebar-active: rgba(45,36,24,0.08); /* 侧边栏选中项底色 */
--bg-code:         rgba(135,89,50,0.09);  /* 代码块淡棕底色 */
--bg-link:         rgba(255,252,245,0.82); /* 链接底色，极浅暖白 */
--bg-link-hover:   rgba(255,252,245,0.72); /* 链接 hover 底色 */
--bg-card:         rgba(135,89,50,0.04);   /* 卡片/提示框底色 */

/* ========== 棕色主色系 ========== */
--brown-primary:   #2D241A;  /* rgb(45,36,24)   主棕色（链接、强调） */
--brown-heading:   #211912;  /* rgb(33,25,18)   标题深棕 */
--brown-body:      #756756;  /* rgb(117,103,86) 正文棕灰 */
--brown-quote:     #5E5245;  /* rgb(94,82,69)   引用文字 */
--brown-nav:       #5D5042;  /* rgb(93,80,66)   导航文字 */
--brown-code:      #5C3B22;  /* rgb(92,59,34)   代码文字 */
--brown-border:    rgba(53,41,27,0.12);  /* 边框色 */
--brown-accent:    #875932;  /* rgb(135,89,50)  强调棕（引用线等） */

/* ========== 文字色阶 ========== */
--text-title:      #7E888B;  /* rgb(126,136,139) H1 标题灰色 */
--text-heading:    #211912;  /* rgb(33,25,18)    H2/H3 深棕 */
--text-body:       #756756;  /* rgb(117,103,86)  正文 */
--text-muted:      #9A8E80;  /* rgba 等效灰棕     弱化文字 */
--text-link:       #2D241A;  /* rgb(45,36,24)    链接 */
--text-disabled:   #C0B8AD;  /* 禁用态 */

/* ========== 边框与分隔 ========== */
--border-light:    rgba(53,41,27,0.12);    /* 浅边框 */
--border-quote:    rgba(135,89,50,0.34);   /* 引用左边框 */
--border-divider:  #E8E0D4;               /* 分隔线 */
--border-sidebar:  #E0D8CC;               /* 侧边栏边框 */

/* ========== 状态色 ========== */
--color-success:   #5B8C5A;  /* 绿色提示 */
--color-info:      #4A7FB5;  /* 蓝色信息 */
--color-warning:   #C49A3C;  /* 棕黄警告 */
--color-danger:    #B85450;  /* 红色危险 */
```

### 1.2 字体规范

```css
/* 正文字体栈 (Sans-serif) */
font-family: "Helvetica Neue", Helvetica, "Avenir Next",
             "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC",
             Arial, sans-serif;

/* 标题字体栈 (Serif - 古典衬线) */
font-family: "Iowan Old Style", "Palatino Linotype",
             "Noto Serif SC", "Source Han Serif SC",
             "Songti SC", Georgia, serif;

/* 代码字体栈 (Monospace) */
font-family: Consolas, "Liberation Mono", Menlo, Courier, monospace;
```

| 元素 | 字号 | 字重 | 行高 | 字体 | 颜色 |
|------|------|------|------|------|------|
| H1 页面标题 | 32px | 200 | 1.4 | Serif | --text-title (#7E888B) |
| H2 章节标题 | 25.5px | 700 | 1.92 | Serif | --text-heading (#211912) |
| H3 小节标题 | 18px | 700 | 1.3 | Serif | --text-heading (#1F1812) |
| H4 子标题 | 15px | 600 | 1.4 | Serif | --text-heading |
| Body 正文 | 16px | 400 | 1.7 | Sans-serif | --text-body (#756756) |
| Body Small | 14px | 400 | 1.6 | Sans-serif | --text-body |
| Blockquote | 17px | 400 | 1.6 | Sans-serif | --brown-quote (#5E5245) |
| Sidebar Link | 14px | 400 | 1.4 | Sans-serif | --brown-nav (#5D5042) |
| Sidebar Active | 14px | 600 | 1.4 | Sans-serif | --brown-primary (#2D241A) |
| Link | 14px | 600 | — | Sans-serif | --text-link (#2D241A) |
| Code Inline | 14px | 400 | 1.92 | Monospace | --brown-code (#5C3B22) |
| Code Block | 13px | 400 | 1.6 | Monospace | --brown-code |
| Caption | 12px | 400 | 1.4 | Sans-serif | --text-muted |

**Tailwind 映射**

```
H1:           text-[32px] font-extralight leading-[1.4] (serif font)
H2:           text-[25.5px] font-bold leading-[1.92] (serif font)
H3:           text-lg font-bold leading-snug (serif font)
Body:         text-base font-normal leading-relaxed text-[#756756]
Body Small:   text-sm font-normal text-[#756756]
Blockquote:   text-[17px] font-normal text-[#5E5245]
Sidebar:      text-sm font-normal text-[#5D5042]
Link:         text-sm font-semibold text-[#2D241A]
Code:         text-sm font-normal font-mono text-[#5C3B22]
```

---

## 二、布局系统

### 2.1 页面结构

```
┌──────────────────────────────────────────────────────┐
│ [Top Bar]  Book Title · Language Toggle · PDF · GitHub│  可选顶栏
├──────────┬───────────────────────────────────────────┤
│          │                                           │
│ SIDEBAR  │           MAIN CONTENT                    │
│ 280px    │           max-width: 800px                │
│          │                                           │
│ · Search │  H1 页面标题 (32px Serif ExtraLight)      │
│ · TOC    │                                           │
│ · Chap 1 │  H2 章节标题 (25.5px Serif Bold)          │
│ · Chap 2 │                                           │
│ · Chap 3 │  正文段落 (16px Sans 棕灰)                │
│ · ...    │                                           │
│ · 附录   │  > 引用块 (17px 棕色左边框)               │
│          │                                           │
│          │  `代码块` (淡棕底 棕色字)                  │
│          │                                           │
│          │  ← Prev    Next →                         │
│          │                                           │
├──────────┴───────────────────────────────────────────┤
│ [Footer]  Powered by · Copyright                      │
└──────────────────────────────────────────────────────┘
```

### 2.2 容器与间距

```css
/* 侧边栏 */
.sidebar {
  width: 280px;
  min-width: 280px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-sidebar);
  overflow-y: auto;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
}

/* 主内容区 */
.main-content {
  margin-left: 280px;
  max-width: 800px;
  padding: 40px 48px;
  margin-right: auto;
}

/* 间距体系 */
--space-xs:    4px;
--space-sm:    8px;
--space-md:    16px;
--space-lg:    24px;
--space-xl:    36px;
--space-2xl:   48px;
--space-3xl:   64px;
--space-section: 43px;   /* H2 上方间距 */
--space-paragraph: 16px; /* 段落间距 */
```

### 2.3 响应式断点

```css
@media (max-width: 1240px) { /* 缩小侧边栏 */ }
@media (max-width: 1000px) { /* 侧边栏变窄 */ }
@media (max-width: 860px)  { /* 侧边栏可折叠 */ }
@media (max-width: 640px)  { /* 移动端：侧边栏隐藏为抽屉 */ }
@media (max-width: 600px)  { /* 小屏优化 */ }
```

---

## 三、组件库

### 3.1 侧边栏导航（Sidebar）

```tsx
<aside className="
  fixed left-0 top-0 h-screen w-[280px]
  bg-[#F5F0E6] border-r border-[#E0D8CC]
  overflow-y-auto
  flex flex-col
">
  {/* 搜索框 */}
  <div className="p-4 border-b border-[#E0D8CC]">
    <input
      type="text"
      placeholder="输入并搜索"
      className="
        w-full px-3 py-2 rounded-md
        bg-white/60 border border-[rgba(53,41,27,0.12)]
        text-sm text-[#5D5042]
        placeholder:text-[#9A8E80]
        focus:outline-none focus:border-[#875932]
        transition-colors duration-200
      "
    />
  </div>

  {/* 导航菜单 */}
  <nav className="flex-1 py-2">
    {/* 选中项 */}
    <a className="
      block px-4 py-2.5
      text-sm font-semibold text-[#2D241A]
      bg-[rgba(45,36,24,0.08)]
      border-r-2 border-[#875932]
    ">
      第 1 章 为什么要把 Claude Code 和 Codex 放在一起看
    </a>

    {/* 普通项 */}
    <a className="
      block px-4 py-2.5
      text-sm text-[#5D5042]
      hover:bg-[rgba(45,36,24,0.04)]
      hover:text-[#2D241A]
      transition-colors duration-200
    ">
      第 2 章 两种控制面
    </a>
  </nav>

  {/* 底部 */}
  <div className="p-4 border-t border-[#E0D8CC] text-xs text-[#9A8E80]">
    Powered by HonKit
  </div>
</aside>
```

### 3.2 顶部导航栏（Top Bar，可选）

```tsx
<header className="
  fixed top-0 left-[280px] right-0 z-40
  h-12 px-6
  bg-[#FFFCF5]/95 backdrop-blur-sm
  border-b border-[#E8E0D4]
  flex items-center justify-between
">
  {/* 书名 */}
  <span className="text-sm font-semibold text-[#2D241A] tracking-wide uppercase">
    Harness Books
  </span>

  {/* 工具栏 */}
  <div className="flex items-center gap-4">
    <a className="text-sm text-[#5D5042] hover:text-[#2D241A] transition-colors">
      中文
    </a>
    <a className="text-sm text-[#9A8E80] hover:text-[#2D241A] transition-colors">
      English
    </a>
    <a className="text-sm text-[#5D5042] hover:text-[#2D241A] transition-colors">
      下载 PDF
    </a>
    <a className="text-sm text-[#5D5042] hover:text-[#2D241A] transition-colors">
      GitHub
    </a>
  </div>
</header>
```

### 3.3 页面标题（H1）

```tsx
<h1
  className="text-[32px] font-extralight leading-[1.4] text-[#7E888B] tracking-wide"
  style={{ fontFamily: '"Iowan Old Style", "Palatino Linotype", "Noto Serif SC", "Source Han Serif SC", serif' }}
>
  Claude Code 和 Codex 的 Harness 设计哲学
</h1>
```

### 3.4 章节标题（H2）

```tsx
<h2
  className="text-[25.5px] font-bold leading-[1.92] text-[#211912] mt-[43px] mb-[22px]"
  style={{ fontFamily: '"Iowan Old Style", "Palatino Linotype", "Noto Serif SC", "Source Han Serif SC", serif' }}
>
  1.1 因为它们比较的是对模型的不信任
</h2>
```

### 3.5 正文段落

```tsx
<p className="text-base text-[#756756] leading-relaxed mb-4">
  如果把 Claude Code 和 Codex 当作两个"会写代码的助手"，
  那比较就会很无聊。无非是谁支持更多工具、谁的上下文窗口更大。
</p>
```

### 3.6 引用块（Blockquote）

```tsx
<blockquote className="
  border-l-[3px] border-[rgba(135,89,50,0.34)]
  pl-4 py-1 my-4
  text-[17px] text-[#5E5245] leading-relaxed
  bg-transparent
">
  "人活在世上，就是为了忍受摧残。"做 harness 也是。
  区别只在于，有人把摧残写进控制流，有人把摧残写进制度层。
</blockquote>
```

### 3.7 行内代码（Inline Code）

```tsx
<code className="
  bg-[rgba(135,89,50,0.09)]
  text-[#5C3B22] text-sm
  px-1.5 py-0.5
  rounded-sm
  font-mono
">
  QueryLoop
</code>
```

### 3.8 代码块（Code Block）

```tsx
<pre className="
  bg-[rgba(135,89,50,0.09)]
  text-[#5C3B22] text-[13px]
  leading-relaxed
  p-4 my-4
  rounded-md
  overflow-x-auto
  font-mono
">
  <code>
{`function harness(model) {
  return model.query({ loop: true });
}`}
  </code>
</pre>
```

### 3.9 链接（Link）

```tsx
{/* 正文链接 */}
<a className="
  text-sm font-semibold text-[#2D241A]
  bg-[rgba(255,252,245,0.82)]
  border border-[rgba(53,41,27,0.12)]
  px-3 py-0 rounded-sm
  hover:bg-[rgba(255,252,245,0.72)]
  transition-colors duration-200
  no-underline
">
  延伸阅读 →
</a>

{/* 简单文字链接 */}
<a className="
  text-[#2D241A] font-semibold
  hover:underline hover:decoration-[rgba(135,89,50,0.34)]
  transition-all duration-200
">
  第 7 章
</a>
```

### 3.10 有序/无序列表

```tsx
{/* 有序列表 */}
<ol className="list-decimal list-inside space-y-1.5 text-base text-[#756756] leading-relaxed my-4 pl-2">
  <li>阅读地图：如何理解第一本书与这本比较书</li>
  <li>序言 两套 Harness，不必假装是同一匹马的附件</li>
  <li>第 1 章 为什么要把 Claude Code 和 Codex 放在一起看</li>
</ol>

{/* 无序列表 */}
<ul className="list-disc list-inside space-y-1.5 text-base text-[#756756] leading-relaxed my-4 pl-2">
  <li>Claude Code 和 Codex 比较的重点不在模型，而在 harness</li>
  <li>harness 是一种权力分配方式</li>
</ul>
```

### 3.11 提示框（Alert / Callout）

```tsx
{/* 信息提示 */}
<div className="
  border-l-4 border-[#4A7FB5]
  bg-[rgba(74,127,181,0.06)]
  rounded-r-md p-4 my-4
">
  <p className="text-sm font-semibold text-[#4A7FB5] mb-1">ℹ️ 提示</p>
  <p className="text-sm text-[#756756] leading-relaxed">
    建议阅读顺序：先看总判断，可以直接跳到第 7 章。
  </p>
</div>

{/* 警告提示 */}
<div className="
  border-l-4 border-[#C49A3C]
  bg-[rgba(196,154,60,0.06)]
  rounded-r-md p-4 my-4
">
  <p className="text-sm font-semibold text-[#C49A3C] mb-1">⚠️ 注意</p>
  <p className="text-sm text-[#756756] leading-relaxed">
    这不是一份功能表，也不是一篇产品评测。
  </p>
</div>
```

### 3.12 翻页导航（Prev / Next）

```tsx
<div className="flex items-center justify-between mt-16 pt-6 border-t border-[#E8E0D4]">
  <a className="
    flex items-center gap-2
    text-sm text-[#5D5042]
    hover:text-[#2D241A]
    transition-colors duration-200
  ">
    <span>←</span>
    <span>序言 两套 Harness</span>
  </a>
  <a className="
    flex items-center gap-2
    text-sm text-[#5D5042]
    hover:text-[#2D241A]
    transition-colors duration-200
  ">
    <span>第 2 章 两种控制面</span>
    <span>→</span>
  </a>
</div>
```

### 3.13 表格

```tsx
<table className="w-full my-4 border-collapse text-sm">
  <thead>
    <tr className="border-b-2 border-[#E8E0D4]">
      <th className="text-left py-2 px-3 font-semibold text-[#2D241A]">维度</th>
      <th className="text-left py-2 px-3 font-semibold text-[#2D241A]">Claude Code</th>
      <th className="text-left py-2 px-3 font-semibold text-[#2D241A]">Codex</th>
    </tr>
  </thead>
  <tbody>
    <tr className="border-b border-[#E8E0D4]">
      <td className="py-2 px-3 text-[#756756]">控制方式</td>
      <td className="py-2 px-3 text-[#756756]">运行时落地</td>
      <td className="py-2 px-3 text-[#756756]">制度层先设防</td>
    </tr>
  </tbody>
</table>
```

---

## 四、设计决策速查表

| 决策项 | 选择 | 说明 |
|--------|------|------|
| 主色调 | 暖棕书卷 Warm Scholarly | 米色底 `#FFFCF5` + 棕色文字 `#2D241A` |
| 标题字体 | 经典衬线 Serif | Iowan Old Style / Palatino / 思源宋体 |
| 正文字体 | 系统无衬线 | Helvetica Neue / PingFang SC |
| 代码字体 | Monospace | Consolas / Menlo |
| 页面布局 | 侧边栏 + 内容区 | 固定 280px 侧边栏，内容区 max-width 800px |
| 引用样式 | 左棕边框 3px | `rgba(135,89,50,0.34)` 色调统一 |
| 代码样式 | 淡棕底 + 棕色字 | 不突兀，融入整体暖色调 |
| 链接样式 | 暖底色 + 细边框 | `rgba(255,252,245,0.82)` 底 + 12% 棕边框 |
| 间距基准 | 8px 倍数 | 48px 内容边距，43px 章节间距 |
| 动效 | 极简过渡 | 仅颜色过渡 200ms ease |
| 文字层次 | 4 级棕灰色 | 深棕→棕灰→弱化→禁用 |
| 导航 | 固定侧边栏 | 米色底 + 右侧细边框 |
| 圆角 | 小圆角 4-8px | 保持方正书卷感，仅代码块/输入框微圆角 |

---

## 五、Tailwind 自定义配置

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  theme: {
    extend: {
      colors: {
        harness: {
          bg:          "#FFFCF5",
          sidebar:     "#F5F0E6",
          brown:       "#2D241A",
          "brown-heading": "#211912",
          "brown-body": "#756756",
          "brown-quote": "#5E5245",
          "brown-nav":  "#5D5042",
          "brown-code": "#5C3B22",
          "brown-accent": "#875932",
          "title-gray": "#7E888B",
          muted:       "#9A8E80",
          divider:     "#E8E0D4",
          "sidebar-border": "#E0D8CC",
          success:     "#5B8C5A",
          info:        "#4A7FB5",
          warning:     "#C49A3C",
          danger:      "#B85450",
        },
      },
      fontFamily: {
        serif: [
          "Iowan Old Style", "Palatino Linotype",
          "Noto Serif SC", "Source Han Serif SC",
          "Songti SC", "Georgia", "serif",
        ],
        sans: [
          "Helvetica Neue", "Helvetica", "Avenir Next",
          "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC",
          "Arial", "sans-serif",
        ],
        mono: [
          "Consolas", "Liberation Mono", "Menlo", "Courier", "monospace",
        ],
      },
      maxWidth: {
        content: "800px",
        sidebar: "280px",
      },
      width: {
        sidebar: "280px",
      },
      spacing: {
        "section": "43px",
      },
    },
  },
};

export default config;
```

---

## 六、快速启动模板

### 完整页面骨架

```tsx
export default function HarnessBookLayout() {
  return (
    <div className="min-h-screen bg-harness-bg text-harness-brown-body flex">

      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-screen w-sidebar bg-harness-sidebar border-r border-harness-sidebar-border overflow-y-auto flex flex-col">

        {/* Search */}
        <div className="p-4 border-b border-harness-sidebar-border">
          <input
            placeholder="输入并搜索"
            className="w-full px-3 py-2 rounded-md bg-white/60 border border-[rgba(53,41,27,0.12)] text-sm text-harness-brown-nav placeholder:text-harness-muted focus:outline-none focus:border-harness-brown-accent"
          />
        </div>

        {/* Book Title */}
        <div className="px-4 py-3 border-b border-harness-sidebar-border">
          <p className="text-xs font-semibold text-harness-muted tracking-widest uppercase">
            Harness Books
          </p>
          <p className="text-sm font-semibold text-harness-brown mt-1">
            Claude Code 和 Codex 的 Harness 设计哲学
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-2">
          <a className="block px-4 py-2.5 text-sm text-harness-brown-nav hover:bg-[rgba(45,36,24,0.04)] hover:text-harness-brown transition-colors">
            Introduction
          </a>
          <a className="block px-4 py-2.5 text-sm font-semibold text-harness-brown bg-[rgba(45,36,24,0.08)] border-r-2 border-harness-brown-accent">
            第 1 章 为什么要把 Claude Code 和 Codex 放在一起看
          </a>
          <a className="block px-4 py-2.5 text-sm text-harness-brown-nav hover:bg-[rgba(45,36,24,0.04)] hover:text-harness-brown transition-colors">
            第 2 章 两种控制面
          </a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="ml-[280px] flex-1">
        <div className="max-w-content mx-auto px-12 py-10">

          {/* Page Title */}
          <h1
            className="text-[32px] font-extralight leading-[1.4] text-harness-title-gray tracking-wide mb-8"
            style={{ fontFamily: '"Iowan Old Style", "Palatino Linotype", "Noto Serif SC", "Source Han Serif SC", serif' }}
          >
            第 1 章 为什么要把 Claude Code 和 Codex 放在一起看
          </h1>

          {/* Section Heading */}
          <h2
            className="text-[25.5px] font-bold leading-[1.92] text-harness-brown-heading mt-section mb-[22px]"
            style={{ fontFamily: '"Iowan Old Style", "Palatino Linotype", "Noto Serif SC", "Source Han Serif SC", serif' }}
          >
            1.1 因为它们比较的是对模型的不信任
          </h2>

          {/* Paragraph */}
          <p className="text-base text-harness-brown-body leading-relaxed mb-4">
            如果把 Claude Code 和 Codex 当作两个"会写代码的助手"，
            那比较就会很无聊。
          </p>

          {/* Blockquote */}
          <blockquote className="border-l-[3px] border-[rgba(135,89,50,0.34)] pl-4 py-1 my-4 text-[17px] text-harness-brown-quote leading-relaxed">
            "人活在世上，就是为了忍受摧残。"做 harness 也是。
          </blockquote>

          {/* Unordered List */}
          <ul className="list-disc list-inside space-y-1.5 text-base text-harness-brown-body leading-relaxed my-4 pl-2">
            <li>harness 是一种权力分配方式</li>
            <li>工程系统的差别，常常不在名词，而在秩序住在哪一层</li>
          </ul>

          {/* Code Block */}
          <pre className="bg-[rgba(135,89,50,0.09)] text-harness-brown-code text-[13px] leading-relaxed p-4 my-4 rounded-md overflow-x-auto font-mono">
            <code>{`function harness(model) {\n  return model.query({ loop: true });\n}`}</code>
          </pre>

          {/* Prev/Next Navigation */}
          <div className="flex items-center justify-between mt-16 pt-6 border-t border-harness-divider">
            <a className="flex items-center gap-2 text-sm text-harness-brown-nav hover:text-harness-brown transition-colors">
              <span>←</span><span>序言</span>
            </a>
            <a className="flex items-center gap-2 text-sm text-harness-brown-nav hover:text-harness-brown transition-colors">
              <span>第 2 章</span><span>→</span>
            </a>
          </div>

        </div>
      </main>
    </div>
  );
}
```
