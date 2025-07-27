# Personal Finance Dashboard Backend

FastAPI backend for the Personal Finance Dashboard application.

## Setup

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

3. Copy `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Development

### Running tests
```bash
pytest
```

### Code formatting
```bash
black .
isort .
flake8
```

### Pre-commit hooks
```bash
pre-commit install
pre-commit run --all-files
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc