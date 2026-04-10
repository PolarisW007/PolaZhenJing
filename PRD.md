# PolaZhenjing v2 — Personal Blog Wiki PRD
# PolaZhenjing v2 — 个人博客 Wiki 产品需求文档

## 1. Background & Motivation / 背景与动机

### Current State (v1) / 当前状态 (v1)

The current implementation is a full-stack application with significant complexity:

当前实现是一个复杂度较高的全栈应用：

| Metric / 指标 | Count / 数量 |
|--------|-------|
| Backend modules / 后端模块 | 7 (auth, thoughts, tags, research, ai, publish, sharing) |
| Database tables / 数据库表 | 5 (users, thoughts, tags, thought_tags, researches) |
| API endpoints / API 端点 | 25+ |
| Source files / 源文件 | ~65+ (Python + TypeScript) |
| External services / 外部服务 | PostgreSQL, OpenAI/Ollama, Tavily, Docker |
| Frontend pages / 前端页面 | 6 (Login, Register, Dashboard, ThoughtEditor, Settings, DeepResearch) |

**Problems / 问题：**
- Requires PostgreSQL + Docker for local development / 本地开发需要 PostgreSQL + Docker
- AI features require hard-to-configure external API keys / AI 功能需要难以配置的外部 API 密钥
- Over-complex auth (JWT + refresh tokens) for a personal tool / 对于个人工具来说认证过于复杂
- Deep Research SSE pipeline is fragile / 深度研究 SSE 管道脆弱
- Too many moving parts / 组件太多

### Desired State (v2) / 期望状态 (v2)

A **lightweight personal blog wiki** with multi-format article input (Markdown, PDF, Word, HTML), stylized HTML blog generation using **Jekyll**, simple authentication, and GitHub Pages publishing.

一个**轻量级个人博客 Wiki**，支持多格式文章输入（Markdown、PDF、Word、HTML），使用 **Jekyll** 生成风格化 HTML 博客，简单认证，发布到 GitHub Pages。

---

## 2. Core Requirements / 核心需求

### R1: Multi-Format Article Input / 多格式文章输入

Users can upload or write articles in multiple formats, which are automatically converted to blog-ready Markdown:

用户可以上传或编写多种格式的文章，系统自动转换为可发布的 Markdown：

| Format / 格式 | Input Method / 输入方式 | Conversion / 转换方式 |
|--------|--------|--------|
| **Markdown** (`.md`) | Direct write or upload / 直接编写或上传 | No conversion needed / 无需转换 |
| **PDF** (`.pdf`) | Upload via web UI / 通过 Web UI 上传 | `PyMuPDF` extracts text + images / 提取文本和图片 |
| **Word** (`.docx`) | Upload via web UI / 通过 Web UI 上传 | `python-docx` + `mammoth` extracts content / 提取内容 |
| **HTML** (`.html`) | Upload via web UI / 通过 Web UI 上传 | `html2text` converts to Markdown / 转换为 Markdown |

- Extracted images are saved to `_posts/assets/images/` automatically / 提取的图片自动保存到 `_posts/assets/images/`
- Each article gets YAML front matter generated automatically: / 每篇文章自动生成 YAML 前置元数据：
  ```yaml
  ---
  layout: post
  title: "Article Title / 文章标题"
  date: 2026-04-07
  tags: [AI, research]
  style: deep-technical
  description: "Brief description / 简要描述"
  ---
  ```

### R2: Blog Style Selection / 博文风格选择

Users select from **5 distinct blog post styles** before generation. Each style defines the HTML layout, typography, color scheme, and content presentation. Styles are inspired by a blend of top AI bloggers/influencers:

用户在生成前从 **5 种不同的博文风格** 中选择。每种风格定义了 HTML 布局、排版、配色和内容呈现方式。风格灵感来源于顶级 AI 博主/意见领袖的混合研究：

#### Style 1: 深度技术 / Deep Technical
- **Inspired by / 灵感来源**: Andrej Karpathy + 谢赛宁 (Saining Xie)
- **Characteristics / 特点**: Code-heavy with syntax highlighting, step-by-step technical walkthroughs, mathematical notation support, minimal decoration, monospace-friendly typography, dark-mode optimized / 代码密集带语法高亮，逐步技术解析，数学公式支持，极简装饰，等宽字体友好，深色模式优化
- **Best for / 适用于**: Technical tutorials, code walkthroughs, algorithm explanations / 技术教程、代码演练、算法解析
- **Visual tone / 视觉基调**: Clean, engineer-focused, GitHub README aesthetic / 简洁、工程师风格、GitHub README 美学

#### Style 2: 学术洞察 / Academic Insight
- **Inspired by / 灵感来源**: Yann LeCun + Fei-Fei Li + 谢赛宁
- **Characteristics / 特点**: Research paper-like structure with clear sections (Abstract, Introduction, Method, Results), citation-style references, balanced visuals and text, serif typography / 类研究论文结构，清晰分节（摘要、引言、方法、结果），引用式参考，视觉与文本平衡，衬线字体
- **Best for / 适用于**: Research summaries, paper reviews, academic discussions / 研究综述、论文评论、学术讨论
- **Visual tone / 视觉基调**: Scholarly, structured, journal-like / 学术、结构化、期刊风格

#### Style 3: 行业前瞻 / Industry Vision
- **Inspired by / 灵感来源**: Sam Altman + 李开复 (Kai-Fu Lee) + 陆奇 (Lu Qi) + Jensen Huang
- **Characteristics / 特点**: Bold headlines, strategic big-picture thinking, clean modern layout, pull-quotes, infographic-friendly sections, future-oriented language / 粗体标题，战略性宏观思维，现代简洁布局，引用语块，信息图友好，面向未来的语言风格
- **Best for / 适用于**: Industry trends, strategy posts, thought leadership / 行业趋势、战略分析、思想领导力
- **Visual tone / 视觉基调**: Executive, modern, magazine-cover feel / 高管风格、现代、杂志封面感

#### Style 4: 轻松科普 / Friendly Explainer
- **Inspired by / 灵感来源**: Andrew Ng + 宝玉 (Baoyu) + Elon Musk (accessibility)
- **Characteristics / 特点**: Storytelling tone, beginner-friendly language, generous whitespace, warm color palette, clear analogies, TL;DR summaries, curated insight boxes / 叙事风格，对初学者友好的语言，大量留白，温暖配色，清晰类比，TL;DR 摘要，精选洞察框
- **Best for / 适用于**: AI education, concept explanations, industry news curation / AI 教育、概念解释、行业新闻策展
- **Visual tone / 视觉基调**: Warm, approachable, textbook-like / 温暖、亲切、教科书风格

#### Style 5: 创意视觉 / Creative Visual
- **Inspired by / 灵感来源**: 歸藏 (Guizang) + 贾扬清 (Yangqing Jia)
- **Characteristics / 特点**: Image-first layout, gallery-style presentation, bold artistic typography, full-width hero images, card-based content sections, visual storytelling / 图片优先布局，画廊风格呈现，粗体艺术字体，全宽头图，卡片式内容区，视觉叙事
- **Best for / 适用于**: AI art showcases, visual demos, product launches, creative projects / AI 艺术展示、视觉演示、产品发布、创意项目
- **Visual tone / 视觉基调**: Artistic, bold, Instagram/portfolio-like / 艺术、大胆、Instagram/作品集风格

### R3: HTML Blog Generation / HTML 博客生成

The system analyzes the uploaded file content and converts it to a personal blog article in the selected style:

系统分析上传的文件内容，将其转换为所选风格的个人博客文章：

- Input file is parsed and converted to clean Markdown / 输入文件被解析并转换为干净的 Markdown
- Content is restructured to match blog article format (intro, sections, conclusion) / 内容被重新组织为博客文章格式（引言、正文分节、总结）
- Jekyll generates static HTML using the selected style's layout template / Jekyll 使用所选风格的布局模板生成静态 HTML
- Images are optimized and properly embedded / 图片被优化并正确嵌入
- Dark/light mode toggle / 深色/浅色模式切换
- Full-text search across all articles / 全文搜索所有文章
- Responsive design for mobile/desktop / 移动端/桌面端响应式设计
- Chinese language support / 中文语言支持

### R4: Simple Authentication / 简单认证

A lightweight personal auth system (single-user oriented):

轻量级个人认证系统（面向单用户）：

- **Register / 注册**: Username + password + QQ email verification / 用户名 + 密码 + QQ 邮箱验证
- **Login / 登录**: Username + password / 用户名 + 密码
- **Email verification / 邮箱验证**: Send verification code to QQ email via SMTP / 通过 SMTP 发送验证码到 QQ 邮箱
- **Password reset / 修改密码**: Authenticated password change / 已登录状态下修改密码
- **Storage / 存储**: SQLite (zero-config, file-based) / SQLite（零配置，基于文件）
- **Session / 会话**: Flask session with secure cookie / Flask 会话 + 安全 Cookie

### R5: GitHub Pages Publishing / GitHub Pages 发布

- One-command publish: `python wiki.py deploy` / 一键发布：`python wiki.py deploy`
- GitHub Actions CI/CD: auto-build and deploy on push to `main` / GitHub Actions CI/CD：推送到 `main` 分支时自动构建和部署
- Custom domain support via CNAME / 通过 CNAME 支持自定义域名

### R6: Simple Wiki Management / 简单 Wiki 管理

- Article list on homepage with title, date, description, tags, and style badge / 首页文章列表，含标题、日期、描述、标签和风格徽章
- Tag-based filtering/navigation / 基于标签的筛选/导航
- Chronological ordering (newest first) / 按时间倒序排列
- CLI tool (`wiki.py`) for power-user operations / CLI 工具（`wiki.py`）用于高级操作

---

## 3. Architecture / 架构

### Why Jekyll over MkDocs / 为什么选 Jekyll 而非 MkDocs

| Aspect / 方面 | Jekyll | MkDocs |
|--------|--------|--------|
| Blog support / 博客支持 | Native, first-class (`_posts/`) / 原生一等支持 | Plugin-based (blog plugin) / 基于插件 |
| Custom layouts / 自定义布局 | Full Liquid template system / 完整 Liquid 模板系统 | Limited Jinja2 overrides / 有限的 Jinja2 覆盖 |
| Theme ecosystem / 主题生态 | 1000+ blog themes / 1000+ 博客主题 | Mainly documentation themes / 主要是文档主题 |
| GitHub Pages / GitHub Pages | Native integration (built-in) / 原生集成（内置） | Requires separate deploy step / 需要额外部署步骤 |
| Multiple styles / 多风格支持 | Easy via multiple layouts / 通过多布局轻松实现 | Difficult / 困难 |
| Purpose / 定位 | Blog-first / 博客优先 | Docs-first / 文档优先 |

**Conclusion / 结论**: Jekyll is the better fit for a personal blog wiki with multiple visual styles.

Jekyll 更适合具有多种视觉风格的个人博客 Wiki。

### What Gets REMOVED / 移除内容
- ❌ FastAPI backend (all 7 modules) / FastAPI 后端（全部 7 个模块）
- ❌ PostgreSQL + Alembic migrations / PostgreSQL + Alembic 迁移
- ❌ React frontend (all TSX files) / React 前端（所有 TSX 文件）
- ❌ Docker Compose (3 containers) / Docker Compose（3 个容器）
- ❌ Complex JWT auth / 复杂的 JWT 认证
- ❌ AI provider integration (OpenAI/Ollama) / AI 提供商集成
- ❌ Deep Research SSE pipeline / 深度研究 SSE 管道
- ❌ Social sharing module / 社交分享模块
- ❌ Vite build toolchain / Vite 构建工具链
- ❌ MkDocs (replaced by Jekyll) / MkDocs（被 Jekyll 替代）

### What Gets ADDED / 新增内容
- ✅ **Jekyll** static site generator with 5 blog style layouts / Jekyll 静态站点生成器 + 5 种博文风格布局
- ✅ **Flask** lightweight management server (auth + upload + conversion) / Flask 轻量管理服务器（认证 + 上传 + 转换）
- ✅ **SQLite** for user auth / SQLite 用于用户认证
- ✅ **File converter** pipeline (PDF/Word/HTML → Markdown) / 文件转换管道（PDF/Word/HTML → Markdown）
- ✅ **QQ email** SMTP verification / QQ 邮箱 SMTP 验证
- ✅ CLI tool (`wiki.py`) / CLI 工具
- ✅ GitHub Actions auto-deploy / GitHub Actions 自动部署

### New Project Structure / 新项目结构

```
PolaZhenJing/
├── app/                              # Flask management server / Flask 管理服务器
│   ├── __init__.py                   # Flask app factory / Flask 应用工厂
│   ├── auth.py                       # Register/login/password reset / 注册/登录/修改密码
│   ├── converter.py                  # PDF/Word/HTML → Markdown / 文件格式转换
│   ├── uploader.py                   # File upload + style selection / 文件上传 + 风格选择
│   ├── mailer.py                     # QQ email SMTP verification / QQ 邮箱验证
│   ├── models.py                     # SQLite User model / SQLite 用户模型
│   └── templates/                    # Jinja2 HTML templates for management UI / 管理界面模板
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── upload.html               # Upload + style picker / 上传 + 风格选择器
│       ├── articles.html             # Article management list / 文章管理列表
│       └── password.html             # Change password / 修改密码
├── _posts/                           # Jekyll blog posts (generated) / Jekyll 博文（生成的）
│   └── 2026-04-07-example.md
├── _layouts/                         # Jekyll layout templates / Jekyll 布局模板
│   ├── default.html                  # Base layout / 基础布局
│   ├── deep-technical.html           # Style 1 / 风格1：深度技术
│   ├── academic-insight.html         # Style 2 / 风格2：学术洞察
│   ├── industry-vision.html          # Style 3 / 风格3：行业前瞻
│   ├── friendly-explainer.html       # Style 4 / 风格4：轻松科普
│   └── creative-visual.html          # Style 5 / 风格5：创意视觉
├── _includes/                        # Jekyll reusable components / Jekyll 可复用组件
│   ├── head.html                     # <head> with SEO/OG tags
│   ├── header.html                   # Site navigation / 站点导航
│   ├── footer.html                   # Site footer / 站点页脚
│   └── style-badge.html              # Style indicator badge / 风格标识徽章
├── assets/                           # Static assets / 静态资源
│   ├── css/
│   │   ├── main.css                  # Global styles / 全局样式
│   │   ├── deep-technical.css        # Style 1 CSS
│   │   ├── academic-insight.css      # Style 2 CSS
│   │   ├── industry-vision.css       # Style 3 CSS
│   │   ├── friendly-explainer.css    # Style 4 CSS
│   │   └── creative-visual.css       # Style 5 CSS
│   └── images/                       # Uploaded/extracted images / 上传/提取的图片
├── _config.yml                       # Jekyll configuration / Jekyll 配置
├── index.html                        # Homepage with article list / 首页文章列表
├── wiki.py                           # CLI management tool / CLI 管理工具
├── requirements.txt                  # Python dependencies / Python 依赖
├── Gemfile                           # Ruby/Jekyll dependencies / Ruby/Jekyll 依赖
├── data/                             # SQLite database storage / SQLite 数据库存储
│   └── wiki.db                       # Auth database / 认证数据库
├── .github/
│   └── workflows/
│       └── deploy.yml                # Auto-deploy on push / 推送时自动部署
├── .gitignore
└── .env.example                      # Environment variables template / 环境变量模板
```

**Total: ~30 well-organized files** (vs. current ~65+ scattered files)

**总计：约 30 个组织良好的文件**（对比当前约 65+ 个分散文件）

---

## 4. Detailed Design / 详细设计

### 4.1 File Conversion Pipeline / 文件转换管道

```
Upload File → Detect Format → Convert to Markdown → Add Front Matter → Save to _posts/
上传文件    → 检测格式     → 转换为 Markdown    → 添加前置元数据   → 保存到 _posts/
```

| Source / 源格式 | Library / 库 | Strategy / 策略 |
|--------|---------|----------|
| PDF | `PyMuPDF (fitz)` | Extract text blocks + images, preserve headings / 提取文本块 + 图片，保留标题 |
| Word | `mammoth` | Convert to HTML first, then to Markdown / 先转 HTML，再转 Markdown |
| HTML | `html2text` | Direct HTML to Markdown conversion / HTML 直接转 Markdown |
| Markdown | — | Pass-through, only add front matter / 直通，仅添加前置元数据 |

### 4.2 Authentication System / 认证系统

Lightweight Flask auth with SQLite:

基于 SQLite 的轻量 Flask 认证：

- **SQLite User Table / 用户表**:
  ```sql
  CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
- **QQ Email SMTP Config / QQ 邮箱 SMTP 配置**:
  - Server: `smtp.qq.com:465` (SSL)
  - Requires QQ email authorization code (not password) / 需要 QQ 邮箱授权码（非密码）
  - Sends 6-digit verification code / 发送 6 位验证码
- **Password hashing / 密码哈希**: `werkzeug.security` (built into Flask) / 内置于 Flask

### 4.3 Jekyll Configuration (`_config.yml`) / Jekyll 配置

```yaml
title: PolaZhenjing
description: Personal AI Knowledge Blog / 个人 AI 知识博客
url: "https://username.github.io"
baseurl: "/PolaZhenJing"

markdown: kramdown
highlighter: rouge
permalink: /:year/:month/:day/:title/

plugins:
  - jekyll-feed
  - jekyll-seo-tag
  - jekyll-paginate

paginate: 10
paginate_path: "/page:num/"

defaults:
  - scope:
      path: "_posts"
      type: "posts"
    values:
      layout: "deep-technical"  # default style / 默认风格
```

### 4.4 Blog Style Layouts / 博文风格布局

Each style is a Jekyll layout file (`_layouts/*.html`) + CSS file (`assets/css/*.css`):

每种风格是一个 Jekyll 布局文件 + CSS 文件：

- Articles specify their style in front matter: `layout: deep-technical` / 文章在前置元数据中指定风格
- All 5 styles share common components via `_includes/` / 所有 5 种风格通过 `_includes/` 共享公共组件
- Dark/light mode toggle is global across all styles / 深色/浅色切换是所有风格的全局功能
- Each style has its own typography, spacing, color palette, and content arrangement / 每种风格有自己的排版、间距、配色和内容排列

### 4.5 Management Web UI / 管理 Web 界面

A minimal Flask-rendered web interface (server-side HTML, no SPA):

极简 Flask 渲染的 Web 界面（服务端 HTML，非 SPA）：

| Page / 页面 | Purpose / 用途 |
|------|---------|
| `/login` | Login form / 登录 |
| `/register` | Register + email verification / 注册 + 邮箱验证 |
| `/upload` | File upload + style picker + preview / 文件上传 + 风格选择 + 预览 |
| `/articles` | Article list with edit/delete / 文章列表（编辑/删除） |
| `/password` | Change password / 修改密码 |

### 4.6 CLI Tool (`wiki.py`) / CLI 工具

```bash
# Create a new article / 创建新文章
python wiki.py new "Article Title" --style deep-technical

# List all articles / 列出所有文章
python wiki.py list

# Local preview with Jekyll / 本地预览
python wiki.py serve

# Build static site / 构建静态站点
python wiki.py build

# Deploy to GitHub Pages / 部署到 GitHub Pages
python wiki.py deploy

# Start management server / 启动管理服务器
python wiki.py admin
```

### 4.7 GitHub Actions (`deploy.yml`) / GitHub Actions 自动部署

Auto-deploy triggered on push to `main`:

推送到 `main` 时触发自动部署：

1. Checkout code / 检出代码
2. Setup Ruby + Jekyll / 安装 Ruby + Jekyll
3. `bundle exec jekyll build` / 构建
4. Deploy to `gh-pages` branch / 部署到 `gh-pages` 分支

---

## 5. User Workflow (End-to-End) / 用户工作流（端到端）

This section describes the complete process flow from login to published article, covering every user-facing step and its backend mechanics.

本节描述从登录到文章发布的完整流程，涵盖每个用户可见步骤及其后端机制。

```
┌─────────┐    ┌───────────┐    ┌────────────┐    ┌───────────┐    ┌────────────┐    ┌───────────┐    ┌───────────┐
│  Login  │───▶│  Wiki     │───▶│  Upload /  │───▶│  Style    │───▶│  HTML      │───▶│  GitHub   │───▶│  Homepage │
│         │    │  Homepage │    │  Paste     │    │  Select   │    │  Generate  │    │  Sync     │    │  Updated  │
└─────────┘    └───────────┘    └────────────┘    └───────────┘    └────────────┘    └───────────┘    └───────────┘
登录            Wiki 首页        上传/粘贴内容     选择风格          HTML 生成         GitHub 同步       首页更新
```

### Step 1: Login Process / 登录流程

**Route / 路由**: `GET /login`, `POST /login`

**UI Elements / 界面元素**:
- Username input field / 用户名输入框
- Password input field (masked) / 密码输入框（掩码显示）
- "Login" submit button / "登录" 提交按钮
- "Register" link → redirects to `/register` / "注册" 链接 → 跳转到 `/register`
- "Forgot password?" link → redirects to `/password` / "忘记密码？" 链接 → 跳转到 `/password`

**Backend Processing / 后端处理**:
1. `POST /login` receives `username` + `password` / 接收用户名和密码
2. Query SQLite `users` table for matching username / 查询 SQLite `users` 表匹配用户名
3. Verify password via `werkzeug.security.check_password_hash()` / 通过 werkzeug 验证密码哈希
4. Check `email_verified == True` / 检查邮箱是否已验证
5. On success: create Flask session, redirect to `/articles` (homepage) / 成功：创建 Flask 会话，重定向到 `/articles`（首页）
6. On failure: re-render login page with error message / 失败：重新渲染登录页并显示错误消息

**Registration Sub-flow / 注册子流程** (`GET /register`, `POST /register`):
1. User fills: username, password, confirm password, QQ email / 用户填写：用户名、密码、确认密码、QQ 邮箱
2. `POST /register` validates inputs (unique username/email, password match, email format `*@qq.com`) / 验证输入（用户名/邮箱唯一、密码一致、邮箱格式 `*@qq.com`）
3. `app/mailer.py` sends 6-digit verification code to QQ email via `smtp.qq.com:465` SSL / 通过 QQ SMTP 发送 6 位验证码
4. User enters verification code on the same page / 用户在同一页面输入验证码
5. On valid code: insert user into SQLite with `email_verified=True`, auto-login, redirect to `/articles` / 验证码正确：插入用户到 SQLite，自动登录，重定向到 `/articles`
6. Verification code expires after 5 minutes / 验证码 5 分钟后过期

**Error Handling / 错误处理**:
| Error / 错误 | Message / 提示信息 |
|-------|--------|
| Wrong password / 密码错误 | "用户名或密码不正确 / Invalid username or password" |
| Email not verified / 邮箱未验证 | "请先完成邮箱验证 / Please verify your email first" |
| Username taken / 用户名已存在 | "该用户名已被注册 / Username already taken" |
| SMTP failure / 邮件发送失败 | "验证码发送失败，请检查邮箱地址 / Failed to send code, check email" |
| Code expired / 验证码过期 | "验证码已过期，请重新获取 / Code expired, please resend" |

**Data Flow / 数据流**:
```
Browser → POST /login → auth.py → SQLite query → check_password_hash()
    ↓ success
Flask session cookie set → redirect /articles
```

---

### Step 2: Wiki Homepage / Wiki 首页

**Route / 路由**: `GET /articles` (management UI) + Jekyll `index.html` (public site)

**UI Elements / 界面元素**:
- **Navigation bar / 导航栏**: Logo, "New Article / 新建文章" button, "Change Password / 修改密码" link, "Logout / 退出" button
- **Article list table / 文章列表**:
  - Each row: title, date, style badge (colored label), tags, description / 每行：标题、日期、风格徽章（彩色标签）、标签、描述
  - Action buttons per row: "Preview / 预览", "Edit / 编辑", "Delete / 删除" / 每行操作按钮
- **Style badge colors / 风格徽章颜色**:
  - 深度技术: `#1a1a2e` (dark blue) / 深蓝
  - 学术洞察: `#2d6a4f` (green) / 绿色
  - 行业前瞻: `#e63946` (red) / 红色
  - 轻松科普: `#f4a261` (orange) / 橙色
  - 创意视觉: `#7b2cbf` (purple) / 紫色
- **Stats summary / 统计摘要**: Total articles count, last published date / 总文章数、最近发布日期
- **"New Article" button / "新建文章" 按钮** → redirects to `/upload` / 跳转到 `/upload`

**Backend Processing / 后端处理**:
1. `@login_required` decorator checks Flask session / 检查 Flask 会话
2. Scan `_posts/` directory for all `.md` files / 扫描 `_posts/` 目录获取所有 `.md` 文件
3. Parse YAML front matter from each file (title, date, tags, style, description) / 解析每个文件的 YAML 前置元数据
4. Sort by date descending / 按日期倒序排列
5. Render `articles.html` template with article list / 渲染 `articles.html` 模板

**Delete Flow / 删除流程**:
1. Click "Delete" → JavaScript confirmation dialog / 点击"删除" → JavaScript 确认对话框
2. `POST /articles/<slug>/delete` removes the `.md` file from `_posts/` / 从 `_posts/` 删除 `.md` 文件
3. Also removes associated images from `assets/images/` / 同时删除 `assets/images/` 下关联的图片
4. Flash success message, redirect back to `/articles` / 闪现成功消息，重定向回 `/articles`

**Error Handling / 错误处理**:
| Error / 错误 | Message / 提示信息 |
|-------|--------|
| Not logged in / 未登录 | Redirect to `/login` / 重定向到 `/login` |
| No articles yet / 暂无文章 | "还没有文章，点击'新建文章'开始吧 / No articles yet, click 'New Article' to start" |
| Delete fails / 删除失败 | "文章删除失败 / Article deletion failed" |

**Data Flow / 数据流**:
```
Flask session → @login_required → scan _posts/*.md → parse YAML → render articles.html
```

---

### Step 3: Document Upload / Content Input / 文档上传 / 内容输入

**Route / 路由**: `GET /upload`, `POST /upload`

**UI Elements / 界面元素**:
- **Tab switcher / 标签切换器**: Two tabs — "Upload File / 上传文件" | "Paste Content / 粘贴内容"
- **Upload File tab / 上传文件标签页**:
  - Drag-and-drop zone with file type icons / 拖拽上传区域，带文件类型图标
  - Accepted formats shown: `.md`, `.pdf`, `.docx`, `.html` / 显示支持的格式
  - File size limit: 20MB / 文件大小限制：20MB
  - "Choose File" button as fallback / "选择文件" 按钮备选
- **Paste Content tab / 粘贴内容标签页**:
  - Large textarea (Markdown editor with monospace font) / 大文本区域（等宽字体 Markdown 编辑器）
  - Placeholder: "Paste your Markdown, HTML, or plain text here... / 在此粘贴 Markdown、HTML 或纯文本..." 
  - Character count indicator / 字符计数指示器
- **Metadata fields / 元数据字段** (both tabs / 两个标签页共有):
  - Title input (auto-detected from file content if possible) / 标题输入（尽可能从文件内容自动检测）
  - Tags input (comma-separated, with autocomplete from existing tags) / 标签输入（逗号分隔，支持现有标签自动补全）
  - Description textarea (2 lines) / 描述文本区域（2 行）
- **"Next: Choose Style →" button / "下一步：选择风格 →" 按钮**

**Backend Processing / 后端处理**:
1. `POST /upload` receives multipart file OR pasted text / 接收多部分文件或粘贴文本
2. Detect input type by file extension or content analysis / 通过文件扩展名或内容分析检测输入类型
3. Call `app/converter.py` to transform input → clean Markdown: / 调用 `app/converter.py` 转换输入为干净的 Markdown：
   - **PDF**: `PyMuPDF (fitz)` → extract text blocks preserving structure, extract embedded images → save to `assets/images/` / 提取文本块保留结构，提取嵌入图片保存到 `assets/images/`
   - **Word (.docx)**: `mammoth.convert_to_html()` → `html2text` → Markdown / 先转 HTML 再转 Markdown
   - **HTML**: `html2text.html2text()` with `body_width=0` (no wrapping) → Markdown / 直接转 Markdown
   - **Markdown**: Pass-through, validate syntax / 直通，验证语法
   - **Pasted text**: Auto-detect if Markdown or plain text, wrap in Markdown if needed / 自动检测是否为 Markdown 或纯文本
4. Auto-detect title: first `# heading` in Markdown, or PDF metadata, or filename / 自动检测标题：Markdown 首个 `# 标题`，或 PDF 元数据，或文件名
5. Store converted Markdown + metadata in Flask session for next step / 将转换后的 Markdown + 元数据存入 Flask 会话供下一步使用

**Error Handling / 错误处理**:
| Error / 错误 | Message / 提示信息 |
|-------|--------|
| Unsupported format / 不支持的格式 | "仅支持 .md, .pdf, .docx, .html 格式 / Only .md, .pdf, .docx, .html supported" |
| File too large / 文件过大 | "文件大小不能超过 20MB / File must be under 20MB" |
| PDF extraction fails / PDF 提取失败 | "PDF 内容提取失败，可能是扫描版 PDF / PDF extraction failed, may be scanned" |
| Empty content / 空内容 | "内容不能为空 / Content cannot be empty" |
| No title detected / 未检测到标题 | Title field left empty, user must fill manually / 标题字段留空，用户需手动填写 |

**Data Flow / 数据流**:
```
File/Text → POST /upload → converter.py (detect + convert) → Markdown in session
                                ↓ (images)
                          assets/images/
```

---

### Step 4: Style Selection / 风格选择

**Route / 路由**: `GET /upload/style` (loaded after upload step)

**UI Elements / 界面元素**:
- **5 style cards / 5 张风格卡片** arranged in a grid (2 columns on desktop, 1 on mobile) / 网格布局（桌面 2 列，移动端 1 列）:
  - Each card shows: / 每张卡片显示：
    - Style name in Chinese + English / 中英文风格名称
    - Mini preview thumbnail (screenshot of sample article in that style) / 迷你预览缩略图（该风格示例文章截图）
    - 2-line description / 2 行简介
    - "Best for" tags / "适用于" 标签
    - Radio button selection / 单选按钮
  - Selected card has highlighted border (style accent color) / 选中卡片显示高亮边框（风格主题色）

| Card / 卡片 | Preview Color / 预览色 | Short Description / 简短描述 |
|------|------|------|
| 深度技术 / Deep Technical | `#1a1a2e` | Code-heavy, dark-mode optimized, GitHub aesthetic / 代码密集，深色优化，GitHub 美学 |
| 学术洞察 / Academic Insight | `#2d6a4f` | Paper-like structure, serif fonts, citations / 论文结构，衬线字体，引用 |
| 行业前瞻 / Industry Vision | `#e63946` | Bold headlines, modern layout, infographics / 粗体标题，现代布局，信息图 |
| 轻松科普 / Friendly Explainer | `#f4a261` | Warm, storytelling, beginner-friendly / 温暖，叙事，入门友好 |
| 创意视觉 / Creative Visual | `#7b2cbf` | Image-first, gallery style, artistic / 图片优先，画廊风格，艺术 |

- **Content preview panel / 内容预览面板** (right side on desktop, below on mobile): / 桌面端右侧，移动端下方：
  - Shows the first 500 chars of converted Markdown rendered in the selected style / 显示转换后 Markdown 的前 500 字符，以所选风格渲染
  - Updates dynamically when user clicks a different style card / 用户点击不同风格卡片时动态更新
- **"← Back" button / "← 返回" 按钮** → returns to upload page / 返回上传页面
- **"Generate Blog Post →" button / "生成博文 →" 按钮** → proceeds to generation / 进入生成步骤

**Backend Processing / 后端处理**:
1. `GET /upload/style` reads converted Markdown from Flask session / 从 Flask 会话读取转换后的 Markdown
2. Preview rendering: server-side Markdown → HTML snippet using the selected layout's CSS / 服务端 Markdown → HTML 片段，使用所选布局的 CSS
3. Style selection stored in session alongside Markdown content / 风格选择与 Markdown 内容一起存入会话

**Error Handling / 错误处理**:
| Error / 错误 | Message / 提示信息 |
|-------|--------|
| No content in session / 会话中无内容 | Redirect to `/upload` with message "请先上传内容 / Please upload content first" |
| No style selected / 未选择风格 | Button disabled until a style is selected / 按钮禁用直到选择风格 |

**Data Flow / 数据流**:
```
Session (Markdown + metadata) → style selection → session updated with style choice
```

---

### Step 5: HTML Generation / HTML 生成

**Route / 路由**: `POST /generate`

**UI Elements / 界面元素**:
- **Progress page / 进度页面** with steps indicator: / 带步骤指示器的进度页面：
  1. ✅ "Preparing content / 准备内容"
  2. ⏳ "Generating front matter / 生成前置元数据"
  3. ⏳ "Building HTML with Jekyll / 使用 Jekyll 构建 HTML"
  4. ⏳ "Optimizing output / 优化输出"
- Each step shows a checkmark when complete / 每步完成后显示勾号
- **Estimated time / 预计时间**: "~5-10 seconds / 约 5-10 秒"
- On completion: / 完成后：
  - "View Article / 查看文章" button → opens generated HTML in new tab / 在新标签页打开生成的 HTML
  - "Sync to GitHub / 同步到 GitHub" button → proceeds to Step 6 / 进入步骤 6
  - "Back to Articles / 返回文章列表" link / 返回文章列表链接

**Backend Processing / 后端处理**:
1. Read Markdown + metadata + style from Flask session / 从 Flask 会话读取 Markdown + 元数据 + 风格
2. **Generate YAML front matter / 生成 YAML 前置元数据**:
   ```yaml
   ---
   layout: <selected-style>       # e.g., deep-technical
   title: "<user-provided-title>"
   date: YYYY-MM-DD HH:MM:SS +0800
   tags: [<user-tags>]
   description: "<user-description>"
   author: <username>
   ---
   ```
3. **Generate filename / 生成文件名**: `YYYY-MM-DD-<slug>.md` (slug from title, max 60 chars, CJK → pinyin or hash) / 从标题生成 slug
4. **Write to `_posts/` / 写入 `_posts/`**: Save front matter + Markdown body as `_posts/YYYY-MM-DD-slug.md`
5. **Run Jekyll build / 运行 Jekyll 构建**:
   ```bash
   bundle exec jekyll build --incremental
   ```
   - Incremental build only regenerates changed files (~2-5 seconds) / 增量构建仅重新生成变更文件（约 2-5 秒）
   - Output goes to `_site/` directory / 输出到 `_site/` 目录
6. **Verify output / 验证输出**: Check that `_site/<year>/<month>/<day>/<slug>/index.html` exists / 检查输出文件是否存在
7. Clear session data (Markdown, metadata) / 清除会话数据

**Error Handling / 错误处理**:
| Error / 错误 | Message / 提示信息 |
|-------|--------|
| Jekyll build fails / Jekyll 构建失败 | "构建失败：<error detail>，请检查文章内容 / Build failed: <error>, check content" |
| Filename collision / 文件名冲突 | Auto-append `-2`, `-3` suffix / 自动追加 `-2`、`-3` 后缀 |
| Disk full / 磁盘满 | "磁盘空间不足 / Insufficient disk space" |
| Session expired / 会话过期 | Redirect to `/upload` / 重定向到 `/upload` |

**Data Flow / 数据流**:
```
Session data → write _posts/YYYY-MM-DD-slug.md → jekyll build --incremental → _site/ HTML output
                  ↓
            assets/images/ (already saved in Step 3)
```

---

### Step 6: GitHub Sync / GitHub 同步

**Route / 路由**: `POST /sync`

**UI Elements / 界面元素**:
- **Sync confirmation dialog / 同步确认对话框**:
  - Shows: article title, style, file path / 显示：文章标题、风格、文件路径
  - Commit message input (pre-filled: `"Add: <article-title>"`) / 提交信息输入（预填：`"Add: <文章标题>"`）
  - "Sync Now / 立即同步" button / 同步按钮
  - "Skip, sync later / 跳过，稍后同步" link / 跳过链接
- **Sync progress / 同步进度**:
  - ⏳ "Adding files / 添加文件"
  - ⏳ "Committing / 提交中"
  - ⏳ "Pushing to GitHub / 推送到 GitHub"
  - ✅ "Published! / 已发布！" with link to live page / 完成后显示在线页面链接

**Backend Processing / 后端处理**:
1. **Git add / 添加文件**: Stage new/modified files / 暂存新增/修改的文件
   ```bash
   git add _posts/YYYY-MM-DD-slug.md assets/images/<related-images>
   ```
2. **Git commit / 提交**:
   ```bash
   git commit -m "Add: <article-title>"
   ```
3. **Git push / 推送**:
   ```bash
   git push origin main
   ```
4. **GitHub Actions trigger / 触发 GitHub Actions**: Push to `main` automatically triggers `.github/workflows/deploy.yml` / 推送到 `main` 自动触发部署工作流
5. **Wait for deployment / 等待部署**: Poll GitHub Actions API or use webhook to confirm deployment complete (~30-60 seconds) / 轮询 GitHub Actions API 或使用 webhook 确认部署完成（约 30-60 秒）
6. **Return live URL / 返回在线 URL**: `https://<username>.github.io/PolaZhenJing/<year>/<month>/<day>/<slug>/`

**Alternative: Manual Sync via CLI / 备选：通过 CLI 手动同步**:
```bash
python wiki.py deploy   # git add + commit + push in one command / 一条命令完成 git add + commit + push
```

**Error Handling / 错误处理**:
| Error / 错误 | Message / 提示信息 |
|-------|--------|
| Git not configured / Git 未配置 | "请先配置 Git 用户信息 / Please configure Git user info first" |
| Push rejected / 推送被拒绝 | "推送失败，请先拉取最新代码 / Push failed, pull latest first" |
| No remote set / 未设置远程仓库 | "请先添加 GitHub 远程仓库 / Please add GitHub remote first" |
| Auth failure / 认证失败 | "GitHub 认证失败，请检查 SSH key 或 token / GitHub auth failed" |
| Actions build fails / Actions 构建失败 | "GitHub Pages 部署失败，请检查 Actions 日志 / Deploy failed, check Actions log" |

**Data Flow / 数据流**:
```
_posts/slug.md + assets/images/ → git add → git commit → git push origin main
    ↓ (triggers)
GitHub Actions → jekyll build → deploy to gh-pages → live at GitHub Pages URL
```

---

### Step 7: Wiki Homepage Update / Wiki 首页更新

**Affected Components / 涉及组件**: Jekyll `index.html` (public) + Flask `/articles` (management)

**What Happens Automatically / 自动发生的事情**:

1. **Public site (Jekyll `index.html`) / 公开站点**:
   - GitHub Actions completes Jekyll build on `gh-pages` branch / GitHub Actions 在 `gh-pages` 分支完成 Jekyll 构建
   - `index.html` uses Liquid templating to loop through all `_posts/`: / `index.html` 使用 Liquid 模板遍历所有 `_posts/`：
     ```liquid
     {% for post in site.posts %}
       <article>
         <span class="style-badge {{ post.layout }}">{{ post.layout }}</span>
         <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
         <time>{{ post.date | date: "%Y-%m-%d" }}</time>
         <p>{{ post.description }}</p>
         <div class="tags">{% for tag in post.tags %}<span>{{ tag }}</span>{% endfor %}</div>
       </article>
     {% endfor %}
     ```
   - New article automatically appears at the top (sorted by date descending) / 新文章自动出现在顶部（按日期倒序）
   - Pagination via `jekyll-paginate` (10 articles per page) / 通过 `jekyll-paginate` 分页（每页 10 篇）
   - RSS feed updated via `jekyll-feed` plugin / RSS 订阅通过 `jekyll-feed` 插件更新
   - SEO tags updated via `jekyll-seo-tag` plugin / SEO 标签通过 `jekyll-seo-tag` 插件更新

2. **Management UI (Flask `/articles`) / 管理界面**:
   - Next visit to `/articles` rescans `_posts/` directory / 下次访问 `/articles` 时重新扫描 `_posts/` 目录
   - New article appears immediately in the management list / 新文章立即出现在管理列表中
   - No cache — always reads from filesystem / 无缓存 — 始终从文件系统读取

**UI Update Details / 界面更新详情**:
- New article card shows: / 新文章卡片显示：
  - Title (linked to the public Jekyll page) / 标题（链接到公开的 Jekyll 页面）
  - Date / 日期
  - Style badge with accent color / 风格徽章（带主题色）
  - Tags / 标签
  - Description excerpt / 描述摘要
  - "Published" status indicator (green dot) if synced to GitHub / 如果已同步到 GitHub 显示"已发布"状态指示器（绿点）
  - "Local only" indicator (yellow dot) if not yet synced / 如果尚未同步显示"仅本地"指示器（黄点）

**Error Handling / 错误处理**:
| Error / 错误 | Message / 提示信息 |
|-------|--------|
| GitHub Pages DNS delay / GitHub Pages DNS 延迟 | "页面可能需要几分钟才能生效 / Page may take a few minutes to appear" |
| Build failure on remote / 远程构建失败 | Show GitHub Actions log link / 显示 GitHub Actions 日志链接 |
| Stale cache in browser / 浏览器缓存 | Suggest hard-refresh (Ctrl+Shift+R) / 建议强制刷新 |

**Data Flow / 数据流**:
```
gh-pages branch updated → GitHub Pages serves new index.html → new article visible
Flask /articles → scan _posts/ → new article in management list
```

---

### Complete Workflow Summary / 完整工作流总结

```
[User] → Login (Flask session) → Wiki Homepage (article list)
  ↓
Upload file (.md/.pdf/.docx/.html) OR paste content
  ↓
converter.py: detect format → extract text + images → clean Markdown
  ↓
Select 1 of 5 blog styles (with live preview)
  ↓
Generate: write _posts/slug.md → jekyll build --incremental → _site/ HTML
  ↓
Sync: git add + commit + push → GitHub Actions → gh-pages deploy
  ↓
Homepage updated: new article appears on public site + management UI
```

**Typical end-to-end time / 典型端到端时间**:
| Step / 步骤 | Time / 时间 |
|------|------|
| Login / 登录 | ~2s |
| Upload + convert / 上传 + 转换 | ~3-10s (depends on file size / 取决于文件大小) |
| Style selection / 风格选择 | User decision / 用户决策 |
| Jekyll build / Jekyll 构建 | ~2-5s (incremental / 增量) |
| Git sync / Git 同步 | ~5-15s (push + CI) |
| GitHub Pages live / GitHub Pages 生效 | ~30-60s |
| **Total (excluding user time) / 总计（不含用户操作时间）** | **~45-90s** |

---

## 6. Migration Plan / 迁移计划

### Task 1: Clean up & remove old code / 清理并移除旧代码
- Delete `backend/` entirely / 完全删除 `backend/`
- Delete `frontend/` entirely / 完全删除 `frontend/`
- Delete `docker-compose.yml` / 删除 `docker-compose.yml`
- Delete `site/` directory / 删除 `site/` 目录

### Task 2: Initialize Jekyll structure / 初始化 Jekyll 结构
- Create `_config.yml` with proper settings / 创建配置文件
- Create `_posts/`, `_layouts/`, `_includes/`, `assets/` directories / 创建目录结构
- Create `index.html` homepage / 创建首页
- Create `Gemfile` with Jekyll dependencies / 创建 Gemfile

### Task 3: Build 5 blog style layouts / 构建 5 种博文风格布局
- Create layout HTML for each style in `_layouts/` / 在 `_layouts/` 创建每种风格的布局 HTML
- Create corresponding CSS in `assets/css/` / 在 `assets/css/` 创建对应 CSS
- Create a sample article per style for testing / 为每种风格创建示例文章用于测试

### Task 4: Build Flask management app / 构建 Flask 管理应用
- Create `app/` with auth, upload, converter, mailer modules / 创建 `app/` 及认证、上传、转换、邮件模块
- Create management UI templates / 创建管理界面模板
- Implement QQ email SMTP verification / 实现 QQ 邮箱验证
- Implement file upload + style selection UI / 实现文件上传 + 风格选择界面

### Task 5: Build file conversion pipeline / 构建文件转换管道
- Implement PDF → Markdown converter / 实现 PDF 转 Markdown
- Implement Word → Markdown converter / 实现 Word 转 Markdown
- Implement HTML → Markdown converter / 实现 HTML 转 Markdown
- Add image extraction and saving / 添加图片提取与保存

### Task 6: Create CLI tool & requirements / 创建 CLI 工具和依赖配置
- Write `wiki.py` with all commands / 编写 wiki.py 及所有命令
- Create `requirements.txt` (Python deps) / 创建 requirements.txt
- Create `Gemfile` (Ruby/Jekyll deps) / 创建 Gemfile

### Task 7: Setup GitHub Actions / 配置 GitHub Actions
- Create `.github/workflows/deploy.yml` / 创建部署工作流
- Create `.gitignore` / 创建 .gitignore
- Create `.env.example` / 创建环境变量模板

---

## 7. Dependencies / 依赖

### Python Dependencies / Python 依赖

| Package / 包名 | Purpose / 用途 |
|---------|--------|
| `flask` | Lightweight web framework for management UI / 轻量 Web 框架 |
| `flask-login` | Session management / 会话管理 |
| `PyMuPDF` | PDF text + image extraction / PDF 文本和图片提取 |
| `mammoth` | Word (.docx) → HTML conversion / Word 转 HTML |
| `html2text` | HTML → Markdown conversion / HTML 转 Markdown |
| `python-dotenv` | Environment variable management / 环境变量管理 |

### Ruby Dependencies / Ruby 依赖

| Gem / 包名 | Purpose / 用途 |
|---------|--------|
| `jekyll` | Static site generator / 静态站点生成器 |
| `jekyll-feed` | RSS feed generation / RSS 订阅 |
| `jekyll-seo-tag` | SEO meta tags / SEO 元标签 |
| `jekyll-paginate` | Article list pagination / 文章列表分页 |

**Total: 6 Python + 4 Ruby packages** (vs. current 30+ mixed deps)

**总计：6 个 Python + 4 个 Ruby 包**（对比当前 30+ 混合依赖）

---

## 8. Comparison Summary / 对比总结

| Aspect / 方面 | v1 (Current / 当前) | v2 (Proposed / 提议) |
|--------|-------------|---------------|
| Architecture / 架构 | Full-stack (FastAPI + React + PostgreSQL) / 全栈 | Jekyll + Flask lite / Jekyll + 轻量 Flask |
| Source files / 源文件 | ~65+ | ~30 (well-organized / 组织良好) |
| Dependencies / 依赖 | 30+ (Python + Node) | 10 (Python + Ruby) |
| Database / 数据库 | PostgreSQL (requires Docker) / 需要 Docker | SQLite (zero-config / 零配置) |
| Auth / 认证 | JWT + refresh tokens | Flask session + QQ email / Flask 会话 + QQ 邮箱 |
| Input formats / 输入格式 | Rich text editor only / 仅富文本编辑器 | Markdown + PDF + Word + HTML |
| Blog styles / 博文风格 | None / 无 | 5 distinct styles / 5 种独特风格 |
| Build time / 构建时间 | Minutes (Docker + npm + DB) / 分钟级 | Seconds (`jekyll build`) / 秒级 |
| Deploy / 部署 | Manual / complex / 手动/复杂 | `git push` (auto-deploy / 自动部署) |
| Local dev / 本地开发 | Docker Compose required / 需要 Docker Compose | `python wiki.py serve` |
| Hosting / 托管 | Self-hosted (3 containers) / 自托管 | GitHub Pages (free / 免费) |
