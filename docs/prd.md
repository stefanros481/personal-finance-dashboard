Here is the updated Product Requirements Document (PRD) incorporating all the latest clarifications and additions:

```markdown
# Product Requirements Document (PRD): Personal Finance Dashboard

## 1. Introduction

### 1.1. Product Purpose
The primary purpose of this personal finance dashboard is to **track your savings towards your pension**.

### 1.2. Vision
[Elaborate on the high-level vision for the dashboard. What is the ultimate impact or value it aims to provide to the user?]

### 1.3. Target Audience
[Who is the primary user of this dashboard? E.g., Individuals focused on long-term retirement planning, investors with diverse portfolios.]

## 2. Features & Functionality

This section details each feature from the project brief, expanding into user stories and acceptance criteria.

### 2.1. Stock Portfolio Management

#### 2.1.1. Stock Transactions (CSV Import & Manual Input)
* **User Story: CSV Import of Transactions**
    * As a user, I want to import my stock transactions via a CSV file, so that I can quickly populate my portfolio data.
    * **Acceptance Criteria:**
        * The system shall allow CSV import with fields: `date`, `ticker`, `quantity`, `price`, `type of transaction` (buy/sell), `commission`, and `exchange rate`.
        * The `exchange rate` in the CSV shall represent the conversion rate between the holding currency and the specific portfolio's currency.
        * The import process shall handle cases where the portfolio currency is different from the base currency (NOK).
        * The system shall allow selection of a **specific portfolio** for the imported transactions.
        * The dashboard shall handle to avoid importing duplicate transactions based on **stock (ticker), date, quantity, and cost/share**.
        * [Add more criteria, e.g., error handling for malformed CSVs, confirmation messages.]
* **User Story: Manual Transaction Management**
    * As a user, I want to manually add, edit, or delete individual stock transactions, so that I can maintain accurate portfolio records beyond CSV imports.
    * **Acceptance Criteria:**
        * The system shall provide an interface to add a new buy or sell transaction with all required fields (date, ticker, quantity, price, type, commission, exchange rate).
        * The system shall allow editing of existing transaction details.
        * The system shall allow deletion of individual transactions.
        * [Add more criteria, e.g., validation rules for manual input.]

#### 2.1.2. Real-time and Historical Stock Prices
* **User Story: View Real-time Stock Prices**
    * As a user, I want to see the real-time prices of my stock holdings, so that I have up-to-date valuations.
    * **Acceptance Criteria:**
        * Stock prices shall be retrieved using the `yfinance` Python package.
        * Real-time prices shall automatically refresh every 60 minutes.
        * The system shall provide an option for the user to manually trigger a refresh of real-time prices.
        * Calls to `yfinance` shall be cached to manage API rate limits.
        * [Add more criteria, e.g., display of last updated timestamp.]
* **User Story: View Historical Stock Prices**
    * As a user, I want to view historical daily closing prices for my stocks, so that I can analyze past performance.
    * **Acceptance Criteria:**
        * The system shall retrieve and store only daily closing prices for historical data.
        * Historical data shall be available for all tracked stocks.
        * [Add more criteria, e.g., specific date range selection for historical view.]

#### 2.1.3. Portfolio Metrics
* **User Story: View Key Portfolio Metrics**
    * As a user, I want to see key financial metrics for my portfolio, so that I can understand its performance and value.
    * **Acceptance Criteria:**
        * The dashboard shall display unrealized gains/losses, total return, dividend income, and average cost per share.
        * Metrics shall be viewable for the **overall portfolio** and **per individual stock**.
    * **User Story: Calculate Average Cost Per Share**
        * As a user, I want the system to accurately calculate the average cost per share, so that I have a clear understanding of my investment basis.
        * **Acceptance Criteria:**
            * Average cost per share shall be calculated per holding **per portfolio**.
            * The average cost shall always be in the **currency of the stock**.
            * Commission fees shall be converted to the stock's currency if they are in a different currency.
            * Calculation formula: `((quantity * cost/share) + (commission fee * exchange rate)) / quantity`.
            * This calculation shall be performed **per transaction** and for the **total portfolio holding** of that stock.

* **User Story: Track Retirement Savings Goal**
    * As a user, I want to set and track a retirement savings goal, so that I can monitor my progress towards my long-term financial objective.
    * **Acceptance Criteria:**
        * The system shall allow setting a retirement savings goal with a **money amount in the base currency** and a **target year**.
        * Progress against this goal shall be **tracked and visualized** on the main dashboard.
        * [Add more criteria, e.g., how progress is calculated, visual representation details.]

#### 2.1.4. Multi-currency Support (for Holdings)
* **User Story: View Multi-currency Portfolio Value**
    * As a user, I want my portfolio value to be displayed in my primary base currency (NOK), even for holdings in other currencies, so that I have a consolidated view.
    * **Acceptance Criteria:**
        * The primary display currency for portfolio value shall be NOK, with the option to configure a different base currency in app settings.
        * The system shall automatically convert foreign currency holdings to the primary display currency for valuation.
    * **User Story: Track Currency Gain/Loss**
        * As a user, I want to see the gain or loss attributed to currency fluctuations for my foreign holdings, so that I understand currency impact on my returns.
        * **Acceptance Criteria:**
            * The app shall track currency gain/loss based on the exchange rate at the purchase date compared to the current exchange rate.

#### 2.1.5. Stock Search and Auto-complete
* **User Story: Search for Stocks with Auto-complete**
    * As a user, I want to search for possible stocks by typing a ticker or company name with auto-complete suggestions, so that I can quickly find and select stocks.
    * **Acceptance Criteria:**
        * The dashboard shall support auto-complete search functionality for stocks.
        * Suggestions shall appear as I type a ticker or stock company name.
        * [Add more criteria, e.g., source of auto-complete data, search performance.]

### 2.2. Portfolio Management Core Functionality

* **User Story: Manage Portfolios**
    * As a user, I want to add, edit, or delete portfolios, so that I can organize my investments effectively.
    * **Acceptance Criteria:**
        * The system shall allow creating a new portfolio with `name`, `stock brokerage firm`, `Portfolio currency`, and `used credit`.
        * The system shall allow editing existing portfolio details.
        * The system shall allow deletion of a portfolio, which will also delete all associated holdings and transactions.
* **User Story: Track Used Credit**
    * As a user, I want to track any credit line used from my brokerage, so that I can monitor my leverage.
    * **Acceptance Criteria:**
        * The system shall allow manual update of the "used credit" value for a portfolio.
        * The dashboard shall visualize any used credit.
        * The dashboard shall display a reminder if credit has been used on any of the portfolios.
        * [Add more criteria, e.g., how "simple function" is defined.]
* **User Story: Manage Holdings**
    * As a user, I want to add holdings via buy transactions and see the total shares per holding, so that I can manage my investment positions.
    * **Acceptance Criteria:**
        * Adding a buy transaction shall automatically update the total shares for that holding within the specified portfolio.
        * The system shall allow deletion of a specific holding, which will also delete all associated transactions for that holding.

### 2.3. Pension Account Management

* **User Story: Track Monthly Pension Value**
    * As a user, I want to track the monthly value of my pension accounts, so that I can monitor its growth over time.
    * **Acceptance Criteria:**
        * The system shall allow monthly input/update of pension values.
        * [Add more criteria, e.g., historical tracking visualization for pension.]
* **User Story: Receive Pension Update Reminders**
    * As a user, I want to receive reminders for regular pension account updates, so that I don't miss tracking.
    * **Acceptance Criteria:**
        * The system shall provide a configurable reminder system for regular pension updates.
* **User Story: Project Future Pension Value**
    * As a user, I want to project my future pension values based on customizable parameters, so that I can plan for retirement.
    * **Acceptance Criteria:**
        * The system shall include an advanced pension projection tool with customizable parameters (e.g., contribution rates, expected returns).
        * The system shall provide visual forecasting of future pension values.

### 2.4. Currency Conversion (General)

* **User Story: Support Multiple Currencies**
    * As a user, I want the dashboard to support multiple currencies, so that I can manage diverse financial assets.
    * **Acceptance Criteria:**
        * The system shall support NOK, USD, EUR, SEK, and CAD by default.
        * The system shall allow users to add new currencies via the Dashboard settings.
* **User Story: Utilize Historical Exchange Rates**
    * As a user, I want the dashboard to use accurate historical exchange rates for portfolio valuation, so that my historical data is correctly represented.
    * **Acceptance Criteria:**
        * The dashboard shall store historical exchange rates.
        * Historical exchange rates shall be retrieved via `yfinance`.
        * Automatic nightly updates for exchange rates.

### 2.5. Third-Party Integration (YNAB)

* **User Story: Integrate with YNAB for Balance Retrieval**
    * As a user, I want the dashboard to retrieve the latest balance for specific savings accounts directly from YNAB, so that I don't have to manually update them.
    * **Acceptance Criteria:**
        * The Account data model shall include a **`ynab_account_id`** field.
        * If `ynab_account_id` is present for an account, the system shall retrieve the latest balance via the YNAB API.
        * If no `ynab_account_id` is present, the account balance shall be manually updated.
        * The Dashboard general settings shall include a **`ynab_budget_id`**.
        * The **YNAB API key** needs to be stored safely (e.g., in a `.env` file).

## 3. Visualization & Reporting

* **User Story: View Interactive Charts**
    * As a user, I want to see interactive charts for my portfolio and pension growth, so that I can easily visualize my financial progress.
    * **Acceptance Criteria:**
        * The system shall provide interactive charts for portfolio growth.
        * The system shall provide interactive charts for pension growth.
        * [Add more criteria, e.g., customizable date ranges, different chart types.]
* **User Story: Generate Downloadable Reports**
    * As a user, I want to download PDF reports of my financial data, so that I can have offline records.
    * **Acceptance Criteria:**
        * The system shall allow generation of downloadable PDF reports.
        * [Add more criteria, e.g., report content customization.]
* **User Story: Visualize Asset Allocation**
    * As a user, I want to see visualizations of my asset allocation and currency distribution, so that I can understand my diversification.
    * **Acceptance Criteria:**
        * The system shall provide visualizations for asset allocation.
        * The system shall provide visualizations for currency distribution.
* **User Story: Customize UI Theme**
    * As a user, I want to switch between dark and light mode, so that I can customize the user interface to my preference.
    * **Acceptance Criteria:**
        * The UI shall support a dark mode.
        * The UI shall support a light mode.
        * The user shall be able to toggle between these modes.

## 4. Scope (In/Out)

### 4.1. In Scope
* All features detailed above.

### 4.2. Out of Scope (for initial version)
* Direct bank integrations (beyond YNAB).
* Complex tax reporting.
* Automated trading.
* [Add any other explicit out-of-scope items that might be implied but not intended for this version.]

## 5. Success Metrics

* performance benchmarks

## 6. Assumptions & Constraints

* **Assumptions:**
    * Reliable access to `yfinance` API for stock and exchange rate data.
    * User has a YNAB account if they wish to use that integration.
    * Users are comfortable with manual data entry for certain account types.
* **Constraints:**
    * Development within the BMad-Method framework.
    * Initial focus on web-based application.

---

You can save this content as `prd.md` in your project's `docs/` folder.
```