# Backend Architecture: FastAPI Backend Proxy

## 1. Introduction

### 1.1. Purpose
This document outlines the backend architecture for the Personal Finance Dashboard, focusing on the FastAPI service that will act as a proxy, data manager, and API layer for the frontend application.

### 1.2. Goals
Given this is a **single-user application**, the primary architectural goals for the backend are **security** (especially for API keys), **reliability** in data retrieval and processing, **maintainability**, and ensuring **data integrity**. Performance will be optimized for responsive API calls and efficient data processing.

## 2. Technology Stack Justification

### 2.1. Core Technologies
* **Python:** A versatile language well-suited for backend development, data processing, and scripting. Its rich ecosystem (FastAPI, SQLAlchemy, pandas, yfinance) makes it efficient for this project's requirements.
* **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. It offers automatic interactive API documentation (Swagger UI/ReDoc), data validation, and serialization, significantly accelerating API development.
* **Database:** **PostgreSQL** (or SQLite for initial local development)
    * **Justification:** PostgreSQL is a robust, open-source relational database known for its reliability, feature set, and strong support for data integrity. For a single-user application, SQLite could serve as a simpler, file-based database for initial local development and testing, offering quick setup without a separate database server. PostgreSQL provides a clear path for future scalability if needed.
* **ORM/ODM:** **SQLAlchemy**
    * **Justification:** A powerful and flexible SQL toolkit and Object-Relational Mapper (ORM) for Python. It provides a full suite of well-known enterprise-level persistence patterns, making database interactions robust, scalable, and maintainable. It supports various databases including PostgreSQL and SQLite. We will use **Alembic** for database migrations alongside SQLAlchemy to manage schema changes effectively.

### 2.2. Other Key Libraries/Tools
* **Dependency Management:** **uv/Astral**
    * **Justification:** uv/Astral (uv project from Astral) is a fast, modern Python package installer and resolver, designed for speed and reliability, significantly improving dependency management and environment setup compared to traditional tools.
* **Caching:** **Redis**
    * **Justification:** An in-memory data store used as a caching layer for `yfinance` data (stock prices, historical data) to reduce external API calls and improve response times. Its speed and versatility make it ideal for temporary, frequently accessed data.
* **Authentication/Authorization:** `python-jose` (for JWT handling), `passlib` (for password hashing)
* **Testing:** `pytest` (for unit and integration testing)
* **Linting/Formatting:** `Black` (uncompromising code formatter), `Flake8` (linter), `Isort` (sorts imports)

## 3. Data Model & Database Design

### 3.1. Database Schema
* **User (Single User Model):**
    * `id` (PK, UUID)
    * `username` (Unique)
    * `hashed_password`
    * `retirement_goal_amount` (Float, nullable)
    * `retirement_goal_year` (Integer, nullable)
* **Portfolio:**
    * `id` (PK, UUID)
    * `user_id` (FK to User)
    * `name` (String)
    * `brokerage_firm` (String)
    * `currency` (String, e.g., "NOK", "USD")
    * `used_credit` (Float)
* **Holding:**
    * `id` (PK, UUID)
    * `portfolio_id` (FK to Portfolio)
    * `ticker` (String)
    * `company_name` (String) - **NEW: Added based on clarification**
    * `current_quantity` (Float) - *Derived from transactions, potentially stored for quick lookup.*
    * `average_cost_per_share` (Float) - *Derived from transactions, potentially stored for quick lookup.*
* **Transaction:**
    * `id` (PK, UUID)
    * `holding_id` (FK to Holding)
    * `date` (Date/DateTime)
    * `quantity` (Float)
    * `price` (Float)
    * `type` (String, e.g., "buy", "sell")
    * `commission` (Float)
    * `exchange_rate` (Float)
    * `average_cost_per_share_at_transaction` (Float) - **NEW: Added based on clarification.** This value is calculated and stored at the time of import or manual entry.
* **PensionAccount:**
    * `id` (PK, UUID)
    * `user_id` (FK to User)
    * `name` (String)
    * `ynab_account_id` (String, nullable)
    * `currency` (String)
* **PensionValueEntry:**
    * `id` (PK, UUID)
    * `pension_account_id` (FK to PensionAccount)
    * `date` (Date)
    * `value` (Float)
    * **Note:** The current summarized value for a `PensionAccount` is derived from the `PensionValueEntry` with the most recent `date` for that account.
* **HistoricalExchangeRate:**
    * `id` (PK, UUID)
    * `base_currency` (String)
    * `target_currency` (String)
    * `date` (Date)
    * `rate` (Float)
* **StockMetadata:**
    * `id` (PK, UUID)
    * `ticker` (String, Unique)
    * `company_name` (String)
    * `exchange` (String)
    * *Used for auto-complete and general stock information.*
* **HistoricalStockPrice:** - **NEW: Added based on clarification**
    * `id` (PK, UUID)
    * `ticker_id` (FK to StockMetadata or `ticker` string directly)
    * `date` (Date)
    * `close_price` (Float)
    * *Stores daily closing prices obtained from yfinance.*

### 3.2. Relationships
* `User` has many `Portfolios`.
* `Portfolio` has many `Holdings`.
* `Holding` has many `Transactions`.
* `User` has many `PensionAccounts`.
* `PensionAccount` has many `PensionValueEntries`.
* `HistoricalStockPrice` relates to `StockMetadata` (or directly by ticker).

### 3.3. Data Integrity
Data integrity will be maintained through:
* **Database Constraints:** Use of primary keys, foreign keys, unique constraints, and NOT NULL constraints to enforce relationships and data validity at the database level.
* **Pydantic Models:** FastAPI's reliance on Pydantic ensures incoming request data is validated against defined schemas before processing, preventing invalid data from reaching the application logic or database.
* **Backend Business Logic Validation:** Implement additional validation within the service layer to enforce complex business rules (e.g., ensuring sell quantity does not exceed current holding quantity, positive values for amounts).

## 4. API Design (FastAPI Endpoints)

[Define the RESTful API endpoints that the frontend will consume. Use clear, descriptive URLs and specify HTTP methods. For each endpoint, consider:
* **Endpoint URL & HTTP Method:** (e.g., `POST /api/v1/users/login`, `GET /api/v1/portfolios`, `POST /api/v1/transactions`)
* **Request Body/Query Parameters:** (Pydantic models for request validation)
* **Response Body:** (Pydantic models for response serialization)
* **Authentication:** (Which endpoints require authentication?)
* **Permissions/Authorization:** (Not complex for single-user, but note any specific checks.)
* **Error Responses:** (e.g., 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Internal Server Error)
]

### Key API Categories:
* **Authentication:**
    * `POST /api/v1/auth/login`: User login, returns JWT.
* **User/Settings:**
    * `GET /api/v1/users/me`: Get current user details.
    * `PUT /api/v1/users/me/retirement-goal`: Update retirement goal amount and year.
    * `GET /api/v1/currencies`: List available currencies.
    * `POST /api/v1/settings/ynab`: Configure YNAB budget ID (API key handled internally).
* **Portfolios:**
    * `POST /api/v1/portfolios`: Create a new portfolio.
    * `GET /api/v1/portfolios`: Get all portfolios for the user.
    * `GET /api/v1/portfolios/{portfolio_id}`: Get details of a specific portfolio.
    * `PUT /api/v1/portfolios/{portfolio_id}`: Update a portfolio.
    * `DELETE /api/v1/portfolios/{portfolio_id}`: Delete a portfolio and its associated data.
    * `PUT /api/v1/portfolios/{portfolio_id}/used-credit`: Update used credit for a portfolio.
* **Transactions:**
    * `POST /api/v1/transactions/import-csv`: Import transactions from CSV.
    * `POST /api/v1/transactions`: Manually add a transaction.
    * `PUT /api/v1/transactions/{transaction_id}`: Update a transaction.
    * `DELETE /api/v1/transactions/{transaction_id}`: Delete a transaction.
    * `GET /api/v1/holdings/{holding_id}/transactions`: Get all transactions for a specific holding (collapsible list).
* **Holdings:**
    * `GET /api/v1/portfolios/{portfolio_id}/holdings`: Get all holdings for a portfolio, including current quantity, average cost, gains/losses.
    * `DELETE /api/v1/holdings/{holding_id}`: Delete a specific holding (and its transactions).
* **Pension:**
    * `GET /api/v1/pension/accounts`: Get all pension accounts.
    * `POST /api/v1/pension/accounts`: Create a new pension account.
    * `GET /api/v1/pension/accounts/{account_id}/values`: Get historical monthly values for an account.
    * `POST /api/v1/pension/accounts/{account_id}/values`: Add a new monthly value entry.
    * `GET /api/v1/pension/projection`: Get projected pension values based on parameters.
* **Third-Party Proxies:**
    * `GET /api/v1/stocks/search`: Proxy for stock auto-complete (to `yfinance` or similar, potentially cached `StockMetadata`).
    * `GET /api/v1/stocks/{ticker}/price`: Proxy for real-time stock price (to `yfinance`, with 15-min cache).
    * `GET /api/v1/stocks/{ticker}/history`: Proxy for historical stock prices (to `yfinance`, storing in `HistoricalStockPrice`, with caching).
    * `GET /api/v1/exchange-rates/{from_currency}/{to_currency}/history`: Proxy for historical exchange rates (to `yfinance`, storing in `HistoricalExchangeRate`, with caching).
    * `GET /api/v1/ynab/accounts/{account_id}/balance`: Proxy to fetch YNAB account balance (securely using API key from `.env`).

## 5. Third-Party Integrations

### 5.1. yfinance Integration
* **Mechanism:** FastAPI will use the `yfinance` Python library directly to fetch stock data (real-time, historical prices, company information).
* **Caching:** A **15-minute cache** will be implemented using **Redis** (or an equivalent in-memory cache) for `yfinance` data (especially real-time prices and frequently accessed historical data) to minimize external API calls and improve response times.
* **Rate Limiting:** Backend logic will include safeguards (e.g., custom rate-limiting, circuit breakers) to prevent excessive calls to `yfinance` and manage potential rate limits, though `yfinance` generally has generous limits for casual use.
* **Error Handling:** `yfinance` API errors (e.g., invalid ticker, API issues) will be caught by the backend, transformed into appropriate HTTP error responses (e.g., 404 Not Found, 500 Internal Server Error), and propagated to the frontend with clear messages.

### 5.2. YNAB API Integration
* **Mechanism:** FastAPI will make HTTP requests to the YNAB API using a standard HTTP client library (e.g., `httpx` or `requests`).
* **API Key Management:** The YNAB API key will be loaded from the backend's **environment variables (`.env` file)** at application startup. It will **never be exposed to the frontend**. All YNAB-related requests from the frontend will be routed through the FastAPI backend, which will securely handle authentication with the YNAB API.
* **Error Handling:** YNAB API errors will be caught and translated into appropriate backend HTTP error responses.

## 6. Authentication & Security

### 6.1. User Authentication
* **Mechanism:** **JSON Web Tokens (JWT)** based authentication.
    * Upon successful login (username/password), the FastAPI backend will generate a short-lived Access Token (JWT) and a longer-lived Refresh Token.
    * The Access Token will be sent to the frontend for inclusion in `Authorization` headers for protected API calls. The Refresh Token can be used to obtain new Access Tokens without re-logging in.
* **Token Storage (Frontend Perspective):** The Access Token will typically be stored in client-side memory or local storage for use in API requests. (Note: Frontend architecture details specific storage).
* **Password Hashing:** User passwords will be securely hashed using **`passlib` (specifically `bcrypt`)** before storage in the database.

### 6.2. API Key Management
* All sensitive third-party API keys (YNAB, potentially yfinance if a paid API is used) are stored **exclusively in environment variables** on the server where the FastAPI application runs. They are loaded at startup and never committed to version control or exposed to the frontend.

### 6.3. Data Validation
* **Pydantic Models:** FastAPI leverages Pydantic for automatic request body validation, query parameter validation, and response serialization. This ensures that all incoming data conforms to expected schemas and all outgoing data is correctly formatted.
* **Business Logic Validation:** Additional, more complex validation rules will be applied within the service layer before data is committed to the database (e.g., checking transaction logic, ensuring unique portfolio names for a user).

### 6.4. Security Best Practices
* **HTTPS Enforcement:** The production deployment environment will enforce HTTPS for all communications between the frontend and backend.
* **CORS Configuration:** FastAPI will be configured with appropriate Cross-Origin Resource Sharing (CORS) policies to allow requests only from the trusted frontend origin.
* **SQL Injection Prevention:** SQLAlchemy ORM inherently protects against SQL injection attacks by using parameterized queries.
* **XSS/CSRF:** FastAPI/web server configurations will protect against common web vulnerabilities like Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF). For JWTs, CSRF is less of an issue compared to session-based authentication, but still considered.

## 7. Error Handling & Logging

### 7.1. Centralized Error Handling
FastAPI's exception handling mechanisms will be used.
* Custom exception handlers will be implemented for specific application errors (e.g., `NotFoundError`, `ConflictError`, `ValidationError`) to return consistent, structured JSON error responses to the frontend with appropriate HTTP status codes (e.g., 404, 409, 422).
* A default exception handler will catch unhandled exceptions and return a generic 500 Internal Server Error, preventing sensitive internal details from being exposed.

### 7.2. Logging Strategy
* Structured logging will be implemented using Python's standard `logging` module, configured to output logs in a machine-readable format (e.g., JSON).
* Logs will include request details, response status codes, error messages, and relevant context (e.g., user ID, portfolio ID).
* During **development**, logs will be output to the console.
* In **production**, logs will be written to standard output (stdout/stderr) so that they can be easily collected by container orchestration platforms (e.g., Docker, Kubernetes) or cloud logging services.

## 8. Development & Deployment

### 8.1. Project Structure
A logical and maintainable project structure for the FastAPI application:

.
├── app/
│   ├── api/                 # API routers (endpoints)
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── portfolios.py
│   │   │   ├── transactions.py
│   │   │   ├── pension.py
│   │   │   └── third_party.py
│   │   └── init.py
│   ├── core/                # Core configurations, settings, constants
│   │   ├── config.py
│   │   ├── security.py      # JWT utilities, password hashing
│   │   └── exceptions.py
│   ├── crud/                # Create, Read, Update, Delete operations for DB models
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   └── ...
│   ├── database/            # DB connection, session management, models
│   │   ├── base.py          # Base for declarative models
│   │   ├── session.py       # DB session setup
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/             # Pydantic models for request/response validation/serialization
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   └── ...
│   ├── services/            # Business logic and external integrations
│   │   ├── yfinance_service.py
│   │   ├── ynab_service.py
│   │   ├── portfolio_calculator.py
│   │   └── ...
│   └── main.py              # FastAPI application instance, global middleware
├── migrations/              # Alembic migration scripts
├── tests/                   # Unit and integration tests
├── .env.example             # Example environment variables
├── pyproject.toml           # Project metadata and uv/Poetry configuration
├── poetry.lock              # (or uv equivalent) Locked dependencies
└── README.md

### 8.2. Environment Management
Different environments (development, staging, production) will be managed using:
* **`.env` files:** For local development, sensitive environment variables will be stored in a `.env` file (not committed to VCS).
* **Environment Variables:** In production deployments, configuration will be provided via environment variables managed by the hosting platform (e.g., Docker environment variables, Kubernetes secrets).
* **Pydantic Settings:** FastAPI's `BaseSettings` (from Pydantic) will be used to load configuration from environment variables with type validation.

### 8.3. Containerization (Optional but Recommended)
**Docker** will be used for containerization.
* A `Dockerfile` will define the build steps for the FastAPI application image.
* A `docker-compose.yml` file will be provided for local development, orchestrating the FastAPI service, PostgreSQL database, and Redis cache, simplifying local setup.

### 8.4. Deployment Strategy
The FastAPI application will be deployed as a containerized service.
* It will run using an ASGI server like **Uvicorn**, often behind a production-grade WSGI server like **Gunicorn** (for process management) or directly within a container orchestration system.
* Deployment targets could include:
    * **Cloud VMs:** Running Docker containers on services like AWS EC2, Google Compute Engine, or Azure VMs.
    * **Container Platforms:** Services like AWS ECS/EKS, Google Kubernetes Engine (GKE), Azure Kubernetes Service (AKS), or simpler platforms like Google Cloud Run for serverless containers.
* A Continuous Integration/Continuous Deployment (CI/CD) pipeline (e.g., using GitHub Actions) will automate testing, image building, and deployment upon code changes.

### 8.5. Testing Strategy
* **Unit Tests:** Focus on testing individual functions, methods, and small logical units in isolation (e.g., CRUD operations, utility functions).
    * **Libraries:** `pytest`.
* **Integration Tests:** Verify interactions between different components (e.g., API endpoints interacting with the database, services calling external APIs with mocks).
    * **Libraries:** `pytest` with `httpx` (for making HTTP requests to the test FastAPI app instance).
* **API Tests:** Focus on testing the public API endpoints end-to-end, ensuring they behave as expected and return correct responses. These might overlap with integration tests but focus more on the external contract of the API.
    * **Libraries:** `pytest` with `httpx` or potentially Postman/Insomnia for manual testing.

