# Design Document — Jollof Intelligence Frontend

## Overview

Jollof Intelligence Frontend is a standalone single-page application (SPA) that surfaces two AI-powered features from the Jollof Intelligence FastAPI backend. The application embodies Nigerian cultural identity through its visual design, tone, and interaction patterns.

**Two core features:**
- **Book Review Simulator (Task A)** — given a user ID and book details, calls `POST /api/v1/task-a/generate-review` and renders an AI-generated Nigerian-English review with a predicted star rating and persona summary.
- **Personalised Book Recommender (Task B)** — given a user ID, a natural-language context, and an optional multi-turn conversation history, calls `POST /api/v1/task-b/recommend` and renders ranked recommendation cards with reasons.

**Technology choices:**
- **React 18** with TypeScript — component model maps cleanly to the two-panel layout; TypeScript enforces the API contract types at compile time.
- **Vite** — fast dev server and build tool; native support for `VITE_API_BASE_URL` env var.
- **CSS Modules** — scoped styles without a heavy CSS-in-JS runtime; keeps the bundle lean.
- **No UI framework** — the design is bespoke (Nigerian cultural identity), so a component library would fight the aesthetic. Custom components are straightforward given the limited scope.
- **fast-check** (property-based testing) — TypeScript-native PBT library for correctness properties.
- **Vitest** — test runner co-located with Vite; zero-config for the project setup.

The frontend communicates exclusively with the backend over HTTP. No backend modifications are made.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (SPA)                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  App Shell                                               │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │  Header  (logo, tagline, nav tabs)               │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │   │
│  │  │  Review Panel    │  │  Recommend Panel             │ │   │
│  │  │  (Task A)        │  │  (Task B)                    │ │   │
│  │  │                  │  │                              │ │   │
│  │  │  ReviewForm      │  │  RecommendForm               │ │   │
│  │  │  ReviewResult    │  │  ConversationHistory         │ │   │
│  │  │  StarRating      │  │  RecommendationCard[]        │ │   │
│  │  │  PersonaSummary  │  │  FollowUpBanner              │ │   │
│  │  │  ColdStartBadge  │  │  ColdStartBadge              │ │   │
│  │  │  ErrorBanner     │  │  ErrorBanner                 │ │   │
│  │  └──────────────────┘  └──────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Client (apiClient.ts)                               │   │
│  │  generateReview()  |  getRecommendations()               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Backend  (http://localhost:8000)                       │
│  POST /api/v1/task-a/generate-review                            │
│  POST /api/v1/task-b/recommend                                  │
└─────────────────────────────────────────────────────────────────┘
```

### State Management

State is managed locally with React's built-in `useState` and `useReducer` hooks — no external state library is needed given the limited scope. Each panel owns its own form state, request state, and result state. Form values are lifted to the `App` component so they survive panel switches (Requirement 6.4).

```
App
├── activePanel: 'review' | 'recommend'
├── reviewFormValues: ReviewFormState        ← persisted across panel switches
├── recommendFormValues: RecommendFormState  ← persisted across panel switches
├── ReviewPanel
│   ├── requestState: idle | loading | success | error
│   ├── result: ReviewResponse | null
│   └── lastRequest: ReviewRequest | null    ← for retry
└── RecommendPanel
    ├── requestState: idle | loading | success | error
    ├── result: RecommendResponse | null
    ├── conversation: ConversationTurn[]
    └── lastRequest: RecommendRequest | null ← for retry
```

### Routing

No client-side router is needed. Panel switching is handled by toggling `activePanel` state — the URL does not change (Requirement 6.3).

---

## Components and Interfaces

### Component Tree

```
App
├── Header
│   ├── AppLogo
│   └── NavTabs
│       ├── NavTab (Review)
│       └── NavTab (Recommend)
├── ReviewPanel
│   ├── ReviewForm
│   │   ├── FormField (user_id)
│   │   ├── FormField (item_title)
│   │   ├── FormField (author)
│   │   ├── FormField (categories)
│   │   ├── FormField (price)
│   │   ├── FormField (description — textarea)
│   │   └── SubmitButton
│   ├── LoadingSpinner (conditional)
│   ├── ErrorBanner (conditional)
│   └── ReviewResult (conditional)
│       ├── StarRating
│       ├── ReviewText
│       ├── PersonaSummary
│       └── ColdStartBadge
└── RecommendPanel
    ├── RecommendForm
    │   ├── FormField (user_id)
    │   ├── FormField (context — textarea)
    │   ├── FormField (top_k — number)
    │   └── SubmitButton
    ├── LoadingSpinner (conditional)
    ├── ErrorBanner (conditional)
    ├── ConversationHistory (conditional)
    │   ├── ConversationTurn[] (role + content)
    │   └── ClearConversationButton
    ├── RecommendationList (conditional)
    │   └── RecommendationCard[]
    │       ├── BookTitle + Author
    │       ├── Categories + Price
    │       ├── ScoreBadge
    │       └── ReasonText
    ├── FollowUpBanner (conditional)
    └── ColdStartBadge (conditional)
```

### Key Component Interfaces

```typescript
// NavTabs
interface NavTabsProps {
  activePanel: 'review' | 'recommend';
  onSwitch: (panel: 'review' | 'recommend') => void;
}

// ReviewForm
interface ReviewFormProps {
  values: ReviewFormState;
  onChange: (values: ReviewFormState) => void;
  onSubmit: (values: ReviewFormState) => void;
  isLoading: boolean;
}

// ReviewResult
interface ReviewResultProps {
  result: ReviewResponse;
}

// StarRating
interface StarRatingProps {
  rating: number; // 1–5
  showNumeric?: boolean;
}

// PersonaSummary
interface PersonaSummaryProps {
  summary: PersonaSummaryData;
}

// RecommendForm
interface RecommendFormProps {
  values: RecommendFormState;
  onChange: (values: RecommendFormState) => void;
  onSubmit: (values: RecommendFormState) => void;
  isLoading: boolean;
}

// ConversationHistory
interface ConversationHistoryProps {
  turns: ConversationTurn[];
  onClear: () => void;
}

// RecommendationCard
interface RecommendationCardProps {
  recommendation: Recommendation;
}

// ErrorBanner
interface ErrorBannerProps {
  message: string;
  onRetry: () => void;
}

// ColdStartBadge
interface ColdStartBadgeProps {
  feature: 'review' | 'recommend';
}

// LoadingSpinner
interface LoadingSpinnerProps {
  label?: string; // for aria-label
}
```

### API Client Interface

```typescript
// src/api/apiClient.ts

export interface ApiClientConfig {
  baseUrl: string;       // from VITE_API_BASE_URL, default http://localhost:8000
  timeoutMs: number;     // 120_000
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };

export interface ApiError {
  kind: 'client' | 'server' | 'network' | 'timeout' | 'parse';
  status?: number;
  message: string;
}

export function generateReview(
  request: ReviewRequest,
  config?: Partial<ApiClientConfig>
): Promise<ApiResult<ReviewResponse>>;

export function getRecommendations(
  request: RecommendRequest,
  config?: Partial<ApiClientConfig>
): Promise<ApiResult<RecommendResponse>>;
```

---

## Data Models

All types mirror the backend API contracts exactly.

```typescript
// ── Task A ──────────────────────────────────────────────────────

export interface ReviewRequest {
  user_id: string;
  product: {
    item_title: string;
    author?: string;
    categories?: string;
    price?: string;
    description?: string;
  };
}

export interface PersonaSummaryData {
  avg_rating: number;
  top_categories: string[];
  tone: string;
  sentiment_tendency: string;
  cold_start: boolean;
}

export interface ReviewResponse {
  user_id: string;
  rating: number;          // 1–5 integer
  review: string;
  persona_summary: PersonaSummaryData;
}

// ── Task B ──────────────────────────────────────────────────────

export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface RecommendRequest {
  user_id: string;
  context: string;
  conversation: ConversationTurn[];
  top_k?: number;          // 1–20, default 5
}

export interface Recommendation {
  item_id: string;
  title: string;
  author: string;
  categories: string;
  price: string;
  score: number;           // 0.0–1.0
  reason: string;
}

export interface RecommendResponse {
  user_id: string;
  recommendations: Recommendation[];
  follow_up?: string;
  cold_start: boolean;
}

// ── Form State ──────────────────────────────────────────────────

export interface ReviewFormState {
  user_id: string;
  item_title: string;
  author: string;
  categories: string;
  price: string;
  description: string;
}

export interface RecommendFormState {
  user_id: string;
  context: string;
  top_k: number;
}

// ── Validation ──────────────────────────────────────────────────

export interface ValidationErrors {
  user_id?: string;
  item_title?: string;
  context?: string;
  top_k?: string;
}

// ── Request State ───────────────────────────────────────────────

export type RequestStatus = 'idle' | 'loading' | 'success' | 'error';

export interface RequestState<T> {
  status: RequestStatus;
  data: T | null;
  error: ApiError | null;
}
```

### Validation Rules

| Field | Rule |
|---|---|
| `user_id` | Required. Non-empty. Only alphanumeric, hyphens, underscores. Max 64 chars. |
| `item_title` | Required. Non-empty. Max 256 chars. |
| `context` | Required. Non-empty. |
| `top_k` | Optional. Integer in range [1, 20]. Defaults to 5. |

Optional fields (`author`, `categories`, `price`, `description`) are omitted from the request payload when empty — they are not sent as empty strings.

### Design Token Reference

```typescript
// src/styles/tokens.ts
export const colors = {
  primary: '#008751',       // Nigerian flag green
  background: '#FFFFFF',    // white
  accent: '#E87722',        // warm orange (Jollof rice)
  accentAlt: '#CC0000',     // deep red (secondary accent)
  textPrimary: '#1A1A1A',   // near-black for body text
  textSecondary: '#555555', // muted text
  surface: '#F9F5F0',       // warm off-white card background
  border: '#D4C5B0',        // warm border
  error: '#CC0000',
  success: '#008751',
  focusRing: '#E87722',     // 3:1+ contrast on white
};

export const breakpoints = {
  mobile: 768,
  tablet: 1024,
};
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Invalid user_id is rejected

*For any* string that is empty, composed entirely of whitespace, contains characters outside `[A-Za-z0-9_-]`, or exceeds 64 characters, the `validateUserId` function SHALL return a non-null error message.

**Validates: Requirements 2.3, 3.3**

### Property 2: Valid user_id is accepted

*For any* non-empty string composed solely of alphanumeric characters, hyphens, and underscores with length between 1 and 64 (inclusive), the `validateUserId` function SHALL return null (no error).

**Validates: Requirements 2.2, 3.2**

### Property 3: Empty optional fields are omitted from the request payload

*For any* `ReviewFormState` where one or more optional fields (`author`, `categories`, `price`, `description`) are empty strings, the `buildReviewRequest` serialisation function SHALL produce a `ReviewRequest` whose `product` object does not contain keys for those empty fields.

**Validates: Requirements 2.2**

### Property 4: Conversation history grows by two turns per submission

*For any* sequence of N successful recommendation submissions (N ≥ 1), the conversation history array length after all N submissions SHALL equal 2×N — one user turn and one assistant turn appended per round.

**Validates: Requirements 3.7, 3.8**

### Property 5: Clearing conversation resets to an empty array

*For any* non-empty conversation history array, invoking the clear-conversation action SHALL produce a conversation array of length 0.

**Validates: Requirements 3.9**

### Property 6: Invalid top_k values are rejected

*For any* numeric value strictly less than 1 or strictly greater than 20, the `validateTopK` function SHALL return a non-null error message.

**Validates: Requirements 3.1**

### Property 7: Valid top_k values are accepted

*For any* integer value in the inclusive range [1, 20], the `validateTopK` function SHALL return null (no error).

**Validates: Requirements 3.1**

### Property 8: API error classification is correct for all HTTP error codes

*For any* HTTP response status code in [400, 499], the `classifyApiError` function SHALL return an `ApiError` with `kind` equal to `'client'`; for any status code in [500, 599], it SHALL return `kind` equal to `'server'`.

**Validates: Requirements 2.7, 3.11, 4.4**

### Property 9: StarRating renders the correct number of filled and empty stars

*For any* integer rating R in [1, 5], the `StarRating` component SHALL render exactly R filled-star elements and exactly (5 − R) empty-star elements, for a total of exactly 5 star elements.

**Validates: Requirements 2.5**

### Property 10: Score values are formatted to two decimal places

*For any* floating-point score value S in [0.0, 1.0], the `formatScore` function SHALL return a string matching the pattern `"Score: X.XX"` where X.XX is S rounded to two decimal places.

**Validates: Requirements 3.5**

### Property 11: All API requests include the Content-Type: application/json header

*For any* valid `ReviewRequest` or `RecommendRequest` object, the `generateReview` and `getRecommendations` functions SHALL include a `Content-Type: application/json` header in the outbound HTTP request.

**Validates: Requirements 4.2**

### Property 12: Form field values are preserved across panel switches

*For any* `ReviewFormState` and `RecommendFormState`, switching from the Review panel to the Recommend panel and back SHALL leave both form states byte-for-byte identical to their values before the switches.

**Validates: Requirements 6.4**

### Property 13: ConversationHistory renders exactly one element per turn

*For any* array of N `ConversationTurn` objects (N ≥ 0), the `ConversationHistory` component SHALL render exactly N turn elements in the DOM, each labelled with its corresponding `role`.

**Validates: Requirements 3.7**

---

## Error Handling

### Error Classification

The API Client classifies all failure modes into five kinds:

| Kind | Trigger | User-facing message pattern |
|---|---|---|
| `client` | HTTP 4xx | "Invalid request — check your inputs" |
| `server` | HTTP 5xx | "The server encountered an error — please try again" |
| `network` | Fetch throws (no connection) | "Could not reach the server — check your connection" |
| `timeout` | AbortController fires at 120 s | "The request timed out — please try again" |
| `parse` | Response body is not valid JSON | "Received an unexpected response from the server" |

### Retry Mechanism

Each panel stores the last submitted request (`lastRequest`). When the user clicks the retry button in the `ErrorBanner`, the panel re-invokes the API call with the stored request — no re-entry of form data is required (Requirements 2.8, 3.12).

### Validation Errors

Validation runs on submit (not on every keystroke, to avoid premature error messages). Errors are displayed inline beneath each offending field. The submit button is not disabled until the user has attempted submission — this avoids confusing users who haven't yet interacted with a field.

### ARIA Live Regions

Two `aria-live="assertive"` regions are mounted at the App root (one per panel) and remain in the DOM at all times. Error messages are written into these regions when an `ErrorBanner` appears, ensuring immediate screen-reader announcement (Requirement 5.3).

```html
<div aria-live="assertive" aria-atomic="true" class="sr-only" id="review-live-region"></div>
<div aria-live="assertive" aria-atomic="true" class="sr-only" id="recommend-live-region"></div>
```

### Focus Management

| Event | Focus destination |
|---|---|
| Loading ends, results present | First result element (review text or first recommendation card) |
| Loading ends, no results / error | Submit button of the active panel |
| Panel switch | First focusable element in the newly active panel |

---

## Testing Strategy

### Dual Testing Approach

Both unit/example-based tests and property-based tests are used. Unit tests cover specific scenarios and integration points; property tests verify universal correctness across a wide input space.

### Property-Based Testing

**Library:** `fast-check` (TypeScript-native, works with Vitest)

Each correctness property from the design document is implemented as a single `fc.assert(fc.property(...))` test configured to run a minimum of 100 iterations.

Tag format in test files:
```typescript
// Feature: jollof-intelligence-frontend, Property 1: user_id validation rejects invalid formats
```

**Properties and their generators:**

| Property | Generator strategy |
|---|---|
| P1 — invalid user_id rejected | `fc.oneof(fc.constant(''), fc.constant('   '), fc.string({ minLength: 65 }), fc.string().filter(s => /[^A-Za-z0-9_-]/.test(s) && s.length > 0))` |
| P2 — valid user_id accepted | `fc.stringMatching(/^[A-Za-z0-9_-]{1,64}$/)` |
| P3 — empty optional fields omitted | `fc.record({ user_id: validUserIdArb, item_title: validTitleArb, author: fc.constant(''), categories: fc.constant(''), price: fc.constant(''), description: fc.constant('') })` |
| P4 — conversation grows by 2 per submission | `fc.array(fc.record({ context: fc.string({ minLength: 1 }), top_k: fc.integer({ min: 1, max: 20 }) }), { minLength: 1, maxLength: 10 })` |
| P5 — clear resets to empty | `fc.array(conversationTurnArb, { minLength: 1 })` |
| P6 — invalid top_k rejected | `fc.oneof(fc.integer({ max: 0 }), fc.integer({ min: 21 }))` |
| P7 — valid top_k accepted | `fc.integer({ min: 1, max: 20 })` |
| P8 — error classification | `fc.oneof(fc.integer({ min: 400, max: 499 }), fc.integer({ min: 500, max: 599 }))` |
| P9 — star rating count | `fc.integer({ min: 1, max: 5 })` |
| P10 — score formatting | `fc.float({ min: 0, max: 1, noNaN: true })` |
| P11 — Content-Type header on all requests | `fc.oneof(reviewRequestArb, recommendRequestArb)` |
| P12 — form values preserved across panel switches | `fc.record({ reviewForm: reviewFormStateArb, recommendForm: recommendFormStateArb })` |
| P13 — ConversationHistory renders N elements | `fc.array(conversationTurnArb, { minLength: 0, maxLength: 20 })` |

### Unit / Example-Based Tests

Unit tests focus on:
- Specific validation edge cases (e.g., `user_id` of exactly 64 chars passes, 65 chars fails)
- API Client: correct headers, correct URL construction, timeout wiring
- `ReviewPanel` renders cold-start badge when `cold_start: true`
- `RecommendPanel` renders "no recommendations" message when `recommendations` is empty
- `ConversationHistory` renders all turns with correct role labels
- `ErrorBanner` renders retry button and calls `onRetry` on click
- `NavTabs` marks the active tab with `aria-selected="true"`

### Integration Tests

- `generateReview` sends correct JSON body and `Content-Type: application/json` header (using `msw` mock service worker)
- `getRecommendations` includes conversation history in the request body
- Timeout: AbortController fires after 120 s (using fake timers)
- Parse error: non-JSON response body surfaces `kind: 'parse'` error

### Accessibility Tests

- `axe-core` (via `@axe-core/react`) run against each panel in Vitest to catch ARIA violations
- Manual keyboard navigation checklist (Tab order, Enter/Space on buttons, focus ring visibility)

### Responsive Layout Tests

- Snapshot tests at three viewport widths (375 px mobile, 900 px tablet, 1280 px desktop) using Vitest + jsdom

### Test File Structure

```
src/
├── api/
│   ├── apiClient.ts
│   └── apiClient.test.ts              # unit + integration tests for API client
│   └── apiClient.property.test.ts     # PBT: P8 (error classification), P11 (Content-Type header)
├── utils/
│   ├── validation.ts
│   ├── validation.test.ts             # unit tests (edge cases, boundary values)
│   └── validation.property.test.ts   # PBT: P1, P2, P6, P7
├── utils/
│   ├── formatters.ts
│   └── formatters.property.test.ts   # PBT: P10 (score formatting)
├── utils/
│   ├── requestBuilder.ts
│   └── requestBuilder.property.test.ts  # PBT: P3 (empty optional fields omitted)
├── components/
│   ├── StarRating/
│   │   ├── StarRating.tsx
│   │   └── StarRating.property.test.ts  # PBT: P9 (star count)
│   ├── ConversationHistory/
│   │   ├── ConversationHistory.tsx
│   │   └── ConversationHistory.property.test.ts  # PBT: P13 (renders N elements)
│   ├── ReviewPanel/
│   │   ├── ReviewPanel.tsx
│   │   └── ReviewPanel.test.ts        # unit: loading, error, cold-start, retry
│   └── RecommendPanel/
│       ├── RecommendPanel.tsx
│       ├── RecommendPanel.test.ts     # unit: loading, error, cold-start, retry, empty results
│       └── RecommendPanel.property.test.ts  # PBT: P4 (conversation grows), P5 (clear resets)
└── App.test.ts                        # unit: panel switching, default panel
└── App.property.test.ts               # PBT: P12 (form values preserved across panel switches)
```
