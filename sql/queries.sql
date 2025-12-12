CREATE DATABASE dataacademy;


-- 1 Number of students per course

SELECT
    c.id,
    c.title,
    COUNT(e.id) AS student_count
FROM course c
LEFT JOIN enrollment e ON e.course_id = c.id
GROUP BY c.id, c.title
ORDER BY student_count DESC;

-- 2 List of students in a given course (by course_id)

SELECT
    s.id,
    s.first_name,
    s.last_name,
    s.email,
    e.status,
    e.final_grade
FROM enrollment e
JOIN student s ON s.id = e.student_id
WHERE e.course_id = 42
ORDER BY s.last_name, s.first_name;

-- 3 Same, but by course title (partial match)

SELECT
    c.title,
    s.first_name,
    s.last_name,
    e.status,
    e.final_grade
FROM course c
JOIN enrollment e ON e.course_id = c.id
JOIN student s ON s.id = e.student_id
WHERE c.title ILIKE '%python%'
ORDER BY c.title, s.last_name;

-- 4 Courses and enrollments for a given student (by email)

SELECT
    s.first_name,
    s.last_name,
    s.email,
    c.title AS course_title,
    c.level,
    e.enrollment_date,
    e.status,
    e.final_grade
FROM student s
JOIN enrollment e ON e.student_id = s.id
JOIN course c     ON c.id = e.course_id
WHERE s.email = 'alice.student23@student.example.com'
ORDER BY e.enrollment_date DESC;

-- 5 Count active vs completed vs dropped per course

SELECT
    c.id,
    c.title,
    e.status,
    COUNT(*) AS count_status
FROM course c
JOIN enrollment e ON e.course_id = c.id
GROUP BY c.id, c.title, e.status
ORDER BY c.title, e.status;

-- 6 Overall status distribution for one teacher

SELECT
    t.id AS teacher_id,
    t.first_name || ' ' || t.last_name AS teacher_name,
    e.status,
    COUNT(*) AS count_status
FROM teacher t
JOIN course c     ON c.teacher_id = t.id
JOIN enrollment e ON e.course_id = c.id
WHERE t.id = 5
GROUP BY t.id, teacher_name, e.status
ORDER BY e.status;

-- 7 Upcoming courses by level (start_date in future)

SELECT
    c.id,
    c.title,
    c.level,
    c.start_date,
    c.end_date,
    t.first_name || ' ' || t.last_name AS teacher_name
FROM course c
JOIN teacher t ON t.id = c.teacher_id
WHERE c.start_date > CURRENT_DATE
ORDER BY c.start_date;

-- 8 Ongoing courses today

SELECT
    c.id,
    c.title,
    c.level,
    c.start_date,
    c.end_date,
    COUNT(e.id) AS enrolled_students
FROM course c
LEFT JOIN enrollment e ON e.course_id = c.id
WHERE c.start_date <= CURRENT_DATE
  AND c.end_date   >= CURRENT_DATE
GROUP BY c.id, c.title, c.level, c.start_date, c.end_date
ORDER BY c.start_date;

-- 9 Top 10 courses by completed enrollments

SELECT
    c.id,
    c.title,
    COUNT(*) AS completed_count
FROM course c
JOIN enrollment e ON e.course_id = c.id
WHERE e.status = 'completed'
GROUP BY c.id, c.title
ORDER BY completed_count DESC
LIMIT 10;

-- 10 Average grade per course (simple A–F mapping)

-- Map letter grade -> numeric points
WITH grades AS (
    SELECT
        e.course_id,
        CASE e.final_grade
            WHEN 'A' THEN 5
            WHEN 'B' THEN 4
            WHEN 'C' THEN 3
            WHEN 'D' THEN 2
            WHEN 'E' THEN 1
            WHEN 'F' THEN 0
        END AS grade_points
    FROM enrollment e
    WHERE e.final_grade IS NOT NULL
)
SELECT
    c.id,
    c.title,
    ROUND(AVG(g.grade_points)::numeric, 2) AS avg_grade_points
FROM course c
JOIN grades g ON g.course_id = c.id
GROUP BY c.id, c.title
ORDER BY avg_grade_points DESC;
