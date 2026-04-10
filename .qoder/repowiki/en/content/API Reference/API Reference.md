# API Reference

<cite>
**Referenced Files in This Document**
- [app/__init__.py](file://app/__init__.py)
- [app/auth.py](file://app/auth.py)
- [app/converter.py](file://app/converter.py)
- [app/uploader.py](file://app/uploader.py)
- [app/mailer.py](file://app/mailer.py)
- [app/templates/upload.html](file://app/templates/upload.html)
- [app/templates/login.html](file://app/templates/login.html)
- [app/templates/register.html](file://app/templates/register.html)
- [app/templates/articles.html](file://app/templates/articles.html)
- [app/templates/base.html](file://app/templates/base.html)
- [_config.yml](file://_config.yml)
- [.github/workflows/deploy.yml](file://.github/workflows/deploy.yml)
- [PRD.md](file://PRD.md)
- [requirements.txt](file://requirements.txt)
</cite>

## Update Summary
**Changes Made**
- Updated to reflect the complete migration from FastAPI REST API to Flask-based management interface
- Removed all REST API documentation sections as they no longer exist
- Added comprehensive documentation for Flask-based authentication system
- Documented file upload and conversion interface with supported formats
- Added blog style management documentation with 5 distinct layouts
- Updated deployment workflow to GitHub Actions with Jekyll static site generation
- Revised architecture to show server-rendered HTML interface instead of REST endpoints

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Authentication System](#authentication-system)
4. [File Upload and Conversion Interface](#file-upload-and-conversion-interface)
5. [Blog Style Management](#blog-style-management)
6. [Article Management](#article-management)
7. [Deployment and Publishing](#deployment-and-publishing)
8. [Configuration](#configuration)
9. [Migration from REST API](#migration-from-rest-api)
10. [Troubleshooting Guide](#troubleshooting-guide)

## Introduction
This document provides comprehensive documentation for PolaZhenJing's new Flask-based management interface that replaced the previous FastAPI RESTful API. The system now operates as a lightweight Flask application with server-rendered HTML templates, integrated with Jekyll for static site generation and GitHub Actions for automated deployment.

**Key Changes from Previous REST API:**
- Complete removal of all REST endpoints and FastAPI backend
- Migration from JWT authentication to Flask session-based authentication
- Implementation of file conversion pipeline for multiple document formats
- Replacement of dynamic API calls with static site generation
- Integration with GitHub Actions for automated deployment to GitHub Pages

## System Architecture
The new architecture consists of a Flask management server that handles authentication and file processing, with Jekyll generating static HTML content for publication.

```mermaid
graph TB
FlaskApp["Flask Management App<br/>app/__init__.py"] --> AuthBP["Authentication Blueprint<br/>app/auth.py"]
FlaskApp --> UploadBP["Upload Blueprint<br/>app/uploader.py"]
FlaskApp --> Converter["File Conversion Pipeline<br/>app/converter.py"]
FlaskApp --> Mailer["Email Verification<br/>app/mailer.py"]
AuthBP --> Templates["Jinja2 Templates<br/>app/templates/"]
UploadBP --> Templates
UploadBP --> Converter
UploadBP --> Jekyll["Jekyll Static Generator<br/>_config.yml"]
Templates --> HTML["Generated HTML Pages"]
Converter --> Posts["_posts/ Directory<br/>Markdown Articles"]
Posts --> Jekyll
Jekyll --> Site["_site/ Directory<br/>Static Website"]
Site --> GitHubPages["GitHub Pages Deployment<br/>.github/workflows/deploy.yml"]
```

**Diagram sources**
- [app/__init__.py:43-61](file://app/__init__.py#L43-L61)
- [app/auth.py:13](file://app/auth.py#L13)
- [app/uploader.py:14](file://app/uploader.py#L14)
- [app/converter.py:1](file://app/converter.py#L1)
- [app/mailer.py](file://app/mailer.py)
- [_config.yml:1-49](file://_config.yml#L1-L49)
- [.github/workflows/deploy.yml:1-62](file://.github/workflows/deploy.yml#L1-L62)

**Section sources**
- [app/__init__.py:43-61](file://app/__init__.py#L43-L61)
- [PRD.md:143-180](file://PRD.md#L143-L180)

## Authentication System
The system uses Flask session-based authentication with SQLite for user management and QQ email SMTP verification.

### Authentication Endpoints
- **POST /admin/login** - User login with username and password
- **POST /admin/register** - User registration with QQ email verification
- **POST /admin/verify** - Email verification with 6-digit code
- **POST /admin/password** - Password change for authenticated users
- **GET /admin/logout** - Logout and clear session

### Authentication Flow
```mermaid
sequenceDiagram
participant User as "User Browser"
participant Auth as "Auth Blueprint"
participant DB as "SQLite Database"
participant Mail as "SMTP Server"
User->>Auth : POST /admin/register
Auth->>DB : Insert user record
Auth->>Mail : Send verification code
Mail-->>Auth : Success/Failure
Auth-->>User : Redirect to /admin/verify
User->>Auth : POST /admin/verify
Auth->>DB : Verify email code
DB-->>Auth : Verified user
Auth-->>User : Redirect to /admin/login
User->>Auth : POST /admin/login
Auth->>DB : Verify credentials
DB-->>Auth : Valid user
Auth-->>User : Set Flask session + redirect
```

**Diagram sources**
- [app/auth.py:26-48](file://app/auth.py#L26-L48)
- [app/auth.py:51-96](file://app/auth.py#L51-L96)
- [app/auth.py:99-133](file://app/auth.py#L99-L133)
- [app/auth.py:136-167](file://app/auth.py#L136-L167)

**Section sources**
- [app/auth.py:26-167](file://app/auth.py#L26-L167)
- [PRD.md:258-280](file://PRD.md#L258-L280)

## File Upload and Conversion Interface
The upload interface supports multiple document formats with automatic conversion to Markdown and style selection.

### Upload Endpoints
- **GET /admin/upload** - Upload form with file upload and paste content options
- **POST /admin/upload** - Process uploaded files or pasted content
- **GET /admin/upload/style** - Style selection interface
- **POST /admin/generate** - Generate final blog post with selected style

### Supported File Formats
| Format | Extension | Processing Method |
|--------|-----------|-------------------|
| Markdown | `.md` | Direct passthrough |
| PDF | `.pdf` | PyMuPDF text extraction + image extraction |
| Word | `.docx`, `.doc` | Mammoth HTML conversion + html2text |
| HTML | `.html`, `.htm` | Direct HTML to Markdown conversion |

### Upload Process Flow
```mermaid
flowchart TD
A[User Upload Form] --> B{File or Paste?}
B --> |File Upload| C[File Validation]
B --> |Paste Content| D[Content Processing]
C --> E[Format Detection]
E --> F[Conversion Pipeline]
D --> F
F --> G[Title Extraction]
G --> H[Style Selection]
H --> I[Final Generation]
I --> J[Markdown Output]
```

**Diagram sources**
- [app/uploader.py:76-118](file://app/uploader.py#L76-L118)
- [app/converter.py:58-87](file://app/converter.py#L58-L87)

**Section sources**
- [app/uploader.py:76-210](file://app/uploader.py#L76-L210)
- [app/converter.py:1-88](file://app/converter.py#L1-L88)
- [PRD.md:40-62](file://PRD.md#L40-L62)

## Blog Style Management
The system supports 5 distinct blog styles with custom layouts and CSS.

### Available Styles
1. **Deep Technical** - Code-heavy, dark-mode optimized
2. **Academic Insight** - Research paper structure, citation format
3. **Industry Vision** - Bold headlines, modern layout
4. **Friendly Explainer** - Warm storytelling, beginner-friendly
5. **Creative Visual** - Image-first, gallery presentation

### Style Selection Interface
The style selection page displays 5 cards with:
- Style name (Chinese + English)
- Mini preview thumbnail
- Brief description
- "Best for" recommendations
- Live content preview

**Section sources**
- [app/uploader.py:16-27](file://app/uploader.py#L16-L27)
- [PRD.md:64-99](file://PRD.md#L64-L99)

## Article Management
The management interface provides CRUD operations for blog posts.

### Article Management Endpoints
- **GET /admin/articles** - List all articles with metadata
- **POST /admin/articles/<filename>/delete** - Delete specific article
- **POST /admin/sync** - Sync to GitHub for deployment

### Article Metadata
Each article includes:
- Title (from front matter or extracted)
- Date (automatically generated)
- Tags (comma-separated)
- Description (optional)
- Style (selected during generation)
- Author (current user)

### Article List Features
- Chronological ordering (newest first)
- Style badges with color coding
- Tag-based filtering
- Action buttons (preview, edit, delete)
- Status indicators (published/local only)

**Section sources**
- [app/uploader.py:171-187](file://app/uploader.py#L171-L187)
- [app/uploader.py:190-210](file://app/uploader.py#L190-L210)
- [PRD.md:428-470](file://PRD.md#L428-L470)

## Deployment and Publishing
The system integrates with GitHub Actions for automated deployment to GitHub Pages.

### Deployment Workflow
```mermaid
sequenceDiagram
participant Dev as "Developer"
participant Git as "Git Repository"
participant GH as "GitHub Actions"
participant JP as "GitHub Pages"
Dev->>Git : Push to main branch
Git->>GH : Trigger workflow
GH->>GH : Checkout repository
GH->>GH : Setup Ruby + Jekyll
GH->>GH : bundle exec jekyll build
GH->>JP : Deploy to gh-pages branch
JP->>JP : Serve static site
```

**Diagram sources**
- [.github/workflows/deploy.yml:27-62](file://.github/workflows/deploy.yml#L27-L62)

### Deployment Endpoints
- **POST /admin/sync** - Manual synchronization to GitHub
- Automatic deployment on pushes to main branch

### GitHub Actions Features
- Auto-build on push to main branch
- Strict build validation
- Artifact upload and deployment
- Environment configuration for GitHub Pages

**Section sources**
- [.github/workflows/deploy.yml:1-62](file://.github/workflows/deploy.yml#L1-L62)
- [PRD.md:628-681](file://PRD.md#L628-L681)

## Configuration
The system uses environment variables and configuration files for customization.

### Environment Variables
- `SECRET_KEY` - Flask application secret key
- `SMTP_HOST` - QQ email SMTP server host
- `SMTP_PORT` - SMTP server port (SSL: 465)
- `SMTP_USERNAME` - QQ email address
- `SMTP_PASSWORD` - QQ email authorization code

### Configuration Files
- `_config.yml` - Jekyll configuration with plugins and defaults
- `Gemfile` - Ruby dependencies for Jekyll
- `requirements.txt` - Python dependencies for Flask app

### Jekyll Configuration
Key settings include:
- Site title and description
- GitHub Pages URL configuration
- Build plugins (feed, SEO, paginate)
- Default layout for posts
- Build exclusions

**Section sources**
- [app/__init__.py:46](file://app/__init__.py#L46)
- [_config.yml:1-49](file://_config.yml#L1-L49)
- [PRD.md:281-307](file://PRD.md#L281-L307)

## Migration from REST API
The system has been completely migrated from the previous FastAPI RESTful architecture to a Flask-based management interface.

### Removed Components
- FastAPI backend with 7 modules (auth, thoughts, tags, research, ai, publish, sharing)
- PostgreSQL database with 5 tables
- JWT authentication system
- AI provider integration (OpenAI/Ollama)
- Complex routing structure
- Docker Compose deployment

### New Architecture Benefits
- **Simplified**: ~30 organized files vs. ~65+ scattered files
- **Zero-config**: SQLite instead of PostgreSQL
- **Fast**: Static site generation instead of dynamic API calls
- **Reliable**: GitHub Actions for automated deployment
- **Lightweight**: Single Flask application with Jekyll

### Migration Impact
- **Authentication**: Changed from JWT to Flask sessions
- **Content Management**: From REST endpoints to file-based Markdown
- **Publishing**: From manual export to automated GitHub Pages
- **Development**: Simplified local setup without Docker/PostgreSQL

**Section sources**
- [PRD.md:160-180](file://PRD.md#L160-L180)
- [PRD.md:770-800](file://PRD.md#L770-L800)

## Troubleshooting Guide

### Common Issues and Solutions

#### Authentication Issues
- **Problem**: "Username not found" or "Incorrect password"
  - **Solution**: Verify credentials in SQLite database
  - **Check**: User registration completed successfully

- **Problem**: "Please verify your email first"
  - **Solution**: Complete email verification process
  - **Check**: Verification code expiration (5 minutes)

#### Upload Issues
- **Problem**: "Unsupported file type"
  - **Solution**: Use supported formats (.md, .pdf, .docx, .html)
  - **Check**: File extension validation

- **Problem**: "Conversion error"
  - **Solution**: Install required dependencies (PyMuPDF, mammoth, html2text)
  - **Check**: Library availability in environment

#### Style Selection Issues
- **Problem**: No style preview available
  - **Solution**: Ensure Jekyll layouts are properly configured
  - **Check**: CSS files in assets/css/ directory

#### Deployment Issues
- **Problem**: "Push failed: Permission denied"
  - **Solution**: Configure Git remote and authentication
  - **Check**: SSH key or GitHub token setup

- **Problem**: "GitHub Pages deployment failed"
  - **Solution**: Check GitHub Actions logs for build errors
  - **Check**: Jekyll configuration and dependencies

**Section sources**
- [app/auth.py:34-48](file://app/auth.py#L34-L48)
- [app/uploader.py:84-100](file://app/uploader.py#L84-L100)
- [app/uploader.py:195-209](file://app/uploader.py#L195-L209)