#!/usr/bin/env python3
"""
Generate synthetic data for the Student-Teacher-Course-Enrollment schema.

Outputs CSV files in ./data that you can load into PostgreSQL.
"""

import csv
import os
import random
from datetime import date, timedelta

from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

# ---------- CONFIG ----------
NUM_TEACHERS = 40
NUM_STUDENTS = 1500
NUM_COURSES = 120
MIN_ENROLLMENTS_PER_STUDENT = 1
MAX_ENROLLMENTS_PER_STUDENT = 4

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def random_date_between(start: date, end: date) -> date:
    """Return a random date between start and end (inclusive)."""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_teachers():
    teachers = []
    for i in range(1, NUM_TEACHERS + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@example.edu"
        bio = fake.sentence(nb_words=12)
        teachers.append(
            {
                "id": i,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "bio": bio,
            }
        )
    return teachers


def generate_students():
    students = []
    start_reg = date(2021, 1, 1)
    end_reg = date(2025, 1, 1)

    for i in range(1, NUM_STUDENTS + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@student.example.com"
        registration_date = random_date_between(start_reg, end_reg)
        students.append(
            {
                "id": i,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "registration_date": registration_date.isoformat(),
            }
        )
    return students


def generate_courses(teachers):
    levels = ["Beginner", "Intermediate", "Advanced"]
    titles_samples = [
        "Python for Data Analysis",
        "Introduction to SQL",
        "Web Development with Flask",
        "Machine Learning Basics",
        "Data Visualization with Python",
        "Linux for Developers",
        "Docker & Containers",
        "Cloud Fundamentals",
        "Object-Oriented Programming",
        "Data Engineering Pipelines",
    ]

    courses = []
    # We'll distribute courses over a time range
    overall_start = date(2023, 1, 1)
    overall_end = date(2025, 12, 31)

    for i in range(1, NUM_COURSES + 1):
        teacher = random.choice(teachers)
        level = random.choice(levels)
        base_title = random.choice(titles_samples)
        title = f"{base_title} #{i}"
        description = fake.paragraph(nb_sentences=3)
        credits = random.choice([3, 4, 5])

        # pick random start/end within 3 months range
        start_date = random_date_between(overall_start, overall_end)
        # course lasts 30-90 days
        duration_days = random.randint(30, 90)
        end_date = start_date + timedelta(days=duration_days)

        courses.append(
            {
                "id": i,
                "title": title,
                "description": description,
                "level": level,
                "credits": credits,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "teacher_id": teacher["id"],
            }
        )
    return courses


def choose_status_and_grade(course_start, course_end, enrollment_date):
    """
    Rough logic:
    - If course is fully in the past vs 'today', more likely completed.
    - If course ongoing, more likely active.
    - Some chance of dropped.
    """
    today = date(2025, 1, 15)

    # convert strings to date if needed
    if isinstance(course_start, str):
        course_start = date.fromisoformat(course_start)
    if isinstance(course_end, str):
        course_end = date.fromisoformat(course_end)

    if course_end < today:
        # course finished
        status = random.choices(
            ["completed", "active", "dropped"],
            weights=[0.75, 0.05, 0.20],
            k=1,
        )[0]
    elif course_start > today:
        # course not started yet
        status = random.choices(
            ["active", "completed", "dropped"],
            weights=[0.70, 0.0, 0.30],
            k=1,
        )[0]
    else:
        # ongoing course
        status = random.choices(
            ["active", "completed", "dropped"],
            weights=[0.60, 0.20, 0.20],
            k=1,
        )[0]

    grade = None
    if status == "completed":
        grade = random.choices(
            ["A", "B", "C", "D", "E", "F"],
            weights=[0.25, 0.30, 0.25, 0.10, 0.05, 0.05],
            k=1,
        )[0]

    return status, grade


def generate_enrollments(students, courses):
    enrollments = []
    enrollment_id = 1

    for student in students:
        # each student joins some random courses
        num_enrollments = random.randint(
            MIN_ENROLLMENTS_PER_STUDENT, MAX_ENROLLMENTS_PER_STUDENT
        )
        chosen_courses = random.sample(courses, num_enrollments)

        for course in chosen_courses:
            course_start = date.fromisoformat(course["start_date"])
            course_end = date.fromisoformat(course["end_date"])

            # enrollment occurs from 30 days before course_start up to 20 days after
            enroll_start = course_start - timedelta(days=30)
            enroll_end = min(course_start + timedelta(days=20), course_end)
            enrollment_date = random_date_between(enroll_start, enroll_end)

            status, grade = choose_status_and_grade(
                course_start, course_end, enrollment_date
            )

            enrollments.append(
                {
                    "id": enrollment_id,
                    "student_id": student["id"],
                    "course_id": course["id"],
                    "enrollment_date": enrollment_date.isoformat(),
                    "status": status,
                    "final_grade": grade or "",
                }
            )
            enrollment_id += 1

    return enrollments


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print(f"Writing CSV files into {DATA_DIR}")

    teachers = generate_teachers()
    students = generate_students()
    courses = generate_courses(teachers)
    enrollments = generate_enrollments(students, courses)

    write_csv(
        os.path.join(DATA_DIR, "teachers.csv"),
        teachers,
        ["id", "first_name", "last_name", "email", "bio"],
    )
    write_csv(
        os.path.join(DATA_DIR, "students.csv"),
        students,
        ["id", "first_name", "last_name", "email", "registration_date"],
    )
    write_csv(
        os.path.join(DATA_DIR, "courses.csv"),
        courses,
        [
            "id",
            "title",
            "description",
            "level",
            "credits",
            "start_date",
            "end_date",
            "teacher_id",
        ],
    )
    write_csv(
        os.path.join(DATA_DIR, "enrollments.csv"),
        enrollments,
        [
            "id",
            "student_id",
            "course_id",
            "enrollment_date",
            "status",
            "final_grade",
        ],
    )

    print("Done.")


if __name__ == "__main__":
    main()
