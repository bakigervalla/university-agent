-- Deterministic seed data. Explicit primary keys keep tests and traces stable.
--
-- Coverage built into this data set:
--   * counts            -> students per offering, courses per teacher
--   * averages          -> AVG(grade_points) per course / per student
--   * grouping          -> GROUP BY teacher, course, semester
--   * filtering         -> by semester, course, teacher, student
--   * joins             -> students <-> enrollments <-> offerings <-> courses/teachers/semesters
--   * NULL handling     -> one enrolled-but-ungraded student (offering 4, Eve)
--   * empty results     -> offering 5 (Databases) has no enrollments

INSERT INTO teachers (id, name, department) VALUES
    (1, 'Ada Lovelace', 'Computer Science'),
    (2, 'Alan Turing',  'Computer Science'),
    (3, 'Grace Hopper', 'Computer Science'),
    (4, 'Carl Gauss',   'Mathematics');

INSERT INTO students (id, name, enrollment_year) VALUES
    (1, 'Alice Smith',   2022),
    (2, 'Bob Jones',     2022),
    (3, 'Carol White',   2023),
    (4, 'Dan Brown',     2023),
    (5, 'Eve Davis',     2024),
    (6, 'Frank Miller',  2024);

INSERT INTO courses (id, code, title, credits) VALUES
    (1, 'CS101',   'Intro to Programming', 3),
    (2, 'CS201',   'Data Structures',      4),
    (3, 'MATH101', 'Calculus I',           4),
    (4, 'CS301',   'Databases',            3);

INSERT INTO semesters (id, term, year, name) VALUES
    (1, 'Fall',   2023, 'Fall 2023'),
    (2, 'Spring', 2024, 'Spring 2024'),
    (3, 'Fall',   2024, 'Fall 2024');

-- course_offerings: (id, course_id, teacher_id, semester_id)
INSERT INTO course_offerings (id, course_id, teacher_id, semester_id) VALUES
    (1, 1, 1, 1),   -- CS101  by Ada Lovelace  in Fall 2023
    (2, 2, 2, 2),   -- CS201  by Alan Turing   in Spring 2024
    (3, 3, 4, 1),   -- MATH101 by Carl Gauss   in Fall 2023
    (4, 1, 3, 3),   -- CS101  by Grace Hopper  in Fall 2024 (same course, new term/teacher)
    (5, 4, 1, 3);   -- CS301  by Ada Lovelace  in Fall 2024 (no enrollments -> empty result demo)

-- enrollments: (id, student_id, offering_id, grade, grade_points)
INSERT INTO enrollments (id, student_id, offering_id, grade, grade_points) VALUES
    (1,  1, 1, 'A',  4.0),
    (2,  2, 1, 'B',  3.0),
    (3,  3, 1, 'A-', 3.7),
    (4,  1, 2, 'B+', 3.3),
    (5,  4, 2, 'C',  2.0),
    (6,  5, 2, 'A',  4.0),
    (7,  2, 3, 'B-', 2.7),
    (8,  3, 3, 'A',  4.0),
    (9,  6, 3, 'F',  0.0),
    (10, 4, 4, 'A',  4.0),
    (11, 5, 4, NULL, NULL),   -- enrolled but not yet graded
    (12, 6, 4, 'B',  3.0);
