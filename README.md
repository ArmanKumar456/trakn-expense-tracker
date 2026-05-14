# TRAKN — Personal Finance Web App

> **Track · Record · Analyze · Know · Navigate**

A complete self-hosted personal finance management system built with Python Flask and Vanilla JavaScript. Free forever, INR-native, runs in any browser.

---

## ✨ Features

| Module | Description |
|---|---|
| 📊 **Dashboard** | Real-time balance, recent transactions, quick actions, AI chat |
| 💸 **Transactions** | Full CRUD, filters, search, CSV export & import |
| 📈 **Income** | Track income sources with category breakdown |
| 📉 **Expenses** | Category-wise expense tracking with history |
| 🎯 **Budgets** | Monthly limits per category with progress bars and alerts |
| 🔄 **Recurring** | Automated bills, subscriptions, and salary tracking |
| 🏆 **Goals** | Save towards targets with progress rings and deadlines |
| 💼 **Net Worth** | Assets vs liabilities balance sheet |
| 📊 **Analytics** | 20+ charts — heatmap, cash flow, forecasts, AI insights |
| 🧮 **Calculator** | EMI, SIP, compound interest, goal SIP calculators |
| 📰 **News** | Financial news feed |
| 📥 **Import/Export** | CSV with field mapping, validation and error reporting |
| 👤 **Profile** | Avatar, password change, personal settings |
| 🔑 **Admin Panel** | User management, platform stats, feedback inbox |
| 💬 **Feedback** | WhatsApp-style threaded chat between users and admin |
| 🤖 **AI Assistant** | Context-aware financial queries using your data |

---

## 🚀 Installation

### Requirements

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/trakn-expense-tracker.git
   cd trakn-expense-tracker
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **Mac/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   cd backend
   python app.py
   ```

6. **Open your browser:**
   ```
   http://localhost:5000
   ```

7. 

---

## 📁 Folder Structure

```
trakn-expense-tracker/
├── backend/
│   ├── app.py              # Main Flask application — all 50+ API routes
│   ├── config.py           # Database configuration
│   └── database.py         # Database wrapper — all DB operations
│
├── data/                   # Created automatically on first run
│   ├── trakn.db            # SQLite database
│   └── users_data.csv      # User registration tracking
│
├── static/
│   ├── css/
│   │   └── styles.css      # Global stylesheet with CSS variables
│   ├── js/
│   │   └── app.js          # FinFlow namespace — 13 service modules
│   └── images/
│       └── favicon.png     # Application icon
│
├── templates/
│   ├── admin.html          # Admin panel — user management & feedback inbox
│   ├── analytics.html      # Charts & analytics — 20+ visualisations
│   ├── budget.html         # Budget management with progress bars
│   ├── calculator.html     # EMI, SIP, compound interest calculators
│   ├── cookies.html        # Cookie policy page
│   ├── dashboard.html      # Main dashboard — balance, quick actions
│   ├── expense.html        # Add & manage expenses
│   ├── feedback.html       # User feedback & WhatsApp-style support chat
│   ├── goals.html          # Financial goals with progress rings
│   ├── import.html         # CSV import & export
│   ├── income.html         # Add & manage income
│   ├── index.html          # Landing page
│   ├── login.html          # Login & Register
│   ├── networth.html       # Net worth — assets vs liabilities
│   ├── news.html           # Financial news feed
│   ├── privacy.html        # Privacy policy page
│   ├── profile.html        # User profile & settings
│   ├── recurring.html      # Recurring transactions — bills & salary
│   ├── terms.html          # Terms and conditions
│   ├── transactions.html   # Full transaction history & management
│   └── welcome.html        # Welcome / onboarding page
│
├── .env                    # Environment variables (create this)
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

---

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register          Register new user
POST   /api/auth/login             User login
GET    /api/auth/verify            Verify JWT token
POST   /api/auth/logout            Logout and blacklist token
```

### Transactions
```
GET    /api/transactions           Get all transactions (with filters)
POST   /api/transactions           Create transaction
GET    /api/transactions/<id>      Get single transaction
PUT    /api/transactions/<id>      Update transaction
DELETE /api/transactions/<id>      Delete transaction
GET    /api/transactions/summary   Monthly summary stats
GET    /api/transactions/export    Export to CSV
POST   /api/transactions/import    Import from CSV
```

### Budgets
```
GET    /api/budgets                Get all budgets
POST   /api/budgets                Create budget
PUT    /api/budgets/<id>           Update budget
DELETE /api/budgets/<id>           Delete budget
```

### Recurring
```
GET    /api/recurring              Get all recurring items
POST   /api/recurring              Create recurring item
PUT    /api/recurring/<id>         Update recurring item
DELETE /api/recurring/<id>         Delete recurring item
```

### Goals
```
GET    /api/goals                  Get all goals
POST   /api/goals                  Create goal
PUT    /api/goals/<id>             Update goal progress
DELETE /api/goals/<id>             Delete goal
```

### Net Worth
```
GET    /api/assets                 Get all assets
POST   /api/assets                 Add asset
DELETE /api/assets/<id>            Delete asset
GET    /api/liabilities            Get all liabilities
POST   /api/liabilities            Add liability
DELETE /api/liabilities/<id>       Delete liability
```

### Profile
```
GET    /api/profile                Get user profile
PUT    /api/profile                Update profile
POST   /api/profile/avatar         Upload avatar image
DELETE /api/profile/avatar         Remove avatar
PUT    /api/profile/password       Change password
```

### Feedback
```
POST   /api/feedback               Submit feedback
GET    /api/feedback/my            Get own feedback history
GET    /api/feedback/unread-replies  Get replies for notifications
GET    /api/feedback/all           (Admin) Get all feedback
POST   /api/feedback/<id>/reply    (Admin) Reply to feedback
DELETE /api/feedback/<id>          (Admin) Delete feedback
GET    /api/feedback/<id>/messages Get chat messages
POST   /api/feedback/<id>/messages Send chat message
```

### Admin
```
GET    /api/admin/stats            Platform statistics
GET    /api/admin/users            Get all users
POST   /api/admin/users            Create user or admin
PUT    /api/admin/users/<id>       Update user (status/role)
DELETE /api/admin/users/<id>       Delete user
GET    /api/admin/export-users     Export users as CSV
```

### Other
```
GET    /api/dashboard              Dashboard data
GET    /api/notifications          User notifications
POST   /api/ai/chat                AI financial assistant
GET    /api/config/social-links    App social links
GET    /api/config/app-info        App info
```

---

## 🔐 Security Features

- **JWT Authentication** — 30-day tokens, blacklisted on logout
- **Rate Limiting** — Login 10/min, Register 5/min, Feedback 20/hr
- **Input Sanitization** — bleach.clean() on all user text inputs
- **Account Lockout** — 5 failed logins → 15 minute lockout
- **Security Headers** — X-Frame-Options, X-XSS-Protection, CSP
- **Role-Based Access** — User and Admin roles with decorator protection
- **Admin Protection** — Admin accounts cannot be deactivated or deleted
- **Password Hashing** — SHA-256 hash (bcrypt migration planned)

---

## 🎨 Frontend Architecture

All JavaScript is organised under the `FinFlow` global namespace:

```javascript
FinFlow.API            // HTTP requests + auth headers
FinFlow.Auth           // Login, register, logout, JWT
FinFlow.Transactions   // CRUD + export/import
FinFlow.Budgets        // Budget operations
FinFlow.Recurring      // Recurring item management
FinFlow.BalanceSheet   // Assets + liabilities
FinFlow.Goals          // Goals CRUD + progress
FinFlow.Profile        // User profile + avatar
FinFlow.Admin          // User management
FinFlow.Utils          // formatCurrency, formatDate, etc.
FinFlow.Validator      // Form validation
FinFlow.Toast          // Notifications
FinFlow.ThemeManager   // Dark/light mode
```

---

## 🌙 Dark / Light Mode

Toggle available on every page. Preference saved to `localStorage`. Built with CSS custom properties — zero JavaScript layout changes needed.

---

## 📊 Analytics Features

- Monthly Income vs Expense line chart (Daily/Weekly/Monthly/Yearly/All Time/Custom)
- Cash Flow running balance trend
- Expense breakdown donut chart
- Income sources donut chart
- Stacked bar chart by category
- Daily spending heatmap (GitHub-style)
- Weekday vs Weekend spending comparison
- Budget usage progress bars
- Recurring expense summary
- Largest transactions list
- Smart AI financial insights
- Expense forecast based on burn rate
- Financial Health Score (0–100)
- Period comparison (this month vs last month)

---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-very-long-random-secret-key-here
```

---

## 🗄️ Database

Default: **SQLite** — zero configuration, single file, easy backup.

```bash
# Backup your data
cp data/trakn.db data/trakn_backup_$(date +%Y%m%d).db
```

MySQL support is available — update `database.py` connection settings and install `pymysql`.

---

## 🖥️ Technologies

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | SQLite (MySQL supported) |
| Auth | JWT (PyJWT) |
| Frontend | Vanilla HTML5, CSS3, JavaScript ES6+ |
| Charts | Chart.js 4.4.1 |
| Security | bleach, flask-limiter |
| Styling | CSS Custom Properties (variables) |

---

## 📋 Known Limitations

- Goals, Assets, and Liabilities use SQLite — data persists correctly
- JWT stored in `localStorage` — acceptable for self-hosted personal use
- No automated test suite yet — manual testing only
- Single SQLite file not suitable for high-concurrency production deployment

---

## 🗺️ Roadmap

- [ ] Multi-currency support
- [ ] Budget overage email alerts  
- [ ] PWA — installable on home screen
- [ ] Bank statement PDF parser
- [ ] UPI transaction auto-import
- [ ] ITR summary report
- [ ] Mobile app (React Native)
- [ ] Google Sheets export

---

## 📄 License

MIT License — free to use, modify, and self-host.

---

## 💬 Support

- Email: support@trakn.com
- Use the in-app **Feedback** page to report bugs or request features
- Admin can reply directly in the feedback chat interface