---
name: pola-wukong-ui
description: "钉钉悟空官网暗金高端 UI 设计系统，深色背景 + 金色点缀 + 玻璃拟态风格，适用于 AI 产品官网、SaaS Landing Page、品牌展示站"
user-invocable: true
triggers:
  - pattern: "/wukongui|/悟空UI|/暗金UI|/高端官网|/landing|/品牌站|悟空风格|金色主题|Dark Gold UI"
---

# PolaWukongUI — 钉钉悟空暗金高端设计系统

> **参考来源**：https://wukong.dingtalk.com/
> **适用场景**：AI 产品官网、SaaS Landing Page、品牌展示站、产品介绍页、下载页
> **技术栈**：Next.js + TailwindCSS + shadcn/ui
> **风格标签**：Dark Premium · Gold Accent · Glass-morphism · Cinematic · Serif Headlines

---

## 一、设计语言核心原则

### 1.1 色彩系统

```css
/* ========== 背景层次 ========== */
--bg-deepest:     #050508;           /* rgb(5,5,8) 页面根背景，接近纯黑 */
--bg-nav:         rgba(5,5,8,0.75);  /* 导航栏半透明背景 */
--bg-card:        rgba(255,255,255,0.06); /* 卡片微透明白 */
--bg-card-hover:  rgba(255,255,255,0.12); /* 卡片 hover 态 */
--bg-gold-subtle: rgba(228,191,122,0.06); /* 极淡金色底色 */
--bg-gold-light:  rgba(228,191,122,0.10); /* 淡金色底色 */

/* ========== 金色主色系 ========== */
--gold-primary:   #E4BF7A;  /* rgb(228,191,122) 主金色 */
--gold-dark:      #D4A050;  /* rgb(212,160,80)  深金色 */
--gold-light:     #F0D8A8;  /* rgb(240,216,168) 浅金色 */
--gold-pale:      #F6E8C8;  /* rgb(246,232,200) 极浅金色 */
--gold-brown:     #6B4300;  /* rgb(107,67,0)    棕金色（金底文字） */
--gold-brown-deep:#5C3800;  /* rgb(92,56,0)     深棕色 */

/* ========== 文字色阶 ========== */
--text-primary:    rgba(255,255,255,1.0);   /* 标题、核心文本 */
--text-secondary:  rgba(255,255,255,0.80);  /* 次要文本 */
--text-body:       rgba(255,255,255,0.65);  /* 正文描述 */
--text-muted:      rgba(255,255,255,0.45);  /* 弱化文本 */
--text-disabled:   rgba(255,255,255,0.38);  /* 禁用态 */
--text-ghost:      rgba(255,255,255,0.12);  /* 极弱/分隔线 */

/* ========== 辅助强调色 ========== */
--accent-blue:     #4FA8FE;  /* rgb(79,168,254)  蓝色点缀 */
--accent-charcoal: #1A1A1A;  /* rgb(26,26,26)    深灰层 */
```

### 1.2 渐变系统

```css
/* 主按钮金色渐变 */
--gradient-gold-btn: linear-gradient(135deg, #E4BF7A, #D4A050);

/* 徽章渐变 */
--gradient-gold-badge: linear-gradient(135deg, #F6E8C8, #E4BF7A);

/* 卡片金色渐变（半透明） */
--gradient-gold-card: linear-gradient(135deg,
  rgba(228,191,122,0.20),
  rgba(240,216,168,0.12)
);

/* Hero 遮罩渐变（视频叠加） */
--gradient-hero-overlay: linear-gradient(
  to bottom,
  rgba(5,5,8,0.55) 0%,
  rgba(5,5,8,0.35) 40%,
  rgba(5,5,8,0.60) 80%,
  rgba(5,5,8,0.95) 100%
);

/* Hero 金色光晕（径向） */
--gradient-hero-glow: radial-gradient(
  circle,
  rgba(228,191,122,0.08) 0%,
  rgba(0,0,0,0) 70%
);
```

### 1.3 字体规范

```css
/* 正文字体栈 (Sans-serif) */
font-family: -apple-system, "system-ui", "PingFang SC", "Hiragino Sans GB",
             "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC",
             "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

/* 标题字体栈 (Serif - 宋体系) */
font-family: "Source Han Serif SC", "Source Han Serif CN",
             "思源宋体 SC", "Songti SC", STSong, serif;

/* 英文展示字体 */
font-family: Syne, "Noto Sans SC", sans-serif;
```

| 元素 | 字号 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| H1 Hero | 84px | 800 | 1.05 | 首屏大标题 |
| H2 Section | 52px | 800 | 1.1 | 板块标题 |
| H3 Feature | 32px | 700 | 1.3 | 功能标题 |
| Body Large | 19px | 400 | 1.7 | 功能描述 |
| Body | 16px | 400 | 1.6 | 正文段落 |
| Button Large | 16px | 600 | — | 大按钮文字 |
| Button | 13px | 600 | — | 标准按钮 |
| Badge | 10px | 600 | — | 徽章/标签 |
| Caption | 12px | 400 | — | 辅助说明 |

**Tailwind 映射**

```
H1:         text-7xl font-extrabold (serif font)
H2:         text-5xl font-extrabold (serif font)
H3:         text-3xl font-bold
Body Large: text-lg font-normal text-white/65
Body:       text-base font-normal text-white/65
Button Lg:  text-base font-semibold
Button:     text-sm font-semibold
Badge:      text-[10px] font-semibold
```

---

## 二、布局系统

### 2.1 容器与间距

```css
/* 内容容器 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 间距基准：8px */
--space-xs:   2px;
--space-sm:   6px;
--space-md:   8px;
--space-lg:   12px;
--space-xl:   14px;
--space-2xl:  16px;
--space-3xl:  24px;
--space-4xl:  36px;
--space-hero-top: 128px;
--space-hero-bottom: 200px;
```

### 2.2 页面结构

```
┌──────────────────────────────────────────┐
│ [Nav]  Logo  ·  Links  ·  CTA  ·  Lang  │  固定导航 64px
├──────────────────────────────────────────┤
│                                          │
│          [Hero] 视频背景 + 遮罩           │  100vh (1040px)
│     H1 大标题 (Serif 84px)               │
│     副标题 (19px 65%白)                   │
│     CTA 卡片组                           │
│                                          │
├──────────────────────────────────────────┤
│                                          │
│     [Features] 编号功能区                 │  交替布局
│     01/02/03/04  图+文 两栏交替           │
│                                          │
├──────────────────────────────────────────┤
│                                          │
│     [Use Cases] 应用场景轮播              │  Carousel
│     04/09 分页 + 标签                    │
│                                          │
├──────────────────────────────────────────┤
│                                          │
│     [Mission/Vision] 使命愿景双栏         │  2-col Grid
│                                          │
├──────────────────────────────────────────┤
│                                          │
│     [CTA] 终极行动召唤                    │
│     "准备好了吗？" + 下载按钮             │
│                                          │
├──────────────────────────────────────────┤
│ [Footer]  版权 · 备案 · 合规链接          │
└──────────────────────────────────────────┘
```

### 2.3 栅格与 Flex

```css
/* 两栏交替布局 */
.feature-row {
  display: flex;
  align-items: center;
  gap: 36px;
}
.feature-row:nth-child(even) { flex-direction: row-reverse; }

/* 双栏网格 */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 36px;
}

/* 卡片列表 */
.card-list {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
```

---

## 三、组件库

### 3.1 按钮（Button）

#### 主按钮 — 金色渐变

```tsx
<button className="
  bg-gradient-to-br from-[#E4BF7A] to-[#D4A050]
  text-[#6B4300] font-semibold text-sm
  px-[18px] py-2 rounded-[10px]
  border-none cursor-pointer
  transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
  hover:shadow-[0_4px_16px_rgba(228,191,122,0.3)]
  hover:-translate-y-0.5
">
  下载悟空
</button>
```

#### 大按钮 — CTA

```tsx
<button className="
  bg-gradient-to-br from-[#E4BF7A] to-[#D4A050]
  text-[#6B4300] font-semibold text-base
  px-9 py-4 rounded-2xl
  hover:shadow-[0_8px_24px_rgba(228,191,122,0.35)]
  hover:-translate-y-1
  transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
">
  立即下载
</button>
```

#### 语言切换按钮

```tsx
<button className="
  px-3.5 py-1.5 rounded-lg text-xs
  bg-transparent text-white/38 border-none
  transition-all duration-300
  data-[active=true]:bg-white/12
  data-[active=true]:text-white
">
  中
</button>
```

### 3.2 导航栏（Navigation）

```tsx
<nav className="
  fixed top-0 w-full z-50
  bg-[rgba(5,5,8,0.75)] backdrop-blur-md
  px-6 h-16 flex items-center justify-between
">
  {/* Logo */}
  <div className="flex items-center gap-3">
    <img src="/logo.svg" className="h-8" />
  </div>

  {/* Links */}
  <div className="flex items-center gap-8">
    <a className="text-white text-base hover:text-[#E4BF7A] transition-colors duration-300">
      产品优势
    </a>
  </div>

  {/* Actions */}
  <div className="flex items-center gap-3">
    {/* Language Toggle */}
    {/* Download Button */}
  </div>
</nav>
```

### 3.3 Hero 区域

```tsx
<section className="
  relative min-h-screen flex flex-col items-center justify-center
  pt-32 pb-[200px] px-6
  overflow-hidden
">
  {/* 视频背景 */}
  <video autoPlay muted loop playsInline
    className="absolute inset-0 w-full h-full object-cover"
    src="/hero-bg.mp4"
  />

  {/* 暗色遮罩 */}
  <div className="absolute inset-0 bg-gradient-to-b
    from-[rgba(5,5,8,0.55)] via-[rgba(5,5,8,0.35)] to-[rgba(5,5,8,0.95)]"
  />

  {/* 金色光晕 */}
  <div className="absolute inset-0 opacity-70"
    style={{ background: 'radial-gradient(circle, rgba(228,191,122,0.08) 0%, transparent 70%)' }}
  />

  {/* 内容 */}
  <div className="relative z-10 text-center max-w-4xl">
    <h1 className="text-7xl font-extrabold text-white leading-tight"
      style={{ fontFamily: '"Source Han Serif SC", serif' }}>
      说句话 悟空帮你搞定
    </h1>
    <p className="mt-6 text-lg text-white/65 max-w-2xl mx-auto">
      悟空是钉钉推出的 AI 智能体工作平台...
    </p>
  </div>
</section>
```

### 3.4 卡片（Card）

#### 金色边框卡片（Glass-morphism）

```tsx
<div className="
  border border-[rgba(212,160,80,0.35)]
  bg-gradient-to-br from-[rgba(228,191,122,0.20)] to-[rgba(240,216,168,0.12)]
  rounded-[10px] p-4
  shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_8px_24px_rgba(228,191,122,0.16)]
  transition-all duration-300
  hover:-translate-y-1
  hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_12px_32px_rgba(228,191,122,0.25)]
">
  <h3 className="text-white font-bold text-lg">标题</h3>
  <p className="text-white/65 text-base mt-2">描述文本...</p>
</div>
```

#### 功能编号卡片

```tsx
<div className="flex items-start gap-6">
  {/* 编号 */}
  <span className="text-5xl font-extrabold text-[#E4BF7A] font-mono opacity-80">
    01
  </span>
  {/* 内容 */}
  <div>
    <h3 className="text-2xl font-bold text-white">身外化身</h3>
    <p className="text-lg text-white/65 mt-3 leading-relaxed">
      对话即行动，说句话悟空帮你搞定...
    </p>
  </div>
</div>
```

### 3.5 徽章（Badge）

```tsx
<span className="
  inline-block
  bg-gradient-to-br from-[#F6E8C8] to-[#E4BF7A]
  text-[#6B4300] text-[10px] font-semibold
  px-2 py-0.5 rounded-lg
  shadow-[inset_0_1px_0_rgba(255,255,255,0.45),0_4px_10px_rgba(212,160,80,0.18)]
">
  NEW
</span>
```

### 3.6 分区标题（Section Header）

```tsx
<div className="text-center mb-16">
  <h2 className="text-5xl font-extrabold text-white"
    style={{ fontFamily: '"Source Han Serif SC", serif' }}>
    为什么选择悟空
  </h2>
  <p className="mt-4 text-lg text-white/65 max-w-xl mx-auto">
    基于通义大模型，深度融合钉钉生态
  </p>
</div>
```

### 3.7 使命愿景双栏

```tsx
<div className="grid grid-cols-2 gap-9">
  <div>
    <p className="text-sm text-[#E4BF7A] font-semibold tracking-widest uppercase mb-4">
      使命 MISSION
    </p>
    <h3 className="text-3xl font-bold text-white leading-snug">
      让每个人都拥有 AI 工作搭档
    </h3>
    <p className="mt-4 text-lg text-white/65 leading-relaxed">
      描述文本...
    </p>
  </div>
  <div>
    <p className="text-sm text-[#E4BF7A] font-semibold tracking-widest uppercase mb-4">
      愿景 VISION
    </p>
    <h3 className="text-3xl font-bold text-white leading-snug">
      重新定义钉钉上的工作方式
    </h3>
    <p className="mt-4 text-lg text-white/65 leading-relaxed">
      描述文本...
    </p>
  </div>
</div>
```

### 3.8 CTA 终极行动召唤

```tsx
<section className="py-32 text-center">
  <h2 className="text-5xl font-extrabold text-white"
    style={{ fontFamily: '"Source Han Serif SC", serif' }}>
    准备好了吗？
  </h2>
  <p className="mt-6 text-lg text-white/65 max-w-xl mx-auto leading-relaxed">
    不是替代团队，而是让每个人拥有团队级别的能力。
    这是悟空正在实现的未来。
  </p>
  <button className="
    mt-10 bg-gradient-to-br from-[#E4BF7A] to-[#D4A050]
    text-[#6B4300] font-semibold text-base
    px-9 py-4 rounded-2xl
    hover:shadow-[0_8px_24px_rgba(228,191,122,0.35)]
    hover:-translate-y-1
    transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
  ">
    下载悟空
  </button>
</section>
```

### 3.9 Footer

```tsx
<footer className="border-t border-white/[0.06] py-8 px-6">
  <div className="max-w-[1200px] mx-auto flex items-center justify-between">
    <div className="flex items-center gap-3">
      <img src="/logo.svg" className="h-6 opacity-60" />
      <span className="text-white/45 text-sm">
        © 2026 钉钉悟空 · AI 工作平台
      </span>
    </div>
    <div className="flex items-center gap-4 text-white/38 text-xs">
      <a className="hover:text-white/65 transition-colors">隐私政策</a>
      <a className="hover:text-white/65 transition-colors">用户协议</a>
    </div>
  </div>
</footer>
```

---

## 四、阴影与特效系统

### 4.1 阴影 Tokens

```css
/* 卡片玻璃拟态阴影 */
--shadow-glass: inset 0 1px 0 rgba(255,255,255,0.35),
                0 8px 24px rgba(228,191,122,0.16);

/* 卡片 hover 加强 */
--shadow-glass-hover: inset 0 1px 0 rgba(255,255,255,0.35),
                      0 12px 32px rgba(228,191,122,0.25);

/* 徽章阴影 */
--shadow-badge: inset 0 1px 0 rgba(255,255,255,0.45),
                0 4px 10px rgba(212,160,80,0.18);

/* 下拉/弹出层阴影 */
--shadow-dropdown: 0 12px 40px rgba(0,0,0,0.25);

/* 按钮 hover 阴影 */
--shadow-btn-hover: 0 4px 16px rgba(228,191,122,0.30);

/* 大按钮 hover 阴影 */
--shadow-btn-lg-hover: 0 8px 24px rgba(228,191,122,0.35);
```

### 4.2 动效系统

```css
/* 主交互缓动 — 弹性感 */
--ease-primary: cubic-bezier(0.16, 1, 0.3, 1);
--duration-primary: 300ms;

/* 标准过渡 */
--ease-default: ease;
--duration-default: 300ms;

/* 快速微交互 */
--duration-fast: 200ms;
```

**Tailwind 映射**

```
transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]  /* 主缓动 */
transition-colors duration-300                                    /* 颜色过渡 */
transition-all duration-200                                       /* 快速微交互 */
```

### 4.3 悬浮效果模板

```tsx
{/* 卡片悬浮上浮 */}
className="hover:-translate-y-1 transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]"

{/* 按钮悬浮 */}
className="hover:-translate-y-0.5 hover:shadow-[0_4px_16px_rgba(228,191,122,0.3)]"

{/* 导航链接变金色 */}
className="hover:text-[#E4BF7A] transition-colors duration-300"
```

---

## 五、设计决策速查表

| 决策项 | 选择 | 说明 |
|--------|------|------|
| 主色调 | 暗金 Dark Gold | 近黑底 `#050508` + 金色点缀 `#E4BF7A` |
| 标题字体 | 宋体 Serif | Source Han Serif SC，增添高端文化感 |
| 正文字体 | 系统无衬线 | PingFang SC / system-ui |
| 按钮风格 | 金色渐变 135° | 棕金文字 `#6B4300`，圆角 10-16px |
| 卡片风格 | 玻璃拟态 | 半透明金色渐变底 + inset 白边 + 金色投影 |
| 间距基准 | 8px 倍数 | 24px 容器边距，36px 板块间距 |
| 动效 | Snappy弹性 | `cubic-bezier(0.16,1,0.3,1)` 300ms |
| 文字层次 | 5 级透明度 | 100% → 80% → 65% → 45% → 38% |
| 导航 | 固定半透明 | 75% 黑底 + backdrop-blur |
| 圆角 | 8-20px | 小组件 8px，按钮 10px，大按钮 16px，卡片 20px |

---

## 六、Tailwind 自定义配置

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  theme: {
    extend: {
      colors: {
        wukong: {
          bg:         "#050508",
          gold:       "#E4BF7A",
          "gold-dark":"#D4A050",
          "gold-light":"#F0D8A8",
          "gold-pale":"#F6E8C8",
          brown:      "#6B4300",
          "brown-deep":"#5C3800",
          blue:       "#4FA8FE",
          charcoal:   "#1A1A1A",
        },
      },
      fontFamily: {
        serif: [
          "Source Han Serif SC", "Source Han Serif CN",
          "思源宋体 SC", "Songti SC", "STSong", "serif",
        ],
        display: ["Syne", "Noto Sans SC", "sans-serif"],
      },
      borderRadius: {
        wk:    "10px",
        "wk-lg": "16px",
        "wk-xl": "20px",
      },
      boxShadow: {
        "wk-glass":
          "inset 0 1px 0 rgba(255,255,255,0.35), 0 8px 24px rgba(228,191,122,0.16)",
        "wk-glass-hover":
          "inset 0 1px 0 rgba(255,255,255,0.35), 0 12px 32px rgba(228,191,122,0.25)",
        "wk-badge":
          "inset 0 1px 0 rgba(255,255,255,0.45), 0 4px 10px rgba(212,160,80,0.18)",
        "wk-dropdown": "0 12px 40px rgba(0,0,0,0.25)",
        "wk-btn":  "0 4px 16px rgba(228,191,122,0.30)",
        "wk-btn-lg": "0 8px 24px rgba(228,191,122,0.35)",
      },
      transitionTimingFunction: {
        wukong: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      maxWidth: {
        container: "1200px",
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
export default function WukongLanding() {
  return (
    <div className="min-h-screen bg-wukong-bg text-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-wukong-bg/75 backdrop-blur-md h-16 px-6 flex items-center justify-between">
        <div className="font-bold text-xl">Logo</div>
        <div className="flex gap-8 text-base">
          <a className="hover:text-wukong-gold transition-colors duration-300">产品优势</a>
          <a className="hover:text-wukong-gold transition-colors duration-300">应用场景</a>
          <a className="hover:text-wukong-gold transition-colors duration-300">使命愿景</a>
        </div>
        <button className="bg-gradient-to-br from-wukong-gold to-wukong-gold-dark text-wukong-brown font-semibold text-sm px-[18px] py-2 rounded-wk">
          立即体验
        </button>
      </nav>

      {/* Hero */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-32 pb-[200px]">
        <div className="absolute inset-0 bg-gradient-to-b from-wukong-bg/55 via-wukong-bg/35 to-wukong-bg/95" />
        <div className="relative z-10 text-center max-w-4xl px-6">
          <h1 className="text-7xl font-extrabold font-serif leading-tight">
            您的产品标题
          </h1>
          <p className="mt-6 text-lg text-white/65 max-w-2xl mx-auto">
            一句话描述您的产品价值主张
          </p>
          <button className="mt-10 bg-gradient-to-br from-wukong-gold to-wukong-gold-dark text-wukong-brown font-semibold text-base px-9 py-4 rounded-wk-lg hover:shadow-wk-btn-lg hover:-translate-y-1 transition-all duration-300 ease-wukong">
            开始使用
          </button>
        </div>
      </section>

      {/* Features with Numbers */}
      <section className="max-w-container mx-auto px-6 py-24 space-y-24">
        {["01","02","03","04"].map((num, i) => (
          <div key={num} className={`flex items-center gap-9 ${i % 2 ? "flex-row-reverse" : ""}`}>
            <div className="flex-1 rounded-wk-xl overflow-hidden bg-white/[0.06] aspect-video" />
            <div className="flex-1">
              <span className="text-5xl font-extrabold text-wukong-gold font-mono opacity-80">{num}</span>
              <h3 className="text-2xl font-bold mt-4">功能标题</h3>
              <p className="text-lg text-white/65 mt-3 leading-relaxed">功能描述文本...</p>
            </div>
          </div>
        ))}
      </section>

      {/* CTA */}
      <section className="py-32 text-center">
        <h2 className="text-5xl font-extrabold font-serif">准备好了吗？</h2>
        <p className="mt-6 text-lg text-white/65 max-w-xl mx-auto">
          行动召唤描述文本
        </p>
        <button className="mt-10 bg-gradient-to-br from-wukong-gold to-wukong-gold-dark text-wukong-brown font-semibold text-base px-9 py-4 rounded-wk-lg hover:shadow-wk-btn-lg hover:-translate-y-1 transition-all duration-300 ease-wukong">
          立即开始
        </button>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-8 px-6">
        <div className="max-w-container mx-auto flex items-center justify-between text-white/45 text-sm">
          <span>© 2026 Your Brand</span>
          <div className="flex gap-4 text-xs text-white/38">
            <a className="hover:text-white/65 transition-colors">隐私政策</a>
            <a className="hover:text-white/65 transition-colors">用户协议</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
```
