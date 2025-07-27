# Personal Finance Dashboard

A single-user personal finance dashboard built with React (Frontend) and FastAPI (Backend). Features portfolio management, pension tracking, YNAB integration, and financial data visualization.

## Project Structure

```
personal-finance-dashboard/
├── backend/          # FastAPI backend
├── docs/            # Project documentation
├── docker-compose.yml
└── README.md
```

## Quick Start

### Using Docker (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the API:**
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/health

3. **Initialize the database (first time only):**
   ```bash
   docker-compose exec backend python scripts/init_db.py
   ```

### Development Setup

For local development without Docker:

1. **Backend:**
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   cp .env.example .env
   # Edit .env with your settings
   alembic upgrade head
   python scripts/init_db.py
   uvicorn app.main:app --reload
   ```

2. **Database:**
   - PostgreSQL: Ensure PostgreSQL is running on localhost:5432
   - Or use SQLite: Update DATABASE_URL in .env to use sqlite:///./finance_dashboard.db

## API Documentation

Once the backend is running:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Test Credentials
- Email: `test@example.com`
- Password: `testpass`

## Development

### Running Tests
```bash
cd backend
pytest
```

### Code Formatting
```bash
cd backend
black .
isort .
flake8
```

## Project Status

**Milestone 1: COMPLETED** ✅
- [x] Backend Project Setup
- [x] Database Setup with SQLAlchemy and Alembic
- [x] JWT Authentication System
- [x] Core Data Models (User, Portfolio, Holdings, Transactions, Pension, Settings)
- [x] Basic CRUD APIs for Portfolios and Settings
- [x] Containerization with Docker

**Next Steps:**
- Milestone 2: Core Backend Integrations & Data Management
- Milestone 3: Frontend Foundation & Core Views
- Milestone 4: Portfolio Management & Transaction Features
- Milestone 5: Pension Tracking & YNAB Integration
- Milestone 6: Settings, Reporting & Polish

See [milestone-plan.md](docs/milestone-plan.md) for the complete development roadmap.