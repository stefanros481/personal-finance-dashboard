# Milestone 2: Core Backend Integrations & Data Management - User Stories

## Story 1: yfinance Integration for Real-time Stock Prices

### User Story
As a user, I want to see real-time stock prices for my holdings so that I can track my portfolio's current value.

### Acceptance Criteria
- [ ] Backend service can fetch real-time stock prices using yfinance
- [ ] API endpoint `/api/v1/stocks/{ticker}/price` returns current price data
- [ ] Stock prices include: current price, previous close, change percentage
- [ ] API handles invalid tickers gracefully with proper error responses
- [ ] Price data includes currency information
- [ ] Service respects yfinance API rate limits

### Technical Notes
- Implement in `app/services/market_data.py`
- Create endpoint in `app/api/v1/endpoints/stocks.py`
- Use async/await for non-blocking requests

---

## Story 2: Redis Caching for Market Data

### User Story
As a system, I need to cache market data to avoid hitting yfinance rate limits and improve response times.

### Acceptance Criteria
- [ ] Redis caching implemented for all yfinance API calls
- [ ] Cache TTL set to 15 minutes for real-time prices
- [ ] Cache TTL set to 24 hours for historical data
- [ ] Cache keys follow consistent naming convention: `stock:{ticker}:price:current`
- [ ] Cache miss triggers fresh data fetch from yfinance
- [ ] Cache invalidation mechanism for manual refresh

### Technical Notes
- Use Redis client in `app/core/cache.py`
- Implement cache decorators for service methods
- Add cache health check to system monitoring

---

## Story 3: Historical Stock Price Data

### User Story
As a user, I want to view historical stock price data to analyze my holdings' performance over time.

### Acceptance Criteria
- [ ] API endpoint `/api/v1/stocks/{ticker}/history` returns historical prices
- [ ] Support date range parameters (start_date, end_date)
- [ ] Return daily closing prices only
- [ ] Store historical data in database for faster subsequent queries
- [ ] Handle missing data gracefully (weekends, holidays)
- [ ] Support pagination for large date ranges

### Technical Notes
- Extend `HistoricalStockPrice` model
- Implement data synchronization service
- Add database indexes for ticker + date queries

---

## Story 4: Enhanced Transaction Logic with Holding Calculations

### User Story
As a user, I want accurate portfolio calculations that include average cost per share and unrealized gains/losses.

### Acceptance Criteria
- [ ] Transaction creation updates holding `current_quantity` correctly
- [ ] Buy transactions increase quantity, sell transactions decrease
- [ ] Average cost per share calculated per transaction: `((quantity * price) + commission) / quantity`
- [ ] Commission fees converted to stock currency if different
- [ ] Holding-level average cost calculated across all transactions
- [ ] Unrealized gain/loss calculated: `(current_price - avg_cost) * quantity`
- [ ] Support for stock splits and dividend adjustments

### Technical Notes
- Enhance `app/services/portfolio.py` with calculation logic
- Add validation for sell transactions not exceeding holdings
- Create audit trail for calculation changes

---

## Story 5: Multi-Currency Exchange Rate Management

### User Story
As a user, I want to track my portfolio in multiple currencies with accurate exchange rate conversions.

### Acceptance Criteria
- [ ] API endpoints for managing supported currencies
- [ ] Daily exchange rate fetching from yfinance (e.g., USDNOK=X)
- [ ] Historical exchange rate storage in database
- [ ] Portfolio value conversion to base currency (NOK)
- [ ] Currency gain/loss calculation for foreign holdings
- [ ] Support for adding new currency pairs via settings

### Technical Notes
- Implement `app/services/currency.py`
- Create scheduled task for daily rate updates
- Add currency validation in transaction endpoints

---

## Story 6: Pension Account Management APIs

### User Story
As a user, I want to track my pension account values over time to monitor my retirement savings progress.

### Acceptance Criteria
- [ ] CRUD APIs for pension accounts
- [ ] API for adding monthly pension value entries
- [ ] Validation to prevent duplicate entries for same month
- [ ] API to retrieve pension value history
- [ ] Support for multiple pension accounts
- [ ] Automatic calculation of growth rates and trends

### Technical Notes
- Implement endpoints in `app/api/v1/endpoints/pension.py`
- Add pension service in `app/services/pension.py`
- Include pension data in dashboard aggregations

---

## Story 7: Robust Global Error Handling

### User Story
As a system, I need comprehensive error handling to provide clear feedback to users and maintain system stability.

### Acceptance Criteria
- [ ] Global exception handler for all API endpoints
- [ ] Custom exception classes for domain-specific errors
- [ ] Consistent error response format with error codes
- [ ] Logging of all errors with request context
- [ ] Graceful handling of third-party API failures
- [ ] Rate limiting protection with appropriate error responses

### Technical Notes
- Implement in `app/core/exceptions.py`
- Add middleware for global error handling
- Create error response schemas

---

## Story 8: Stock Search and Auto-complete

### User Story
As a user, I want to search for stocks by ticker or company name when adding new transactions.

### Acceptance Criteria
- [ ] API endpoint `/api/v1/stocks/search` with query parameter
- [ ] Search by ticker symbol or company name
- [ ] Return ticker, company name, exchange, and currency
- [ ] Limit results to 10 items for performance
- [ ] Cache search results for popular queries
- [ ] Support for multiple exchanges (NASDAQ, NYSE, etc.)

### Technical Notes
- Use yfinance ticker search functionality
- Implement caching for search results
- Add debouncing on frontend to reduce API calls

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests cover API endpoints
- [ ] API documentation updated
- [ ] Error handling implemented
- [ ] Performance considerations addressed
- [ ] Code review completed
- [ ] Manual testing completed

## Priority Order
1. **Story 1 & 2**: yfinance Integration + Redis Caching (Foundation)
2. **Story 4**: Enhanced Transaction Logic (Core calculations)
3. **Story 5**: Currency Management (Multi-currency support)
4. **Story 3**: Historical Data (Analysis capability)
5. **Story 6**: Pension APIs (Additional feature)
6. **Story 8**: Stock Search (User experience)
7. **Story 7**: Error Handling (Polish and robustness)