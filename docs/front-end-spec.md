# UI/UX Specification: Personal Finance Dashboard

## 1. Introduction

### 1.1. Purpose
This document outlines the user interface (UI) and user experience (UX) design for the Personal Finance Dashboard, based on the requirements defined in the PRD.

### 1.2. Design Principles
[What are the core design principles for this dashboard? E.g., clarity, intuitiveness, accessibility, efficiency, modern aesthetics. Consider how React, shadcn/ui, and Tailwind support these.]

### 1.3. Frontend Technologies
* **Framework/Library:** React
* **UI Component Library:** shadcn/ui
* **Styling Framework:** Tailwind CSS

## 2. User Flows

[Illustrate the key user flows. Use diagrams (e.g., simple text-based flowcharts) or descriptive steps. Consider:
* Onboarding/First-time setup
* Adding a new portfolio
* Importing CSV transactions
* Manually adding a transaction
* Viewing portfolio summary
* Checking pension progress
* Updating used credit
* Switching UI theme (dark/light mode)
* Adding a new currency
* Setting/tracking retirement goal
* Accessing YNAB integration settings
* Generating reports
]

## 3. Wireframes / Screen Layouts

[For each major screen or view, provide low-fidelity wireframes or descriptions of the layout. Focus on element placement and hierarchy. Consider using textual descriptions or simple ASCII art if direct image embedding is not possible.

* **Dashboard Overview:**
    * Main navigation
    * Summary of key metrics (total portfolio value, pension progress, quick access to portfolios)
    * Retirement goal visualization
    * Reminders (e.g., used credit, pension updates)
* **Portfolio Details View:**
    * Specific portfolio name, currency, brokerage
    * Holdings list with real-time prices, quantity, average cost, gains/losses
    * Transaction history table (collapsible, opens when user clicks the holding)
    * Actions (Add transaction, Delete holding, Import CSV)
* **Add/Edit Portfolio Form:**
    * Fields for name, brokerage, currency, initial used credit
* **Add/Edit Transaction Form:**
    * Fields for date, ticker, quantity, price, type, commission, exchange rate, portfolio selection.
    * Auto-complete for stock search.
* **Pension Management View:**
    * **Monthly Value Input/Display:**
        * Clear input field(s) for monthly pension values.
        * A button next to the input field to fetch the account balance value via YNAB API (conditionally displayed/enabled if `ynab_account_id` is present).
    * **Projection Tool Interface:**
        * Input fields or sliders for customizable parameters (e.g., expected annual contribution, expected annual rate of return, inflation rate, current age, desired retirement age).
        * Clear labels and intuitive controls.
    * **Charts for Pension Growth:**
        * Historical chart (line chart) showing monthly values.
        * Projection chart for forecasted growth.
* **Settings View:**
    * Base currency selection
    * Adding new currencies
    * YNAB integration settings (budget ID)
    * Input fields for **Retirement Savings Goal (amount)** and **Planned Retirement Year**.
    * Note on YNAB API Key: It should only be stored in a `.env` file, not in a database. Updating it via UI is a good-to-have but not critical for initial version.
* **Reports View:**
    * Options for report generation (e.g., date range, type)
]

## 4. UI Components & Style Guide

[Define the common UI components and styling conventions, keeping shadcn/ui and Tailwind in mind.
* **Typography:** (Font family, sizes for headings, body text)
* **Color Palette:** (Primary, secondary, accent colors; text colors, background colors for light/dark mode)
* **Buttons:** (Primary, secondary, tertiary states; sizes)
* **Forms:** (Input fields, text areas, dropdowns, checkboxes, radio buttons; states like error, focus)
* **Navigation:** (Global navigation, sub-navigation patterns)
* **Tables:** (Structure, sorting, pagination)
* **Charts:** (Types to be used - e.g., line, bar, pie; general styling)
* **Modals/Dialogs:** (Confirmation, input)
* **Notifications/Toasts:** (Success, error, info messages)
* **Icons:** (Iconography style)
]

## 5. Accessibility Considerations

[How will the design ensure accessibility for users with disabilities? Consider:
* Keyboard navigation
* Screen reader compatibility (ARIA attributes)
* Color contrast ratios
* Focus states
* Form labels
]

## 6. Interaction Design

[Describe key interactions that are not immediately obvious from static wireframes.]

* **Auto-complete behavior for stock search:**
    * Suggestions should appear as responsive as the `yfinance` API allows (with caching to help).
    * A maximum of 5 suggestions should be shown.
    * If there are no matches, "No data" should be displayed.
    * User should be able to select a suggestion via **click or keyboard navigation**.
* **Error feedback for forms and imports:**
    * Error messages should appear primarily inline, and then as a top banner based on context.
    * Language should be actionable.
    * Validation errors should be highlighted directly in the form if possible.
    * After an import error, affected rows should be shown.
* **Loading states for data retrieval (e.g., yfinance calls):**
    * Skeleton loaders should be used as visual indicators.
    * Placement of indicators should be decided based on context (e.g., over a specific widget).
    * If a data fetch fails or takes too long, the whole data fetch should fail, and a message should be shown with the reason.
* **Drag-and-drop:**
    * Useful for reordering portfolios and accounts.
    * Interactions should be visually indicated by highlighting drop zones.
* **Animations/Transitions:**
    * No specific animations are desired at this time, implying that subtle, quick, and smooth standard transitions would be acceptable.

## 7. Future Considerations (Optional)

[Any UI/UX aspects that are out of scope for the initial version but might be considered later.]

---

You can save this content as `front-end-spec.md` in your project's `docs/` folder.