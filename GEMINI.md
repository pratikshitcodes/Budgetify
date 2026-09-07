# Budgetify - Engineering Reference & GEMINI.md

This document serves as the foundational architectural and engineering guide for the **Budgetify** (Expense Tracker) project. Future Gemini CLI sessions must strictly adhere to the standards, patterns, and boundaries outlined here.

---

## 1. Project Purpose
**Budgetify** is a personal finance management application with:
*   **Personal Tracking:** Core expense CRUD, categorized tracking, and monthly budgeting.
*   **Social Group Splitting:** A Splitwise-like shared expense tracker enabling multi-user groups, customized payment splits, and automated balance settlements.
*   **Analytical Reporting:** Visual breakdowns, period-over-period comparisons, downloadabe CSV/PDF statements, and gamified saving metrics ("Savings Battle").
*   **AI Smart Interface:** A natural-language chatbot ("Budgetify AI") driven by LLM tool-calling (via Groq) that directly inspects, logs, updates, and reviews expenses.

---

## 2. System Architecture
The application uses a cleanly decoupled **client-server** architecture.

```
┌───────────────────────────────────────────────────────────┐
│                     FRONTEND (Client)                     │
│               Vanilla HTML / CSS / JavaScript             │
├─────────────────────────────────────┬─────────────────────┤
│   UI Dashboard / Visual Panels      │  Chat & SSE Stream  │
└──────────────────┬──────────────────┴──────────▲──────────┘
                   │ HTTP REST                   │ SSE
                   ▼ (Bearer Token Auth)         │ (Server-Sent Events)
┌────────────────────────────────────────────────┴──────────┐
│                     BACKEND (Server)                      │
│                  FastAPI Web Framework                    │
├──────────────────┬──────────────────┬─────────────────────┤
│   API Routers    │ Services Layer   │   AI Agent (Groq)   │
└──────────────────┼──────────────────┴─────────────────────┘
                   ▼ ORM (SQLAlchemy)
┌───────────────────────────────────────────────────────────┐
│                    DATABASE (Storage)                     │
│                PostgreSQL (via Alembic)                   │
└───────────────────────────────────────────────────────────┘
```

---

## 3. Backend Directory Structure
```
backend/
├── alembic.ini                  # Database migration configuration
├── requirements.txt              # Production and development dependencies
├── alembic/                      # Auto-generated DB migration versions
│   └── versions/                 # Version scripts defining migration steps
└── app/                         # Fast API Application source
    ├── database.py               # Engine connection pooling and get_db session dependency
    ├── main.py                   # App startup, CORS configuration, and router aggregation
    ├── models.py                 # Declarative SQLAlchemy models
    ├── oauth.py                  # JWT authorization, validation, and session extraction
    ├── prompts.py                # AI System prompt setting guidelines for Budgetify AI
    ├── schemas.py                # Pydantic core data-validation schemas
    ├── utils.py                  # Crypto utilities (password hashing) and math helpers
    ├── routers/                  # Network endpoint route mappings
    │   ├── users.py              # User registration endpoint
    │   ├── auth.py               # Credentials checking, token emission, and token renewal
    │   ├── expenses.py           # Personal transactions, aggregates, and monthly budgets
    │   ├── groups.py             # Collaborative user directories and group bill structures
    │   ├── reports.py            # Aggregated report compilation and download triggers
    │   └── ai.py                 # Web interface chat handlers (REST & SSE Stream endpoints)
    └── services/                 # Core business transactions (decoupled from HTTP)
        ├── expense_service.py    # Standard personal transactions logic
        ├── analytics_service.py  # Trend parsing and balance calculations
        ├── group_service.py      # Split allocation matrices and ledger settlement
        └── report_service.py     # High-fidelity PDF & CSV generators
```

---

## 4. Database & SQLAlchemy Models (`app/models.py`)

Tables are created dynamically using SQLAlchemy Declarative models. They map 1:1 with PostgreSQL relational entities:

### `User`
*   `id` (Integer, Primary Key)
*   `email` (String, Unique, Indexed, Nullable=False)
*   `password` (String, Nullable=False) — Contains bcrypt hashed string.

### `Expense`
*   `id` (Integer, Primary Key)
*   `title` (String, Indexed, Nullable=False)
*   `amount` (Numeric(10,2), Nullable=False) — Precision-safe monetary value.
*   `description` (String, Nullable=False)
*   `category` (String, Nullable=False)
*   `created_at` (TIMESTAMP with Timezone, default=text('now()'), Nullable=False)
*   `owner_id` (Integer, ForeignKey("users.id"), Nullable=False)

### `Budget`
*   `id` (Integer, Primary Key)
*   `amount` (Numeric(10,2), Nullable=False)
*   `user_id` (Integer, ForeignKey("users.id"), Nullable=False)
*   `month` (Integer, Nullable=False)
*   `year` (Integer, Nullable=False)
*   *Constraints:* `UniqueConstraint('user_id', 'month', 'year', name='unique_user_month_budget')`

### `Group`
*   `id` (Integer, Primary Key)
*   `name` (String, Nullable=False)
*   `owner_id` (Integer, ForeignKey("users.id"), Nullable=False)
*   `created_at` (TIMESTAMP with Timezone, default=text('now()'), Nullable=False)

### `GroupMember`
*   `id` (Integer, Primary Key)
*   `group_id` (Integer, ForeignKey("groups.id", ondelete="CASCADE"), Nullable=False)
*   `name` (String, Nullable=False) — Can be an ad-hoc member or link to a real user.
*   `user_id` (Integer, ForeignKey("users.id"), Nullable=True) — Links ad-hoc members to active system users.

### `GroupExpense`
*   `id` (Integer, Primary Key)
*   `group_id` (Integer, ForeignKey("groups.id", ondelete="CASCADE"), Nullable=False)
*   `title` (String, Nullable=False)
*   `amount` (Numeric(10,2), Nullable=False)
*   `paid_by_member_id` (Integer, ForeignKey("group_members.id"), Nullable=False)
*   `created_at` (TIMESTAMP with Timezone, default=text('now()'), Nullable=False)

### `GroupExpenseSplit`
*   `id` (Integer, Primary Key)
*   `expense_id` (Integer, ForeignKey("group_expenses.id", ondelete="CASCADE"), Nullable=False)
*   `member_id` (Integer, ForeignKey("group_members.id"), Nullable=False)
*   `share_amount` (Numeric(10,2), Nullable=False)

### Relationship Design Constraint:
*   There are **no explicit SQLAlchemy relationship fields** (e.g., `relationship(...)`) defined inside `models.py`. Joins and relational maps must be executed manually via database sessions inside the Service layer.

---

## 5. API Routers & Responsibilities

| Router Path | Tags | Primary Responsibilities |
| :--- | :--- | :--- |
| `/users` | `Users` | Registers new users, checks for duplicates, hashes passwords. |
| `/login` | `Authentication` | Validates credentials, issues JWT access/refresh tokens, renews access tokens. |
| `/expenses` | `CRUD Operation` | Handles user transactions CRUD. All query patterns automatically scopes by `owner_id`. |
| `/budget-status`| — | Evaluates budget structures, category leaders, and period aggregate comparisons. |
| `/groups` | `Groups` | Creates/manages groups, registers group members, posts split entries, deletes groups. |
| `/reports` | `Reports` | Generates summary structures, compiles and streams PDF/CSV report files. |
| `/chat` | `CHAT-BOT-FUNCTIONS`| Accepts chat inquiries, routes queries to agent execution, streams tokens via SSE. |

---

## 6. Services & Responsibilities

The application encapsulates complex mutations in pure, stateless functions within `app/services/`:

*   **`expense_service`**: Exposes direct database queries for standard individual expenses (`get_expense`, `add_expense`, `delete_expense`, `search_expenses`).
*   **`analytics_service`**: Performs statistical and mathematical aggregation. Calculates monthly summaries, comparisons, and "Month Battles" directly utilizing database sum/count functions.
*   **`group_service`**: Resolves transactional consistency for group dynamics. Calculates split shares, records group member relationships, creates split models, and formats group settlement structures.
*   **`report_service`**: Transforms database analytical models into formatted binary document structures:
    *   `generate_pdf`: Compiles analytical JSON dicts into a high-fidelity PDF byte-stream (using reportlab or system templates).
    *   `generate_csv`: Formats financial summaries into a standard raw CSV string.

---

## 7. Authentication & Authorization Flow

Standardized **OAuth2 Password Bearer Flow** is strictly enforced:

1.  **Login**: Frontend issues a `POST` request with form-encoded payload (`username`, `password`) to `/login/`.
2.  **Token Issuance**: Backend validates credentials, signs a JWT with the user's ID using HS256, and returns:
    ```json
    {
      "access_token": "<jwt_access_token>",
      "refresh_token": "<jwt_refresh_token>",
      "token_type": "bearer"
    }
    ```
3.  **Client Management**: Frontend securely retains tokens in `localStorage` under `token` and `refresh_token`.
4.  **Authorized Requests**: All protected REST endpoint calls must include the authorization header:
    ```http
    Authorization: Bearer <jwt_access_token>
    ```
5.  **Verification Dependency**: Endpoint protection is implemented via the FastAPI dependency injectible `get_current_user`:
    ```python
    CurrentUser = Annotated[schemas.Token, Depends(oauth.get_current_user)]
    ```
6.  **Token Lifecycle**: Access tokens expire in **30 minutes**. Refresh tokens expire in **7 days**. When the client encounters a `401 Unauthorized` state, it POSTs the refresh token to `/login/refresh_token` to retrieve a new short-lived access token.

---

## 8. AI Agent Architecture

The smart chatbot integration operates as a stateful, tool-calling loop:

### Network Interfaces:
*   `/chat/chat`: Accepts structured requests (`message`, `history`) and returns a static JSON payload containing the complete agent reply and any generated report links.
*   `/chat/stream`: An SSE (Server-Sent Events) endpoint that streams text chunks to the chat window in real-time.

### Agent Engine (`app/routers/agents.py`):
*   Uses the `groq` SDK calling the `openai/gpt-oss-120b` (or equivalent) model.
*   Injects rules from `app/prompts.py` (representing the identity "Budgetify AI").
*   Implements a recursive loop (limit of 5 steps) checking for `tool_calls`. When the LLM decides to call a tool, the agent dynamically parses the parameters, executes the mapped service function, appends the tool results back to the thread, and executes a follow-up completion.

### Dynamic Agent Tools:
*   `get_expenses(month, year)`
*   `search_expenses(keyword, month, year)` — *Required check prior to any delete/update operation.*
*   `add_expense(...)` / `update_expense(...)` / `delete_expense(...)`
*   `get_monthly_summary(month, year)` / `compare_months(...)`
*   `generate_monthly_report(month, year)` / `generate_comparison_report(...)`

---

## 9. Frontend Structure & API Interaction

The frontend code utilizes a structural pattern:
*   **Central Dispatcher (`frontend/api.js`)**: Wraps native `fetch` requests. Integrates interceptors to load authorization tokens, manage header settings, resolve API URLs, and trigger fallback workflows on auth failure.
*   **Module-Based Scripting**: HTML views map 1:1 with corresponding Javascript files (e.g., `analytics.html` references `analytics.js`).
*   **Live Streams**: The AI interface in `chat.js` hooks into the SSE streaming endpoint via `EventSource` and directly appends returned character sequences to the active DOM element.

---

## 10. Core Dependencies
*   **`fastapi`**: Web endpoint definition, dependency injection, and automatic OpenAPI generation.
*   **`SQLAlchemy`**: Relational model design, object-relational abstraction, query compilation.
*   **`python-jose[cryptography]`**: Safe payload coding, JWT signatures, and decryption.
*   **`passlib[bcrypt]`**: Safe hash production and user password checking.
*   **`psycopg2-binary`**: High-performance PostgreSQL transport.
*   **`groq`**: Fast inference interaction interface with LLM endpoints.

---

## 11. Engineering Conventions & Constraints

Future work on this codebase must adhere strictly to these constraints:

### A. Data Isolation & Security (Strict Core Mandate)
*   **Isolation Guarantee:** Every data query, write, update, or deletion must be scoped explicitly by `owner_id == current_user.id` or equivalent member-validation structures. Do not rely on client-side routing logic to protect cross-tenant security.
*   **Tool Constraints:** AI Agent tools must fetch, update, and modify parameters exclusively through secure service-layer channels containing authenticated user records.
*   **No Raw SQL:** Always construct database transactions through SQLAlchemy Session interfaces (`db.query`).

### B. Coding Patterns & Architecture
*   **Service Separation:** Controllers/Routers must contain minimal logic. Database mutations, calculations, and integrations must reside inside specialized, stateless services in `app/services/`.
*   **Type Safety:** Annotate all parameters and dependencies cleanly. Leverage Annotated dependency blocks:
    ```python
    DbSession = Annotated[Session, Depends(get_db)]
    CurrentUser = Annotated[schemas.Token, Depends(oauth.get_current_user)]
    ```
*   **Data Validation:** Pydantic models must be used for serialization constraints. Leverage legacy `@validator` annotations for custom numeric positive boundaries or string strip routines as per the existing code style in `app/schemas.py`.
*   **Schema Conversions:** Always use `.model_dump()` rather than legacy `.dict()` when preparing Pydantic models for insert sequences, matching Pydantic v2 conventions.

### C. AI Agent Safeguards
*   The AI agent **must never** execute updates or deletions without searching and confirming the precise ID beforehand.
*   The AI agent **must never** perform complex calculations itself. It must defer to calculated outputs returned by analytic services (`get_monthly_summary`, `compare_months`).
