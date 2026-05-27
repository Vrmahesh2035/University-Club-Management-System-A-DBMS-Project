-- ============================================================
--  University Club Management System — schema.sql
--  Demonstrates 1NF, 2NF, and 3NF normalization
-- ============================================================

CREATE DATABASE IF NOT EXISTS university_club_db;
USE university_club_db;

-- ============================================================
-- 1NF: All attributes are atomic (no repeating groups,
--      no multi-valued attributes).  Every table has a PK.
-- ============================================================

-- DEPARTMENTS
-- dept_code is a simple atomic attribute (no list of codes).
-- faculty_dean is kept here because it depends only on dept_id
-- (not on any student or club).
CREATE TABLE IF NOT EXISTS departments (
    dept_id      INT AUTO_INCREMENT PRIMARY KEY,
    dept_name    VARCHAR(100) NOT NULL UNIQUE,
    dept_code    VARCHAR(10)  NOT NULL UNIQUE,
    faculty_dean VARCHAR(100) NOT NULL
);

-- ============================================================
-- 3NF: phone → student, email → student (no transitive deps).
-- The student's department info lives in `departments`,
-- not repeated here — removing the transitive dependency
--   student_id → dept_id → dept_name / dept_code
-- ============================================================

-- STUDENTS
CREATE TABLE IF NOT EXISTS students (
    student_id      INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,   -- 1NF: atomic
    phone           VARCHAR(15)  UNIQUE,             -- 1NF: one phone per row
    dept_id         INT          NOT NULL,
    enrollment_year YEAR         NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE RESTRICT
);

-- CLUB CATEGORIES  (3NF — separates category metadata from clubs)
CREATE TABLE IF NOT EXISTS club_categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description   TEXT
);

-- CLUBS
-- budget and room_number depend ONLY on club_id (no transitive dep).
CREATE TABLE IF NOT EXISTS clubs (
    club_id       INT AUTO_INCREMENT PRIMARY KEY,
    club_name     VARCHAR(100) NOT NULL UNIQUE,
    category_id   INT          NOT NULL,
    description   TEXT,
    founded_year  YEAR         NOT NULL,
    room_number   VARCHAR(20),
    budget        DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (category_id) REFERENCES club_categories(category_id) ON DELETE RESTRICT
);

-- ADVISORS  (3NF — advisor info is NOT mixed into clubs/memberships)
-- An advisor's department depends on the advisor, not on any club.
CREATE TABLE IF NOT EXISTS advisors (
    advisor_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50)  NOT NULL,
    last_name  VARCHAR(50)  NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    dept_id    INT          NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE RESTRICT
);

-- CLUB–ADVISOR ASSIGNMENT  (resolves many-to-many)
-- 2NF: the only non-key attribute (assigned_date) depends on
--      the FULL composite key (club_id, advisor_id).
CREATE TABLE IF NOT EXISTS club_advisor_assignments (
    club_id       INT  NOT NULL,
    advisor_id    INT  NOT NULL,
    assigned_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (club_id, advisor_id),
    FOREIGN KEY (club_id)    REFERENCES clubs(club_id)     ON DELETE CASCADE,
    FOREIGN KEY (advisor_id) REFERENCES advisors(advisor_id) ON DELETE CASCADE
);

-- POSITIONS  (3NF — role metadata separated; avoids repeating
--             role descriptions across every membership row)
CREATE TABLE IF NOT EXISTS positions (
    position_id   INT AUTO_INCREMENT PRIMARY KEY,
    position_name VARCHAR(50) NOT NULL UNIQUE,
    description   TEXT
);

-- MEMBERSHIPS  (composite PK: student_id + club_id)
-- 2NF: every non-key column (position_id, join_date, status)
--      depends on BOTH student_id AND club_id, not just one.
-- 3NF: role details live in `positions`, not repeated here.
CREATE TABLE IF NOT EXISTS memberships (
    membership_id INT  AUTO_INCREMENT PRIMARY KEY,
    student_id    INT  NOT NULL,
    club_id       INT  NOT NULL,
    position_id   INT  NOT NULL,
    join_date     DATE NOT NULL DEFAULT (CURRENT_DATE),
    status        ENUM('active','inactive','suspended') NOT NULL DEFAULT 'active',
    UNIQUE KEY uq_student_club (student_id, club_id),   -- 2NF composite candidate key
    FOREIGN KEY (student_id)  REFERENCES students(student_id)  ON DELETE CASCADE,
    FOREIGN KEY (club_id)     REFERENCES clubs(club_id)        ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(position_id) ON DELETE RESTRICT
);

-- VENUES  (3NF — venue capacity/location separated from events)
CREATE TABLE IF NOT EXISTS venues (
    venue_id  INT AUTO_INCREMENT PRIMARY KEY,
    venue_name VARCHAR(100) NOT NULL UNIQUE,
    capacity   INT          NOT NULL,
    location   VARCHAR(150)
);

-- EVENTS
-- 3NF: venue details (capacity, location) are NOT in this table;
--      they live in `venues` to avoid transitive dependency
--        event_id → venue_id → capacity / location
CREATE TABLE IF NOT EXISTS events (
    event_id         INT AUTO_INCREMENT PRIMARY KEY,
    event_name       VARCHAR(150) NOT NULL,
    event_date       DATE         NOT NULL,
    event_time       TIME         NOT NULL,
    club_id          INT          NOT NULL,
    venue_id         INT          NOT NULL,
    description      TEXT,
    max_participants INT          NOT NULL DEFAULT 50,
    status           ENUM('upcoming','ongoing','completed','cancelled') NOT NULL DEFAULT 'upcoming',
    FOREIGN KEY (club_id)  REFERENCES clubs(club_id)   ON DELETE CASCADE,
    FOREIGN KEY (venue_id) REFERENCES venues(venue_id) ON DELETE RESTRICT
);

-- EVENT REGISTRATIONS  (composite PK: event_id + student_id)
-- 2NF: registration_date and attendance_status depend on the
--      FULL composite key, not just event_id or student_id alone.
CREATE TABLE IF NOT EXISTS event_registrations (
    registration_id   INT AUTO_INCREMENT PRIMARY KEY,
    event_id          INT  NOT NULL,
    student_id        INT  NOT NULL,
    registration_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    attendance_status ENUM('registered','attended','absent') NOT NULL DEFAULT 'registered',
    UNIQUE KEY uq_event_student (event_id, student_id),   -- 2NF composite candidate key
    FOREIGN KEY (event_id)   REFERENCES events(event_id)     ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- ============================================================
--  SEED DATA
-- ============================================================

INSERT IGNORE INTO departments (dept_name, dept_code, faculty_dean) VALUES
('Computer Science',        'CS',   'Dr. Ramesh Kumar'),
('Electronics Engineering', 'ECE',  'Dr. Priya Nair'),
('Mechanical Engineering',  'ME',   'Dr. Suresh Rao'),
('Business Administration', 'MBA',  'Dr. Anita Sharma'),
('Arts & Humanities',       'AH',   'Dr. Vijay Menon');

INSERT IGNORE INTO club_categories (category_name, description) VALUES
('Technical',   'Coding, robotics, and engineering clubs'),
('Cultural',    'Arts, music, dance, and drama clubs'),
('Sports',      'Athletic and recreational clubs'),
('Social',      'Community service and social welfare clubs'),
('Academic',    'Subject-specific study and research clubs');

INSERT IGNORE INTO positions (position_name, description) VALUES
('President',       'Overall leadership and representation of the club'),
('Vice President',  'Assists president and manages internal affairs'),
('Secretary',       'Handles communication and meeting minutes'),
('Treasurer',       'Manages club finances and budget'),
('Event Manager',   'Organizes and coordinates club events'),
('Member',          'General club member');

INSERT IGNORE INTO venues (venue_name, capacity, location) VALUES
('Main Auditorium',     500, 'Block A, Ground Floor'),
('Seminar Hall 1',      100, 'Block B, First Floor'),
('Seminar Hall 2',      100, 'Block B, Second Floor'),
('Open Air Theatre',    300, 'Central Campus'),
('Computer Lab 1',       40, 'Block C, Ground Floor'),
('Sports Complex',     1000, 'North Campus');

INSERT IGNORE INTO students (first_name, last_name, email, phone, dept_id, enrollment_year) VALUES
('Arjun',   'Sharma',    'arjun.sharma@uni.edu',    '9876543210', 1, 2022),
('Priya',   'Nair',      'priya.nair@uni.edu',      '9876543211', 2, 2022),
('Rohit',   'Verma',     'rohit.verma@uni.edu',     '9876543212', 1, 2023),
('Sneha',   'Patel',     'sneha.patel@uni.edu',     '9876543213', 4, 2021),
('Aakash',  'Singh',     'aakash.singh@uni.edu',    '9876543214', 3, 2023),
('Kavya',   'Reddy',     'kavya.reddy@uni.edu',     '9876543215', 5, 2022),
('Vikram',  'Iyer',      'vikram.iyer@uni.edu',     '9876543216', 1, 2021),
('Anjali',  'Gupta',     'anjali.gupta@uni.edu',    '9876543217', 2, 2024),
('Rahul',   'Mehta',     'rahul.mehta@uni.edu',     '9876543218', 4, 2022),
('Divya',   'Krishnan',  'divya.krishnan@uni.edu',  '9876543219', 5, 2023);

INSERT IGNORE INTO advisors (first_name, last_name, email, dept_id) VALUES
('Prof. Arun',    'Pillai',   'arun.pillai@uni.edu',   1),
('Prof. Meena',   'Joshi',    'meena.joshi@uni.edu',   2),
('Prof. Deepak',  'Tiwari',   'deepak.tiwari@uni.edu', 3),
('Prof. Sunita',  'Bose',     'sunita.bose@uni.edu',   4);

INSERT IGNORE INTO clubs (club_name, category_id, description, founded_year, room_number, budget) VALUES
('Code Crafters',         1, 'Competitive programming and open-source club', 2018, 'C-101', 50000.00),
('Robotics Arena',        1, 'Robotics and automation enthusiasts',           2019, 'C-102', 75000.00),
('Cultural Canvas',       2, 'Dance, music, and fine arts collective',        2015, 'A-201', 60000.00),
('Drama Guild',           2, 'Theatre and performing arts club',              2016, 'A-202', 45000.00),
('Sports Federation',     3, 'Multi-sport coordination committee',            2010, 'GYM-1', 100000.00),
('Social Impact Cell',    4, 'Community service and NGO partnerships',        2017, 'B-301', 30000.00),
('Debate Society',        5, 'Competitive debating and public speaking',      2014, 'B-201', 25000.00),
('Entrepreneurship Cell', 4, 'Startup culture and innovation hub',            2020, 'B-302', 80000.00);

INSERT IGNORE INTO club_advisor_assignments (club_id, advisor_id, assigned_date) VALUES
(1, 1, '2024-01-10'),
(2, 1, '2024-01-10'),
(3, 2, '2024-01-15'),
(4, 2, '2024-01-15'),
(5, 3, '2024-01-20'),
(6, 4, '2024-01-20'),
(7, 4, '2024-01-20'),
(8, 4, '2024-01-25');

INSERT IGNORE INTO memberships (student_id, club_id, position_id, join_date, status) VALUES
(1, 1, 1, '2022-08-01', 'active'),
(2, 3, 2, '2022-08-05', 'active'),
(3, 1, 6, '2023-08-01', 'active'),
(4, 8, 1, '2021-09-01', 'active'),
(5, 5, 6, '2023-08-10', 'active'),
(6, 3, 3, '2022-08-05', 'active'),
(7, 2, 1, '2021-08-01', 'active'),
(8, 1, 6, '2024-08-01', 'active'),
(9, 7, 2, '2022-09-01', 'active'),
(10, 4, 6, '2023-08-15', 'active'),
(1, 7, 6, '2022-09-05', 'active'),
(2, 6, 4, '2022-09-10', 'active');

INSERT IGNORE INTO events (event_name, event_date, event_time, club_id, venue_id, description, max_participants, status) VALUES
('HackFest 2025',            '2025-03-15', '09:00:00', 1, 1, '24-hour coding marathon',                   200, 'completed'),
('Robo-Wars Championship',   '2025-04-10', '10:00:00', 2, 6, 'Inter-college robot battle competition',    150, 'completed'),
('Annual Cultural Night',    '2025-04-20', '18:00:00', 3, 1, 'Showcase of dance, music, and drama',       500, 'completed'),
('Startup Pitch Day',        '2025-05-01', '10:00:00', 8, 2, 'Present your startup idea to investors',    100, 'completed'),
('Debate Grand Prix',        '2025-11-20', '10:00:00', 7, 3, 'Annual inter-department debate tournament',  80, 'upcoming'),
('Tech Symposium 2025',      '2025-12-05', '09:00:00', 1, 1, 'Guest lectures and paper presentations',   300, 'upcoming'),
('Sports Day 2025',          '2025-12-15', '07:00:00', 5, 6, 'Annual inter-department sports meet',      1000, 'upcoming');

INSERT IGNORE INTO event_registrations (event_id, student_id, registration_date, attendance_status) VALUES
(1, 1, '2025-03-10', 'attended'),
(1, 3, '2025-03-11', 'attended'),
(1, 7, '2025-03-11', 'attended'),
(2, 7, '2025-04-05', 'attended'),
(3, 2, '2025-04-15', 'attended'),
(3, 6, '2025-04-15', 'attended'),
(4, 4, '2025-04-25', 'attended'),
(5, 9, '2025-11-15', 'registered'),
(5, 1, '2025-11-16', 'registered'),
(6, 1, '2025-11-20', 'registered'),
(6, 3, '2025-11-21', 'registered'),
(7, 5, '2025-11-25', 'registered');
