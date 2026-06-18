-- University schema for the LangGraph QA agent.
--
-- Design notes:
--   * Names are NOT NULL (every student and teacher has a name).
--   * A course is taught by a teacher in a specific semester via course_offerings.
--   * Students enroll in offerings (not raw courses), so the same course in two
--     semesters is two distinct enrollable offerings.
--   * Grades are represented as a letter plus numeric grade_points so that both
--     human-readable filtering ("students with a B") and aggregation (AVG GPA)
--     work cleanly. A NULL grade means "enrolled but not yet graded".
--
-- Standard ANSI SQL kept dialect-neutral where practical. Foreign keys must be
-- enabled by the adapter (SQLite enforces them only when PRAGMA is set).

CREATE TABLE teachers (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    department  TEXT
);

CREATE TABLE students (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    enrollment_year  INTEGER
);

CREATE TABLE courses (
    id       INTEGER PRIMARY KEY,
    code     TEXT NOT NULL UNIQUE,
    title    TEXT NOT NULL,
    credits  INTEGER NOT NULL DEFAULT 3
);

CREATE TABLE semesters (
    id     INTEGER PRIMARY KEY,
    term   TEXT NOT NULL,          -- e.g. 'Fall', 'Spring'
    year   INTEGER NOT NULL,
    name   TEXT NOT NULL,          -- denormalized label, e.g. 'Fall 2023'
    UNIQUE (term, year)
);

-- A specific delivery of a course by one teacher in one semester.
CREATE TABLE course_offerings (
    id           INTEGER PRIMARY KEY,
    course_id    INTEGER NOT NULL REFERENCES courses(id),
    teacher_id   INTEGER NOT NULL REFERENCES teachers(id),
    semester_id  INTEGER NOT NULL REFERENCES semesters(id),
    UNIQUE (course_id, teacher_id, semester_id)
);

-- A student's enrollment in one offering, with an optional grade.
CREATE TABLE enrollments (
    id            INTEGER PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students(id),
    offering_id   INTEGER NOT NULL REFERENCES course_offerings(id),
    grade         TEXT,            -- letter grade, NULL until graded
    grade_points  REAL,            -- 0.0-4.0 scale, NULL until graded
    UNIQUE (student_id, offering_id),
    CHECK (
        (grade IS NULL AND grade_points IS NULL)
        OR (grade IS NOT NULL AND grade_points IS NOT NULL)
    ),
    CHECK (grade_points IS NULL OR (grade_points >= 0.0 AND grade_points <= 4.0))
);

CREATE INDEX idx_offerings_course   ON course_offerings(course_id);
CREATE INDEX idx_offerings_teacher  ON course_offerings(teacher_id);
CREATE INDEX idx_offerings_semester ON course_offerings(semester_id);
CREATE INDEX idx_enrollments_student  ON enrollments(student_id);
CREATE INDEX idx_enrollments_offering ON enrollments(offering_id);
