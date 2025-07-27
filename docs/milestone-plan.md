# Milestone Plan: Personal Finance Dashboard

## Project Overview
This project aims to develop a single-user personal finance dashboard using React (Frontend) and FastAPI (Backend). The dashboard will enable users to manage portfolios, track pension growth, integrate with YNAB, and visualize financial data.

## Key Principles for Planning
* **Single User Focus:** Prioritize core functionalities for a single user.
* **Backend First (API Foundation):** Establish core backend services, including API proxies, before extensive frontend development.
* **Iterative Development:** Deliver features in logical, manageable phases.
* **Maintainability:** Prioritize clean code and good architecture to ensure long-term maintainability.

---

## High-Level Timeline
This timeline is an estimate and assumes a focused development effort.

* **Total Estimated Duration:** ~12-16 weeks (3-4 months) for a fully functional MVP.

---

## Milestones

### 1. Milestone 1: Project Setup & Core Backend Infrastructure ✅ COMPLETED
* **Duration:** ~2 weeks
* **Goal:** Establish foundational backend services, database, authentication, and basic API structure.
* **Key Deliverables:**
    1.1. `[x]` **Backend Project Setup:** FastAPI project initialized with uv/Astral, Black, Flake8, Isort, Pytest.
    1.2. `[x]` **Database Setup:** PostgreSQL/SQLite configured with SQLAlchemy ORM and Alembic migrations.
    1.3. `[x]` **User & Authentication System:** JWT-based authentication implemented (login endpoint, password hashing).
    1.4. `[x]` **Core Data Models:** Database models defined for User, Portfolio, Holding, Transaction, PensionAccount, PensionValueEntry, StockMetadata, HistoricalExchangeRate, HistoricalStockPrice.
    1.5. `[x]` **Basic CRUD APIs:** Initial API endpoints for User (login), Portfolio (CRUD), and basic Settings.
    1.6. `[x]` **Containerization:** Dockerfile and docker-compose.yml for backend, DB, and Redis cache.

---

### 2. Milestone 2: Core Backend Integrations & Data Management
* **Duration:** ~3-4 weeks
* **Goal:** Implement third-party API proxies, advanced data management (transactions, holdings calculations), and caching.
* **Key Deliverables:**
    2.1. `[ ]` **yfinance Integration:** Backend proxy for yfinance (real-time prices, historical prices, company info) implemented.
    2.2. `[ ]` **Redis Caching:** 15-minute caching for yfinance data implemented using Redis.
    2.3. `[ ]` **Transaction & Holding Logic:** Backend logic for adding/importing transactions, calculating `average_cost_per_share_at_transaction`, and deriving `current_quantity` and `average_cost_per_share` for holdings.
    2.4. `[ ]` **Pension Data Management:** Backend APIs for creating pension accounts and adding monthly value entries.
    2.5. `[ ]` **Currency Management:** Backend APIs for managing base and additional currencies.
    2.6. `[ ]` **Robust Error Handling:** Global API error handling and specific exception handling implemented.

---

### 3. Milestone 3: Frontend Foundation & Core Views
* **Duration:** ~3-4 weeks
* **Goal:** Set up the frontend project, implement core UI components, basic routing, and integrate with initial backend APIs.
* **Key Deliverables:**
    3.1. `[ ]` **Frontend Project Setup:** React project initialized with Vite, shadcn/ui, Tailwind CSS, ESLint, Prettier, Jest, React Testing Library.
    3.2. `[ ]` **Core UI Components:** Implementation of reusable components (buttons, inputs, cards, navigation) using shadcn/ui.
    3.3. `[ ]` **Routing:** React Router DOM configured with basic routes (Dashboard, Portfolios, Settings, Login).
    3.4. `[ ]` **Authentication Flow:** Frontend login form, JWT handling, protected routes.
    3.5. `[ ]` **Dashboard Overview View:** Basic layout and display of static/mock data for key metrics.
    3.6. `[ ]` **API Client Integration:** Axios setup for communication with the FastAPI backend.
    3.7. `[ ]` **Global State Management:** Zustand setup for global application state (e.g., auth, theme).
    3.8. `[ ]` **Server State Management:** TanStack Query integrated for efficient data fetching and caching from backend APIs.

---

### 4. Milestone 4: Portfolio Management & Transaction Features
* **Duration:** ~2-3 weeks
* **Goal:** Enable full portfolio management, including detailed holdings display and transaction handling.
* **Key Deliverables:**
    4.1. `[ ]` **Portfolio Details View:** Frontend implementation to display portfolio details, list holdings with current prices/gains/losses.
    4.2. `[ ]` **Transaction History:** Display transaction history for individual holdings (collapsible table).
    4.3. `[ ]` **Add/Edit Portfolio:** Forms for creating and updating portfolios.
    4.4. `[ ]` **Add/Edit/Delete Transaction:** Forms and logic for manual transaction entry, editing, and deletion.
    4.5. `[ ]` **CSV Import:** Frontend interface and logic to upload and process CSV transaction data via backend API.
    4.6. `[ ]` **Drag-and-Drop:** Implementation for reordering portfolios and accounts.
    4.7. `[ ]` **Auto-complete for Stock Search:** Frontend auto-complete functionality integrated with backend stock search proxy.

---

### 5. Milestone 5: Pension Tracking & YNAB Integration
* **Duration:** ~1-2 weeks
* **Goal:** Implement pension management features, projections, and YNAB integration.
* **Key Deliverables:**
    5.1. `[ ]` **Pension Management View:** Frontend UI for monthly value input, display of historical values.
    5.2. `[ ]` **Pension Projection Tool:** UI for inputting parameters (contributions, return rates) and displaying projections.
    5.3. `[ ]` **YNAB Integration Settings:** Frontend UI for configuring YNAB budget ID.
    5.4. `[ ]` **Fetch YNAB Balance:** Button functionality to fetch account balance via YNAB API proxy.
    5.5. `[ ]` **Pension Charts:** Visualizations for historical pension growth and future projections (using Recharts).

---

### 6. Milestone 6: Settings, Reporting & Polish (MVP Completion)
* **Duration:** ~1-2 weeks
* **Goal:** Finalize core settings, implement basic reporting, and polish the application for initial release.
* **Key Deliverables:**
    6.1. `[ ]` **Settings View:** Implement UI for base currency selection, adding new currencies, updating retirement goals.
    6.2. `[ ]` **Reporting View:** Basic report generation functionality (e.g., summary reports over date ranges).
    6.3. `[ ]` **Error Feedback:** Consistent error feedback implementation across forms and data operations.
    6.4. `[ ]` **Loading States:** Implementation of skeleton loaders and other loading indicators.
    6.5. `[ ]` **Accessibility Enhancements:** Review and address critical accessibility considerations (keyboard navigation, ARIA labels).
    6.6. `[ ]` **Comprehensive Testing:** Ensure unit, integration, and E2E tests are passing.
    6.7. `[ ]` **Deployment Pipeline:** Finalize CI/CD pipeline for automated builds and deployment.
```