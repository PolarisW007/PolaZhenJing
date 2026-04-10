# Backend Application

<cite>
**Referenced Files in This Document**
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)
- [backend/app/database.py](file://backend/app/database.py)
- [backend/app/common/middleware.py](file://backend/app/common/middleware.py)
- [backend/app/common/exceptions.py](file://backend/app/common/exceptions.py)
- [backend/app/common/models.py](file://backend/app/common/models.py)
- [backend/app/auth/router.py](file://backend/app/auth/router.py)
- [backend/app/auth/service.py](file://backend/app/auth/service.py)
- [backend/app/thoughts/router.py](file://backend/app/thoughts/router.py)
- [backend/app/thoughts/service.py](file://backend/app/thoughts/service.py)
- [backend/app/tags/router.py](file://backend/app/tags/router.py)
- [backend/app/tags/service.py](file://backend/app/tags/service.py)
- [backend/app/ai/router.py](file://backend/app/ai/router.py)
- [backend/app/ai/factory.py](file://backend/app/ai/factory.py)
- [backend/app/publish/router.py](file://backend/app/publish/router.py)
- [backend/app/sharing/router.py](file://backend/app/sharing/router.py)
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

## Introduction
This document describes the backend application for PolaZhenJing, a FastAPI-based AI-powered personal knowledge wiki and sharing platform. It explains the application structure, initialization and configuration management, modular routers for authentication, thoughts, tags, AI integration, publishing, and sharing, the middleware and exception handling systems, database integration, application lifecycle, logging configuration, service-layer architecture, and security considerations including CORS and request processing pipeline.

## Project Structure
The backend is organized around a FastAPI application factory that wires together configuration, middleware, exception handlers, and modular routers. Each functional domain (auth, thoughts, tags, AI, publish, sharing) is implemented as a separate package with its own router, service, models, and schemas. A shared common layer provides middleware, exceptions, and ORM models. Database integration uses SQLAlchemy asynchronous sessions.

```mermaid
graph TB
subgraph "FastAPI App"
MAIN["main.py<br/>App factory, lifespan, routers, health"]
CFG["config.py<br/>Settings"]
DB["database.py<br/>Engine, session, Base"]
end
subgraph "Common Layer"
MW["common/middleware.py<br/>CORS, request logging"]
EX["common/exceptions.py<br/>Custom exceptions, handlers"]
CM["common/models.py<br/>TimestampMixin, User"]
end
subgraph "Routers"
AUTH_R["auth/router.py"]
THOUGHTS_R["thoughts/router.py"]
TAGS_R["tags/router.py"]
AI_R["ai/router.py"]
PUBLISH_R["publish/router.py"]
SHARE_R["sharing/router.py"]
end
MAIN --> CFG
MAIN --> DB
MAIN --> MW
MAIN --> EX
MAIN --> AUTH_R
MAIN --> THOUGHTS_R
MAIN --> TAGS_R
MAIN --> AI_R
MAIN --> PUBLISH_R
MAIN --> SHARE_R
AUTH_R --> CM
THOUGHTS_R --> CM
TAGS_R --> CM
AI_R --> CM
PUBLISH_R --> CM
SHARE_R --> CM
```

**Diagram sources**
- [backend/app/main.py:1-88](file://backend/app/main.py#L1-L88)
- [backend/app/config.py:1-61](file://backend/app/config.py#L1-L61)
- [backend/app/database.py:1-62](file://backend/app/database.py#L1-L62)
- [backend/app/common/middleware.py:1-59](file://backend/app/common/middleware.py#L1-L59)
- [backend/app/common/exceptions.py:1-87](file://backend/app/common/exceptions.py#L1-L87)
- [backend/app/common/models.py:1-76](file://backend/app/common/models.py#L1-L76)
- [backend/app/auth/router.py:1-91](file://backend/app/auth/router.py#L1-L91)
- [backend/app/thoughts/router.py:1-115](file://backend/app/thoughts/router.py#L1-L115)
- [backend/app/tags/router.py:1-72](file://backend/app/tags/router.py#L1-L72)
- [backend/app/ai/router.py:1-109](file://backend/app/ai/router.py#L1-L109)
- [backend/app/publish/router.py:1-64](file://backend/app/publish/router.py#L1-L64)
- [backend/app/sharing/router.py:1-46](file://backend/app/sharing/router.py#L1-L46)

**Section sources**
- [backend/app/main.py:1-88](file://backend/app/main.py#L1-L88)
- [backend/app/config.py:1-61](file://backend/app/config.py#L1-L61)

## Core Components
- Application factory and lifecycle: The FastAPI app is created with title, version, and lifespan. The lifespan initializes logging and disposes the database engine on shutdown.
- Configuration: Centralized settings via pydantic-settings with environment variable overrides and a .env file.
- Database: Asynchronous SQLAlchemy engine and session factory with a shared declarative Base and a dependency to supply sessions.
- Middleware: CORS configuration and request logging middleware registered at startup.
- Exception handling: Global handlers for custom application exceptions and generic unhandled exceptions.
- Modular routers: Six routers under distinct prefixes for authentication, thoughts, tags, AI, publishing, and sharing.

**Section sources**
- [backend/app/main.py:28-87](file://backend/app/main.py#L28-L87)
- [backend/app/config.py:15-61](file://backend/app/config.py#L15-L61)
- [backend/app/database.py:23-62](file://backend/app/database.py#L23-L62)
- [backend/app/common/middleware.py:22-59](file://backend/app/common/middleware.py#L22-L59)
- [backend/app/common/exceptions.py:66-87](file://backend/app/common/exceptions.py#L66-L87)

## Architecture Overview
The backend follows a layered architecture:
- Presentation layer: FastAPI routers define endpoints and depend on services.
- Service layer: Implements business logic and orchestrates database operations.
- Persistence layer: SQLAlchemy async ORM with a shared Base and session dependency.
- Cross-cutting concerns: Configuration, middleware, exception handling, and logging.

```mermaid
graph TB
CLIENT["Client"]
FADEP["FastAPI App<br/>main.py"]
CORS["CORS Middleware"]
LOGMW["Request Logging Middleware"]
EXCH["Exception Handlers"]
AUTH["Auth Router"]
THOUGHTS["Thoughts Router"]
TAGS["Tags Router"]
AI["AI Router"]
PUBLISH["Publish Router"]
SHARE["Share Router"]
SVC_AUTH["Auth Service"]
SVC_THOUGHTS["Thoughts Service"]
SVC_TAGS["Tags Service"]
SVC_AI["AI Factory + Providers"]
SVC_PUBLISH["Publish Service"]
SVC_SHARE["Share Service"]
DB["SQLAlchemy Async Engine<br/>Sessions"]
MODELS["Shared Models"]
CLIENT --> FADEP
FADEP --> CORS
FADEP --> LOGMW
FADEP --> EXCH
FADEP --> AUTH
FADEP --> THOUGHTS
FADEP --> TAGS
FADEP --> AI
FADEP --> PUBLISH
FADEP --> SHARE
AUTH --> SVC_AUTH
THOUGHTS --> SVC_THOUGHTS
TAGS --> SVC_TAGS
AI --> SVC_AI
PUBLISH --> SVC_PUBLISH
SHARE --> SVC_SHARE
SVC_AUTH --> DB
SVC_THOUGHTS --> DB
SVC_TAGS --> DB
SVC_AI --> DB
SVC_PUBLISH --> DB
SVC_SHARE --> DB
SVC_AUTH --> MODELS
SVC_THOUGHTS --> MODELS
SVC_TAGS --> MODELS
SVC_SHARE --> MODELS
```

**Diagram sources**
- [backend/app/main.py:39-87](file://backend/app/main.py#L39-L87)
- [backend/app/common/middleware.py:22-59](file://backend/app/common/middleware.py#L22-L59)
- [backend/app/common/exceptions.py:66-87](file://backend/app/common/exceptions.py#L66-L87)
- [backend/app/auth/router.py:1-91](file://backend/app/auth/router.py#L1-L91)
- [backend/app/thoughts/router.py:1-115](file://backend/app/thoughts/router.py#L1-L115)
- [backend/app/tags/router.py:1-72](file://backend/app/tags/router.py#L1-L72)
- [backend/app/ai/router.py:1-109](file://backend/app/ai/router.py#L1-L109)
- [backend/app/publish/router.py:1-64](file://backend/app/publish/router.py#L1-L64)
- [backend/app/sharing/router.py:1-46](file://backend/app/sharing/router.py#L1-L46)
- [backend/app/database.py:23-62](file://backend/app/database.py#L23-L62)
- [backend/app/common/models.py:40-76](file://backend/app/common/models.py#L40-L76)

## Detailed Component Analysis

### Application Initialization and Lifecycle
- App creation: FastAPI is instantiated with metadata and a lifespan manager.
- Lifespan: Logs startup and shutdown messages; disposes the async engine.
- Health endpoint: Lightweight GET /health returning app name, version, and status.

```mermaid
sequenceDiagram
participant Proc as "Process"
participant App as "FastAPI App"
participant Lif as "Lifespan"
participant DB as "SQLAlchemy Engine"
Proc->>App : Import main.py
App->>Lif : Start lifespan
Lif->>Proc : Log "Starting PolaZhenjing v..."
App->>DB : Initialize engine (from config)
Proc-->>App : Serve requests
App->>Lif : End lifespan
Lif->>DB : dispose()
Lif-->>Proc : Log "Shut down gracefully"
```

**Diagram sources**
- [backend/app/main.py:28-45](file://backend/app/main.py#L28-L45)
- [backend/app/database.py:23-30](file://backend/app/database.py#L23-L30)

**Section sources**
- [backend/app/main.py:28-87](file://backend/app/main.py#L28-L87)

### Configuration Management
- Centralized settings class loads from a .env file and supports environment overrides.
- Includes application metadata, database URL, JWT settings, AI provider configuration, site/publishing settings, and CORS origins.

```mermaid
flowchart TD
A["Load .env"] --> B["Parse settings"]
B --> C{"Key present?"}
C --> |Yes| D["Use env value"]
C --> |No| E["Use default"]
D --> F["Expose settings singleton"]
E --> F
```

**Diagram sources**
- [backend/app/config.py:23-27](file://backend/app/config.py#L23-L27)

**Section sources**
- [backend/app/config.py:15-61](file://backend/app/config.py#L15-L61)

### Database Integration
- Asynchronous engine configured with debug echo, connection pooling, and pre-ping.
- Session factory bound to the engine; dependency yields sessions and handles commit/rollback.
- Shared declarative Base used by all ORM models.

```mermaid
classDiagram
class Engine {
+create_async_engine(url, echo, pool_pre_ping, pool_size, max_overflow)
}
class AsyncSessionMaker {
+async_session_factory(bind, class_, expire_on_commit)
}
class Base {
+declarative base
}
class get_db {
+AsyncGenerator[AsyncSession]
+commit/rollback
}
Engine <.. AsyncSessionMaker : "bind"
AsyncSessionMaker <.. get_db : "yield session"
Base <.. get_db : "models inherit"
```

**Diagram sources**
- [backend/app/database.py:23-62](file://backend/app/database.py#L23-L62)

**Section sources**
- [backend/app/database.py:23-62](file://backend/app/database.py#L23-L62)

### Middleware System
- CORS: Configured via settings with allow-all methods and headers and credential support.
- Request logging: HTTP middleware that logs method, path, status code, and elapsed time.

```mermaid
flowchart TD
Start(["Incoming HTTP Request"]) --> CORS["CORS Middleware"]
CORS --> Logger["Request Logging Middleware"]
Logger --> Router["Route Dispatch"]
Router --> Handler["Endpoint Handler"]
Handler --> Resp["Response"]
Resp --> End(["Return to Client"])
```

**Diagram sources**
- [backend/app/common/middleware.py:22-59](file://backend/app/common/middleware.py#L22-L59)

**Section sources**
- [backend/app/common/middleware.py:22-59](file://backend/app/common/middleware.py#L22-L59)

### Exception Handling Patterns
- Custom exceptions encapsulate status code and detail for consistent error responses.
- Global handlers convert custom exceptions to JSON with detail and map generic exceptions to a safe internal server error.

```mermaid
flowchart TD
A["Handler raises AppException"] --> B["Global handler returns JSONResponse"]
C["Handler raises Exception"] --> D["Global handler returns 500 JSONResponse"]
B --> E["Client receives structured error"]
D --> E
```

**Diagram sources**
- [backend/app/common/exceptions.py:66-87](file://backend/app/common/exceptions.py#L66-L87)

**Section sources**
- [backend/app/common/exceptions.py:16-87](file://backend/app/common/exceptions.py#L16-L87)

### Authentication Module
- Routers: register, login, refresh, and current user profile retrieval.
- Services: password hashing/verification, JWT token creation/refresh/decoding, user registration and authentication.
- Dependencies: current user extraction for protected endpoints.

```mermaid
sequenceDiagram
participant Client as "Client"
participant AuthR as "Auth Router"
participant AuthS as "Auth Service"
participant DB as "Database"
Client->>AuthR : POST /auth/register
AuthR->>AuthS : register_user(...)
AuthS->>DB : insert User (hashed password)
DB-->>AuthS : success
AuthS-->>AuthR : User
AuthR-->>Client : 201 UserResponse
Client->>AuthR : POST /auth/login
AuthR->>AuthS : authenticate_user(...)
AuthS->>DB : select User
DB-->>AuthS : User
AuthS-->>AuthR : access_token, refresh_token
AuthR-->>Client : TokenResponse
Client->>AuthR : POST /auth/refresh
AuthR->>AuthS : decode_token(refresh)
AuthS-->>AuthR : payload
AuthR-->>Client : TokenResponse
```

**Diagram sources**
- [backend/app/auth/router.py:37-91](file://backend/app/auth/router.py#L37-L91)
- [backend/app/auth/service.py:91-165](file://backend/app/auth/service.py#L91-L165)

**Section sources**
- [backend/app/auth/router.py:1-91](file://backend/app/auth/router.py#L1-L91)
- [backend/app/auth/service.py:1-165](file://backend/app/auth/service.py#L1-L165)

### Thoughts Module
- Routers: list/create/get/update/delete thoughts with filters and pagination.
- Services: create, read, list with category/tag/status/search filters, update thought fields and tags, delete thought.

```mermaid
flowchart TD
Start(["GET /api/thoughts"]) --> Filters["Apply filters:<br/>category, tag, search, status"]
Filters --> Paginate["Order by created_at desc<br/>Offset/Limit"]
Paginate --> LoadTags["Eager load tags"]
LoadTags --> Return["Return items + total"]
```

**Diagram sources**
- [backend/app/thoughts/router.py:36-62](file://backend/app/thoughts/router.py#L36-L62)
- [backend/app/thoughts/service.py:81-134](file://backend/app/thoughts/service.py#L81-L134)

**Section sources**
- [backend/app/thoughts/router.py:1-115](file://backend/app/thoughts/router.py#L1-L115)
- [backend/app/thoughts/service.py:1-172](file://backend/app/thoughts/service.py#L1-L172)

### Tags Module
- Routers: list/create/get/update/delete tags; list with usage counts.
- Services: create tag with unique slug, list with count via left join/group by, update tag name/color, delete tag.

```mermaid
flowchart TD
A["GET /api/tags"] --> B["SELECT Tag LEFT JOIN thought_tags GROUP BY Tag.id"]
B --> C["Return TagWithCountResponse list"]
```

**Diagram sources**
- [backend/app/tags/router.py:31-34](file://backend/app/tags/router.py#L31-L34)
- [backend/app/tags/service.py:57-80](file://backend/app/tags/service.py#L57-L80)

**Section sources**
- [backend/app/tags/router.py:1-72](file://backend/app/tags/router.py#L1-L72)
- [backend/app/tags/service.py:1-102](file://backend/app/tags/service.py#L1-L102)

### AI Integration Module
- Router: endpoints for polish, summarize, suggest-tags, expand thought; depends on AI provider from factory.
- Factory: selects provider based on configuration ("openai" or "ollama"), cached as singleton.

```mermaid
classDiagram
class BaseAIProvider {
+polish_text(text, style)
+generate_summary(text, max_length)
+suggest_tags(text, max_tags)
+expand_thought(text, direction)
}
class OpenAIProvider
class OllamaProvider
class Factory {
+get_ai_provider() BaseAIProvider
}
BaseAIProvider <|-- OpenAIProvider
BaseAIProvider <|-- OllamaProvider
Factory --> BaseAIProvider : "returns instance"
```

**Diagram sources**
- [backend/app/ai/router.py:1-109](file://backend/app/ai/router.py#L1-L109)
- [backend/app/ai/factory.py:18-44](file://backend/app/ai/factory.py#L18-L44)

**Section sources**
- [backend/app/ai/router.py:1-109](file://backend/app/ai/router.py#L1-L109)
- [backend/app/ai/factory.py:1-44](file://backend/app/ai/factory.py#L1-L44)

### Publishing Module
- Router: publish a single thought to Markdown and trigger a full MkDocs build; returns messages and file paths.

**Section sources**
- [backend/app/publish/router.py:1-64](file://backend/app/publish/router.py#L1-L64)

### Sharing Module
- Router: generate share data (links and Open Graph metadata) for a thought by assembling title, slug, summary, and tag names.

**Section sources**
- [backend/app/sharing/router.py:1-46](file://backend/app/sharing/router.py#L1-L46)

### Security Considerations and CORS
- CORS: Enabled with origins from settings, credentials allowed, wildcard methods and headers.
- JWT: Secret key, algorithm, and expiry configured; tokens used for protected endpoints.
- Request logging: Captures method, path, status, and latency for observability.

**Section sources**
- [backend/app/common/middleware.py:22-36](file://backend/app/common/middleware.py#L22-L36)
- [backend/app/config.py:37-41](file://backend/app/config.py#L37-L41)
- [backend/app/common/middleware.py:40-59](file://backend/app/common/middleware.py#L40-L59)

### Request Processing Pipeline
- Order: CORS → Request Logging → Route Resolution → Endpoint Handler → Response.
- Exceptions: Global handlers convert exceptions to JSON responses.

```mermaid
sequenceDiagram
participant C as "Client"
participant CORS as "CORS Middleware"
participant LOG as "Logging Middleware"
participant RT as "Router"
participant H as "Handler"
participant EH as "Exception Handlers"
C->>CORS : HTTP Request
CORS->>LOG : Next
LOG->>RT : Next
RT->>H : Invoke handler
H-->>EH : Raise AppException or Exception?
EH-->>C : JSON error or success
```

**Diagram sources**
- [backend/app/common/middleware.py:40-59](file://backend/app/common/middleware.py#L40-L59)
- [backend/app/common/exceptions.py:66-87](file://backend/app/common/exceptions.py#L66-L87)

## Dependency Analysis
- Cohesion: Each router/package encapsulates a bounded context (auth, thoughts, tags, AI, publish, share).
- Coupling: Routers depend on services; services depend on database sessions and shared models; AI router depends on factory/provider abstractions.
- External dependencies: FastAPI, Starlette (CORS), SQLAlchemy asyncio, Pydantic, passlib, python-jose, slugify, alembic.

```mermaid
graph LR
MAIN["main.py"] --> AUTH_R["auth/router.py"]
MAIN --> THOUGHTS_R["thoughts/router.py"]
MAIN --> TAGS_R["tags/router.py"]
MAIN --> AI_R["ai/router.py"]
MAIN --> PUBLISH_R["publish/router.py"]
MAIN --> SHARE_R["sharing/router.py"]
AUTH_R --> AUTH_S["auth/service.py"]
THOUGHTS_R --> THOUGHTS_S["thoughts/service.py"]
TAGS_R --> TAGS_S["tags/service.py"]
AI_R --> AI_F["ai/factory.py"]
AUTH_S --> DB["database.py"]
THOUGHTS_S --> DB
TAGS_S --> DB
AI_SVC["ai service usage"] --> DB
PUBLISH_S["publish service usage"] --> DB
SHARE_S["share service usage"] --> DB
AUTH_R --> CM["common/models.py"]
THOUGHTS_R --> CM
TAGS_R --> CM
SHARE_R --> CM
```

**Diagram sources**
- [backend/app/main.py:58-71](file://backend/app/main.py#L58-L71)
- [backend/app/auth/router.py:1-91](file://backend/app/auth/router.py#L1-L91)
- [backend/app/thoughts/router.py:1-115](file://backend/app/thoughts/router.py#L1-L115)
- [backend/app/tags/router.py:1-72](file://backend/app/tags/router.py#L1-L72)
- [backend/app/ai/router.py:1-109](file://backend/app/ai/router.py#L1-L109)
- [backend/app/publish/router.py:1-64](file://backend/app/publish/router.py#L1-L64)
- [backend/app/sharing/router.py:1-46](file://backend/app/sharing/router.py#L1-L46)
- [backend/app/database.py:23-62](file://backend/app/database.py#L23-L62)
- [backend/app/common/models.py:40-76](file://backend/app/common/models.py#L40-L76)

**Section sources**
- [backend/app/main.py:58-71](file://backend/app/main.py#L58-L71)

## Performance Considerations
- Asynchronous database: Uses SQLAlchemy asyncio to avoid blocking I/O.
- Connection pooling: Configured pool size and overflow to handle concurrent requests.
- Pagination and eager loading: Thought listing uses pagination and selectinload to reduce N+1 queries.
- Caching: AI provider is cached as a singleton to avoid repeated instantiation.
- Logging overhead: Request logging measures latency; keep enabled in production for observability.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Health check: Use GET /health to verify application availability and version.
- CORS errors: Verify allowed origins match the frontend origin.
- Authentication failures: Check JWT secret, algorithm, and expiry settings; ensure user is active.
- Database connectivity: Confirm DATABASE_URL and pool settings; enable DEBUG to see SQL logs.
- AI provider errors: Ensure AI_PROVIDER is set to supported values and provider endpoints are reachable.

**Section sources**
- [backend/app/main.py:74-87](file://backend/app/main.py#L74-L87)
- [backend/app/common/middleware.py:22-36](file://backend/app/common/middleware.py#L22-L36)
- [backend/app/config.py:37-57](file://backend/app/config.py#L37-L57)
- [backend/app/database.py:23-30](file://backend/app/database.py#L23-L30)

## Conclusion
PolaZhenJing’s backend is a modular, layered FastAPI application with centralized configuration, robust middleware and exception handling, and a clean separation between routers and services. It integrates asynchronously with PostgreSQL, enforces security via CORS and JWT, and exposes focused APIs for authentication, thought management, tagging, AI assistance, publishing, and sharing. The architecture supports scalability and maintainability while keeping cross-cutting concerns explicit and configurable.