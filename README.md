# DataAcademy – Teacher Dashboard

PostgreSQL + Python + Streamlit demo for a simple **education platform**.

It models a small online academy with **students**, **teachers**, **courses**, and **enrollments**, loads ~5k rows of synthetic data into PostgreSQL, and exposes a **teacher-friendly analytics dashboard** built in Streamlit.

This project is designed as a **portfolio piece** to show:

- SQL & database design (PostgreSQL)
- Data generation and loading
- Practical queries for a real-world scenario
- A small but clean dashboard in Streamlit

---

## ✨ Features

- **Relational schema** for:
  - `student`, `teacher`, `course`, `enrollment`
- **Synthetic dataset** (~5,000 rows total) generated with Python + Faker
- **Streamlit dashboard** with 4 tabs:
  1. **Course Overview** – filter by teacher, level, date range; see per-course stats
  2. **Student Search** – search by name/email and view enrollments & grades
  3. **Manage Students** – add a new student and enroll them into courses
  4. **SQL Insights** – run predefined SQL queries and see visualizations
- Uses **SQLAlchemy** for DB access and **Altair** for charts

---

## 🧱 Tech stack

- **PostgreSQL** – database
- **Python 3.10+**
- **SQLAlchemy** – DB layer
- **Streamlit** – web UI
- **Pandas** – data handling
- **Altair** – charts
- **Faker** – synthetic data generation (in optional script)

---

## 📁 Project structure

```text
dataacademy-portfolio/
├── app/
│   └── dashboard.py          # Streamlit app (main entry point)
├── data/
│   ├── teachers.csv
│   ├── students.csv
│   ├── courses.csv
│   └── enrollments.csv
├── scripts/
│   └── generate_data.py      # (optional) script to generate synthetic CSVs
├── sql/
│   ├── schema.sql            # CREATE TABLE statements + constraints
│   └── upload_data.sql       
├── .gitignore
├── requirements.txt
└── README.md
```
#### 🚀 Getting started
**1. Prerequisites**

Python 3.10+

PostgreSQL 14+ installed and running

psql available in your terminal (psql --version should work)

**2. Clone the repo**

```
git clone https://github.com/<your-username>/dataacademy-teacher-dashboard.git
cd dataacademy-teacher-dashboard
```
**3. Create and activate a virtual environment**

```
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```
**4. Install dependencies**

```
pip install -r requirements.txt
```

#### 🗄️ Create the PostgreSQL database
**Step 1 – Create the dataacademy database**

```
psql -U postgres
```

Inside psql:

```
CREATE DATABASE dataacademy;
\q
```

**Step 2 – Apply the schema**

From the project root:

```
psql -U postgres -d dataacademy -f sql/schema.sql
```


This creates the four tables:

- student

- teacher

- course

- enrollment

#### 📥 Load sample data with psql

**1. Connect to the database**

From the project root:

```
psql -U postgres -d dataacademy
```

(Optional) Change directory inside psql so we can use relative paths:

```
\cd '/absolute/path/to/dataacademy-teacher-dashboard'
```

**2. Load the CSV files using \COPY**

```
-- Teachers
\COPY teacher (id, first_name, last_name, email, bio)
FROM 'data/teachers.csv'
WITH (FORMAT csv, HEADER true);

-- Students
\COPY student (id, first_name, last_name, email, registration_date)
FROM 'data/students.csv'
WITH (FORMAT csv, HEADER true);

-- Courses
\COPY course (id, title, description, level, credits, start_date, end_date, teacher_id)
FROM 'data/courses.csv'
WITH (FORMAT csv, HEADER true);

-- Enrollments
\COPY enrollment (id, student_id, course_id, enrollment_date, status, final_grade)
FROM 'data/enrollments.csv'
WITH (FORMAT csv, HEADER true);
```

**3. Fix sequences (so new inserts use the next ID)**

Because the CSVs provide explicit IDs, we move the sequences to the max ID:

```
SELECT setval(pg_get_serial_sequence('teacher',   'id'), (SELECT MAX(id) FROM teacher));
SELECT setval(pg_get_serial_sequence('student',   'id'), (SELECT MAX(id) FROM student));
SELECT setval(pg_get_serial_sequence('course',    'id'), (SELECT MAX(id) FROM course));
SELECT setval(pg_get_serial_sequence('enrollment','id'), (SELECT MAX(id) FROM enrollment));
```

**4. Verify the data**

```
SELECT COUNT(*) FROM teacher;     -- ~40
SELECT COUNT(*) FROM student;     -- ~1500
SELECT COUNT(*) FROM course;      -- ~120
SELECT COUNT(*) FROM enrollment;  -- ~3800
```

If everything looks good: \q to exit psql.

#### ▶️ Run the Streamlit dashboard

Make sure your virtual environment is active and you’re in the project root:

```
streamlit run app/dashboard.py
```

Streamlit will open your browser at something like http://localhost:8501.

## 🧭 Dashboard overview
#### 📚 Course Overview

Filter courses by:

Teacher

Course level (Beginner / Intermediate / Advanced)

Start date range

See per-course stats:

Total enrollments

Active / completed / dropped counts

Top-10 courses visualized as a horizontal bar chart.

#### 🧑‍🎓 Student Search

Search students by first name, last name, full name, or email.

View basic student info.

See all enrollments for a selected student:

Course title

Level

Enrollment date

Status

Final grade

#### ➕ Manage Students

Add a new student (first name, last name, email, registration date).

Optionally enroll them into multiple courses in one step.

Protects against duplicate email addresses (unique constraint on student.email).

Includes a Clear form button to quickly add another student.

#### 🧠 SQL Insights

Choose from predefined example SQL queries, such as:

Students per course

Enrollment status distribution

Active enrollments per level

Courses per teacher

See:

The exact SQL used

A sample of the result (first 10 rows)

A chart visualizing the full result set (Altair)

### 🧩 Extending the project

Ideas for future improvements:

Add authentication (e.g. teacher login).

Track assignments / quizzes and display more detailed performance analytics.

Allow teachers to update student status / grades directly in the UI.

Add Docker support for easy “one-command” startup (db + app).

Deploy the Streamlit app to a public URL (Streamlit Community Cloud, etc.).
