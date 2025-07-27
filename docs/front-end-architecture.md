# Frontend Architecture: Personal Finance Dashboard

## 1. Introduction

### 1.1. Purpose
This document details the frontend architecture for the Personal Finance Dashboard, translating the UI/UX specifications into a technical blueprint for development.

### 1.2. Goals
Given this is a **single-user application**, the primary architectural goals are **maintainability** and a **smooth user experience** for the core functionalities. Performance will be optimized where it directly impacts user experience (e.g., responsiveness of data displays), but not at the cost of significant complexity given the single-user scope. These goals align well with the chosen technologies (React for UI, shadcn/ui for components, Tailwind for styling) which promote modularity, reusability, and efficient development.

## 2. Technology Stack Justification

### 2.1. Core Technologies
* **React:** A leading JavaScript library for building user interfaces, ideal for a dynamic dashboard with complex, interactive components. Its component-based approach promotes reusability and maintainability.
* **shadcn/ui:** Provides a collection of beautifully designed and accessible UI components built with Radix UI and styled with Tailwind CSS. It accelerates UI development, ensures consistency, and is easily customizable to fit the dashboard's aesthetic.
* **Tailwind CSS:** A utility-first CSS framework that enables rapid UI development by composing classes directly in markup. It promotes consistency, reduces CSS bundle size, and simplifies custom styling.

### 2.2. Other Key Libraries/Frameworks
* **Routing:** **React Router DOM**
    * **Justification:** It is the industry standard for client-side routing in React applications, providing robust features for declarative navigation, nested routes, and route protection, which are essential for a multi-view dashboard.
* **Data Fetching & Server State Management:** **TanStack Query (React Query)**
    * **Justification:** While raw data fetching will be handled by the FastAPI backend, TanStack Query is ideal for managing the *state* of that server data on the frontend. It provides powerful caching, automatic re-fetching (e.g., for real-time stock prices every 60 mins), background updates, and built-in loading/error states, significantly reducing boilerplate and improving developer experience and perceived performance. This ensures the frontend efficiently consumes data served by the backend.
* **Form Management:** **React Hook Form**
    * **Justification:** Chosen for its performance, unopinionated approach, and emphasis on uncontrolled components, which reduces re-renders. It offers robust validation capabilities and seamless integration with UI libraries like shadcn/ui, making form handling efficient and reliable.
* **Charting:** **Recharts**
    * **Justification:** A flexible charting library built specifically for React, offering declarative components for various chart types needed for portfolio and pension growth visualizations. It integrates well with React's component model and allows for customization to match the dashboard's design.
* **Date Management:** **date-fns**
    * **Justification:** A lightweight and modular JavaScript date utility library. It provides a comprehensive set of functions for parsing, formatting, validating, and manipulating dates, which are crucial for handling transaction dates, historical data, and pension projections. Its immutability helps prevent side effects.

## 3. Component Architecture

### 3.1. Component Structure & Hierarchy
The React components will be organized using a **feature-based structure**. This approach promotes clear separation of concerns, enhances maintainability, and makes it easier to locate relevant code for specific functionalities.

**Example Component Hierarchy for "Portfolio Details View":**

.
src/
├── features/
│   ├── portfolios/
│   │   ├── components/
│   │   │   ├── HoldingsList.tsx
│   │   │   ├── HoldingItem.tsx
│   │   │   ├── TransactionHistoryTable.tsx (collapsible within HoldingItem)
│   │   │   ├── AddTransactionForm.tsx
│   │   │   └── DeleteHoldingDialog.tsx
│   │   ├── hooks/
│   │   │   └── usePortfolioData.ts (for fetching portfolio-specific data)
│   │   ├── pages/
│   │   │   └── PortfolioDetailsPage.tsx  (Container for a specific portfolio's view)
│   │   └── types/
│   │       └── portfolio.ts (TypeScript types)
│   ├── pension/
│   │   ├── components/
│   │   │   ├── PensionInputForm.tsx
│   │   │   ├── PensionProjectionTool.tsx
│   │   │   └── PensionGrowthChart.tsx
│   │   ├── pages/
│   │   │   └── PensionManagementPage.tsx
│   │   └── ...
│   ├── settings/
│   │   └── ...
│   └── dashboard/
│       └── ...
├── components/ (Shared UI components, potentially from shadcn/ui or very generic custom ones)
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Card.tsx
│   └── ...
├── hooks/ (Global or general utility hooks)
│   └── useAuth.ts
│   └── useCurrencyConverter.ts
├── layouts/
│   ├── MainLayout.tsx (Includes Header, Sidebar, main content area)
│   └── AuthLayout.tsx
├── services/ (API clients, e.g., axios instances, yfinance/YNAB wrappers for backend communication)
│   ├── api.ts (Axios instance)
│   └── ynabService.ts
│   └── ...
├── store/ (Global state management, e.g., Zustand stores)
│   └── authStore.ts
│   └── settingsStore.ts
├── utils/
│   ├── dateUtils.ts
│   ├── currencyUtils.ts
│   └── ...
├── App.tsx
└── main.tsx

### 3.2. Reusability Strategy
To ensure components are highly reusable and composable:
* **Clear Prop Interfaces:** Define explicit and minimal props for presentational components, leveraging TypeScript for strong typing.
* **Composition over Inheritance:** Favor composing smaller, dumber components into larger, smarter ones.
* **Context API for Theming/Global Data:** Use React Context for global concerns like theme (dark/light mode), currency settings, or user authentication status, avoiding prop drilling for widely used data.
* **Custom Hooks:** Abstract reusable logic (e.g., data fetching, form handling, authentication) into custom React Hooks.
* **Storybook (Optional but Recommended):** Use a tool like Storybook to develop and document components in isolation, promoting reusability and consistent usage across the application.
* **Shadcn/ui Components:** Leverage shadcn/ui's composable components as building blocks, customizing them via Tailwind CSS.

## 4. State Management

### 4.1. Global State Management
**Zustand** will be chosen for global state management.
* **Justification:** For a single-user application with varying data sources and features, Zustand offers a lightweight, performant, and simple API. It avoids much of the boilerplate associated with larger state management libraries, making it easy to learn and maintain, while still providing robust solutions for managing global application state (e.g., user authentication status, UI theme, global settings). Its approach of creating small, isolated stores fits well with a feature-based architecture.

### 4.2. Local Component State
React's built-in `useState` and `useReducer` hooks will be used for managing component-specific state that does not need to be shared globally or persisted.

### 4.3. Server State Management
While the raw fetching of data from `yfinance` and YNAB will primarily be handled by the **FastAPI Backend**, the **frontend will utilize TanStack Query (React Query)** to manage the *server state* (cached data from API calls).
* **Justification:** TanStack Query excels at handling asynchronous data (server state), providing automatic caching, re-fetching (e.g., for stock prices every 60 minutes), optimistic updates, and built-in loading/error states, significantly reducing boilerplate and improving developer experience and perceived performance. This offloads complex data fetching logic from components and global state, ensuring the UI is always in sync with the backend data efficiently, improving both developer experience and perceived application performance.

## 5. Data Flow & Management

### 5.1. Data Flow Diagram (Conceptual)
The application will follow a **unidirectional data flow** pattern:
1.  **User Interaction:** User performs an action (e.g., clicks a button, types into an input).
2.  **Component Event:** The UI component triggers an event handler.
3.  **Action/Hook Call:** The event handler dispatches an action (for global state update) or calls a custom hook (for data fetching/local state update).
4.  **State Update:**
    * **Global State:** A Zustand store updates its state based on the action.
    * **Server State:** TanStack Query handles data fetching from the backend and updates its cache.
    * **Local State:** `useState`/`useReducer` updates component-specific state.
5.  **Re-render UI:** React detects state changes and re-renders the affected components, reflecting the updated data or UI state.

### 5.2. Data Models (Frontend Representation)
Backend data models (e.g., from FastAPI) will often be consumed directly. However, in some cases, data transformation or "DTOs" (Data Transfer Objects) might be used on the frontend to:
* **Flatten nested structures:** Make data easier to consume by UI components.
* **Enrich data:** Add computed properties that are useful for display but not present in the raw backend response (e.g., `isPositiveGain` boolean).
* **Normalize data:** For complex nested relationships, storing data in a normalized form in the frontend cache (e.g., if using a Redux-like global state for specific complex data) might optimize lookups.
* **Type Safety:** Leverage TypeScript interfaces to strictly define frontend data shapes, ensuring consistency and catching errors at compile time.

## 6. API Integration Strategy

### 6.1. Backend API Communication
* **HTTP Client:** **Axios** will be used for communication with the FastAPI backend.
    * **Justification:** Axios is a popular, promise-based HTTP client that offers features like interceptors for requests and responses, automatic JSON transformation, and robust error handling, which simplifies API communication.
* **Error Handling for API Calls:** API errors will be handled consistently across the application using a combination of a global Axios interceptor and localized error handling.
    * **Global Interceptor:** Catches common error responses (e.g., 401 Unauthorized, 500 Internal Server Error) to display generic notifications or trigger re-authentication.
    * **Local Error Handling:** Specific API calls will use `try...catch` blocks or `TanStack Query`'s error handling capabilities (`onError` callbacks) to display context-specific error messages to the user (e.g., "Failed to import transactions: Invalid CSV format").
    * **Actionable Messages:** Error messages displayed to the user will be clear, concise, and actionable where possible.

### 6.2. Third-Party API Integration
* **yfinance Integration:** The frontend will integrate with `yfinance` data indirectly by making **direct client calls to the FastAPI backend**. The FastAPI backend will serve as a proxy for `yfinance` requests.
    * **Caching Strategy:** The FastAPI backend will implement a general cache of **15 minutes** for `yfinance` data to reduce redundant calls to the external API and improve response times.
* **YNAB API Integration:** The frontend will integrate with the YNAB API **through the FastAPI backend API gateway**.
    * **Authentication:** The YNAB API key, which is stored securely in the backend's `.env` file, will never be exposed to the frontend. The frontend will authenticate with the FastAPI backend, and the backend will then use its securely stored YNAB API key to make requests to the YNAB API on behalf of the user. This ensures the API key remains safe on the server side.

### 6.3. Authentication & Authorization
* **Authentication:** User authentication will be handled using **JSON Web Tokens (JWT)**.
    * When the single user logs in, the FastAPI backend will issue a JWT.
    * This JWT will be securely stored on the client-side (e.g., in HTTP-only cookies or localStorage, depending on security considerations).
    * Subsequent API requests will include this JWT for authentication.
* **Authorization:** As this is explicitly a **single-user application with no need for shared access or different user roles**, a complex authorization system is not required beyond ensuring the authenticated user is accessing their own data (implicitly handled by the single-user design and backend data partitioning).

## 7. Routing Strategy

### 7.1. Client-Side Routing
**React Router DOM** will be used for client-side routing.
* **Justification:** It's the most widely adopted and flexible routing library for React, offering declarative routing that integrates seamlessly with React components.
* **Protected Routes:** Protected routes (requiring authentication) will be implemented using **wrapper components**. A higher-order component or a custom `Route` component will check for the presence and validity of the authentication token. If the user is not authenticated, they will be redirected to a login page.

### 7.2. URL Structure
Clear and consistent URL patterns will be used:
* `/dashboard`: Main dashboard overview.
* `/portfolios`: List of all portfolios.
* `/portfolios/:id`: Details view for a specific portfolio.
* `/pension`: Pension management view.
* `/settings`: Application settings.
* `/login`: User login page.

## 8. Performance Considerations

Given this is a single-user application where extreme optimization for concurrent users is not a primary concern, focus will be on delivering a smooth and responsive experience for that single user.

* **Virtualization:** For large lists, such as transaction history tables within portfolios, virtualization libraries (e.g., `react-window` or `react-virtualized`) will be employed to render only visible rows, significantly improving performance and memory usage.
* **Lazy Loading (Code Splitting):** Routes and large components will be lazy-loaded using React's `lazy` and `Suspense` to reduce initial bundle size and speed up initial page load times.
* **Memoization:** `React.memo`, `useMemo`, and `useCallback` hooks will be used judiciously to prevent unnecessary re-renders of complex components or expensive calculations.
* **Efficient Data Fetching (TanStack Query):** Leveraging TanStack Query's caching and background refetching will ensure data is available quickly without constant full re-fetches.

## 9. Scalability and Maintainability

### 9.1. Folder Structure
The project will follow a **feature-based folder structure** combined with common utility directories:

src/
├── api/             # Axios instance, API client functions
├── assets/          # Images, icons, fonts
├── components/      # Reusable, generic UI components (e.g., buttons, modals, alerts)
├── features/        # Business domain-specific features
│   ├── auth/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── pages/
│   ├── dashboard/
│   │   ├── components/
│   │   └── pages/
│   ├── portfolios/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── types/
│   ├── pension/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── pages/
│   └── settings/
│       ├── components/
│       └── pages/
├── hooks/           # General utility React hooks (e.g., useLocalStorage)
├── layouts/         # High-level layout components (e.g., MainLayout, AuthLayout)
├── lib/             # Utility functions, helpers, constants (non-React specific)
│   ├── utils.ts
│   ├── constants.ts
│   ├── config.ts
│   └── yfinance.ts (Client-side proxy for yfinance data from backend)
├── store/           # Zustand stores for global state
│   └── authStore.ts
│   └── settingsStore.ts
├── types/           # Global TypeScript types and interfaces
├── App.tsx          # Main application component
├── main.tsx         # Entry point
└── index.css        # Tailwind CSS directives

### 9.2. Naming Conventions
* **Components:** PascalCase (e.g., `PortfolioDetailsPage`, `HoldingItem`).
* **Hooks:** `use` prefix for custom hooks (e.g., `usePortfolioData`).
* **Files:** PascalCase for React components, kebab-case for CSS/utility files (e.g., `my-utility.ts`).
* **Variables/Functions:** camelCase.
* **Types/Interfaces:** PascalCase.

### 9.3. Linting & Formatting
**ESLint** (with recommended React and TypeScript configurations) and **Prettier** will be used to enforce code quality, consistency, and formatting across the codebase. Pre-commit hooks (e.g., with Husky and lint-staged) will be configured to automatically check and format code before commits.

### 9.4. Testing Strategy
* **Unit Tests:** Will be implemented for individual React components (presentational and container), custom hooks, and utility functions.
    * **Libraries:** **Jest** (test runner) and **React Testing Library** (for testing React components in a user-centric way).
* **Integration Tests:** Focus on testing the interaction between several components or modules, or the integration with local data sources/mocks.
    * **Libraries:** **React Testing Library** and **Jest**.
* **End-to-End (E2E) Tests:** Will simulate full user flows through the application from start to finish in a real browser environment.
    * **Libraries:** **Cypress** (for its developer-friendly API and real-time reloading).

## 10. Error Handling & Logging

### 10.1. Client-Side Error Boundaries
**React Error Boundaries** will be used to gracefully handle JavaScript errors that occur within the component tree during rendering, in lifecycle methods, and in constructors.
* A top-level `ErrorBoundary` component will be implemented to catch errors and display a fallback UI, preventing the entire application from crashing.
* More granular error boundaries may be placed around specific widgets or sections (e.g., a chart component) to isolate potential failures without disrupting the whole page.

### 10.2. Global Error Handling
* Unhandled promise rejections and other global errors will be caught at the application root level (e.g., `window.onerror`, `window.onunhandledrejection`) to provide a last-resort fallback message to the user.
* API errors will be centrally managed via Axios interceptors and TanStack Query's error handling, as detailed in section 6.1.

### 10.3. Frontend Logging
* During **development**, errors and important debug information will be logged to the **browser's console**.
* For **production**, given it's a single-user application, a simple but effective logging strategy will be sufficient:
    * Critical errors caught by error boundaries or global handlers could be optionally sent to a lightweight external logging service (e.g., Sentry's free tier, or simply a custom webhook to a private log storage) if real-time alerting is desired. Otherwise, backend logging of failed API calls initiated by the frontend might suffice.
    * General application events or user actions will not be extensively logged to external services in this initial version, focusing on error reporting.

## 11. Build Process & Deployment

### 11.1. Build Tools
The React application will be built using **Vite**.
* **Justification:** Vite offers extremely fast cold server start times and instant hot module replacement (HMR), significantly improving developer experience. It uses Rollup for production builds, resulting in optimized bundles.

### 11.2. Deployment Strategy
The frontend application will be deployed as **static assets** to a content delivery network (CDN) or a static site hosting service (e.g., Vercel, Netlify, or a simple Nginx server).
* A Continuous Integration/Continuous Deployment (CI/CD) pipeline (e.g., using GitHub Actions) will automate the build, test, and deployment process upon code changes to the main branch.
