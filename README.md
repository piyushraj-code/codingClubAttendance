# Enigma - Club Attendance & Daily Quiz Web Application

A full-featured, production-ready attendance management and daily quiz web application for university and college clubs. Built with **Python Django 5**, **MySQL**, and configured for high-availability cloud deployment on **Microsoft Azure** (Azure App Service / Azure Container Apps + Azure Database for MySQL Flexible Server).

---

## 🌟 Key Features

### 1. Student Authentication & Registration
- **Self-Registration**: Students register with **Full Name**, **Semester (1–8)**, **Roll Number (Unique)**, **Branch / Department**, **Email Address (Unique, used as login ID)**, **Password**, and **Mobile Number (Unique)**, with optional Profile Picture and Bio.
- **Login**: Fast, secure sign-in via Email and Password.
- **Dual-Channel OTP Password Reset**:
  - Reset password using **Email OTP** or **Mobile SMS OTP**.
  - Secure 6-digit one-time code with a 10-minute expiry and attempt security.
  - Development preview mode auto-logs OTP for testing without external SMS gateway costs.

### 2. Student Portal & Peer Social Tracking
- **Interactive Dashboard**:
  - Overall attendance percentage with color-coded status (<60% warning, >=75% qualified).
  - Total sessions, Present, Absent, and Late breakdown.
  - Today's Daily Quiz widget with live status and points tracker.
  - Recent activity log and upcoming club sessions.
- **Profile Management**:
  - View personal profile, update profile picture, bio, branch, semester, and mobile.
- **Peer Transparency & Social Following**:
  - Browse and search fellow students in the **Peer Directory** by name, roll number, or branch.
  - **Follow / Unfollow** peer students.
  - Inspect peers' public profiles, view their attendance consistency rate, and check each other's attendance records.
- **Club Leaderboards**:
  - **Top Daily Quiz Champions** ranked by quiz points.
  - **Top Attendance Consistency** ranked by attendance percentage.

### 3. Daily Quiz (Interactive Poll Format)
- **Community Poll Interface**: Daily challenge with questions and 4 poll choices.
- **Instant Result & Explanations**:
  - When students submit their choice, the app immediately displays the live percentage breakdown of all community votes (like a poll).
  - Visually flags whether the student was correct and awards **+10 Club Points**.
  - Displays the **Detailed Explanation** authored by the admin, explaining the underlying concept.
  - Strictly enforces **one attempt per student per quiz**.

### 4. Master Admin Portal
- **Master Admin Login**: Dedicated admin access at `/admin-portal/login/`.
- **Central Command Dashboard**: Real-time stats on registered students, club sessions, today's attendance count, and quiz engagement.
- **Day-Wise Batch Attendance Marking**:
  - Select any Date and Club Activity.
  - Filter students by branch, semester, or search query.
  - **Quick Bulk Action Buttons**: "Mark All Present", "Mark All Absent", "Mark All Late".
  - Individual toggle pills: **Present**, **Absent**, **Late**, **Excused**, with optional remarks.
  - Saves the entire roster with a single click.
- **Daily Quiz Creator & Manager**:
  - Form to set date, title, question prompt, 4 choices, toggle which choice is the correct answer, provide a detailed explanation, and set points.
  - **Quiz Analytics**: View voter breakdown, selected choices, and student timestamps.
- **Club Activities & Events Manager**: Schedule workshops, hackathons, and meetings.
- **Export to CSV**: One-click download of attendance logs for academic reporting.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Backend Framework** | Python 3.12, Django 5.0 |
| **Database** | MySQL (with PyMySQL adapter) / SQLite (zero-config local dev fallback) |
| **Frontend** | Tailwind CSS CDN, FontAwesome 6 Icons, Google Fonts (Inter) |
| **Static Files** | WhiteNoise 6.12 (compressed manifest caching) |
| **WSGI Server** | Gunicorn |
| **Deployment Target** | Microsoft Azure App Service / Azure Container Apps |
| **Containerization** | Docker & Docker Compose |

---

## 🚀 Getting Started Locally

### 1. Clone & Enter Project
```bash
git clone <repo-url>
cd ClubAttendanceLaptop
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (or use the provided `.env.example`):
```ini
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,*
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Database (defaults to SQLite for local development; switch to mysql when ready)
DB_ENGINE=sqlite
DB_NAME=club_attendance_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 4. Apply Migrations & Seed Sample Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 5. Run the Local Server
```bash
python manage.py runserver
```
Visit: `http://127.0.0.1:8000/`

---

## 🔑 Default Seed Accounts

| Role | Email | Password | Details |
|---|---|---|---|
| **Master Admin** | `admin@club.edu` | `Admin@123` | Full administrative control & day-wise attendance marking |
| **Student 1** | `arun.sharma@example.com` | `Student@123` | Roll: `22CSE001`, Branch: `CSE`, Sem: 5 |
| **Student 2** | `priya.verma@example.com` | `Student@123` | Roll: `22CSE002`, Branch: `CSE`, Sem: 5 |
| **Student 3** | `rahul.kumar@example.com` | `Student@123` | Roll: `22IT015`, Branch: `IT`, Sem: 4 |
| **Student 4** | `sneha.patel@example.com` | `Student@123` | Roll: `23AIML008`, Branch: `AIML`, Sem: 3 |
| **Student 5** | `rohan.singh@example.com` | `Student@123` | Roll: `21ECE044`, Branch: `ECE`, Sem: 6 |

---

## 🧪 Running Automated Tests

Run the full Django test suite (accounts, attendance, quizzes, OTP, and batch marking):
```bash
python manage.py test
```
*Result: 9 automated unit & integration tests, all passing.*

---

## ☁️ Azure Cloud Deployment

Full deployment instructions are available in [`deploy/azure-deploy.md`](deploy/azure-deploy.md).

### Quick Summary for Azure:
1. **Azure Database for MySQL Flexible Server**:
   - Create flexible server with firewall rule `0.0.0.0` (Allow Azure Services).
   - Set `DB_ENGINE=mysql`, `DB_HOST=<server>.mysql.database.azure.com`, `DB_NAME=club_attendance_db`.
2. **Azure App Service (Linux / Docker)**:
   - Build container image using the included `Dockerfile` and push to Azure Container Registry (ACR).
   - Set Application Settings (`SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DB_*`).
   - The container automatically runs migrations, WhiteNoise static collection, and starts Gunicorn on port 8000 via [`deploy/startup.sh`](deploy/startup.sh).
