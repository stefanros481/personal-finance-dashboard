# Personal Finance Dashboard Makefile
# Provides convenient commands for development workflow

.PHONY: help setup start start-dev stop restart clean build logs ps
.PHONY: backend-setup backend-install backend-dev backend-shell
.PHONY: db-init db-migrate db-reset db-shell
.PHONY: lint format test test-cov pre-commit
.PHONY: docs docs-redoc shell

# Default target
.DEFAULT_GOAL := help

# Colors for terminal output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

## Show this help message
help:
	@echo "$(BLUE)Personal Finance Dashboard - Available Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)🚀 Development Workflow:$(RESET)"
	@echo "  $(YELLOW)setup$(RESET)           - Initial project setup"
	@echo "  $(YELLOW)start$(RESET)           - Start all services with Docker Compose"
	@echo "  $(YELLOW)start-dev$(RESET)       - Start services in development mode"
	@echo "  $(YELLOW)stop$(RESET)            - Stop all services"
	@echo "  $(YELLOW)restart$(RESET)         - Restart all services"
	@echo "  $(YELLOW)build$(RESET)           - Build Docker images"
	@echo ""
	@echo "$(GREEN)🔧 Backend Development:$(RESET)"
	@echo "  $(YELLOW)backend-setup$(RESET)   - Setup backend environment with uv"
	@echo "  $(YELLOW)backend-install$(RESET) - Install backend dependencies"
	@echo "  $(YELLOW)backend-dev$(RESET)     - Run backend in development mode"
	@echo "  $(YELLOW)backend-shell$(RESET)   - Enter backend container shell"
	@echo ""
	@echo "$(GREEN)🗄️  Database Commands:$(RESET)"
	@echo "  $(YELLOW)db-init$(RESET)         - Initialize database"
	@echo "  $(YELLOW)db-migrate$(RESET)      - Run database migrations"
	@echo "  $(YELLOW)db-reset$(RESET)        - Reset database (drop and recreate)"
	@echo "  $(YELLOW)db-shell$(RESET)        - Connect to database shell"
	@echo ""
	@echo "$(GREEN)🧹 Code Quality:$(RESET)"
	@echo "  $(YELLOW)lint$(RESET)            - Run all linting tools"
	@echo "  $(YELLOW)format$(RESET)          - Format code with black and isort"
	@echo "  $(YELLOW)test$(RESET)            - Run tests"
	@echo "  $(YELLOW)test-cov$(RESET)        - Run tests with coverage"
	@echo "  $(YELLOW)pre-commit$(RESET)      - Setup and run pre-commit hooks"
	@echo ""
	@echo "$(GREEN)📚 Documentation:$(RESET)"
	@echo "  $(YELLOW)docs$(RESET)            - Open API documentation"
	@echo "  $(YELLOW)docs-redoc$(RESET)      - Open ReDoc documentation"
	@echo ""
	@echo "$(GREEN)🔍 Monitoring & Debug:$(RESET)"
	@echo "  $(YELLOW)logs$(RESET)            - View logs from all services"
	@echo "  $(YELLOW)logs-backend$(RESET)    - View backend logs specifically"
	@echo "  $(YELLOW)ps$(RESET)              - Show running containers"
	@echo "  $(YELLOW)shell$(RESET)           - Interactive shell in backend container"
	@echo "  $(YELLOW)clean$(RESET)           - Clean up Docker containers and volumes"

# =============================================================================
# Development Workflow
# =============================================================================

## Initial project setup
setup:
	@echo "$(BLUE)🔧 Setting up Personal Finance Dashboard...$(RESET)"
	@echo "$(GREEN)✓ Checking Docker installation...$(RESET)"
	@docker --version || (echo "$(RED)❌ Docker not found. Please install Docker first.$(RESET)" && exit 1)
	@docker-compose --version || (echo "$(RED)❌ Docker Compose not found. Please install Docker Compose first.$(RESET)" && exit 1)
	@echo "$(GREEN)✓ Docker installation verified$(RESET)"
	@echo "$(GREEN)✓ Project setup complete!$(RESET)"
	@echo "$(YELLOW)💡 Next steps:$(RESET)"
	@echo "   1. Run '$(YELLOW)make start$(RESET)' to start all services"
	@echo "   2. Visit http://localhost:8000/api/docs for API documentation"

## Start all services with Docker Compose
start:
	@echo "$(BLUE)🚀 Starting Personal Finance Dashboard...$(RESET)"
	@chmod +x start.sh
	@./start.sh

## Start services in development mode
start-dev:
	@echo "$(BLUE)🔧 Starting services in development mode...$(RESET)"
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✓ Development services started$(RESET)"
	@echo "$(YELLOW)📋 Available services:$(RESET)"
	@echo "   • API Documentation: http://localhost:8000/api/docs"
	@echo "   • API Health Check: http://localhost:8000/health"

## Stop all services
stop:
	@echo "$(BLUE)🛑 Stopping all services...$(RESET)"
	@docker-compose down
	@echo "$(GREEN)✓ All services stopped$(RESET)"

## Restart all services
restart: stop start

## Build Docker images
build:
	@echo "$(BLUE)🔨 Building Docker images...$(RESET)"
	@docker-compose build
	@echo "$(GREEN)✓ Docker images built$(RESET)"

# =============================================================================
# Backend Development
# =============================================================================

## Setup backend environment with uv
backend-setup:
	@echo "$(BLUE)🔧 Setting up backend environment...$(RESET)"
	@cd backend && uv venv
	@echo "$(GREEN)✓ Virtual environment created$(RESET)"
	@echo "$(YELLOW)💡 Activate with: source backend/.venv/bin/activate$(RESET)"

## Install backend dependencies
backend-install:
	@echo "$(BLUE)📦 Installing backend dependencies...$(RESET)"
	@cd backend && uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Backend dependencies installed$(RESET)"

## Run backend in development mode (local)
backend-dev:
	@echo "$(BLUE)🔧 Starting backend in development mode...$(RESET)"
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Enter backend container shell
backend-shell:
	@docker-compose exec backend bash

# =============================================================================
# Database Commands
# =============================================================================

## Initialize database
db-init:
	@echo "$(BLUE)🗄️  Initializing database...$(RESET)"
	@docker-compose exec backend python scripts/init_db.py
	@echo "$(GREEN)✓ Database initialized$(RESET)"

## Run database migrations
db-migrate:
	@echo "$(BLUE)⬆️  Running database migrations...$(RESET)"
	@docker-compose exec backend alembic upgrade head
	@echo "$(GREEN)✓ Database migrations completed$(RESET)"

## Reset database (drop and recreate)
db-reset:
	@echo "$(RED)⚠️  This will delete all data! Press Ctrl+C to cancel...$(RESET)"
	@sleep 3
	@echo "$(BLUE)🔄 Resetting database...$(RESET)"
	@docker-compose down -v
	@docker-compose up -d db redis
	@sleep 5
	@docker-compose up -d backend
	@sleep 10
	@make db-init
	@echo "$(GREEN)✓ Database reset completed$(RESET)"

## Connect to database shell
db-shell:
	@echo "$(BLUE)🗄️  Connecting to database...$(RESET)"
	@docker-compose exec db psql -U finance_user -d finance_dashboard

# =============================================================================
# Code Quality
# =============================================================================

## Run all linting tools
lint:
	@echo "$(BLUE)🧹 Running linting tools...$(RESET)"
	@cd backend && python -m black --check .
	@cd backend && python -m isort --check-only .
	@cd backend && python -m flake8
	@cd backend && python -m mypy .
	@echo "$(GREEN)✓ All linting checks passed$(RESET)"

## Format code with black and isort
format:
	@echo "$(BLUE)🎨 Formatting code...$(RESET)"
	@cd backend && python -m black .
	@cd backend && python -m isort .
	@echo "$(GREEN)✓ Code formatted$(RESET)"

## Run tests
test:
	@echo "$(BLUE)🧪 Running tests...$(RESET)"
	@cd backend && python -m pytest
	@echo "$(GREEN)✓ Tests completed$(RESET)"

## Run tests with coverage
test-cov:
	@echo "$(BLUE)🧪 Running tests with coverage...$(RESET)"
	@cd backend && python -m pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Tests with coverage completed$(RESET)"
	@echo "$(YELLOW)📊 Coverage report: backend/htmlcov/index.html$(RESET)"

## Setup and run pre-commit hooks
pre-commit:
	@echo "$(BLUE)🔧 Setting up pre-commit hooks...$(RESET)"
	@cd backend && pre-commit install
	@cd backend && pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit hooks configured and run$(RESET)"

# =============================================================================
# Documentation
# =============================================================================

## Open API documentation
docs:
	@echo "$(BLUE)📚 Opening API documentation...$(RESET)"
	@open http://localhost:8000/api/docs 2>/dev/null || echo "$(YELLOW)Visit: http://localhost:8000/api/docs$(RESET)"

## Open ReDoc documentation
docs-redoc:
	@echo "$(BLUE)📚 Opening ReDoc documentation...$(RESET)"
	@open http://localhost:8000/api/redoc 2>/dev/null || echo "$(YELLOW)Visit: http://localhost:8000/api/redoc$(RESET)"

# =============================================================================
# Monitoring & Debug
# =============================================================================

## View logs from all services
logs:
	@docker-compose logs -f

## View backend logs specifically
logs-backend:
	@docker-compose logs -f backend

## Show running containers
ps:
	@docker-compose ps

## Interactive shell in backend container
shell:
	@docker-compose exec backend bash

## Clean up Docker containers and volumes
clean:
	@echo "$(RED)⚠️  This will remove all containers and volumes! Press Ctrl+C to cancel...$(RESET)"
	@sleep 3
	@echo "$(BLUE)🧹 Cleaning up Docker resources...$(RESET)"
	@docker-compose down -v --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✓ Cleanup completed$(RESET)"