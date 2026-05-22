# Implementation Plan: Jollof Intelligence Frontend

## Overview

Build a React 18 + TypeScript + Vite SPA with React Router for page-level routing. The `/review` route hosts the Book Review Simulator (Task A) and the `/recommend` route hosts the Personalised Book Recommender (Task B). The app embodies Nigerian cultural identity through its colour palette, tone, and layout. All backend communication is centralised in a typed API client module. Property-based tests (fast-check + Vitest) validate the 13 correctness properties defined in the design document.

---

## Tasks

- [x] 1. Project scaffold and routing setup
  - Initialise a Vite + React 18 + TypeScript project (`npm create vite@latest jollof-intelligence-frontend -- --template react-ts`)
  - Install dependencies: `react-router-dom@6`, `fast-check`, `vitest`, `@vitest/coverage-v8`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, `msw`, `@axe-core/react`
  - Configure `vite.config.ts` with Vitest test environment (`jsdom`), coverage, and path aliases (`@/` → `src/`)
  - Create `.env` with `VITE_API_BASE_URL=http://localhost:8000` and `.env.example` with the same key and a placeholder value
  - Create `src/styles/tokens.ts` with the full design-token set (colours, breakpoints) from the design document
  - Create `src/styles/global.css` with CSS reset, base typography, and focus-ring styles meeting WCAG 2.1 AA (3:1 contrast)
  - Wire React Router in `src/main.tsx`: wrap `<App />` in `<BrowserRouter>`; define routes `/review` and `/recommend` in `App.tsx`; redirect `/` to `/review`
  - _Requirements: 1.2, 1.3, 6.2_

- [x] 2. Shared types and data models
  - [x] 2.1 Create `src/types/api.ts` with all API contract types
    - Define `ReviewRequest`, `ReviewResponse`, `PersonaSummaryData`, `ConversationTurn`, `RecommendRequest`, `Recommendation`, `RecommendResponse`
    - Define `ApiError` (with `kind: 'client' | 'server' | 'network' | 'timeout' | 'parse'`, `status?: number`, `message: string`) and `ApiResult<T>` discriminated union
    - _Requirements: 4.1, 4.4, 4.5_
  - [x] 2.2 Create `src/types/forms.ts` with all form and UI state types
    - Define `ReviewFormState`, `RecommendFormState`, `ValidationErrors`, `RequestStatus`, `RequestState<T>`
    - _Requirements: 2.1, 3.1_

- [x] 3. Validation utilities and property tests
  - [x] 3.1 Implement `src/utils/validation.ts`
    - Write `validateUserId(value: string): string | null` — rejects empty, whitespace-only, chars outside `[A-Za-z0-9_-]`, and length > 64
    - Write `validateTopK(value: number): string | null` — rejects values < 1 or > 20
    - Write `validateItemTitle(value: string): string | null` — rejects empty and length > 256
    - Write `validateContext(value: string): string | null` — rejects empty
    - _Requirements: 2.2, 2.3, 3.1, 3.3_
  - [x] 3.2 Implement `src/utils/requestBuilder.ts`
    - Write `buildReviewRequest(form: ReviewFormState): ReviewRequest` — omits optional fields (`author`, `categories`, `price`, `description`) when their value is an empty string
    - _Requirements: 2.2_
  - [ ]* 3.3 Write property tests for validation utilities (`src/utils/validation.property.test.ts`)
    - **Property 1: Invalid user_id is rejected**
    - **Validates: Requirements 2.3, 3.3**
    - **Property 2: Valid user_id is accepted**
    - **Validates: Requirements 2.2, 3.2**
    - **Property 6: Invalid top_k values are rejected**
    - **Validates: Requirements 3.1**
    - **Property 7: Valid top_k values are accepted**
    - **Validates: Requirements 3.1**
  - [ ]* 3.4 Write property test for request builder (`src/utils/requestBuilder.property.test.ts`)
    - **Property 3: Empty optional fields are omitted from the request payload**
    - **Validates: Requirements 2.2**

- [x] 4. Formatters and property tests
  - [x] 4.1 Implement `src/utils/formatters.ts`
    - Write `formatScore(score: number): string` — returns `"Score: X.XX"` with score rounded to two decimal places
    - Write `formatAvgRating(avg: number): string` — returns the value formatted to one decimal place
    - _Requirements: 2.5, 3.5_
  - [ ]* 4.2 Write property test for formatters (`src/utils/formatters.property.test.ts`)
    - **Property 10: Score values are formatted to two decimal places**
    - **Validates: Requirements 3.5**

- [x] 5. API client module and tests
  - [x] 5.1 Implement `src/api/apiClient.ts`
    - Read `VITE_API_BASE_URL` from `import.meta.env`; fall back to `http://localhost:8000`
    - Implement `generateReview(request: ReviewRequest, config?): Promise<ApiResult<ReviewResponse>>` using `fetch` with `AbortController` (120 s timeout), `Content-Type: application/json` header, and JSON body serialisation
    - Implement `getRecommendations(request: RecommendRequest, config?): Promise<ApiResult<RecommendResponse>>` with the same timeout and header pattern
    - Implement `classifyApiError(status: number): ApiError` — maps 4xx → `'client'`, 5xx → `'server'`
    - Handle network failures (fetch throws) → `kind: 'network'`, timeout (AbortError) → `kind: 'timeout'`, non-JSON body → `kind: 'parse'`
    - Extract `detail` field from error response bodies; fall back to raw text or generic message
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 5.2 Write unit and integration tests for the API client (`src/api/apiClient.test.ts`)
    - Use `msw` handlers to mock `POST /api/v1/task-a/generate-review` and `POST /api/v1/task-b/recommend`
    - Test: correct JSON body sent, `Content-Type: application/json` header present, 2xx response parsed correctly
    - Test: 4xx response → `kind: 'client'`, 5xx response → `kind: 'server'`, non-JSON body → `kind: 'parse'`
    - Test: AbortController fires after 120 s using Vitest fake timers → `kind: 'timeout'`
    - Test: `getRecommendations` includes `conversation` array in request body
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 5.3 Write property tests for the API client (`src/api/apiClient.property.test.ts`)
    - **Property 8: API error classification is correct for all HTTP error codes**
    - **Validates: Requirements 2.7, 3.11, 4.4**
    - **Property 11: All API requests include the Content-Type: application/json header**
    - **Validates: Requirements 4.2**

- [ ] 6. Shared UI components
  - [x] 6.1 Implement `src/components/LoadingSpinner/LoadingSpinner.tsx` with CSS Module
    - Animated spinner with `role="status"` and `aria-label` prop (default: "Loading…")
    - _Requirements: 2.4, 3.4, 5.1_
  - [x] 6.2 Implement `src/components/ErrorBanner/ErrorBanner.tsx` with CSS Module
    - Displays `message` prop; renders a "Retry" button that calls `onRetry`
    - Writes `message` into the panel's ARIA live region (passed as `liveRegionId` prop) on mount
    - _Requirements: 2.7, 2.8, 3.11, 3.12, 5.3_
  - [x] 6.3 Implement `src/components/ColdStartBadge/ColdStartBadge.tsx` with CSS Module
    - Renders a contextual notice badge; `feature` prop controls copy ("review" vs "recommend")
    - _Requirements: 2.6, 3.10_
  - [ ] 6.4 Implement `src/components/StarRating/StarRating.tsx` with CSS Module
    - Renders exactly 5 star elements: R filled stars and (5 − R) empty stars for rating R
    - Optionally renders the numeric value alongside (`showNumeric` prop)
    - Each star element has a `data-testid` of `"star-filled"` or `"star-empty"` for test queries
    - _Requirements: 2.5_
  - [ ]* 6.5 Write property test for StarRating (`src/components/StarRating/StarRating.property.test.ts`)
    - **Property 9: StarRating renders the correct number of filled and empty stars**
    - **Validates: Requirements 2.5**
  - [x] 6.6 Implement `src/components/FormField/FormField.tsx` with CSS Module
    - Renders a labelled `<input>` or `<textarea>` with `aria-label` / `aria-describedby` wired to an inline error message element
    - Accepts `id`, `label`, `value`, `onChange`, `error`, `required`, `type`, `as` (`'input' | 'textarea'`) props
    - _Requirements: 2.1, 3.1, 5.1, 5.4_

- [x] 7. App shell, Header, NavTabs, and routing
  - [x] 7.1 Implement `src/components/Header/Header.tsx` with CSS Module
    - Renders the application name "Jollof Intelligence" and a Naija-flavoured tagline
    - Applies the Nigerian colour palette (primary green, white background, warm accent) from design tokens
    - _Requirements: 1.1, 1.4_
  - [x] 7.2 Implement `src/components/NavTabs/NavTabs.tsx` with CSS Module
    - Renders two `<NavLink>` elements (from `react-router-dom`) linking to `/review` and `/recommend`
    - Active link receives `aria-current="page"` and a visual active style (underline / filled background)
    - Keyboard-navigable with Tab and Enter/Space
    - On mobile (≤ 768 px) tabs scroll horizontally without overflowing the viewport
    - _Requirements: 1.2, 1.3, 1.5, 5.1, 5.4_
  - [x] 7.3 Implement `src/App.tsx` with React Router routes and ARIA live regions
    - Define `<Routes>`: `<Route path="/review" element={<ReviewPage />} />`, `<Route path="/recommend" element={<RecommendPage />} />`, `<Route path="*" element={<Navigate to="/review" replace />} />`
    - Lift `reviewFormValues` and `recommendFormValues` state to `App` so they survive route changes
    - Mount two `aria-live="assertive" aria-atomic="true"` regions (`#review-live-region`, `#recommend-live-region`) at the App root
    - Pass form state and setters down to the respective page components via props
    - _Requirements: 1.2, 1.3, 5.3, 6.3, 6.4_

- [ ] 8. Review page (`/review` route — Task A)
  - [ ] 8.1 Implement `src/pages/ReviewPage/ReviewPage.tsx` with CSS Module
    - Owns `requestState: RequestState<ReviewResponse>` and `lastRequest: ReviewRequest | null` local state
    - Receives `formValues: ReviewFormState` and `onFormChange` from `App`
    - On submit: run validation; if errors show inline messages and return; otherwise call `generateReview`, set loading state within 100 ms, clear previous results
    - On success: set result, move focus to the review text element
    - On error: set error state, move focus to the submit button
    - Renders `ReviewForm`, `LoadingSpinner`, `ErrorBanner` (with retry wired to `lastRequest`), and `ReviewResult`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 5.2, 6.1_
  - [ ] 8.2 Implement `src/pages/ReviewPage/ReviewForm.tsx`
    - Six `FormField` instances: `user_id` (required), `item_title` (required), `author`, `categories`, `price`, `description` (textarea)
    - Submit button disabled while `isLoading` is true
    - Inline validation errors displayed beneath each offending field on submit attempt
    - All fields have descriptive `aria-label` attributes
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.1, 5.4_
  - [ ] 8.3 Implement `src/pages/ReviewPage/ReviewResult.tsx`
    - Renders `StarRating` (with `showNumeric`), review text, `PersonaSummary`, and `ColdStartBadge` (when `cold_start` is true)
    - `PersonaSummary` displays `avg_rating` (via `formatAvgRating`), `top_categories` as comma-separated list, `tone`, `sentiment_tendency`
    - First result element receives `tabIndex={-1}` and a `ref` for programmatic focus
    - _Requirements: 2.5, 2.6_
  - [ ]* 8.4 Write unit tests for ReviewPage (`src/pages/ReviewPage/ReviewPage.test.ts`)
    - Test: loading spinner appears on submit, submit button disabled during loading
    - Test: result renders with correct star count, review text, persona summary fields
    - Test: `cold_start: true` renders `ColdStartBadge`
    - Test: error state renders `ErrorBanner` with retry button; clicking retry re-sends last request
    - Test: validation errors shown for empty `user_id` and `item_title`
    - Test: stale results cleared when new submission begins
    - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

- [ ] 9. Checkpoint — Ensure all tests pass
  - Run `vitest --run` and confirm all tests pass. Ask the user if any questions arise before continuing.

- [ ] 10. Recommend page (`/recommend` route — Task B)
  - [ ] 10.1 Implement `src/pages/RecommendPage/RecommendPage.tsx` with CSS Module
    - Owns `requestState: RequestState<RecommendResponse>`, `conversation: ConversationTurn[]`, and `lastRequest: RecommendRequest | null` local state
    - Receives `formValues: RecommendFormState` and `onFormChange` from `App`
    - On submit: run validation; if errors show inline messages and return; otherwise call `getRecommendations` with current `conversation`, set loading state within 100 ms
    - On success: append user turn + assistant turn to `conversation`, set result, move focus to first recommendation card
    - On error: set error state, move focus to submit button
    - On clear: reset `conversation` to `[]`, clear result state
    - Renders `RecommendForm`, `LoadingSpinner`, `ErrorBanner` (with retry), `ConversationHistory`, recommendation list, `FollowUpBanner`, `ColdStartBadge`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 5.2, 6.1_
  - [ ] 10.2 Implement `src/pages/RecommendPage/RecommendForm.tsx`
    - Three `FormField` instances: `user_id` (required), `context` (required, textarea), `top_k` (number, default 5)
    - Submit button disabled while `isLoading` is true
    - Inline validation errors on submit attempt
    - All fields have descriptive `aria-label` attributes
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.1, 5.4_
  - [ ] 10.3 Implement `src/components/ConversationHistory/ConversationHistory.tsx` with CSS Module
    - Renders exactly one element per `ConversationTurn`, each labelled with its `role`
    - Renders a "Clear conversation" button that calls `onClear`; button has `aria-label="Clear conversation history"`
    - Only rendered when `turns.length > 0`
    - _Requirements: 3.7, 3.9_
  - [ ]* 10.4 Write property test for ConversationHistory (`src/components/ConversationHistory/ConversationHistory.property.test.ts`)
    - **Property 13: ConversationHistory renders exactly one element per turn**
    - **Validates: Requirements 3.7**
  - [ ] 10.5 Implement `src/pages/RecommendPage/RecommendationCard.tsx` with CSS Module
    - Renders `title`, `author`, `categories`, `price`, `score` (via `formatScore`), and `reason`
    - First card receives `tabIndex={-1}` and a `ref` for programmatic focus
    - _Requirements: 3.5_
  - [ ] 10.6 Implement `src/pages/RecommendPage/FollowUpBanner.tsx` with CSS Module
    - Renders the `follow_up` string in a visually distinct area below the recommendation cards
    - Only rendered when `follow_up` is a non-empty string
    - _Requirements: 3.6_
  - [ ]* 10.7 Write unit tests for RecommendPage (`src/pages/RecommendPage/RecommendPage.test.ts`)
    - Test: loading spinner appears on submit, submit button disabled during loading
    - Test: recommendation cards render with correct fields and formatted score
    - Test: `cold_start: true` renders `ColdStartBadge`
    - Test: `follow_up` string renders `FollowUpBanner`
    - Test: empty `recommendations` array renders "no recommendations" message
    - Test: error state renders `ErrorBanner` with retry; clicking retry re-sends last request
    - Test: validation errors shown for empty `user_id` and `context`
    - Test: "Clear conversation" resets conversation and results
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.9, 3.10, 3.11, 3.12, 3.13_
  - [ ]* 10.8 Write property tests for RecommendPage (`src/pages/RecommendPage/RecommendPage.property.test.ts`)
    - **Property 4: Conversation history grows by two turns per submission**
    - **Validates: Requirements 3.7, 3.8**
    - **Property 5: Clearing conversation resets to an empty array**
    - **Validates: Requirements 3.9**

- [ ] 11. App-level integration and property tests
  - [ ] 11.1 Write property test for form value preservation (`src/App.property.test.ts`)
    - **Property 12: Form field values are preserved across panel switches**
    - **Validates: Requirements 6.4**
  - [ ]* 11.2 Write responsive snapshot tests (`src/App.test.ts`)
    - Render `App` at 375 px, 900 px, and 1280 px viewport widths using jsdom
    - Assert that the navigation header, NavTabs, and route outlet are visible at all three widths
    - Assert that on mobile (375 px) the NavTabs do not overflow the viewport
    - _Requirements: 1.5_
  - [ ]* 11.3 Write accessibility tests using axe-core (`src/App.accessibility.test.ts`)
    - Run `axe` against the rendered `/review` route and assert zero violations
    - Run `axe` against the rendered `/recommend` route and assert zero violations
    - _Requirements: 1.6, 5.1, 5.3, 5.4, 5.5_

- [ ] 12. Final checkpoint — Ensure all tests pass
  - Run `vitest --run` and confirm all tests pass. Ask the user if any questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- React Router `<NavLink>` is used for `/review` and `/recommend` routes so the browser URL updates on navigation, satisfying the user's explicit requirement for page-level routing while still being a SPA (no full page reload)
- Form values (`reviewFormValues`, `recommendFormValues`) are lifted to `App` and passed as props to each page component so they survive route changes (Requirement 6.4)
- The two ARIA live regions are mounted at the `App` root and remain in the DOM at all times; `ErrorBanner` writes into the appropriate region via `liveRegionId` prop
- `fast-check` property tests run a minimum of 100 iterations each; tag format: `// Feature: jollof-intelligence-frontend, Property N: <title>`
- All CSS is scoped via CSS Modules; design tokens from `src/styles/tokens.ts` are imported directly into module files
- `msw` is used for API integration tests; configure `src/mocks/server.ts` with `setupServer` and import in `vitest.setup.ts`

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1", "2.2"] },
    { "id": 1, "tasks": ["3.1", "3.2", "4.1"] },
    { "id": 2, "tasks": ["3.3", "3.4", "4.2", "5.1"] },
    { "id": 3, "tasks": ["5.2", "5.3", "6.1", "6.2", "6.3", "6.4"] },
    { "id": 4, "tasks": ["6.5", "6.6", "7.1", "7.2"] },
    { "id": 5, "tasks": ["7.3"] },
    { "id": 6, "tasks": ["8.1", "8.2", "8.3", "10.1", "10.2", "10.3", "10.5", "10.6"] },
    { "id": 7, "tasks": ["8.4", "10.4", "10.7", "10.8"] },
    { "id": 8, "tasks": ["11.1", "11.2", "11.3"] }
  ]
}
```
