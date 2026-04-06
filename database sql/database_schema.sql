-- Database Schema for Office Attendance System
-- This file contains only table structures (no data)
-- Import this via phpMyAdmin or SQL command line

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

-- --------------------------------------------------------

CREATE TABLE `employees` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `emp_id` varchar(30) NOT NULL UNIQUE,
  `full_name` varchar(120) NOT NULL,
  `mobile` varchar(20) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `designation` varchar(80) DEFAULT NULL,
  `joining_date` date DEFAULT NULL,
  `address` text DEFAULT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'Employee',
  `status` varchar(20) NOT NULL DEFAULT 'Active',
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

CREATE TABLE `admins` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `username` varchar(50) NOT NULL UNIQUE,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `last_login_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

CREATE TABLE `attendance` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `emp_id` varchar(30) NOT NULL,
  `att_date` date NOT NULL,
  `in_time` time DEFAULT NULL COMMENT 'Entry scan time',
  `out_time` time DEFAULT NULL COMMENT 'Exit scan time ',
  `status` varchar(20) NOT NULL COMMENT 'Present|Late|Leave|Absent',
  `is_late` tinyint(1) NOT NULL DEFAULT 0,
  `source` varchar(30) DEFAULT 'Camera',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  `leave_status` varchar(20) DEFAULT 'Not Applied',
  `attendance_locked` tinyint(1) DEFAULT 0,
  UNIQUE KEY `uniq_emp_date` (`emp_id`,`att_date`),
  KEY `idx_att_date` (`att_date`),
  KEY `idx_att_status` (`status`),
  CONSTRAINT `fk_att_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

CREATE TABLE `attendance_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `emp_id` varchar(30) NOT NULL,
  `att_date` datetime NOT NULL COMMENT 'Exact scan timestamp',
  `action` varchar(10) NOT NULL COMMENT 'ENTRY or EXIT',
  `scan_method` varchar(20) DEFAULT 'face_recognition' COMMENT 'How scan was captured',
  `created_at` datetime DEFAULT current_timestamp(),
  KEY `idx_log_emp_date` (`emp_id`),
  KEY `idx_log_datetime` (`att_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

CREATE TABLE `employee_credentials` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `emp_id` varchar(30) NOT NULL UNIQUE,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `must_change_password` tinyint(1) NOT NULL DEFAULT 1,
  `last_login_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  CONSTRAINT `fk_creds_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

CREATE TABLE `face_profiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `emp_id` varchar(30) NOT NULL UNIQUE,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  `face_image_path` varchar(500) DEFAULT NULL,
  `profile_pic_path` varchar(500) DEFAULT NULL,
  CONSTRAINT `fk_face_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

CREATE TABLE `leave_applications` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `emp_id` varchar(30) NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `leave_type` varchar(30) NOT NULL,
  `reason` text DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Pending' COMMENT 'Pending|Approved|Rejected',
  `reviewed_by` varchar(30) DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `auto_overridden` tinyint(1) DEFAULT 0 COMMENT 'TRUE if employee came in on leave day',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  KEY `idx_leave_dates` (`from_date`,`to_date`,`status`),
  CONSTRAINT `fk_leave_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMIT;
