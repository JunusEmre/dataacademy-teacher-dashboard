-- Drop tables in dependency order if you rerun
DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS teacher;

-- STUDENT
CREATE TABLE student (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name        VARCHAR(50)  NOT NULL,
    last_name         VARCHAR(50)  NOT NULL,
    email             VARCHAR(100) NOT NULL UNIQUE,
    registration_date DATE         NOT NULL,
    -- simple sanity check: registration not before year 2000
    CONSTRAINT chk_student_registration_date
        CHECK (registration_date >= DATE '2000-01-01')
);

-- TEACHER
CREATE TABLE teacher (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name VARCHAR(50)  NOT NULL,
    last_name  VARCHAR(50)  NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    bio        TEXT
);

-- COURSE
CREATE TABLE course (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title       VARCHAR(100) NOT NULL,
    description TEXT,
    level       VARCHAR(20)  NOT NULL,
    credits     INTEGER      NOT NULL DEFAULT 3,
    start_date  DATE,
    end_date    DATE,
    teacher_id  INTEGER      NOT NULL,
    CONSTRAINT fk_course_teacher
        FOREIGN KEY (teacher_id) REFERENCES teacher(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_course_level
        CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
    CONSTRAINT chk_course_dates
        CHECK (
            start_date IS NULL
            OR end_date IS NULL
            OR end_date >= start_date
        ),
    CONSTRAINT chk_course_credits
        CHECK (credits > 0)
);

-- Useful index for lookups by teacher
CREATE INDEX idx_course_teacher_id ON course(teacher_id);

-- ENROLLMENT
CREATE TABLE enrollment (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id      INTEGER NOT NULL,
    course_id       INTEGER NOT NULL,
    enrollment_date DATE    NOT NULL,
    status          VARCHAR(20) NOT NULL,
    final_grade     VARCHAR(5),
    CONSTRAINT fk_enrollment_student
        FOREIGN KEY (student_id) REFERENCES student(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_enrollment_course
        FOREIGN KEY (course_id)  REFERENCES course(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_enrollment_status
        CHECK (status IN ('active', 'completed', 'dropped')),
    CONSTRAINT chk_enrollment_grade
        CHECK (
            final_grade IS NULL
            OR final_grade IN ('A','B','C','D','E','F')
        )
);

-- Useful indexes
CREATE INDEX idx_enrollment_student_id ON enrollment(student_id);
CREATE INDEX idx_enrollment_course_id  ON enrollment(course_id);
CREATE INDEX idx_enrollment_status     ON enrollment(status);
