# Article Presentation System

<cite>
**Referenced Files in This Document**
- [_config.yml](file://_config.yml)
- [requirements.txt](file://requirements.txt)
- [app/__init__.py](file://app/__init__.py)
- [app/auth.py](file://app/auth.py)
- [app/converter.py](file://app/converter.py)
- [app/mailer.py](file://app/mailer.py)
- [app/uploader.py](file://app/uploader.py)
- [wiki.py](file://wiki.py)
- [Gemfile](file://Gemfile)
- [index.html](file://index.html)
- [_layouts/default.html](file://_layouts/default.html)
- [_layouts/deep-technical.html](file://_layouts/deep-technical.html)
- [_includes/head.html](file://_includes/head.html)
- [assets/css/main.css](file://assets/css/main.css)
- [PRD.md](file://PRD.md)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
The Article Presentation System is a lightweight personal blog wiki designed to streamline content creation and publishing. It supports multi-format article input (Markdown, PDF, Word, HTML), automatic conversion to blog-ready Markdown, flexible blog style selection (five distinct layouts), and seamless GitHub Pages publishing. The system combines a Flask-based management server for authentication, uploads, and conversions with a Jekyll-powered static site generator for blog rendering and publishing.

## Project Structure
The project is organized into two primary layers:
- Flask management server (app/): Handles authentication, file uploads, content conversion, style selection, and article management.
- Jekyll static site (root): Generates styled HTML blogs from Markdown posts, manages pagination, SEO, and theme assets.

```mermaid
graph TB
subgraph "Flask Management Server (app/)"
A_init["app/__init__.py<br/>App factory, DB init, routes"]
A_auth["app/auth.py<br/>Login, register, verify, password"]
A_conv["app/converter.py<br/>PDF/DOCX/HTML → Markdown"]
A_mail["app/mailer.py<br/>QQ email SMTP verification"]
A_up["app/uploader.py<br/>Upload, style select, generate, sync"]
end
subgraph "Jekyll Static Site"
J_cfg["_config.yml<br/>Jekyll config, plugins, defaults"]
J_layout["_layouts/*.html<br/>Blog layouts (5 styles)"]
J_inc["_includes/*.html<br/>Shared components"]
J_css["assets/css/*.css<br/>Global + style-specific CSS"]
J_posts["_posts/*.md<br/>Generated blog posts"]
J_index["index.html<br/>Homepage with pagination"]
end
subgraph "CLI Tool"
CLI_wiki["wiki.py<br/>Serve/build/admin/new/list/deploy"]
end
subgraph "External"
Ext_gem["Gemfile<br/>Ruby/Jekyll deps"]
Ext_req["requirements.txt<br/>Python deps"]
end
A_init --> A_auth
A_init --> A_conv
A_init --> A_mail
A_init --> A_up
A_up --> J_posts
CLI_wiki --> J_cfg
CLI_wiki --> J_layout
CLI_wiki --> J_css
CLI_wiki --> J_index
J_cfg --> J_layout
J_cfg --> J_inc
J_cfg --> J_css
Ext_gem --> J_cfg
Ext_req --> A_init
```

**Diagram sources**
- [app/__init__.py:43-76](file://app/__init__.py#L43-L76)
- [app/auth.py:13-168](file://app/auth.py#L13-L168)
- [app/converter.py:1-108](file://app/converter.py#L1-L108)
- [app/mailer.py:1-53](file://app/mailer.py#L1-L53)
- [app/uploader.py:23-518](file://app/uploader.py#L23-L518)
- [_config.yml:1-50](file://_config.yml#L1-L50)
- [_layouts/default.html:1-12](file://_layouts/default.html#L1-L12)
- [_includes/head.html:1-23](file://_includes/head.html#L1-L23)
- [assets/css/main.css:1-522](file://assets/css/main.css#L1-L522)
- [Gemfile:1-7](file://Gemfile#L1-L7)
- [requirements.txt:1-8](file://requirements.txt#L1-L8)
- [wiki.py:1-165](file://wiki.py#L1-L165)

**Section sources**
- [_config.yml:1-50](file://_config.yml#L1-L50)
- [Gemfile:1-7](file://Gemfile#L1-L7)
- [requirements.txt:1-8](file://requirements.txt#L1-L8)
- [PRD.md:181-239](file://PRD.md#L181-L239)

## Core Components
- Flask Application Factory: Creates the Flask app, initializes SQLite database, registers blueprints, and serves assets.
- Authentication Module: Provides login, registration with QQ email verification, password change, and session management.
- File Converter: Converts PDF, DOCX, HTML, and Markdown into clean Markdown, extracting images and detecting titles.
- Mailer: Sends 6-digit verification codes via QQ Email SMTP.
- Uploader: Manages upload and style selection, generates front matter, writes posts to _posts/, builds Jekyll site, and syncs to GitHub.
- CLI Tool: Offers commands for local preview, building, admin server, creating posts, listing posts, and deploying.

**Section sources**
- [app/__init__.py:43-76](file://app/__init__.py#L43-L76)
- [app/auth.py:26-168](file://app/auth.py#L26-L168)
- [app/converter.py:78-108](file://app/converter.py#L78-L108)
- [app/mailer.py:8-53](file://app/mailer.py#L8-L53)
- [app/uploader.py:299-518](file://app/uploader.py#L299-L518)
- [wiki.py:35-130](file://wiki.py#L35-L130)

## Architecture Overview
The system follows a clear separation of concerns:
- Flask handles user interactions, authentication, and content ingestion.
- Converter transforms heterogeneous inputs into standardized Markdown.
- Jekyll renders styled HTML from Markdown posts with shared layouts and assets.
- GitHub Pages publishes the static site.

```mermaid
graph TB
U["User"]
FL["Flask Routes<br/>auth.py, uploader.py"]
CV["Converter<br/>converter.py"]
DB["SQLite DB<br/>users table"]
FS["_posts/ (Markdown)"]
JE["Jekyll Build<br/>_config.yml, _layouts/, _includes/"]
GH["GitHub Pages"]
U --> FL
FL --> DB
FL --> CV
CV --> FS
FL --> FS
FS --> JE
JE --> GH
```

**Diagram sources**
- [app/auth.py:26-168](file://app/auth.py#L26-L168)
- [app/converter.py:78-108](file://app/converter.py#L78-L108)
- [app/uploader.py:299-518](file://app/uploader.py#L299-L518)
- [_config.yml:25-32](file://_config.yml#L25-L32)
- [_layouts/default.html:1-12](file://_layouts/default.html#L1-L12)
- [_includes/head.html:15-18](file://_includes/head.html#L15-L18)

## Detailed Component Analysis

### Flask Application Factory
- Initializes SQLite database with WAL mode for improved concurrency.
- Registers blueprints for authentication and uploading.
- Serves assets from the assets/ directory.
- Provides a simple index route that redirects authenticated users to the upload page.

```mermaid
flowchart TD
Start(["App Factory"]) --> InitDB["Init SQLite users table"]
InitDB --> RegBP["Register auth + uploader blueprints"]
RegBP --> RouteIdx["Index route: redirect to upload/login"]
RouteIdx --> Assets["Static asset endpoint /assets/<path>"]
Assets --> End(["Ready"])
```

**Diagram sources**
- [app/__init__.py:26-76](file://app/__init__.py#L26-L76)

**Section sources**
- [app/__init__.py:9-41](file://app/__init__.py#L9-L41)
- [app/__init__.py:64-76](file://app/__init__.py#L64-L76)

### Authentication System
- Login: Validates credentials against SQLite, ensures email verification, sets session.
- Registration: Validates inputs, stores hashed password, sends 6-digit verification code via QQ SMTP, marks email as verified upon successful code entry.
- Password Change: Requires current password verification and updates hash.
- Logout: Clears session.

```mermaid
sequenceDiagram
participant U as "User"
participant A as "auth.py"
participant DB as "SQLite users"
participant M as "mailer.py"
U->>A : POST /admin/login
A->>DB : Query user by username
DB-->>A : User record
A->>A : Verify password hash
A->>DB : Check email_verified
A-->>U : Set session and redirect
U->>A : POST /admin/register
A->>DB : Insert user with hashed password
A->>M : send_verification_code()
M-->>A : Sent status
A-->>U : Redirect to /admin/verify
U->>A : POST /admin/verify
A->>DB : UPDATE email_verified = 1
A-->>U : Redirect to /admin/login
```

**Diagram sources**
- [app/auth.py:26-134](file://app/auth.py#L26-L134)
- [app/mailer.py:8-53](file://app/mailer.py#L8-L53)

**Section sources**
- [app/auth.py:26-168](file://app/auth.py#L26-L168)
- [app/mailer.py:8-53](file://app/mailer.py#L8-L53)

### File Conversion Pipeline
- Detects format by extension or content and routes to appropriate converter.
- PDF: Extracts text blocks, detects headings by font size, preserves page breaks.
- DOCX: Uses Mammoth to HTML, then html2text to Markdown.
- HTML: Uses html2text to convert to Markdown.
- Markdown: Pass-through with validation.
- Extracts title from first heading or first line.

```mermaid
flowchart TD
In(["Input File/Text"]) --> Detect["Detect Extension/Type"]
Detect --> |PDF| PDFConv["convert_pdf()<br/>PyMuPDF"]
Detect --> |DOCX| DocxConv["convert_docx()<br/>Mammoth + html2text"]
Detect --> |HTML| HtmlConv["convert_html()<br/>html2text"]
Detect --> |MD| MdPass["Pass-through"]
PDFConv --> OutMd["Clean Markdown"]
DocxConv --> OutMd
HtmlConv --> OutMd
MdPass --> OutMd
OutMd --> Title["extract_title()"]
Title --> End(["Return Markdown"])
```

**Diagram sources**
- [app/converter.py:78-108](file://app/converter.py#L78-L108)

**Section sources**
- [app/converter.py:7-108](file://app/converter.py#L7-L108)

### Uploader and Article Generation
- Upload: Accepts file or pasted content, converts to Markdown, saves draft to data/drafts, stores draft_id in session.
- Style Selection: Renders style cards with live preview and accent colors.
- Generate: Builds front matter (layout, title, date, tags, optional description/summary), writes to _posts/, optionally auto-syncs to GitHub.
- Articles: Scans _posts/, parses front matter, renders management list.
- View/Delete: Renders individual article previews and deletes posts.

```mermaid
sequenceDiagram
participant U as "User"
participant UP as "uploader.py"
participant CV as "converter.py"
participant FS as "_posts/"
participant JE as "Jekyll"
U->>UP : POST /admin/upload
UP->>CV : detect_and_convert()
CV-->>UP : Markdown + title
UP->>UP : Save draft to data/drafts
UP-->>U : Redirect to /admin/upload/style
U->>UP : POST /admin/generate
UP->>UP : Build front matter
UP->>FS : Write _posts/YYYY-MM-DD-slug.md
UP->>JE : bundle exec jekyll build
JE-->>UP : _site/ built
UP-->>U : Success + optional auto-sync
```

**Diagram sources**
- [app/uploader.py:299-437](file://app/uploader.py#L299-L437)
- [app/converter.py:78-108](file://app/converter.py#L78-L108)

**Section sources**
- [app/uploader.py:299-518](file://app/uploader.py#L299-L518)

### Jekyll Configuration and Styling
- Jekyll configuration enables feed, SEO, and pagination plugins, sets permalink and defaults for posts.
- Layouts define the structure for each style; shared includes provide common components.
- CSS includes global styles and style-specific styles; head.html injects style-specific CSS based on page.layout.

```mermaid
graph LR
CFG["_config.yml<br/>plugins, defaults, paginate"]
DEF["_layouts/default.html"]
DT["_layouts/deep-technical.html"]
HEAD["_includes/head.html"]
MAIN["assets/css/main.css"]
DT --> DEF
HEAD --> MAIN
HEAD --> DT
CFG --> DEF
CFG --> DT
```

**Diagram sources**
- [_config.yml:19-32](file://_config.yml#L19-L32)
- [_layouts/default.html:1-12](file://_layouts/default.html#L1-L12)
- [_layouts/deep-technical.html:1-22](file://_layouts/deep-technical.html#L1-L22)
- [_includes/head.html:15-18](file://_includes/head.html#L15-L18)
- [assets/css/main.css:50-56](file://assets/css/main.css#L50-L56)

**Section sources**
- [_config.yml:19-32](file://_config.yml#L19-L32)
- [_layouts/default.html:1-12](file://_layouts/default.html#L1-L12)
- [_layouts/deep-technical.html:1-22](file://_layouts/deep-technical.html#L1-L22)
- [_includes/head.html:15-18](file://_includes/head.html#L15-L18)
- [assets/css/main.css:50-56](file://assets/css/main.css#L50-L56)

### CLI Tool (wiki.py)
- Commands: serve (Jekyll local preview), build (static site), admin (Flask server), new (create post), list (posts), deploy (git add/commit/push).
- Integrates with Jekyll and project root for seamless development and deployment workflows.

**Section sources**
- [wiki.py:35-130](file://wiki.py#L35-L130)

## Dependency Analysis
- Python dependencies: Flask, Flask-Login, PyMuPDF, Mammoth, html2text, python-dotenv, python-slugify.
- Ruby dependencies: Jekyll, jekyll-feed, jekyll-seo-tag, jekyll-paginate.
- Internal coupling:
  - uploader.py depends on converter.py and Jekyll build.
  - auth.py depends on SQLite and mailer.py.
  - app/__init__.py centralizes DB initialization and blueprint registration.

```mermaid
graph TB
Req["requirements.txt"]
Gem["Gemfile"]
A_init["app/__init__.py"]
A_auth["app/auth.py"]
A_conv["app/converter.py"]
A_up["app/uploader.py"]
Wiki["wiki.py"]
Req --> A_init
Req --> A_auth
Req --> A_conv
Req --> A_up
Gem --> Wiki
A_up --> Wiki
A_auth --> A_init
A_conv --> A_up
```

**Diagram sources**
- [requirements.txt:1-8](file://requirements.txt#L1-L8)
- [Gemfile:1-7](file://Gemfile#L1-L7)
- [app/__init__.py:43-59](file://app/__init__.py#L43-L59)
- [app/auth.py:13-13](file://app/auth.py#L13-L13)
- [app/converter.py:1-1](file://app/converter.py#L1-L1)
- [app/uploader.py:18-19](file://app/uploader.py#L18-L19)
- [wiki.py:54-60](file://wiki.py#L54-L60)

**Section sources**
- [requirements.txt:1-8](file://requirements.txt#L1-L8)
- [Gemfile:1-7](file://Gemfile#L1-L7)
- [app/__init__.py:43-59](file://app/__init__.py#L43-L59)
- [app/uploader.py:18-19](file://app/uploader.py#L18-L19)

## Performance Considerations
- SQLite with WAL mode improves concurrent reads/writes.
- Jekyll incremental build reduces rebuild time for single posts.
- Image extraction and saving occur during conversion; ensure sufficient disk space.
- PDF text extraction relies on PyMuPDF; scanned PDFs may fail extraction.
- HTML to Markdown conversion avoids line wrapping for readability.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Authentication
  - Wrong credentials: Ensure username exists and password matches hash.
  - Unverified email: Complete QQ email verification flow.
  - Registration conflicts: Unique username/email required.
- Upload and Conversion
  - Unsupported format: Only .md, .pdf, .docx, .html accepted.
  - File too large: Limit 20MB uploads.
  - PDF extraction failures: Scanned PDFs unsupported.
  - Empty content: Provide non-empty input.
- Generation and Sync
  - Jekyll build failures: Check content validity and front matter.
  - Git configuration missing: Configure user.name and user.email.
  - Push rejected: Pull latest changes before pushing.
  - GitHub Actions build failures: Review Actions logs.

**Section sources**
- [app/auth.py:36-48](file://app/auth.py#L36-L48)
- [app/converter.py:90-91](file://app/converter.py#L90-L91)
- [app/uploader.py:310-332](file://app/uploader.py#L310-L332)
- [app/uploader.py:420-436](file://app/uploader.py#L420-L436)

## Conclusion
The Article Presentation System offers a streamlined workflow for creating, styling, and publishing blog articles. By combining Flask for management and Jekyll for rendering, it achieves simplicity, flexibility, and efficient publishing to GitHub Pages. The five blog styles enable diverse presentation while maintaining a cohesive design system.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### User Workflow (End-to-End)
```mermaid
flowchart LR
Login["Login"] --> Wiki["Wiki Homepage"]
Wiki --> Upload["Upload/Paste Content"]
Upload --> Style["Select Blog Style"]
Style --> Generate["Generate Markdown + Front Matter"]
Generate --> Jekyll["Jekyll Build"]
Jekyll --> GitHub["Sync to GitHub"]
GitHub --> Publish["GitHub Pages Live"]
```

**Diagram sources**
- [PRD.md:369-381](file://PRD.md#L369-L381)
- [app/uploader.py:299-437](file://app/uploader.py#L299-L437)

### Homepage Rendering
- Jekyll index.html loops through site.posts, displaying style badges, titles, dates, descriptions, and tags via pagination.

**Section sources**
- [index.html:18-68](file://index.html#L18-L68)