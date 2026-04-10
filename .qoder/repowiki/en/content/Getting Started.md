# Getting Started

<cite>
**Referenced Files in This Document**
- [docker-compose.yml](file://docker-compose.yml)
- [backend/Dockerfile](file://backend/Dockerfile)
- [frontend/Dockerfile](file://frontend/Dockerfile)
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/config.py](file://backend/app/config.py)
- [backend/requirements.txt](file://backend/requirements.txt)
- [backend/alembic.ini](file://backend/alembic.ini)
- [backend/app/database.py](file://backend/app/database.py)
- [backend/migrations/env.py](file://backend/migrations/env.py)
- [backend/app/auth/router.py](file://backend/app/auth/router.py)
- [backend/app/auth/schemas.py](file://backend/app/auth/schemas.py)
- [backend/app/thoughts/models.py](file://backend/app/thoughts/models.py)
- [frontend/src/api/client.ts](file://frontend/src/api/client.ts)
- [frontend/src/pages/Login.tsx](file://frontend/src/pages/Login.tsx)
- [frontend/src/pages/Register.tsx](file://frontend/src/pages/Register.tsx)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites and System Requirements](#prerequisites-and-system-requirements)
3. [Development Environment Setup](#development-environment-setup)
4. [Database Configuration](#database-configuration)
5. [Local Deployment with Docker Compose](#local-deployment-with-docker-compose)
6. [Initial Application Setup](#initial-application-setup)
7. [Environment Variable Configuration](#environment-variable-configuration)
8. [First-Time User Onboarding](#first-time-user-onboarding)
9. [Running the Application Locally](#running-the-application-locally)
10. [Accessing the Dashboard and Creating Your First Thought](#accessing-the-dashboard-and-creating-your-first-thought)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Verification Steps](#verification-steps)
13. [Conclusion](#conclusion)

## Introduction
This guide helps you set up PolaZhenJing locally using Docker Compose. It covers prerequisites, environment setup, database configuration, local deployment, initial configuration, environment variables, onboarding, and first-time usage. By the end, you will have a working instance with a PostgreSQL database, a FastAPI backend, and a React frontend, plus a first thought created in the system.

## Prerequisites and System Requirements
- Operating system: macOS, Linux, or Windows with Docker Desktop
- Docker Engine and Docker Compose installed and running
- At least 4 GB RAM recommended for smooth operation
- Ports 5432 (PostgreSQL), 8000 (backend), and 5173 (frontend) should be free on your host

**Section sources**
- [docker-compose.yml:9-67](file://docker-compose.yml#L9-L67)

## Development Environment Setup
- Clone the repository to your machine
- Ensure Docker and Docker Compose are installed and accessible from your terminal
- Verify Docker daemon is running

[No sources needed since this section provides general guidance]

## Database Configuration
PolaZhenJing uses PostgreSQL for persistence. The compose file provisions a Postgres 16 container with a dedicated volume for data persistence. The backend connects using an async SQLAlchemy engine configured via environment variables.

Key points:
- Database image: postgres:16-alpine
- Volume: pgdata persists data across container restarts
- Health check ensures readiness before backend starts
- Backend uses DATABASE_URL to connect to the database

**Section sources**
- [docker-compose.yml:10-27](file://docker-compose.yml#L10-L27)
- [backend/app/database.py:24-36](file://backend/app/database.py#L24-L36)
- [backend/app/config.py:34-36](file://backend/app/config.py#L34-L36)

## Local Deployment with Docker Compose
Follow these steps to bring up the stack:

1. Build images and start services:
   - docker-compose up --build
2. Wait for all containers to become healthy:
   - The db service healthcheck runs a readiness probe against the database
   - The backend waits for the db to be healthy before starting
3. Access the backend health endpoint to confirm it’s ready:
   - curl http://localhost:8000/health

Notes:
- The backend exposes port 8000
- The frontend exposes port 5173
- Volumes mount the source code for live reload during development

**Section sources**
- [docker-compose.yml:28-63](file://docker-compose.yml#L28-L63)
- [backend/Dockerfile:8-29](file://backend/Dockerfile#L8-L29)
- [frontend/Dockerfile:8-20](file://frontend/Dockerfile#L8-L20)
- [backend/app/main.py:74-88](file://backend/app/main.py#L74-L88)

## Initial Application Setup
After the stack is healthy, initialize the database schema using Alembic migrations.

Steps:
1. Run migrations inside the backend container:
   - docker-compose exec backend alembic upgrade head
2. Confirm migrations applied:
   - docker-compose exec backend alembic current

What happens:
- Alembic reads DATABASE_URL from environment variables
- It detects all ORM models and applies pending migrations
- The offline/online migration environment is configured in env.py

**Section sources**
- [backend/alembic.ini:4-6](file://backend/alembic.ini#L4-L6)
- [backend/migrations/env.py:14-48](file://backend/migrations/env.py#L14-L48)

## Environment Variable Configuration
Configure runtime behavior via environment variables. The backend loads settings from a .env file and supports overrides via docker-compose environment blocks.

Critical variables (default values shown in compose):
- DATABASE_URL: postgresql+asyncpg://polazj:polazj_secret@db:5432/polazj_db
- JWT_SECRET_KEY: change-me-in-production-use-strong-secret
- AI_PROVIDER: openai
- OPENAI_API_KEY: (optional)
- OPENAI_BASE_URL: https://api.openai.com/v1
- OLLAMA_BASE_URL: http://host.docker.internal:11434
- SITE_BASE_URL: https://yourusername.github.io/PolaZhenJing

Notes:
- The backend also defines CORS_ORIGINS for frontend origins
- The frontend Axios client sends requests to the backend proxy path

**Section sources**
- [docker-compose.yml:34-42](file://docker-compose.yml#L34-L42)
- [backend/app/config.py:23-57](file://backend/app/config.py#L23-L57)
- [frontend/src/api/client.ts:14-17](file://frontend/src/api/client.ts#L14-L17)

## First-Time User Onboarding
New users register and log in to the system. The frontend provides dedicated pages for registration and login.

Flow:
1. Visit the frontend at http://localhost:5173
2. Navigate to the registration page and fill out the form
3. Submit to create a new user account
4. Go to the login page and enter credentials
5. After successful login, you are redirected to the dashboard

Behind the scenes:
- Registration and login endpoints are defined in the backend auth router
- Request schemas enforce field constraints (e.g., minimum length for username/password)
- Successful login returns JWT tokens stored by the frontend

**Section sources**
- [frontend/src/pages/Register.tsx:17-33](file://frontend/src/pages/Register.tsx#L17-L33)
- [frontend/src/pages/Login.tsx:17-31](file://frontend/src/pages/Login.tsx#L17-L31)
- [backend/app/auth/router.py:37-68](file://backend/app/auth/router.py#L37-L68)
- [backend/app/auth/schemas.py:19-31](file://backend/app/auth/schemas.py#L19-L31)

## Running the Application Locally
Once everything is built and migrated:

1. Start the stack:
   - docker-compose up --build
2. Confirm backend health:
   - curl http://localhost:8000/health
3. Open the frontend in your browser:
   - http://localhost:5173

Optional: Tail logs for debugging
- docker-compose logs -f backend
- docker-compose logs -f frontend

**Section sources**
- [docker-compose.yml:28-63](file://docker-compose.yml#L28-L63)
- [backend/app/main.py:74-88](file://backend/app/main.py#L74-L88)

## Accessing the Dashboard and Creating Your First Thought
After logging in, you land on the dashboard. From here, create your first thought:

1. Open the editor from the dashboard
2. Enter a title and content
3. Optionally add tags and set a category
4. Save as draft or publish directly

Under the hood:
- The Thought model defines fields like title, slug, content, summary, category, status, author, and tags
- Status defaults to draft; published thoughts are publicly shareable
- Tags are many-to-many via an association table

**Section sources**
- [backend/app/thoughts/models.py:30-66](file://backend/app/thoughts/models.py#L30-L66)

## Troubleshooting Guide
Common issues and resolutions:

- Backend cannot connect to database:
  - Ensure the db container is healthy and the database URL matches compose service name and credentials
  - Check that migrations were applied after bringing up the stack
  - Reference: [docker-compose.yml:14-26](file://docker-compose.yml#L14-L26), [backend/app/database.py:24-36](file://backend/app/database.py#L24-L36)

- Port conflicts:
  - Change exposed ports in docker-compose.yml if 5432, 8000, or 5173 are in use
  - Reference: [docker-compose.yml:18-21](file://docker-compose.yml#L18-L21), [docker-compose.yml:42-43](file://docker-compose.yml#L42-L43), [docker-compose.yml:57-58](file://docker-compose.yml#L57-L58)

- JWT errors or unauthorized responses:
  - Verify JWT_SECRET_KEY is set consistently across backend and frontend
  - Ensure the Axios client attaches Authorization headers automatically
  - Reference: [backend/app/config.py:37-41](file://backend/app/config.py#L37-L41), [frontend/src/api/client.ts:19-26](file://frontend/src/api/client.ts#L19-L26)

- Migration failures:
  - Re-run migrations inside the backend container
  - Confirm DATABASE_URL in alembic.ini matches the backend environment
  - Reference: [backend/migrations/env.py:37-48](file://backend/migrations/env.py#L37-L48), [backend/alembic.ini:4-6](file://backend/alembic.ini#L4-L6)

- AI provider configuration:
  - Set OPENAI_API_KEY and OPENAI_BASE_URL or configure OLLAMA_BASE_URL depending on AI_PROVIDER
  - Reference: [backend/app/config.py:43-49](file://backend/app/config.py#L43-L49), [docker-compose.yml:37-40](file://docker-compose.yml#L37-L40)

**Section sources**
- [docker-compose.yml:14-26](file://docker-compose.yml#L14-L26)
- [backend/app/database.py:24-36](file://backend/app/database.py#L24-L36)
- [backend/app/config.py:37-49](file://backend/app/config.py#L37-L49)
- [frontend/src/api/client.ts:19-26](file://frontend/src/api/client.ts#L19-L26)
- [backend/migrations/env.py:37-48](file://backend/migrations/env.py#L37-L48)
- [backend/alembic.ini:4-6](file://backend/alembic.ini#L4-L6)

## Verification Steps
Confirm a successful installation with these checks:

- Backend health:
  - curl http://localhost:8000/health returns status "ok" with app name and version
  - Reference: [backend/app/main.py:74-88](file://backend/app/main.py#L74-L88)

- Database connectivity:
  - docker-compose exec backend python -c "from app.database import engine; print('Connected')"
  - Reference: [backend/app/database.py:24-36](file://backend/app/database.py#L24-L36)

- Migrations applied:
  - docker-compose exec backend alembic current shows the latest revision
  - Reference: [backend/migrations/env.py:51-54](file://backend/migrations/env.py#L51-L54)

- Frontend reachable:
  - Open http://localhost:5173 and verify the login/register pages
  - Reference: [frontend/src/pages/Login.tsx:34-51](file://frontend/src/pages/Login.tsx#L34-L51), [frontend/src/pages/Register.tsx:36-51](file://frontend/src/pages/Register.tsx#L36-L51)

- Authentication flow:
  - Register a user, log in, and verify JWT tokens are stored and refreshed automatically
  - Reference: [backend/app/auth/router.py:37-91](file://backend/app/auth/router.py#L37-L91), [frontend/src/api/client.ts:28-60](file://frontend/src/api/client.ts#L28-L60)

**Section sources**
- [backend/app/main.py:74-88](file://backend/app/main.py#L74-L88)
- [backend/app/database.py:24-36](file://backend/app/database.py#L24-L36)
- [backend/migrations/env.py:51-54](file://backend/migrations/env.py#L51-L54)
- [frontend/src/pages/Login.tsx:34-51](file://frontend/src/pages/Login.tsx#L34-L51)
- [frontend/src/pages/Register.tsx:36-51](file://frontend/src/pages/Register.tsx#L36-L51)
- [backend/app/auth/router.py:37-91](file://backend/app/auth/router.py#L37-L91)
- [frontend/src/api/client.ts:28-60](file://frontend/src/api/client.ts#L28-L60)

## Conclusion
You now have a fully functional local instance of PolaZhenJing. The stack includes PostgreSQL, a FastAPI backend, and a React frontend, with automated migrations and a secure JWT-based authentication flow. Use the dashboard to onboard as a new user and create your first thought. For production, rotate secrets, configure AI providers, and review CORS origins.

[No sources needed since this section summarizes without analyzing specific files]