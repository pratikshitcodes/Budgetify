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

## Database Schema
```
users     — id, email, password
expenses  — id, title, amount, category, description, created_at, owner_id
budgets   — id, amount, month, year, user_id
           — UniqueConstraint on (user_id, month, year)
```
