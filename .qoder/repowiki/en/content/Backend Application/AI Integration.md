# AI Integration

<cite>
**Referenced Files in This Document**
- [PRD.md](file://PRD.md)
- [app/__init__.py](file://app/__init__.py)
- [app/auth.py](file://app/auth.py)
- [app/converter.py](file://app/converter.py)
- [app/mailer.py](file://app/mailer.py)
- [app/uploader.py](file://app/uploader.py)
- [app/templates/base.html](file://app/templates/base.html)
- [app/templates/upload.html](file://app/templates/upload.html)
- [app/templates/style_select.html](file://app/templates/style_select.html)
- [_config.yml](file://_config.yml)
- [index.html](file://index.html)
- [requirements.txt](file://requirements.txt)
- [wiki.py](file://wiki.py)
- [_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md](file://_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md)
</cite>

## Update Summary
**Changes Made**
- Updated to reflect the removal of AI provider integrations (OpenAI/Ollama) as part of architectural simplification
- Added comprehensive educational content about AI engineering evolution from Prompt to Context to Harness
- Updated architecture overview to show the new Flask-based content creation workflow
- Removed all references to AI provider factory pattern, strategy pattern, and AI routing endpoints
- Added new section on AI engineering foundations and system design principles
- Updated project structure to reflect the simplified Flask application without AI services

## Table of Contents
1. [Introduction](#introduction)
2. [Educational Foundation: AI Engineering Evolution](#educational-foundation-ai-engineering-evolution)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Architecture Overview](#architecture-overview)
6. [Detailed Component Analysis](#detailed-component-analysis)
7. [Content Creation Workflow](#content-creation-workflow)
8. [Authentication System](#authentication-system)
9. [File Conversion Pipeline](#file-conversion-pipeline)
10. [Blog Generation and Publishing](#blog-generation-and-publishing)
11. [Configuration and Deployment](#configuration-and-deployment)
12. [Migration from Previous Architecture](#migration-from-previous-architecture)
13. [Conclusion](#conclusion)

## Introduction
This document explains the content creation and publishing system for PolaZhenJing, focusing on the streamlined Flask-based architecture that replaced the previous AI-integrated system. The new architecture emphasizes simplicity, zero-configuration SQLite storage, and direct GitHub Pages publishing without external AI services. Users can upload or paste content in multiple formats, select from five distinct blog styles, and publish directly to GitHub Pages with automatic Jekyll site generation.

**Updated** Removed AI provider integrations (OpenAI/Ollama) as part of architectural simplification. Focus shifted to content creation and publishing rather than AI assistance. The system now includes comprehensive educational content about AI engineering evolution from Prompt to Context to Harness, providing foundational knowledge for AI system design and implementation.

## Educational Foundation: AI Engineering Evolution

### From Prompt to Context to Harness

The repository now includes foundational knowledge about AI engineering evolution, establishing a framework for understanding AI system design and implementation. This educational content provides critical insights into the progression of AI engineering practices.

**Prompt Engineering** solves the fundamental communication challenge: how to effectively instruct AI models. This phase focuses on optimizing the "how to speak" aspect, including role definition, instruction structuring, and output formatting.

**Context Engineering** addresses information management challenges: what information should be provided to the model. This phase introduces external knowledge sources, memory systems, and tool integration to create comprehensive information environments.

**Harness Engineering** deals with production reliability: how to make AI systems stable and predictable in real-world applications. This phase encompasses observability, lifecycle management, validation systems, and operational controls.

These three engineering domains represent a hierarchical progression where each builds upon the previous: Prompt ⊂ Context ⊂ Harness. Understanding this evolution is crucial for designing robust AI systems that move beyond experimental prototypes to production-ready solutions.

**Section sources**
- [_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md:10-42](file://_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md#L10-L42)

## Project Structure
The simplified PolaZhenJing architecture centers around a lightweight Flask application that manages content creation, conversion, and publishing workflows. The system maintains a clear separation between management interfaces and the final Jekyll-generated static site.

```mermaid
graph TB
subgraph "Flask Management Server"
APP["app/__init__.py<br/>Application Factory"]
AUTH["app/auth.py<br/>Authentication"]
UP["app/uploader.py<br/>Content Upload & Management"]
CONV["app/converter.py<br/>File Conversion"]
MAIL["app/mailer.py<br/>Email Verification"]
END["Educational Content<br/>AI Engineering Evolution"]
end
subgraph "Content Management"
TEMPLATES["app/templates/<br/>Jinja2 Templates"]
DB["data/wiki.db<br/>SQLite Database"]
END2["_posts/<br/>Educational Articles"]
end
subgraph "Static Site Generation"
JEKYLL["_config.yml<br/>Jekyll Configuration"]
LAYOUTS["_layouts/<br/>Blog Style Layouts"]
INCLUDES["_includes/<br/>Shared Components"]
ASSETS["assets/<br/>CSS & Images"]
END3["Educational Articles<br/>Context & Harness"]
end
subgraph "Publishing"
POSTS["_posts/<br/>Generated Articles"]
GITHUB[".github/workflows/<br/>GitHub Actions"]
end
APP --> AUTH
APP --> UP
APP --> CONV
APP --> MAIL
APP --> END
APP --> TEMPLATES
APP --> DB
UP --> CONV
UP --> POSTS
UP --> END2
JEKYLL --> LAYOUTS
JEKYLL --> INCLUDES
JEKYLL --> ASSETS
POSTS --> GITHUB
END --> END3
```

**Diagram sources**
- [app/__init__.py:43-76](file://app/__init__.py#L43-L76)
- [app/auth.py:13](file://app/auth.py#L13)
- [app/uploader.py:14](file://app/uploader.py#L14)
- [app/converter.py:1](file://app/converter.py#L1)
- [app/mailer.py:1](file://app/mailer.py#L1)
- [_config.yml](file://_config.yml)
- [_posts/](file://_posts/)
- [.github/workflows/](file://.github/workflows/)
- [_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md](file://_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md)

**Section sources**
- [PRD.md:181-234](file://PRD.md#L181-L234)
- [app/__init__.py:43-76](file://app/__init__.py#L43-L76)

## Core Components
- **Flask Application Factory**: Creates and configures the Flask application with proper database initialization and blueprint registration.
- **Authentication System**: Lightweight Flask-based authentication with SQLite storage and QQ email verification.
- **Content Upload Manager**: Handles file uploads, paste content, and style selection with drag-and-drop interface.
- **File Conversion Pipeline**: Converts PDF, Word, HTML, and other formats to clean Markdown with image extraction.
- **Blog Generation Engine**: Creates Jekyll-compatible articles with YAML front matter and publishes to GitHub Pages.
- **Educational Content Module**: Comprehensive AI engineering evolution content providing foundational knowledge for system design.
- **Template System**: Jinja2-based templates for management UI with responsive design.
- **Static Site Generator**: Jekyll configuration for multi-style blog generation with automated deployment.

**Section sources**
- [app/__init__.py:43-76](file://app/__init__.py#L43-L76)
- [app/auth.py:13](file://app/auth.py#L13)
- [app/uploader.py:14](file://app/uploader.py#L14)
- [app/converter.py:1](file://app/converter.py#L1)
- [PRD.md:280-307](file://PRD.md#L280-L307)

## Architecture Overview
The new PolaZhenJing architecture follows a simplified three-tier approach: Management Interface (Flask), Content Processing (Conversion Pipeline), and Publishing (Jekyll + GitHub Pages). This eliminates the complexity of external AI services while maintaining powerful content creation capabilities. The architecture now includes educational content modules that provide foundational knowledge for AI system design.

```mermaid
classDiagram
class FlaskApp {
+create_app() Flask
+get_db() sqlite3.Connection
+close_db(e)
+init_db(app)
}
class AuthSystem {
+login_required(view)
+login()
+register()
+verify()
+change_password()
+logout()
}
class ContentUploader {
+upload()
+style_select()
+generate()
+articles()
+delete_article()
+sync()
}
class ConverterPipeline {
+detect_and_convert()
+convert_pdf()
+convert_docx()
+convert_html()
+extract_title()
}
class JekyllGenerator {
+build_site()
+generate_front_matter()
+process_styles()
}
class EducationalContent {
+ai_engineering_evolution()
+prompt_to_context()
+harness_design()
+system_architecture()
}
FlaskApp --> AuthSystem : "manages"
FlaskApp --> ContentUploader : "manages"
ContentUploader --> ConverterPipeline : "uses"
ContentUploader --> JekyllGenerator : "generates"
ContentUploader --> EducationalContent : "integrates"
```

**Diagram sources**
- [app/__init__.py:43-76](file://app/__init__.py#L43-L76)
- [app/auth.py:16-167](file://app/auth.py#L16-L167)
- [app/uploader.py:76-210](file://app/uploader.py#L76-L210)
- [app/converter.py:58-87](file://app/converter.py#L58-L87)

## Detailed Component Analysis

### Flask Application Factory
The application factory pattern creates a configured Flask instance with proper database initialization, secret key configuration, and blueprint registration. It ensures proper cleanup of database connections and initializes the SQLite schema.

**Section sources**
- [app/__init__.py:43-76](file://app/__init__.py#L43-L76)

### Authentication System
Lightweight Flask-based authentication with SQLite storage, featuring user registration with QQ email verification, password hashing, and session management. Supports single-user oriented workflow with email-based verification.

**Section sources**
- [app/auth.py:16-167](file://app/auth.py#L16-L167)

### Content Upload Manager
Handles multiple content input methods including file uploads with drag-and-drop, paste content editing, and style selection. Provides real-time preview and metadata management for article creation.

**Section sources**
- [app/uploader.py:76-210](file://app/uploader.py#L76-L210)

### File Conversion Pipeline
Multi-format conversion system supporting PDF, Word, HTML, and Markdown files. Extracts text and images, preserves formatting, and generates clean Markdown output with automatic image saving.

**Section sources**
- [app/converter.py:58-87](file://app/converter.py#L58-L87)

### Educational Content Integration
Comprehensive AI engineering evolution content that provides foundational knowledge for system design. This educational module covers the progression from Prompt to Context to Harness engineering, establishing critical frameworks for understanding AI system architecture and implementation.

**Section sources**
- [_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md:10-42](file://_posts/2026-04-18-cong-promptdao-context-engineeringzai-dao-harness-aigong-che.md#L10-L42)

### Template System
Jinja2-based templates providing responsive design with dark theme, interactive elements, and style cards for blog selection. Includes comprehensive styling for all management interfaces.

**Section sources**
- [app/templates/base.html:10-226](file://app/templates/base.html#L10-L226)
- [app/templates/upload.html:1-82](file://app/templates/upload.html#L1-L82)
- [app/templates/style_select.html:1-41](file://app/templates/style_select.html#L1-L41)

## Content Creation Workflow
The content creation process follows a streamlined seven-step workflow from login to published article, eliminating AI assistance in favor of direct content processing and publication. The workflow now includes educational content integration that provides foundational knowledge for AI system design.

```mermaid
sequenceDiagram
participant User as "User"
participant Login as "Login Page"
participant Upload as "Upload Page"
participant Style as "Style Selection"
participant Gen as "Generation"
participant Educ as "Educational Content"
participant Sync as "GitHub Sync"
participant Site as "Public Site"
User->>Login : Access Management
Login->>User : Login/Registration
User->>Upload : Upload Content
Upload->>Gen : Convert & Process
Gen->>Style : Select Blog Style
Style->>Gen : Generate HTML
Gen->>Educ : Integrate Educational Content
Educ->>Sync : Prepare for Publishing
Sync->>Site : Deploy to GitHub Pages
Site->>User : Article Live!
```

**Diagram sources**
- [PRD.md:369-381](file://PRD.md#L369-L381)
- [app/uploader.py:76-210](file://app/uploader.py#L76-L210)

## Authentication System
The authentication system provides a lightweight, single-user oriented approach with QQ email verification and SQLite storage. Features include password hashing, session management, and email-based user verification.

**Section sources**
- [app/auth.py:26-167](file://app/auth.py#L26-L167)
- [PRD.md:258-280](file://PRD.md#L258-L280)

## File Conversion Pipeline
Supports multiple input formats with specialized conversion libraries for each format type. Extracts text, preserves structure, and handles image embedding for comprehensive content processing.

**Section sources**
- [app/converter.py:7-87](file://app/converter.py#L7-L87)
- [PRD.md:244-257](file://PRD.md#L244-L257)

## Blog Generation and Publishing
Direct Jekyll integration with automatic site generation, multi-style support, and GitHub Pages deployment. Eliminates external AI services in favor of pure content processing and static site generation. Educational content is seamlessly integrated into the publishing workflow.

**Section sources**
- [PRD.md:100-114](file://PRD.md#L100-L114)
- [PRD.md:628-680](file://PRD.md#L628-L680)

## Configuration and Deployment
Minimal configuration requirements with environment variable management and automated deployment through GitHub Actions. Zero-dependency SQLite storage and streamlined dependency management. Educational content is automatically processed and published through the same workflow.

**Section sources**
- [PRD.md:813-838](file://PRD.md#L813-L838)
- [PRD.md:356-366](file://PRD.md#L356-L366)

## Migration from Previous Architecture
The migration eliminated complex AI integrations, external databases, and multi-container deployments in favor of a simplified Flask-based system with direct GitHub Pages publishing and zero-configuration SQLite storage. The educational content module was added to provide foundational knowledge for AI system design.

**Section sources**
- [PRD.md:160-170](file://PRD.md#L160-L170)
- [PRD.md:841-856](file://PRD.md#L841-L856)

## Conclusion
PolaZhenJing's simplified architecture successfully replaces AI-assisted content creation with a streamlined content management system. The new Flask-based approach eliminates external dependencies, reduces complexity, and provides direct publishing capabilities through GitHub Pages. Users benefit from a simpler setup process, faster content creation workflow, and reliable static site generation without the overhead of AI service integrations.

**Updated** The system now includes comprehensive educational content about AI engineering evolution, providing foundational knowledge for understanding the progression from Prompt to Context to Harness engineering. This educational foundation supports users who want to move beyond content creation to building robust AI systems, establishing critical frameworks for AI system design and implementation.