-- Create the database
CREATE DATABASE IF NOT EXISTS `school_results`;
USE `school_results`;

CREATE TABLE `sms_section` (
  `section_id` varchar(255) PRIMARY KEY,
  `section` varchar(255)
);

CREATE TABLE `sms_subjects` (
  `subject_id` varchar(255) PRIMARY KEY,
  `subject` varchar(255),
  `code` varchar(10) UNIQUE
);

CREATE TABLE `sms_teacher` (
  `teacher_id` varchar(10) PRIMARY KEY,
  `name` varchar(255),
  `subject_code` varchar(10)
);

INSERT INTO `sms_section` (`section_id`, `section`) VALUES
('G6', 'Grade 6'),
('G7', 'Grade 7'),
('G8', 'Grade 8'),
('G9', 'Grade 9');

INSERT INTO `sms_subjects` (`subject_id`, `subject`, `code`) VALUES
('ENG', 'English', 'ENG'),
('MATH', 'Mathematics', 'MATH'),
('SCI', 'Science', 'SCI'),
('SIN', 'Sinhala', 'SIN'),
('REL', 'Religion', 'REL');

INSERT INTO `sms_teacher` (`teacher_id`, `name`, `subject_code`) VALUES
('T001', 'Kasun Perera', 'ENG'),
('T002', 'Nimali Silva', 'MATH'),
('T003', 'Sunil Fernando', 'SCI'),
('T004', 'Kamal Herath', 'SIN'),
('T005', 'Anoma Rajapaksa', 'REL');

CREATE TABLE `sms_classes` (
  `class_id` varchar(10) PRIMARY KEY,
  `name` varchar(10),
  `section_id` varchar(255)
);

INSERT INTO `sms_classes` (`class_id`, `name`, `section_id`) VALUES
('6A', '6-A', 'G6'),
('6B', '6-B', 'G6'),
('6C', '6-C', 'G6'),
('6D', '6-D', 'G6'),
('6E', '6-E', 'G6'),
('7A', '7-A', 'G7'),
('7B', '7-B', 'G7'),
('7C', '7-C', 'G7'),
('7D', '7-D', 'G7'),
('7E', '7-E', 'G7'),
('8A', '8-A', 'G8'),
('8B', '8-B', 'G8'),
('8C', '8-C', 'G8'),
('8D', '8-D', 'G8'),
('8E', '8-E', 'G8'),
('9A', '9-A', 'G9'),
('9B', '9-B', 'G9'),
('9C', '9-C', 'G9'),
('9D', '9-D', 'G9'),
('9E', '9-E', 'G9');

CREATE TABLE `sms_students` (
  `student_id` varchar(10) PRIMARY KEY,
  `name` varchar(255),
  `class_id` varchar(10)
);

INSERT INTO `sms_students` (`student_id`, `name`, `class_id`) VALUES
('S001', 'John Smith', '6A'),
('S002', 'Jane Doe', '6A'),
('S003', 'Michael Johnson', '6B'),
('S004', 'Sarah Williams', '7A'),
('S005', 'David Brown', '8C');

CREATE TABLE `sms_marks` (
  `mark_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `student_id` varchar(10) NOT NULL,
  `subject_id` varchar(255) NOT NULL,
  `term` enum('1','2','3') NOT NULL,
  `marks` decimal(5,2) NOT NULL,
  `year` year NOT NULL
);

INSERT INTO `sms_marks` (`student_id`, `subject_id`, `term`, `marks`, `year`) VALUES
('S001', 'ENG', '1', 85.50, 2024),
('S001', 'MATH', '1', 90.00, 2024),
('S001', 'SCI', '1', 78.00, 2024),
('S002', 'ENG', '1', 92.00, 2024),
('S002', 'MATH', '1', 88.50, 2024);

CREATE TABLE `sms_user` (
  `u_id` varchar(11) PRIMARY KEY,
  `first_name` varchar(50),
  `last_name` varchar(50),
  `email` varchar(50),
  `password` varchar(255),
  `type` varchar(250) DEFAULT 'general',
  `status` enum('active','pending','deleted') DEFAULT 'pending'
);

INSERT INTO `sms_user` (`u_id`, `first_name`, `last_name`, `email`, `password`, `type`, `status`) VALUES
('admin_1', 'Admin', 'User', 'admin@school.edu', '12345678', 'administrator', 'active');

-- Add Foreign Key Constraints at the End
ALTER TABLE `sms_classes`
  ADD FOREIGN KEY (`section_id`) REFERENCES `sms_section` (`section_id`);

ALTER TABLE `sms_students`
  ADD FOREIGN KEY (`class_id`) REFERENCES `sms_classes` (`class_id`);

ALTER TABLE `sms_marks`
  ADD FOREIGN KEY (`student_id`) REFERENCES `sms_students` (`student_id`),
  ADD FOREIGN KEY (`subject_id`) REFERENCES `sms_subjects` (`subject_id`);

ALTER TABLE `sms_teacher`
  ADD FOREIGN KEY (`subject_code`) REFERENCES `sms_subjects` (`code`);

-- Add Indexes for Performance
CREATE INDEX idx_teacher_subject ON `sms_teacher` (`subject_code`);
CREATE INDEX idx_class_section ON `sms_classes` (`section_id`);
CREATE INDEX idx_student_class ON `sms_students` (`class_id`);
CREATE INDEX idx_marks_student ON `sms_marks` (`student_id`);
CREATE INDEX idx_marks_subject ON `sms_marks` (`subject_id`);