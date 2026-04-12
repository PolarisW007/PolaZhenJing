---
name: pola-pmframe-ui
description: "PMFrame 极简暖白产品框架 UI 设计系统，米白背景 + 深棕文字 + 衬线标题 + 分类色彩标签 + 网格卡片布局，适用于工具库、框架集合、方法论目录、知识卡片索引、SaaS 功能清单"
user-invocable: true
triggers:
  - pattern: "/pmframeui|/pmframe|/极简卡片|/工具库UI|/方法论UI|/框架目录|/知识卡片|PMFrame UI|Minimal Grid UI"
---

# PolaPMFrameUI — PMFrame 极简暖白产品框架设计系统

> **参考来源**：https://pmframe.works/
> **适用场景**：工具库 / 框架集合、方法论目录、知识卡片索引、SaaS 功能清单、分类标签体系页
> **技术栈**：Next.js + TailwindCSS（或纯 CSS）
> **风格标签**：Warm Minimal · Grid Cards · Category Colors · Serif Headlines · Functional Elegance

---

## 一、设计语言核心原则

### 1.1 色彩系统

```css
/* ========== 背景层次 ========== */
--bg-page:       #ffffff;           /* rgb(255,255,255) 页面根背景，纯白 */
--bg-surface:    #f8f7f4;           /* rgb(248,247,244) 次级表面，暖灰白 */
--bg-surface2:   #f0ede8;           /* rgb(240,237,232) 第三层面，淡暖灰 */
--bg-card:       #ffffff;           /* rgb(255,255,255) 卡片默认背景 */
--bg-card-hover: #f8f7f4;           /* 卡片 hover 态 */
--bg-fav:        #fdf8ec;           /* rgb(253,248,236) 收藏底色 */

/* ========== 文字色阶 ========== */
--text-primary:   #1a1916;  /* rgb(26,25,22)    标题、核心文字 */
--text-secondary: #6b6660;  /* rgb(107,102,96)  次要文字 */
--text-muted:     #9b9590;  /* rgb(155,149,144) 弱化文字 */

/* ========== 边框 ========== */
--border-default: #e8e4de;  /* rgb(232,228,222) 默认边框 */
--border-dark:    #d4cfc8;  /* rgb(212,207,200) 深边框 */

/* ========== 强调色 ========== */
--accent:         #1a1916;  /* 强调色 = 主文字色 */
--accent-green:   #1a7a4a;  /* rgb(26,122,74)  品牌绿（PMF） */
--color-fav:      #e8a820;  /* rgb(232,168,32) 收藏金 */

/* ========== 叠加层 ========== */
--overlay:        rgba(26,25,22,0.5);  /* 模态遮罩 */
```

### 1.2 分类色彩系统（7 组）

```css
/* Discovery 发现 */
--cat-discovery-bg:     #e8f5ee;  --cat-discovery-text:   #1a5c38;  --cat-discovery-border: #b8dfc8;
/* Define 定义 */
--cat-define-bg:        #e8eef8;  --cat-define-text:      #1a3a6b;  --cat-define-border:    #b8cce8;
/* Ideation 构思 */
--cat-ideation-bg:      #fdf3e3;  --cat-ideation-text:    #7a4a0a;  --cat-ideation-border:  #f0d4a0;
/* Validation 验证 */
--cat-validation-bg:    #fce8e8;  --cat-validation-text:  #7a1a1a;  --cat-validation-border:#f0b8b8;
/* Execution 执行 */
--cat-execution-bg:     #ede8f8;  --cat-execution-text:   #3a1a6b;  --cat-execution-border: #c8b8e8;
/* Growth 增长 */
--cat-growth-bg:        #e8f8e8;  --cat-growth-text:      #1a5a1a;  --cat-growth-border:    #b8dbb8;
/* System 系统 */
--cat-system-bg:        #f8e8f3;  --cat-system-text:      #6b1a52;  --cat-system-border:    #e8b8d8;
```

### 1.3 字体规范

```css
/* 正文字体栈 (Sans-serif) — DM Sans */
font-family: "DM Sans", -apple-system, "PingFang SC",
             "Noto Sans CJK SC", "Helvetica Neue", sans-serif;

/* 标题字体栈 (Serif — DM Serif Display) */
font-family: "DM Serif Display", "Noto Serif SC",
             "Source Han Serif SC", Georgia, serif;

/* 等宽字体栈 (Monospace — JetBrains Mono) */
font-family: "JetBrains Mono", Consolas, "Liberation Mono",
             Menlo, Courier, monospace;
```

| 元素 | 字号 | 字重 | 行高 | 字距 | 字体 | 颜色 |
|------|------|------|------|------|------|------|
| H1 Hero | clamp(36px,5vw,64px) | 400 | 1.1 | -0.02em | Serif | --text-primary |
| H2 Modal Title | 26px | 400 | 1.2 | — | Serif | --text-primary |
| Body | 15px | 400 | 1.6 | — | Sans | --text-secondary |
| Card Title | 14px | 600 | 1.35 | — | Sans | --text-primary |
| Card Desc | 12.5px | 400 | 1.55 | — | Sans | --text-secondary |
| Button | 13px | 400 | — | — | Sans | varies |
| Label / Tag | 10px | 500 | — | 0.04em | Mono | category color |
| Caption | 11px | 500 | — | 0.04em | Mono | --text-muted |
| Site Domain | 13px | 500 | — | 0.04em | Mono | --text-secondary |

**Tailwind 映射**

```
H1:          text-[clamp(36px,5vw,64px)] font-normal leading-[1.1] tracking-tight (serif)
H2:          text-[26px] font-normal leading-[1.2] (serif)
Body:        text-[15px] font-normal leading-relaxed text-[#6b6660]
Card Title:  text-sm font-semibold text-[#1a1916]
Card Desc:   text-[12.5px] font-normal text-[#6b6660] leading-[1.55]
Button:      text-[13px] font-normal
Label/Tag:   text-[10px] font-medium tracking-wide font-mono uppercase
Caption:     text-[11px] font-medium tracking-wide font-mono text-[#9b9590]
```

---

## 二、布局系统

### 2.1 页面结构

```
┌──────────────────────────────────────────────────────┐
│ [Header]  max-width: 1600px                          │
│  ┌─────────────────────┬────────────────────────┐    │
│  │ 域名标识 + H1 大标题 │  引用 (右列，移动端隐藏) │    │
│  │ + 描述文字           │                        │    │
│  └─────────────────────┴────────────────────────┘    │
├──────────────────────────────────────────────────────┤
│ [Controls]  sticky 筛选栏                             │
│  🔍 搜索框 · 分类筛选按钮 · ⭐ 收藏 · 数量计数        │
├──────────────────────────────────────────────────────┤
│                                                      │
│ [Grid]  auto-fill, minmax(240px, 1fr)                │
│  ┌──────┬──────┬──────┬──────┬──────┐               │
│  │ Card │ Card │ Card │ Card │ Card │               │
│  ├──────┼──────┼──────┼──────┼──────┤               │
│  │ Card │ Card │ Card │ Card │ Card │  1px 网格间距  │
│  ├──────┼──────┼──────┼──────┼──────┤               │
│  │ Card │ Card │ Card │ ...  │      │               │
│  └──────┴──────┴──────┴──────┴──────┘               │
│                                                      │
├──────────────────────────────────────────────────────┤
│ [Footer]  版权 · 链接                                 │
└──────────────────────────────────────────────────────┘
```

### 2.2 容器与间距

```css
/* 主容器 */
.container {
  max-width: 1600px;
  margin: 0 auto;
}

/* Header */
.header {
  padding: 64px 48px 48px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
}

/* 筛选栏（Sticky） */
.controls {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 28px 48px;
  background: var(--bg-page);
  border-bottom: 1px solid var(--border-default);
}

/* 网格区域 */
.grid-container {
  padding: 32px 48px 64px;
}

/* 卡片网格 */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1px;                   /* 1px 间距 = 视觉边框线 */
  background: var(--border-default); /* 间隙底色 = 网格线 */
  border: 1px solid var(--border-default);
}

/* 间距体系 */
--space-xs:    4px;
--space-sm:    8px;
--space-md:    14px;
--space-lg:    24px;
--space-xl:    32px;
--space-2xl:   48px;
--space-3xl:   64px;
```

### 2.3 响应式断点

```css
@media (max-width: 1100px) { /* 侧栏隐藏部分内容 */ }
@media (max-width: 900px)  { /* Header 变单列，Quote 隐藏 */ }
@media (max-width: 768px)  { /* 模态导航按钮隐藏 */ }
@media (max-width: 600px)  { /* 移动端：Header/Grid 间距缩小，Modal meta 隐藏 */ }
```

---

## 三、组件库

### 3.1 筛选按钮（Filter Button）

```tsx
{/* 默认态 */}
<button className="
  px-3.5 py-1.5 rounded-full
  bg-white text-[#6b6660] text-[13px]
  border border-[#d4cfc8]
  cursor-pointer
  transition-all duration-150
  hover:bg-[#f8f7f4] hover:text-[#1a1916]
">
  Discovery
</button>

{/* 选中态 */}
<button className="
  px-3.5 py-1.5 rounded-full
  bg-[#1a1916] text-white text-[13px]
  border border-[#1a1916]
  cursor-pointer
">
  Discovery
</button>
```

### 3.2 收藏筛选按钮

```tsx
<button className="
  px-3.5 py-1.5 rounded-full
  bg-[#fdf8ec] text-[#9a7210] text-[13px]
  border border-[#e8c870]
  cursor-pointer
  transition-all duration-150
  hover:bg-[#5a4a10] hover:text-white
">
  ⭐ Favorites
</button>
```

### 3.3 搜索框（Search Input）

```tsx
<div className="relative">
  {/* 搜索图标 */}
  <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#9b9590]" />

  <input
    type="text"
    placeholder="Search frameworks..."
    className="
      w-full h-[33px]
      pl-9 pr-3.5
      bg-white text-[#1a1916] text-[13px]
      border border-[#d4cfc8] rounded-md
      placeholder:text-[#9b9590]
      focus:outline-none focus:border-[#1a1916]
      transition-colors duration-150
      font-[DM_Sans]
    "
  />
</div>
```

### 3.4 网格卡片（Grid Card）

```tsx
<div className="
  bg-white p-[22px_24px]
  border-r border-b border-[#e8e4de]
  cursor-pointer
  transition-colors duration-[120ms]
  hover:bg-[#f8f7f4]
  flex flex-col gap-2
  relative overflow-hidden
">
  {/* 编号 */}
  <span className="text-[10px] font-mono text-[#9b9590]">001</span>

  {/* 标题 */}
  <h3 className="text-sm font-semibold text-[#1a1916] leading-[1.35]">
    User Interview Script
  </h3>

  {/* 分类标签 */}
  <span className="
    inline-block self-start
    text-[10px] font-medium font-mono tracking-wide
    px-2 py-0.5 rounded-[3px]
    bg-[#e8f5ee] text-[#1a5c38]
  ">
    DISCOVERY
  </span>

  {/* 描述 */}
  <p className="text-[12.5px] text-[#6b6660] leading-[1.55]">
    A structured guide to conducting effective user interviews...
  </p>

  {/* Ghost 装饰元素（右下角） */}
  <div className="
    absolute -bottom-2 -right-2
    w-[100px] h-[100px]
    opacity-[0.07] group-hover:opacity-[0.13]
    transition-opacity duration-300
    text-[#9b9590]
  ">
    {/* SVG 图标 */}
  </div>

  {/* 收藏标记（可选） */}
  <span className="absolute top-2 right-2 text-sm text-[#e8a820]">★</span>
</div>
```

### 3.5 Header 区域

```tsx
<header className="max-w-[1600px] mx-auto px-12 pt-16 pb-12">
  <div className="grid grid-cols-2 gap-12">
    {/* 左列 */}
    <div>
      {/* 域名标识 */}
      <span className="
        text-[13px] font-mono font-medium tracking-wide text-[#6b6660]
      ">
        pmframe.works — <span className="text-[#1a7a4a]">PMF</span>rameworks
      </span>

      {/* 大标题 */}
      <h1
        className="mt-4 text-[clamp(36px,5vw,64px)] font-normal leading-[1.1] tracking-tight text-[#1a1916]"
        style={{ fontFamily: '"DM Serif Display", "Noto Serif SC", serif' }}
      >
        Product Frameworks
      </h1>

      {/* 描述 */}
      <p className="mt-4 text-[15px] text-[#6b6660] leading-relaxed max-w-lg">
        A curated collection of essential frameworks...
      </p>
    </div>

    {/* 右列 — 引用 */}
    <div className="flex items-end">
      <blockquote className="
        pl-6 py-5 border-l-2 border-[#d4cfc8]
        max-w-xs
      ">
        <p className="text-[15px] text-[#6b6660] leading-relaxed italic">
          "If you can not measure it, you can not improve it."
        </p>
        <cite className="block mt-2 text-[11px] font-mono text-[#9b9590] not-italic tracking-wide">
          — Peter Drucker
        </cite>
      </blockquote>
    </div>
  </div>
</header>
```

### 3.6 模态详情弹窗（Modal）

```tsx
{/* 遮罩 */}
<div className="
  fixed inset-0 z-[100]
  bg-[rgba(26,25,22,0.5)] backdrop-blur-[4px]
  flex items-center justify-center
  p-6
">
  {/* 弹窗容器 */}
  <div className="
    w-full max-w-[640px] h-[560px]
    bg-white border border-[#d4cfc8] rounded-xl
    flex flex-col
    animate-[slideUp_0.2s_ease]
    overflow-hidden
  ">
    {/* Hero 区域（分类色彩背景） */}
    <div className="
      px-10 py-14 rounded-t-xl
      bg-[#e8f5ee]   /* ← 按分类变化 */
      relative flex items-center justify-center
    ">
      {/* 分类 Pill */}
      <span className="
        absolute top-5 left-5
        text-[10px] font-mono tracking-widest
        bg-white/70 px-2.5 py-1 rounded
      ">
        DISCOVERY
      </span>

      {/* 关闭按钮 */}
      <button className="
        absolute top-5 right-5
        text-[13px] font-mono text-[#9b9590]
        bg-white/70 px-2.5 py-1 rounded
        hover:bg-white/95 hover:text-[#1a1916]
        transition-colors duration-150
      ">
        ESC
      </button>

      {/* 标题 */}
      <h2
        className="text-[26px] font-normal leading-[1.2] text-[#1a1916] text-center"
        style={{ fontFamily: '"DM Serif Display", serif' }}
      >
        User Interview Script
      </h2>
    </div>

    {/* 内容 + 侧边元信息（黄金比例分割） */}
    <div className="flex flex-1 overflow-hidden">
      {/* 主内容 */}
      <div className="flex-[1.618] px-8 py-7 overflow-y-auto">
        <p className="text-[15px] text-[#6b6660] leading-relaxed">
          Framework description...
        </p>
        <a className="
          inline-block mt-6
          bg-[#1a1916] text-white text-[13px] font-medium
          px-6 py-2.5 rounded-lg
          hover:opacity-[0.85]
          transition-opacity duration-150
        ">
          Learn More →
        </a>
      </div>

      {/* Meta 侧边栏 */}
      <div className="
        flex-1 px-6 py-7
        bg-[#f8f7f4] border-l border-[#e8e4de]
        rounded-br-xl overflow-y-auto
      ">
        <p className="text-[10px] font-mono tracking-widest text-[#9b9590] uppercase mb-3">
          Details
        </p>
        <dl className="space-y-3 text-[12.5px] text-[#6b6660]">
          <div>
            <dt className="text-[10px] font-mono text-[#9b9590] uppercase tracking-wide">Category</dt>
            <dd className="mt-0.5">Discovery</dd>
          </div>
          <div>
            <dt className="text-[10px] font-mono text-[#9b9590] uppercase tracking-wide">Difficulty</dt>
            <dd className="mt-0.5">Beginner</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>

  {/* 左右导航按钮 */}
  <button className="
    absolute left-2 w-10 h-10 rounded-full
    bg-white/15 text-white/80 text-[22px]
    border border-white/30
    hover:bg-white/30 hover:text-white
    transition-all duration-150
  ">‹</button>
  <button className="
    absolute right-2 w-10 h-10 rounded-full
    bg-white/15 text-white/80 text-[22px]
    border border-white/30
    hover:bg-white/30 hover:text-white
    transition-all duration-150
  ">›</button>
</div>
```

### 3.7 Footer

```tsx
<footer className="px-12 py-8 border-t border-[#e8e4de]">
  <div className="max-w-[1600px] mx-auto flex items-center justify-between">
    <span className="text-[11px] font-mono text-[#9b9590] tracking-wide">
      © 2026 PMFrame.works
    </span>
    <div className="flex gap-4 text-[11px] font-mono text-[#9b9590]">
      <a className="hover:text-[#1a1916] transition-colors duration-150">About</a>
      <a className="hover:text-[#1a1916] transition-colors duration-150">GitHub</a>
    </div>
  </div>
</footer>
```

---

## 四、动效与特效系统

### 4.1 动画关键帧

```css
/* 模态滑入 */
@keyframes slideUp {
  0%   { opacity: 0; transform: translateY(16px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* PMF 品牌彩虹渐变 */
@keyframes pmf-gradient {
  0%   { background-position: 0% center; }
  100% { background-position: 200% center; }
}

/* 提示淡入淡出 */
@keyframes hintFade {
  0%   { opacity: 0; }
  15%  { opacity: 1; }
  70%  { opacity: 1; }
  100% { opacity: 0; }
}
```

### 4.2 过渡系统

```css
/* 默认过渡 */
transition: all 0.15s ease;

/* 卡片过渡 */
transition: background-color 0.12s ease;

/* 标签/按钮过渡 */
transition: all 0.15s ease;

/* Ghost 装饰元素 */
transition: opacity 0.3s ease;
```

### 4.3 PMF 品牌 Hover 彩虹效果

```tsx
<span className="
  relative inline-block
  hover:animate-[pmf-gradient_2s_linear_infinite]
  hover:bg-clip-text hover:text-transparent
  hover:scale-[1.08] hover:tracking-widest
  transition-all duration-300
"
  style={{
    backgroundImage: 'linear-gradient(90deg, #1a7a4a, #2a9d5c, #f5a623, #e8734a, #d94f8c, #7b61ff, #1a7a4a)',
    backgroundSize: '200%',
  }}
>
  PMF
</span>
```

---

## 五、设计决策速查表

| 决策项 | 选择 | 说明 |
|--------|------|------|
| 主色调 | 暖白极简 Warm Minimal | 纯白底 `#ffffff` + 暖灰面 `#f8f7f4` + 深棕字 `#1a1916` |
| 标题字体 | DM Serif Display | 优雅衬线，H1 font-weight 400（轻盈大气） |
| 正文字体 | DM Sans | 干净圆润，现代无衬线 |
| 等宽字体 | JetBrains Mono | 标签、编号、元信息使用 |
| 页面布局 | 全幅网格卡片 | max-width 1600px，auto-fill 240px 列 |
| 卡片风格 | 无阴影 · 1px 网格线 | gap: 1px + 背景色 = 视觉网格线 |
| 分类标签 | 7 组色彩 | 每组含 bg/text/border 三色，语义清晰 |
| 模态布局 | 黄金比例 1.618 : 1 | 内容区 flex 1.618 + Meta 区 flex 1 |
| 圆角 | 3-12px 分层 | 标签 3px，按钮 full，输入框 6px，模态 12px |
| 动效 | 极简 120-150ms | 仅颜色/透明度过渡，无弹性曲线 |
| 阴影 | 无阴影 | 纯粹边框 + 背景色区分层次 |
| 文字层次 | 3 级 | 主文字 `#1a1916` → 次要 `#6b6660` → 弱化 `#9b9590` |
| 按钮风格 | 胶囊 pill | 深底白字 / 白底灰字，border-radius: 100px |
| 遮罩 | 半透明 + blur | `rgba(26,25,22,0.5)` + backdrop-blur 4px |

---

## 六、Tailwind 自定义配置

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  theme: {
    extend: {
      colors: {
        pmf: {
          bg:          "#ffffff",
          surface:     "#f8f7f4",
          surface2:    "#f0ede8",
          text:        "#1a1916",
          "text-sec":  "#6b6660",
          muted:       "#9b9590",
          border:      "#e8e4de",
          "border-dk": "#d4cfc8",
          green:       "#1a7a4a",
          fav:         "#e8a820",
          "fav-bg":    "#fdf8ec",
        },
        // 分类色
        "cat-discovery":  { bg: "#e8f5ee", text: "#1a5c38", border: "#b8dfc8" },
        "cat-define":     { bg: "#e8eef8", text: "#1a3a6b", border: "#b8cce8" },
        "cat-ideation":   { bg: "#fdf3e3", text: "#7a4a0a", border: "#f0d4a0" },
        "cat-validation": { bg: "#fce8e8", text: "#7a1a1a", border: "#f0b8b8" },
        "cat-execution":  { bg: "#ede8f8", text: "#3a1a6b", border: "#c8b8e8" },
        "cat-growth":     { bg: "#e8f8e8", text: "#1a5a1a", border: "#b8dbb8" },
        "cat-system":     { bg: "#f8e8f3", text: "#6b1a52", border: "#e8b8d8" },
      },
      fontFamily: {
        serif: [
          "DM Serif Display", "Noto Serif SC",
          "Source Han Serif SC", "Georgia", "serif",
        ],
        sans: [
          "DM Sans", "-apple-system", "PingFang SC",
          "Noto Sans CJK SC", "Helvetica Neue", "sans-serif",
        ],
        mono: [
          "JetBrains Mono", "Consolas",
          "Liberation Mono", "Menlo", "monospace",
        ],
      },
      maxWidth: {
        container: "1600px",
        modal:     "640px",
      },
      borderRadius: {
        tag:   "3px",
        modal: "12px",
      },
      keyframes: {
        slideUp: {
          "0%":   { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "slide-up": "slideUp 0.2s ease",
      },
    },
  },
};

export default config;
```

---

## 七、快速启动模板

### 完整页面骨架

```tsx
export default function PMFrameLayout() {
  const categories = [
    { id: "discovery",  label: "Discovery",  bg: "#e8f5ee", text: "#1a5c38" },
    { id: "define",     label: "Define",     bg: "#e8eef8", text: "#1a3a6b" },
    { id: "ideation",   label: "Ideation",   bg: "#fdf3e3", text: "#7a4a0a" },
    { id: "validation", label: "Validation", bg: "#fce8e8", text: "#7a1a1a" },
    { id: "execution",  label: "Execution",  bg: "#ede8f8", text: "#3a1a6b" },
    { id: "growth",     label: "Growth",     bg: "#e8f8e8", text: "#1a5a1a" },
    { id: "system",     label: "System",     bg: "#f8e8f3", text: "#6b1a52" },
  ];

  return (
    <div className="min-h-screen bg-pmf-bg text-pmf-text font-sans">

      {/* Header */}
      <header className="max-w-container mx-auto px-12 pt-16 pb-12 grid grid-cols-2 gap-12">
        <div>
          <span className="text-[13px] font-mono font-medium tracking-wide text-pmf-text-sec">
            pmframe.works — <span className="text-pmf-green font-medium">PMF</span>rameworks
          </span>
          <h1
            className="mt-4 text-[clamp(36px,5vw,64px)] font-normal leading-[1.1] tracking-tight"
            style={{ fontFamily: '"DM Serif Display", serif' }}
          >
            Product Frameworks
          </h1>
          <p className="mt-4 text-[15px] text-pmf-text-sec leading-relaxed max-w-lg">
            A curated collection of essential frameworks for product managers.
          </p>
        </div>
        <div className="flex items-end max-md:hidden">
          <blockquote className="pl-6 py-5 border-l-2 border-pmf-border-dk max-w-xs">
            <p className="text-[15px] text-pmf-text-sec leading-relaxed italic">
              "If you can not measure it, you can not improve it."
            </p>
            <cite className="block mt-2 text-[11px] font-mono text-pmf-muted not-italic tracking-wide">
              — Peter Drucker
            </cite>
          </blockquote>
        </div>
      </header>

      {/* Controls */}
      <div className="sticky top-0 z-10 bg-pmf-bg border-b border-pmf-border px-12 py-7 flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative mr-3">
          <input
            placeholder="Search frameworks..."
            className="h-[33px] pl-9 pr-3.5 bg-white text-[13px] border border-pmf-border-dk rounded-md placeholder:text-pmf-muted focus:outline-none focus:border-pmf-text"
          />
        </div>
        {/* Filters */}
        {categories.map(cat => (
          <button key={cat.id} className="px-3.5 py-1.5 rounded-full text-[13px] bg-white text-pmf-text-sec border border-pmf-border-dk hover:bg-pmf-surface hover:text-pmf-text transition-all duration-150">
            {cat.label}
          </button>
        ))}
        <button className="px-3.5 py-1.5 rounded-full text-[13px] bg-pmf-fav-bg text-[#9a7210] border border-[#e8c870] transition-all duration-150">
          ⭐ Favorites
        </button>
        {/* Count */}
        <span className="ml-auto text-[11px] font-mono text-pmf-muted tracking-wide">
          127 frameworks
        </span>
      </div>

      {/* Grid */}
      <div className="max-w-container mx-auto px-12 py-8 pb-16">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-px bg-pmf-border border border-pmf-border">
          {[1,2,3,4,5,6].map(n => (
            <div key={n} className="bg-white p-[22px_24px] cursor-pointer transition-colors duration-[120ms] hover:bg-pmf-surface flex flex-col gap-2 relative overflow-hidden group">
              <span className="text-[10px] font-mono text-pmf-muted">{String(n).padStart(3,"0")}</span>
              <h3 className="text-sm font-semibold leading-[1.35]">Framework Title</h3>
              <span className="inline-block self-start text-[10px] font-medium font-mono tracking-wide px-2 py-0.5 rounded-[3px] bg-[#e8f5ee] text-[#1a5c38]">
                DISCOVERY
              </span>
              <p className="text-[12.5px] text-pmf-text-sec leading-[1.55]">
                Brief description of what this framework does...
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="px-12 py-8 border-t border-pmf-border">
        <div className="max-w-container mx-auto flex items-center justify-between">
          <span className="text-[11px] font-mono text-pmf-muted tracking-wide">
            © 2026 PMFrame.works
          </span>
          <div className="flex gap-4 text-[11px] font-mono text-pmf-muted">
            <a className="hover:text-pmf-text transition-colors duration-150">About</a>
            <a className="hover:text-pmf-text transition-colors duration-150">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
```
