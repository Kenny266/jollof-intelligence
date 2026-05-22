# Requirements Document

## Introduction

Jollof Intelligence Frontend is a web application that surfaces two AI-powered features from the existing Jollof Intelligence FastAPI backend (running at `http://localhost:8000`). The UI embodies Nigerian cultural identity — warm colours, Naija tone, and a clean, minimalistic layout — while providing two clear interaction panels:

1. **Book Review Simulator** — given a user ID and book details, generate an authentic Nigerian-English review with a predicted rating (Task A).
2. **Personalised Book Recommender** — given a user ID, a natural-language context, and an optional conversation history, return a ranked list of book recommendations with reasons (Task B).

The frontend is a standalone single-page application (SPA) that communicates exclusively with the existing backend API. No backend modifications are permitted.

---

## Glossary

- **App**: The Jollof Intelligence Frontend single-page application.
- **User**: A person interacting with the App through a web browser.
- **Review_Panel**: The UI section dedicated to Task A (book review simulation).
- **Recommend_Panel**: The UI section dedicated to Task B (book recommendations).
- **API_Client**: The frontend module responsible for all HTTP communication with the backend.
- **Review_Request**: The JSON payload sent to `POST /api/v1/task-a/generate-review`.
- **Recommend_Request**: The JSON payload sent to `POST /api/v1/task-b/recommend`.
- **Review_Response**: The JSON payload returned by the Task A endpoint.
- **Recommend_Response**: The JSON payload returned by the Task B endpoint.
- **Conversation_Turn**: A single `{role, content}` object within the multi-turn conversation history for Task B.
- **Loading_State**: A visual indicator shown while an API request is in flight.
- **Error_State**: A visual indicator shown when an API request fails or returns an error.
- **Cold_Start**: A scenario where the backend has no prior history for the given `user_id` and falls back to context-only inference.

---

## Requirements

### Requirement 1: Application Shell and Navigation

**User Story:** As a user, I want a clearly structured single-page application with a Nigerian cultural identity, so that I can navigate between the two features intuitively and feel the Naija vibe.

#### Acceptance Criteria

1. THE App SHALL render a top-level navigation header containing the application name "Jollof Intelligence" and a tagline that reflects Nigerian cultural identity (e.g., "Your Naija Book Oracle" or equivalent Naija-flavoured phrase).
2. THE App SHALL provide navigation controls (tabs or equivalent) that allow the User to switch between the Review_Panel and the Recommend_Panel without a full page reload; the active panel's tab SHALL be visually distinguished from inactive tabs (e.g., underline, bold weight, or filled background) so the User can identify which panel is currently active.
3. WHEN the App first loads, THE App SHALL display the Review_Panel as the default active panel and the Review tab SHALL be marked as active.
4. THE App SHALL apply a colour palette inspired by Nigerian culture: primary green (#008751 or equivalent Nigerian-flag green), white (#FFFFFF) background, and a warm accent (e.g., orange #E87722 or red #CC0000 consistent with Jollof rice aesthetic); these three roles SHALL be consistently applied across all UI surfaces.
5. THE App SHALL be fully responsive, adapting its layout for mobile (≤ 768 px), tablet (769 px – 1024 px), and desktop (≥ 1025 px) viewports; on mobile the navigation controls SHALL stack or scroll horizontally rather than overflow the viewport.
6. THE App SHALL meet WCAG 2.1 Level AA colour-contrast requirements (minimum 4.5:1 for normal text, 3:1 for large text and UI components) for all text and interactive elements.

---

### Requirement 2: Book Review Simulator (Task A)

**User Story:** As a user, I want to enter a user ID and book details and receive an AI-generated Nigerian-English review with a star rating, so that I can see how the system models a reader's voice.

#### Acceptance Criteria

1. THE Review_Panel SHALL display an input form containing the following fields: `user_id` (required), `item_title` (required), `author` (optional), `categories` (optional), `price` (optional), and `description` (optional).
2. WHEN the User submits the review form with a `user_id` that is non-empty and contains only alphanumeric characters, hyphens, or underscores (max 64 characters) and an `item_title` that is non-empty (max 256 characters), THE API_Client SHALL send a Review_Request to `POST /api/v1/task-a/generate-review` with the provided field values, omitting optional fields that are empty.
3. WHEN the User submits the review form with an empty `user_id` or empty `item_title`, THE Review_Panel SHALL prevent form submission and display an inline validation message directly beneath the offending field(s) identifying the missing required field(s).
4. WHILE a Review_Request is in flight, THE Review_Panel SHALL display a Loading_State (spinner or skeleton) and disable the submit button to prevent duplicate submissions.
5. WHEN a Review_Response is received, THE Review_Panel SHALL clear any previous results and display: the generated `review` text; the predicted `rating` as a visual star indicator (1–5 filled stars, with the numeric value shown alongside); and the `persona_summary` fields (`avg_rating` formatted to one decimal place, `top_categories` as a comma-separated list, `tone`, `sentiment_tendency`, and `cold_start` as a boolean badge).
6. WHEN the `cold_start` field in the Review_Response is `true`, THE Review_Panel SHALL display a contextual notice (e.g., a banner or info badge) informing the User that the review was generated without prior reading history.
7. IF the API_Client receives an HTTP error response (status ≥ 400) for a Review_Request, THEN THE Review_Panel SHALL display an Error_State message that distinguishes between a client error (4xx — e.g., "Invalid request — check your inputs") and a server error (5xx — e.g., "The server encountered an error — please try again"), and SHALL offer a retry action button. IF the API_Client receives a network failure or timeout, THEN THE Review_Panel SHALL display an Error_State message indicating a connectivity issue (e.g., "Could not reach the server — check your connection") and SHALL offer a retry action button.
8. WHEN the User clicks the retry action in the Review_Panel Error_State, THE API_Client SHALL re-send the most recent Review_Request without requiring the User to re-enter form data.
9. WHEN a new Review_Request submission begins, THE Review_Panel SHALL clear any previously displayed review results before showing the Loading_State, so that stale results are not visible alongside the new request.

---

### Requirement 3: Personalised Book Recommender (Task B)

**User Story:** As a user, I want to enter a user ID and a natural-language context to receive personalised book recommendations with Nigerian-flavoured reasons, so that I can discover books that match my taste.

#### Acceptance Criteria

1. THE Recommend_Panel SHALL display an input form containing the following fields: `user_id` (required, text), `context` (required, textarea), and `top_k` (optional, numeric input, default value 5, valid range 1–20).
2. WHEN the User submits the recommendation form with a non-empty `user_id` and a non-empty `context`, THE API_Client SHALL send a Recommend_Request to `POST /api/v1/task-b/recommend` with the provided field values and the current conversation history.
3. IF the User submits the recommendation form with an empty `user_id` or empty `context`, THEN THE Recommend_Panel SHALL prevent form submission and display an inline validation message directly beneath the offending field(s) identifying the missing required field(s).
4. WHILE a Recommend_Request is in flight, THE Recommend_Panel SHALL display a Loading_State (spinner or skeleton) and disable the submit button to prevent duplicate submissions.
5. WHEN a Recommend_Response is received, THE Recommend_Panel SHALL display each recommendation as a card containing: `title`, `author`, `categories`, `price`, `score` rendered as a decimal between 0.00 and 1.00 (e.g., "Score: 0.94"), and `reason`.
6. WHEN a Recommend_Response includes a non-empty `follow_up` string, THE Recommend_Panel SHALL display the follow-up question in a visually distinct area below the recommendation cards.
7. THE Recommend_Panel SHALL maintain a visible conversation history panel showing all prior Conversation_Turns for the current session, with each turn labelled by its `role` ("user" or "assistant").
8. WHEN the User submits a new recommendation request in the same session, THE API_Client SHALL include all prior Conversation_Turns in the `conversation` array of the Recommend_Request.
9. WHEN the User clicks the "Clear conversation" control, THE Recommend_Panel SHALL reset the conversation history to an empty array and clear the results area, returning the panel to its initial state.
10. WHEN the `cold_start` field in the Recommend_Response is `true`, THE Recommend_Panel SHALL display a contextual notice informing the User that recommendations were generated without prior reading history.
11. IF the API_Client receives an HTTP error response (status ≥ 400) for a Recommend_Request, THEN THE Recommend_Panel SHALL display an Error_State message distinguishing client errors (4xx) from server errors (5xx), and SHALL offer a retry action button. IF the API_Client receives a network failure or timeout, THEN THE Recommend_Panel SHALL display an Error_State message indicating a connectivity issue and SHALL offer a retry action button.
12. WHEN the User clicks the retry action in the Recommend_Panel Error_State, THE API_Client SHALL re-send the most recent Recommend_Request without requiring the User to re-enter form data.
13. WHEN a Recommend_Response is received with an empty `recommendations` array, THE Recommend_Panel SHALL display a message informing the User that no recommendations were found for the given context (e.g., "No recommendations found — try a different context or user ID").

---

### Requirement 4: API Client and Communication

**User Story:** As a developer, I want a well-structured API client module, so that all backend communication is centralised, consistent, and easy to maintain.

#### Acceptance Criteria

1. THE API_Client SHALL send all requests to the base URL `http://localhost:8000` by default, with the base URL configurable via an environment variable (e.g., `VITE_API_BASE_URL` or `REACT_APP_API_BASE_URL`).
2. THE API_Client SHALL set the `Content-Type: application/json` header on all outbound requests.
3. THE API_Client SHALL parse JSON response bodies for both success (2xx) and error (≥ 400) responses; IF the response body is not valid JSON, THEN THE API_Client SHALL treat the response as a network-level failure and surface a generic parse error message to the calling panel.
4. WHEN the backend returns an HTTP status code ≥ 400, THE API_Client SHALL extract and surface the error detail from the response body to the calling panel; IF the response body does not contain a `detail` field, THEN THE API_Client SHALL surface the raw response body text or a generic fallback message (e.g., "An unexpected error occurred").
5. THE API_Client SHALL enforce a request timeout of 120 seconds, after which THE API_Client SHALL abort the request and treat it as a network failure, surfacing a timeout-specific message to the calling panel.

---

### Requirement 5: Accessibility and Usability

**User Story:** As a user with assistive technology, I want the application to be accessible and keyboard-navigable, so that I can use all features regardless of my input method.

#### Acceptance Criteria

1. THE App SHALL assign descriptive `aria-label` or `aria-labelledby` attributes to all interactive form elements (inputs, textareas, buttons, and navigation controls).
2. THE App SHALL manage keyboard focus correctly: WHEN a Loading_State ends and results are present, THE App SHALL move focus to the first result element; WHEN a Loading_State ends and no results are present (e.g., empty recommendations or an error), THE App SHALL return focus to the submit button.
3. WHEN an Error_State is displayed, THE App SHALL announce the error message to screen readers using an ARIA live region with `aria-live="assertive"` so that the announcement is immediate.
4. THE App SHALL ensure all interactive elements (form inputs, buttons, navigation tabs, retry actions, clear-conversation control) are reachable and operable via keyboard navigation using Tab, Shift+Tab, Enter, and Space keys.
5. THE App SHALL provide visible focus indicators on all interactive elements; focus ring styles SHALL meet WCAG 2.1 Level AA contrast requirements (minimum 3:1 contrast ratio between the focus indicator colour and the adjacent background).

---

### Requirement 6: Performance and User Experience

**User Story:** As a user, I want the application to feel fast and responsive, so that I am not left wondering whether my actions have been registered.

#### Acceptance Criteria

1. THE App SHALL display the Loading_State within 100 ms of the User submitting a form (measured from the submit event to the first visible loading indicator render).
2. THE App SHALL render the initial page shell — defined as the navigation header, panel tabs, and form structure being visible and interactive — within 3 seconds on a standard broadband connection (≥ 10 Mbps download speed).
3. WHEN results are received, THE App SHALL render them without a full page reload (i.e., the browser URL SHALL not change and the page SHALL not flash or blank during result rendering).
4. THE App SHALL preserve form field values across panel switches so that the User does not lose entered data when navigating between the Review_Panel and the Recommend_Panel.
