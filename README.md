#Budgetify
> Personal finance tracker with spending analysis and insights 
## TECH STACK
  |
LAYER
  |
  |
Technology
  |
  |
-----
  |
-----
  |
  |
Backend
  |
FastAPI
  |
  |
Database
  |
PostgreSQL
  |
  |
ORM
  |
SQLAlchemy
  |
  |
Auth
  |
JWT(access + refresh tokens)
  |
  |
Frontend
  |
Vanilla JS, HTML, CSS
## ⚙️ Local Setup
```bash
git clone https://github.com/pratikshitcodes/budgetify.git
cd budgetify/backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # fill in your values
uvicorn app.main:app --reload
```
## Auth Flow
- Register → `POST /users/`
- Login → `POST /login/` — returns access + refresh token
- Access token expires in 30 mins
- Refresh → `POST /login/refresh_token`
- All expense routes are owner-scoped


## API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| POST | /users/ | Register |
| POST | /login/ | Login |
| POST | /login/refresh_token | Get new access token |
| GET | /expenses/ | Get expenses (paginated) |
| POST | /expenses/ | Add expense |
| PUT | /expenses/{id} | Update expense |
| DELETE | /expenses/{id} | Delete expense |
| GET | /budget-status/ | Current month total |
| POST | /budget-status/ | Full budget analysis |

## Done
- [x] Expense CRUD with JWT auth
- [x] Owner-scoped data (users only see their own data)
- [x] JWT access + refresh token backend
- [x] Paginated expense listing
- [x] Month-over-month spending comparison
- [x] Top category detection
- [x] Budget status engine (Safe / Warning / Danger / Overspent)
- [x] Spending insight generation
- [x] Login page with error handling

## In Progress
- [ ] Registration page
- [ ] Refresh token frontend integration
- [ ] Dashboard connected to real API data
- [ ] Add expense form submission

## Roadmap
- [ ] Alembic migrations
- [ ] Category-wise budgets
- [ ] Smarter AI predictions (spend projection, anomaly detection)
- [ ] Charts and analytics
- [ ] Export to CSV
- [ ] Deployment

Major Architectural Refactor (Day 20)

During development, I realized that my initial backend design had several architectural flaws. Instead of patching the code, I redesigned the API to follow better REST principles and improve scalability.

Problems in the Initial Design
1.Fetched unnecessary data
After login, the application fetched expenses from all months, even though the user only needed data for a single selected month.
This increased database load and wasted bandwidth.

2.No month navigation
The dashboard always displayed the current month.
Users couldn't switch back to previous months or analyze old spending.

3.Budget couldn't be updated
Once a budget was created, there was no dedicated way to modify it.

4.Single endpoint with multiple responsibilities
A single POST /budget-status endpoint was responsible for:
Initializing the monthly budget
Performing budget analytics
Returning dashboard data
This violated the Single Responsibility Principle and made the API difficult to maintain.
Solution

The backend architecture was redesigned by separating responsibilities into dedicated endpoints.

1. GET Budget Analytics

Returns analytics for the selected month and year.

GET /budget-status?month={month}&year={year}

2. POST Budget

Creates a budget only if it doesn't already exist for the selected month.

POST /budget-status

3. PUT Budget

Updates the budget for a specific month and year.

PUT /budget-status?month={month}&year={year}
Month & Year Synchronization

Introduced a global Month-Year selector that synchronizes data across the entire application.

The selected month and year are now consistently applied to:

Dashboard
Expense List
Budget Analytics
Monthly Analysis
Charts
Budget Updates

This allows users to seamlessly analyze any month instead of being restricted to the current one.

Outcome

This refactor resulted in:

Better API design
Clear separation of responsibilities
Reduced unnecessary database queries
Improved scalability
Easier frontend integration
Better user experience through historical month analysis

Day 21

1.Fixed the budget update bug where the user had to click twice to update the budget.

2.Fixed the month synchronization bug, ensuring Analytics and Monthly pages always load the currently selected month's data.

3.Fixed the safe daily spending logic by showing daily spending recommendations only for the current month and remaining budget insights for past months.
## Database Schema
```
users     — id, email, password
expenses  — id, title, amount, category, description, created_at, owner_id
budgets   — id, amount, month, year, user_id
           — UniqueConstraint on (user_id, month, year)
```
