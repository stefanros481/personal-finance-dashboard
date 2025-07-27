# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **single-user personal finance dashboard** built with FastAPI (backend) and designed for React (frontend). It provides portfolio management, pension tracking, YNAB integration, and financial data visualization capabilities.

## Essential Commands

### Development Workflow
- `make start` - Start all services using Docker Compose (uses start.sh script)
- `make start-dev` - Start services in development mode with hot reload
- `make stop` - Stop all services
- `make build` - Build Docker images

### Backend Development  
- `make backend-setup` - Setup backend environment with uv
- `make backend-install` - Install backend dependencies with uv
- `make backend-dev` - Run backend locally with hot reload
- `cd backend && uvicorn app.main:app --reload` - Direct backend development server

### Database Operations
- `make db-init` - Initialize database with test data
- `make db-migrate` - Run Alembic migrations
- `make db-reset` - Reset database (destructive operation)
- `docker-compose exec backend alembic upgrade head` - Direct migration command

### Code Quality & Testing
- `make test` - Run pytest test suite
- `make lint` - Run black, isort, flake8, mypy
- `make format` - Format code with black and isort
- `cd backend && pytest` - Direct test execution
- `cd backend && pytest --cov=app --cov-report=html` - Test with coverage

### Documentation & Monitoring
- `make docs` - Open API documentation at http://localhost:8000/api/docs
- `make logs` - View all service logs
- `make logs-backend` - View backend logs only

## Architecture Overview

### Backend Structure (FastAPI)
```
backend/app/
├── api/v1/           # API endpoints organized by domain
│   ├── auth.py       # JWT authentication
│   ├── portfolios.py # Portfolio CRUD and holdings
│   ├── settings.py   # User settings management
│   └── health.py     # Health checks
├── core/             # Core configuration and utilities
│   ├── config.py     # Pydantic settings with environment variables
│   ├── security.py   # JWT utilities, password hashing
│   ├── database.py   # SQLAlchemy setup and session management
│   └── deps.py       # FastAPI dependencies (auth, DB)
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic models for request/response validation
└── services/         # Business logic and external integrations
```

### Key Architectural Patterns

**API Structure**: All endpoints use `/api/v1/` prefix. Documentation available at `/api/docs`, not `/docs`.

**Database Models**: Uses SQLAlchemy with Alembic migrations. Core entities:
- `User` (single-user application)
- `Portfolio` → `Holding` → `Transaction` (portfolio hierarchy)
- `PensionAccount` → `PensionValueEntry` (pension tracking)
- `Settings` (user preferences)

**Authentication**: JWT-based with `python-jose` and `passlib[bcrypt]`. Access tokens expire in 30 minutes.

**Configuration**: Pydantic Settings loads from environment variables. Uses `.env` for local development.

**Dependencies**: Project uses `uv` for dependency management, not pip or poetry.

### Data Flow & Business Logic

**Portfolio Calculations**: 
- `current_quantity` and `average_cost_per_share` are derived from transactions
- Supports multiple currencies with exchange rate tracking
- Handles buy/sell transactions with commission calculations

**Third-Party Integrations**: 
- Backend acts as secure proxy for YNAB API (API keys stored server-side only)
- yfinance integration for stock data with Redis caching (15-minute cache)
- Historical data stored in database for performance

**Security Model**:
- Single-user application with JWT authentication
- All sensitive API keys (YNAB, etc.) stored as environment variables
- Frontend never sees third-party API keys

## Development Context

**Current Status**: Milestone 1 completed (basic backend infrastructure, auth, core models, Docker setup)

**Testing**: Uses pytest with FastAPI TestClient. Database tests should use test database or transactions that rollback.

**Code Style**: Black (line-length 88), isort (black profile), flake8, mypy with strict typing.

**Docker Setup**: 
- Backend runs on port 8000
- PostgreSQL on port 5432 
- Redis on port 6379
- All services orchestrated with docker-compose

## Important Implementation Notes

**Database Relationships**: Portfolios contain Holdings, Holdings contain Transactions. Deleting a portfolio cascades to its holdings and transactions.

**API Versioning**: All endpoints prefixed with `/api/v1/`. OpenAPI docs served at `/api/docs`.

**Environment Configuration**: Uses Pydantic Settings for type-safe environment variable loading. Required vars: `SECRET_KEY`, `DATABASE_URL`.

**Error Handling**: FastAPI exception handlers return structured JSON errors. Use appropriate HTTP status codes (400, 401, 404, 422, 500).

**Async/Await**: FastAPI endpoints can be async where beneficial, especially for database operations and external API calls.

## Key Files to Understand

- `backend/app/main.py` - FastAPI application setup, CORS, middleware
- `backend/app/core/config.py` - Environment configuration and settings
- `backend/app/api/v1/api.py` - Main API router that includes all endpoint modules
- `backend/pyproject.toml` - Project dependencies and tool configuration
- `docker-compose.yml` - Service orchestration for development
- `start.sh` - Project startup script with health checks and database initialization