# Project Brief: Personal Finance Dashboard

## 1. Project Purpose

The primary purpose of this personal finance dashboard is to **track your savings towards your pension**.

## 2. Consolidated Features

### 2.1. Stock Portfolio Management

* **Stock Transactions (CSV Import & Manual Input)**
    * **CSV Import Data:** The CSV import should include `date`, `ticker`, `quantity`, `price`, `type of transaction` (buy/sell), `commission`, and `exchange rate`.
        * The `exchange rate` refers to the conversion rate between the **holding currency** and the **specific portfolio's currency**.
        * The **portfolio currency** is not necessarily the base currency (NOK).
        * Transactions should be imported to a **specific portfolio**.
    * **Manual Management:** Users will also need the ability to manually add or edit transactions directly within the app.

* **Real-time and Historical Stock Prices**
    * **Real-time Price Refresh:** Automatic refresh every 60 minutes with a manual refresh option. Calls should be cached to avoid `yfinance` rate limiting. Stock holding current price will be retrieved using the **yfinance Python package**.
    * **Historical Data:** Only daily closing prices are required for historical data points.

* **Portfolio Metrics**
    * **Metrics Included:** Unrealized gains/losses, total return, dividend income, and average cost per share.
    * **Average Cost Per Share Calculation:**
        * Calculated **per portfolio**.
        * Always in the **currency of the stock** (e.g., USD for a Nasdaq stock).
        * Commission fees need to be **converted to the stock's currency** if they are in a different currency (e.g., NOK from a Norwegian brokerage).
        * Formula: `Average cost / share = ((quantity * cost/share) + (commission fee * exchange rate)) / quantity`.
        * This calculation should be performed **per transaction** as well as for the **total portfolio holding** of that specific stock.
    * **Viewing Options:** These metrics should be viewable both for the overall portfolio and per individual stock.

* **Multi-currency Support (for Holdings)**
    * **Primary Display Currency:** NOK (configurable in app settings).
    * **Currency Gain/Loss:** Tracked based on the exchange rate at the purchase date compared to the current exchange rate.

### 2.2. Portfolio Management Core Functionality

* Ability to add a Portfolio with data such as `name`, `stock brokerage firm`, `Portfolio currency`, and `used credit`.
* **Used Credit Tracking:** Track a credit line from the brokerage used for trading. This value will be manually updated regularly. The Dashboard should provide a reminder if credit has been used on any of the portfolios.
* Ability to add holdings by adding buy transactions; the portfolio will keep track of total shares per holding.
* Ability to delete a holding and all the transactions for that holding.
* Ability to delete a portfolio, with all its holdings and transactions.

### 2.3. Pension Account Management

* Monthly pension value tracking.
* Reminder system for regular updates.
* Advanced pension projection tool with customizable parameters.
* Visual forecasting of future pension values.

### 2.4. Currency Conversion (General)

* Supported currencies: NOK, USD, EUR, SEK, **CAD**.
* The application should provide the capability to add new currencies via the Dashboard settings if needed.
* To improve performance, the dashboard will store historical exchange rates.
* These historical exchange rates will be retrieved using **yfinance**.

### 2.5. Third-Party Integration (YNAB)

* Retrieve the latest balance from YNAB for specific savings accounts.
* An account that is connected to YNAB should have a **`ynab_account_id`** field in its data model.
* If a `ynab_account_id` is present for an account, the dashboard will retrieve the latest balance via the YNAB API.
* If no `ynab_account_id` is present, the account balance will be manually updated.
* There needs to be a **`ynab_budget_id`** in the Dashboard's general settings.
* The **YNAB API key** needs to be stored safely (e.g., in a `.env` file).

### 2.6. Goals

* **Retirement Savings Goal:**
    * A retirement savings goal will be added at the Dashboard level.
    * This goal will consist of a **money amount in the base currency** and a **target year** (retirement year).
    * The dashboard should **track and visualize progress** against this goal on the main dashboard.

## 3. Visualization & Reporting

* Interactive charts for portfolio and pension growth.
* Downloadable PDF reports.
* Asset allocation and currency distribution visualizations.
* Dark/light mode UI.

---

You can save this content as `project-brief.md` in your project's `docs/` folder.