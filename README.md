# University Club Management System (UCMS)

A full-stack Flask + MySQL web application demonstrating **1NF, 2NF, and 3NF** database normalization.

---

## Features
- **Dashboard** – stats, upcoming events, top clubs
- **Clubs** – CRUD with categories, budget, advisor tracking
- **Students** – CRUD with department linkage
- **Events** – CRUD with venue, registration tracking
- **Departments** – manage academic departments
- **Memberships** – assign students to clubs with roles/positions
- **Reports** – visual bar charts for analytics
- **NF Theory page** – interactive explanation of 1NF, 2NF, 3NF with examples

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- MySQL 8.0+
- pip

### Step 1 — Configure MySQL
Edit `config.py` and set your MySQL credentials:

```python
MYSQL_USER     = "root"        # your MySQL username
MYSQL_PASSWORD = "yourpass"    # your MySQL password
MYSQL_HOST     = "localhost"
MYSQL_DB       = "university_club_db"
```

### Step 2 — Create the Database

Open MySQL Workbench or run in terminal:

```bash
mysql -u root -p < schema.sql
```

Or manually:
```sql
SOURCE /path/to/schema.sql;
```

This creates the database, all tables, and inserts seed data automatically.

### Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Run the App

```bash
python app.py
```

Visit: **http://127.0.0.1:5000**

---

## Database Schema (Normalization)

### Tables

| Table | Purpose |
|-------|---------|
| `departments` | Academic departments (1NF – atomic) |
| `students` | Students with FK to departments (3NF – no transitive dep) |
| `clubs` | Clubs with FK to categories (3NF) |
| `club_categories` | Separated from clubs (3NF – removes transitive dep) |
| `advisors` | Faculty advisors |
| `club_advisor_assignments` | M:N bridge — composite PK (2NF) |
| `positions` | Role metadata separated (3NF) |
| `memberships` | Student-club membership — composite candidate key (2NF) |
| `venues` | Venue details separated from events (3NF) |
| `events` | Club events with FK to venues (3NF) |
| `event_registrations` | Event registrations — composite candidate key (2NF) |

### Normal Form Compliance

**1NF** – All attributes are atomic. Multi-valued relationships (student ↔ club, student ↔ event) are represented as separate rows in junction tables.

**2NF** – Composite-keyed tables (`memberships`, `event_registrations`, `club_advisor_assignments`) have no partial dependencies — every non-key attribute depends on the FULL composite key.

**3NF** – No transitive dependencies:
- `student_id → dept_id → dept_name` eliminated by moving dept info to `departments`
- `club_id → category_id → category_name` eliminated by `club_categories`
- `event_id → venue_id → capacity` eliminated by `venues`
- `membership_id → position_id → position_name` eliminated by `positions`

---

## Project Structure

```
university_club_management/
├── app.py               # Flask routes
├── config.py            # DB config
├── schema.sql           # Database schema + seed data
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html
    ├── index.html
    ├── normalization.html
    ├── reports.html
    ├── clubs/
    │   ├── list.html, detail.html, add.html
    ├── members/
    │   ├── list.html, detail.html, add.html, membership.html
    ├── events/
    │   ├── list.html, detail.html, add.html
    └── departments/
        ├── list.html, add.html
```
