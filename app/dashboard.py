#!/usr/bin/env python3
"""
Minimal Teacher Dashboard for the DataAcademy database.

Features:
- Filter courses by teacher, level, date range.
- View course-level stats (student counts, status breakdown).
- Search students by name/email and inspect enrollments.
- Add a new student and enroll them in one or more courses.
- Explore example SQL queries and see visualizations of the results.
"""

import os
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
import altair as alt

# ---------- DB CONNECTION ----------


def get_db_url():
    """
    Build the PostgreSQL connection URL.

    Priority:
    1. Streamlit secrets (for local + Cloud)
    2. Environment variables (fallback)
    """
    # 1) Streamlit secrets
    if "db" in st.secrets:
        db_conf = st.secrets["db"]
        user = db_conf.get("user")
        password = db_conf.get("password")
        host = db_conf.get("host", "localhost")
        port = db_conf.get("port", "5432")
        db   = db_conf.get("name", "dataacademy")
        sslmode = db_conf.get("sslmode", None)
    else:
        # 2) Environment variables
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        db   = os.getenv("DB_NAME", "dataacademy")
        sslmode = os.getenv("DB_SSLMODE", None)

    base_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

    # Append SSL parameters if provided (needed for Neon)
    if sslmode:
        return f"{base_url}?sslmode={sslmode}"
    return base_url


@st.cache_resource
def get_engine():
    """Create and cache a SQLAlchemy engine."""
    engine = create_engine(get_db_url(), echo=False, future=True)
    return engine


def run_query(query, params=None):
    """Helper to run a SELECT and return a DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def run_exec(query, params=None):
    """Helper to run INSERT/UPDATE/DELETE with transaction."""
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        return result


# ---------- EXAMPLE SQL QUERIES (for Insights tab) ----------

EXAMPLE_QUERIES = {
    "Students per course": """
        SELECT
            c.id,
            c.title,
            COUNT(e.student_id) AS student_count
        FROM course c
        LEFT JOIN enrollment e ON e.course_id = c.id
        GROUP BY c.id, c.title
        ORDER BY student_count DESC, c.title;
    """,
    "Enrollment status distribution": """
        SELECT
            e.status,
            COUNT(*) AS enrollment_count
        FROM enrollment e
        GROUP BY e.status
        ORDER BY enrollment_count DESC;
    """,
    "Active enrollments per level": """
        SELECT
            c.level,
            COUNT(*) AS active_enrollments
        FROM enrollment e
        JOIN course c ON c.id = e.course_id
        WHERE e.status = 'active'
        GROUP BY c.level
        ORDER BY active_enrollments DESC;
    """,
    "Courses per teacher": """
        SELECT
            t.id,
            t.first_name || ' ' || t.last_name AS teacher_name,
            COUNT(c.id) AS course_count
        FROM teacher t
        LEFT JOIN course c ON c.teacher_id = t.id
        GROUP BY t.id, teacher_name
        ORDER BY course_count DESC, teacher_name;
    """,
}

QUERY_DESCRIPTIONS = {
    "Students per course": "Counts how many students are enrolled in each course, sorted by the most popular courses.",
    "Enrollment status distribution": "Shows how many enrollments are active, completed, or dropped across the whole academy.",
    "Active enrollments per level": "Shows how many active enrollments exist for each course level (Beginner/Intermediate/Advanced).",
    "Courses per teacher": "Shows each teacher and how many courses they are currently responsible for.",
}

# ---------- HELPERS FOR MANAGE-STUDENTS FORM ----------


def clear_new_student_form():
    """Callback to clear the new-student form fields."""
    st.session_state["first_name_input"] = ""
    st.session_state["last_name_input"] = ""
    st.session_state["email_input"] = ""
    st.session_state["reg_date_input"] = date.today()
    st.session_state["courses_input"] = []


# ---------- UI LAYOUT ----------

st.set_page_config(
    page_title="DataAcademy Teacher Dashboard",
    layout="wide",
)

st.title("📊 DataAcademy – Teacher Dashboard")

tab_overview, tab_student, tab_manage, tab_insights = st.tabs(
    [
        "📚 Course Overview",
        "🧑‍🎓 Student Search",
        "➕ Manage Students",
        "🧠 SQL Insights",
    ]
)

# Preload lookup data used in multiple places
teachers_df = run_query(
    "SELECT id, first_name || ' ' || last_name AS name FROM teacher ORDER BY name;"
)
courses_df = run_query(
    "SELECT id, title, level, start_date, end_date, teacher_id FROM course;"
)


# ---------- TAB 1: COURSE OVERVIEW ----------
with tab_overview:
    st.subheader("Course Overview & Stats")

    # Sidebar-like filters in a container
    with st.expander("Filters", expanded=True):
        # Teacher filter
        teacher_options = ["All"] + teachers_df["name"].tolist()
        teacher_choice = st.selectbox("Teacher", teacher_options)

        # Level filter
        levels = ["Beginner", "Intermediate", "Advanced"]
        level_filter = st.multiselect("Course level", levels, default=levels)

        # Date range filter (based on course start_date)
        min_date = pd.to_datetime(courses_df["start_date"]).min().date()
        max_date = pd.to_datetime(courses_df["start_date"]).max().date()
        start_filter, end_filter = st.date_input(
            "Course start date range",
            (min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    # Build WHERE clause dynamically
    filters = []
    params = {}

    if teacher_choice != "All":
        teacher_id = int(
            teachers_df.loc[teachers_df["name"] == teacher_choice, "id"].iloc[0]
        )
        filters.append("c.teacher_id = :teacher_id")
        params["teacher_id"] = teacher_id

    if level_filter:
        filters.append("c.level = ANY(:levels)")
        params["levels"] = level_filter

    if start_filter:
        filters.append("c.start_date >= :start_date")
        params["start_date"] = start_filter
    if end_filter:
        filters.append("c.start_date <= :end_date")
        params["end_date"] = end_filter

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query_courses_stats = f"""
        SELECT
            c.id,
            c.title,
            c.level,
            c.start_date,
            c.end_date,
            t.first_name || ' ' || t.last_name AS teacher_name,
            COUNT(e.id) AS total_enrollments,
            SUM(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END)     AS active_count,
            SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END)  AS completed_count,
            SUM(CASE WHEN e.status = 'dropped' THEN 1 ELSE 0 END)    AS dropped_count
        FROM course c
        JOIN teacher t ON t.id = c.teacher_id
        LEFT JOIN enrollment e ON e.course_id = c.id
        {where_clause}
        GROUP BY c.id, c.title, c.level, c.start_date, c.end_date, teacher_name
        ORDER BY c.start_date;
    """

    course_stats_df = run_query(query_courses_stats, params)

    st.write("### Course Stats")
    st.dataframe(course_stats_df, use_container_width=True)

    # Optional chart: total enrollments per course (top 10, horizontal)
    if not course_stats_df.empty:
        st.write("### Top courses by enrollments")

        # Take top 10 courses by total_enrollments
        chart_df = (
            course_stats_df.sort_values("total_enrollments", ascending=False)
            .head(10)
            .copy()
        )

        # Horizontal bar chart with readable labels + tooltips
        bar_height = 35  # pixels per bar
        chart_height = max(200, bar_height * len(chart_df))

        chart = (
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X("total_enrollments:Q", title="Total enrollments"),
                y=alt.Y("title:N", sort="-x", title="Course"),
                tooltip=[
                    alt.Tooltip("title:N", title="Course"),
                    alt.Tooltip("level:N", title="Level"),
                    alt.Tooltip("teacher_name:N", title="Teacher"),
                    alt.Tooltip("total_enrollments:Q", title="Total"),
                    alt.Tooltip("active_count:Q", title="Active"),
                    alt.Tooltip("completed_count:Q", title="Completed"),
                    alt.Tooltip("dropped_count:Q", title="Dropped"),
                ],
            )
            .properties(
                height=chart_height,
                width="container",
            )
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No courses match the selected filters.")


# ---------- TAB 2: STUDENT SEARCH ----------
with tab_student:
    st.subheader("Search Students & View Enrollments")

    st.caption(
        "Tip: you can search by first name, last name, full name (e.g. 'Amanda Gill') or email."
    )

    # Show a few example students to play with
    sample_students = run_query(
        """
        SELECT id, first_name, last_name, email, registration_date
        FROM student
        ORDER BY id
        LIMIT 10;
    """
    )

    with st.expander("Show 10 example students you can search for", expanded=False):
        if sample_students.empty:
            st.write("No students found (did you load the CSVs?).")
        else:
            st.dataframe(
                sample_students[["id", "first_name", "last_name", "email"]],
                use_container_width=True,
            )

    search_term = st.text_input(
        "Search by name or email (partial match)",
        placeholder="e.g. Amanda, Gill, Amanda Gill, amanda.gill4@student.example.com",
    )

    if search_term:
        query_students = """
            SELECT
                id,
                first_name,
                last_name,
                email,
                registration_date
            FROM student
            WHERE first_name ILIKE '%' || :term || '%'
               OR last_name  ILIKE '%' || :term || '%'
               OR email      ILIKE '%' || :term || '%'
               -- full name match: 'Amanda Gill'
               OR (first_name || ' ' || last_name) ILIKE '%' || :term || '%'
            ORDER BY last_name, first_name
            LIMIT 50;
        """
        students_found = run_query(query_students, {"term": search_term})

        st.write(f"Found {len(students_found)} student(s).")
        st.dataframe(students_found, use_container_width=True)

        if not students_found.empty:
            # If exactly one student found, use them directly
            if len(students_found) == 1:
                selected_id = int(students_found.iloc[0]["id"])
                selected_label = (
                    f"{students_found.iloc[0]['first_name']} "
                    f"{students_found.iloc[0]['last_name']} "
                )
                st.caption(f"Showing enrollments for: {selected_label}")
            else:
                # If multiple results, let the user choose
                selected_id = st.selectbox(
                    "Select a student to view their enrollments",
                    students_found["id"].tolist(),
                    format_func=lambda sid: students_found.loc[
                        students_found["id"] == sid,
                        ["first_name", "last_name", "email"],
                    ]
                    .agg(" ".join, axis=1)
                    .iloc[0],
                )

            if selected_id:
                enrollments_query = """
                    SELECT
                        c.title AS course_title,
                        c.level,
                        e.enrollment_date,
                        e.status,
                        e.final_grade
                    FROM enrollment e
                    JOIN course c ON c.id = e.course_id
                    WHERE e.student_id = :sid
                    ORDER BY e.enrollment_date DESC;
                """
                enroll_df = run_query(enrollments_query, {"sid": int(selected_id)})

                st.write("### Enrollments")
                st.dataframe(enroll_df, use_container_width=True)


# ---------- TAB 3: MANAGE STUDENTS ----------
with tab_manage:
    st.subheader("Add New Student & Enroll Them")
# Set default date only via session_state (not via value=)

    if "reg_date_input" not in st.session_state:
        st.session_state["reg_date_input"] = date.today()

    with st.form("add_student_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input(
                "First name",
                key="first_name_input",
            )
            registration_date = st.date_input(
                "Registration date",
                key="reg_date_input",
            )
        with col2:
            last_name = st.text_input(
                "Last name",
                key="last_name_input",
            )
            email = st.text_input(
                "Email",
                key="email_input",
            )

        st.write("Enroll in courses (optional):")
        # Multi-select from all courses
        course_options = {
            f"{row['title']} (#{row['id']})": int(row["id"])
            for _, row in courses_df.iterrows()
        }
        selected_courses_labels = st.multiselect(
            "Select course(s)",
            list(course_options.keys()),
            key="courses_input",
        )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            submitted = st.form_submit_button("Create student and enroll")
        with btn_col2:
            # This button will call the callback, which is allowed to modify
            # the widget keys in st.session_state.
            st.form_submit_button("Clear form", on_click=clear_new_student_form)

    # Handle Create student
    if submitted:
        if not first_name or not last_name or not email:
            st.error("First name, last name and email are required.")
        else:
            try:
                # Insert student and get new id
                result = run_exec(
                    """
                    INSERT INTO student (first_name, last_name, email, registration_date)
                    VALUES (:fn, :ln, :em, :reg_date)
                    RETURNING id;
                    """,
                    {
                        "fn": first_name,
                        "ln": last_name,
                        "em": email,
                        "reg_date": registration_date,
                    },
                )
                new_student_id = result.scalar_one()

                # Enroll in selected courses
                for label in selected_courses_labels:
                    course_id = course_options[label]
                    run_exec(
                        """
                        INSERT INTO enrollment (student_id, course_id, enrollment_date, status)
                        VALUES (:sid, :cid, CURRENT_DATE, 'active');
                        """,
                        {"sid": new_student_id, "cid": course_id},
                    )

                st.success(
                    f"Student created with ID {new_student_id}. "
                    f"Enrollments created for {len(selected_courses_labels)} course(s)."
                )
            except Exception as e:
                msg = str(e)
                if "duplicate key value violates unique constraint" in msg and (
                    "student_email_key" in msg or "email" in msg
                ):
                    st.error(
                        "A student with this email already exists. "
                        "Each student must have a unique email address."
                    )
                else:
                    st.error(f"Error while saving to database: {e}")


# ---------- TAB 4: SQL INSIGHTS ----------
with tab_insights:
    st.subheader("SQL Insights – Examples + Visualizations")
    st.caption(
        "Pick an example SQL query, see the raw SQL, a sample of the result, "
        "and a chart based on the full result set."
    )

    # Let user choose which predefined query to explore
    query_name = st.selectbox("Choose an example query", list(EXAMPLE_QUERIES.keys()))

    sql_text = EXAMPLE_QUERIES[query_name]
    st.write("#### SQL")
    st.code(sql_text.strip(), language="sql")

    # Short explanation of what the query does
    st.caption(QUERY_DESCRIPTIONS.get(query_name, ""))

    # Run the selected query
    df = run_query(sql_text)

    if df.empty:
        st.warning("This query returned no rows for the current data.")
    else:
        st.write(f"#### Result sample (showing first 10 of {len(df)} rows)")
        st.dataframe(df.head(10), use_container_width=True)

        st.write("#### Visualization")

        # Different chart depending on which query is selected
        if query_name == "Students per course":
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("student_count:Q", title="Number of students"),
                    y=alt.Y("title:N", sort="-x", title="Course"),
                    tooltip=[
                        alt.Tooltip("title:N", title="Course"),
                        alt.Tooltip("student_count:Q", title="Students"),
                    ],
                )
                .properties(
                    height=max(200, 30 * len(df)),
                    width="container",
                )
            )
            st.altair_chart(chart, use_container_width=True)

        elif query_name == "Enrollment status distribution":
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("status:N", title="Status"),
                    y=alt.Y("enrollment_count:Q", title="Enrollments"),
                    tooltip=[
                        alt.Tooltip("status:N", title="Status"),
                        alt.Tooltip("enrollment_count:Q", title="Count"),
                    ],
                )
                .properties(height=300, width="container")
            )
            st.altair_chart(chart, use_container_width=True)

        elif query_name == "Active enrollments per level":
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("level:N", title="Course level"),
                    y=alt.Y("active_enrollments:Q", title="Active enrollments"),
                    tooltip=[
                        alt.Tooltip("level:N", title="Level"),
                        alt.Tooltip("active_enrollments:Q", title="Active enrollments"),
                    ],
                )
                .properties(height=300, width="container")
            )
            st.altair_chart(chart, use_container_width=True)

        elif query_name == "Courses per teacher":
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "course_count:Q",
                        title="Number of courses",
                        axis=alt.Axis(tickMinStep=1, format="d"),  # integer ticks
                    ),
                    y=alt.Y("teacher_name:N", sort="-x", title="Teacher"),
                    tooltip=[
                        alt.Tooltip("teacher_name:N", title="Teacher"),
                        alt.Tooltip("course_count:Q", title="Courses"),
                    ],
                )
                .properties(
                    height=max(200, 25 * len(df)),
                    width="container",
                )
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info(
                "No visualization configured for this query yet – feel free to add one!"
            )
