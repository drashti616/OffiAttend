-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 14, 2026 at 03:19 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `office_attendance`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `last_login_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `username`, `password_hash`, `full_name`, `email`, `created_at`, `last_login_at`) VALUES
(1, 'drashti.616', '$2b$12$TMjIEE4X/ehDxmQUXFVYSeu/gPx06KKBbp70XCeHWoNwrpLewrj5C', 'Drashti Rathod', 'dras@gmail.com', '2026-02-22 23:22:50', '2026-03-14 19:34:49');

-- --------------------------------------------------------

--
-- Table structure for table `attendance`
--

CREATE TABLE `attendance` (
  `id` int(11) NOT NULL,
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
  `attendance_locked` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `attendance`
--

INSERT INTO `attendance` (`id`, `emp_id`, `att_date`, `in_time`, `out_time`, `status`, `is_late`, `source`, `created_at`, `updated_at`, `leave_status`, `attendance_locked`) VALUES
(7, 'emp001', '2026-02-23', '15:53:09', '17:03:41', 'Late', 1, 'Camera', '2026-02-23 15:53:09', '2026-02-23 17:03:41', 'Not Applied', 0),
(9, 'emp002', '2026-02-24', NULL, NULL, 'Leave', 0, 'System', '2026-02-24 09:00:15', '2026-02-24 22:41:30', 'Approved', 0),
(10, 'emp001', '2026-02-24', '11:22:52', '12:29:13', 'Late', 1, 'Camera', '2026-02-24 11:22:52', '2026-02-24 12:29:13', 'Not Applied', 0),
(12, 'emp002', '2026-02-23', NULL, NULL, 'Absent', 0, 'System', '2026-02-24 22:42:56', '2026-02-24 22:43:07', 'Not Applied', 0),
(17, 'emp001', '2026-02-25', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-02-25 10:00:19', '2026-02-25 19:21:46', 'Not Applied', 0),
(18, 'emp002', '2026-02-25', NULL, NULL, 'Leave', 0, 'Auto-Generator', '2026-02-25 10:00:19', '2026-02-25 19:21:46', 'Approved', 0),
(20, 'emp005', '2026-02-25', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-02-25 10:00:19', '2026-02-25 19:21:46', 'Not Applied', 0),
(29, 'emp001', '2026-02-26', '11:17:33', NULL, 'Late', 1, 'Camera', '2026-02-26 11:17:33', NULL, 'Not Applied', 0),
(39, 'emp002', '2026-02-26', NULL, NULL, 'Leave', 0, 'Camera', '2026-02-26 20:32:34', '2026-02-26 20:35:21', 'Approved', 0),
(41, 'emp005', '2026-02-26', NULL, NULL, 'Absent', 0, 'Camera', '2026-02-26 20:32:34', '2026-02-26 20:35:21', 'Not Applied', 0),
(54, 'emp001', '2026-02-27', '18:17:46', '18:54:40', 'Late', 1, 'Auto_Slot_Generator', '2026-02-27 10:13:34', '2026-02-27 20:56:04', 'Rejected', 1),
(55, 'emp002', '2026-02-27', NULL, NULL, 'Absent', 0, 'Auto_Slot_Generator', '2026-02-27 10:13:34', '2026-02-27 20:56:04', 'Not Applied', 1),
(57, 'emp005', '2026-02-27', NULL, NULL, 'Absent', 0, 'Auto_Slot_Generator', '2026-02-27 10:13:34', '2026-02-27 20:56:04', 'Not Applied', 1),
(62, 'emp001', '2026-02-28', '12:34:20', '18:51:31', 'Late', 1, 'Auto-Generator', '2026-02-28 10:55:52', '2026-02-28 22:28:53', 'Rejected', 1),
(63, 'emp002', '2026-02-28', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-02-28 10:55:52', '2026-02-28 19:28:09', 'Not Applied', 1),
(65, 'emp005', '2026-02-28', '13:25:33', '13:29:42', 'Late', 1, 'Auto-Generator', '2026-02-28 10:55:52', '2026-02-28 19:28:09', 'Not Applied', 1),
(218, 'emp001', '2026-03-01', '10:59:40', NULL, 'Present', 0, 'Auto-Generator', '2026-03-01 10:58:05', '2026-03-01 10:59:40', 'Rejected', 0),
(219, 'emp002', '2026-03-01', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-01 10:58:05', NULL, 'Not Applied', 0),
(220, 'emp005', '2026-03-01', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-01 10:58:05', NULL, 'Not Applied', 0),
(221, 'emp001', '2026-03-05', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-05 21:26:17', '2026-03-05 21:26:17', 'Not Applied', 1),
(222, 'emp002', '2026-03-05', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-05 21:26:17', '2026-03-05 21:26:17', 'Not Applied', 1),
(223, 'emp005', '2026-03-05', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-05 21:26:17', '2026-03-05 21:26:17', 'Not Applied', 1),
(249, 'emp001', '2026-03-06', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-06 09:14:29', '2026-03-06 19:15:04', 'Not Applied', 1),
(250, 'emp002', '2026-03-06', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-06 09:14:29', '2026-03-06 19:15:04', 'Not Applied', 1),
(251, 'emp005', '2026-03-06', NULL, NULL, 'Leave', 0, 'Auto-Generator', '2026-03-06 09:14:29', '2026-03-06 19:15:04', 'Not Applied', 1),
(252, 'emp001', '2026-03-07', '19:11:09', NULL, 'Late', 1, 'Auto-Generator', '2026-03-07 18:48:35', '2026-03-07 19:41:15', 'Not Applied', 1),
(253, 'emp002', '2026-03-07', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-07 18:48:35', '2026-03-07 19:41:15', 'Not Applied', 1),
(254, 'emp005', '2026-03-07', '19:12:07', NULL, 'Late', 1, 'Auto-Generator', '2026-03-07 18:48:35', '2026-03-07 19:41:15', 'Not Applied', 1),
(255, 'emp001', '2026-03-08', '11:52:30', '18:29:57', 'Late', 1, 'Auto-Generator', '2026-03-08 11:51:35', '2026-03-08 19:15:01', 'Not Applied', 1),
(256, 'emp002', '2026-03-08', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-08 11:51:35', '2026-03-08 19:15:01', 'Not Applied', 1),
(257, 'emp005', '2026-03-08', '11:56:15', '18:47:17', 'Late', 1, 'Auto-Generator', '2026-03-08 11:51:35', '2026-03-08 19:15:01', 'Approved', 1),
(258, 'emp001', '2026-03-09', '10:01:59', '16:46:36', 'Present', 0, 'Auto-Generator', '2026-03-09 08:58:36', '2026-03-10 08:31:14', 'Not Applied', 1),
(259, 'emp002', '2026-03-09', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-09 08:58:36', '2026-03-10 08:31:13', 'Not Applied', 1),
(260, 'emp005', '2026-03-09', NULL, NULL, 'Leave', 0, 'Auto-Generator', '2026-03-09 08:58:36', '2026-03-10 08:31:14', 'Not Applied', 1),
(261, 'emp006', '2026-03-09', '10:09:23', NULL, 'Present', 0, 'Auto-Generator', '2026-03-09 09:06:41', '2026-03-10 08:31:14', 'Not Applied', 1),
(262, 'emp001', '2026-03-10', '13:04:59', '13:30:51', 'Late', 1, 'Auto-Generator', '2026-03-10 08:16:44', '2026-03-10 22:56:39', 'Not Applied', 1),
(263, 'emp002', '2026-03-10', '18:08:23', NULL, 'Late', 1, 'Auto-Generator', '2026-03-10 08:16:44', '2026-03-10 22:56:39', 'Not Applied', 1),
(264, 'emp005', '2026-03-10', NULL, NULL, 'Leave', 0, 'Auto-Generator', '2026-03-10 08:16:44', '2026-03-10 22:56:39', 'Not Applied', 1),
(265, 'emp006', '2026-03-10', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-10 08:16:44', '2026-03-10 22:56:39', 'Not Applied', 1),
(266, 'emp001', '2026-03-11', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-11 20:38:34', '2026-03-11 20:38:34', 'Not Applied', 1),
(267, 'emp002', '2026-03-11', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-11 20:38:34', '2026-03-11 20:38:34', 'Not Applied', 1),
(268, 'emp005', '2026-03-11', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-11 20:38:34', '2026-03-11 20:38:34', 'Not Applied', 1),
(269, 'emp006', '2026-03-11', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-11 20:38:34', '2026-03-11 20:38:34', 'Not Applied', 1),
(270, 'emp001', '2026-03-12', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-12 19:41:18', '2026-03-12 19:41:18', 'Not Applied', 1),
(271, 'emp002', '2026-03-12', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-12 19:41:18', '2026-03-12 19:41:18', 'Not Applied', 1),
(272, 'emp005', '2026-03-12', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-12 19:41:18', '2026-03-12 19:41:18', 'Not Applied', 1),
(273, 'emp006', '2026-03-12', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-12 19:41:18', '2026-03-12 19:41:18', 'Not Applied', 1),
(294, 'emp001', '2026-03-13', '17:55:30', '18:07:43', 'Late', 1, 'System_Morning', '2026-03-13 17:42:07', '2026-03-13 19:15:16', 'Not Applied', 1),
(295, 'emp002', '2026-03-13', NULL, NULL, 'Absent', 0, 'System_Morning', '2026-03-13 17:42:07', '2026-03-13 19:15:16', 'Not Applied', 1),
(296, 'emp005', '2026-03-13', NULL, NULL, 'Absent', 0, 'System_Morning', '2026-03-13 17:42:07', '2026-03-13 19:15:16', 'Rejected', 1),
(297, 'emp006', '2026-03-13', NULL, NULL, 'Absent', 0, 'System_Morning', '2026-03-13 17:42:07', '2026-03-13 19:15:16', 'Not Applied', 1),
(298, 'emp001', '2026-03-14', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-14 19:34:16', '2026-03-14 19:34:16', 'Not Applied', 1),
(299, 'emp002', '2026-03-14', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-14 19:34:16', '2026-03-14 19:34:16', 'Not Applied', 1),
(300, 'emp005', '2026-03-14', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-14 19:34:16', '2026-03-14 19:34:16', 'Rejected', 1),
(301, 'emp006', '2026-03-14', NULL, NULL, 'Absent', 0, 'Auto-Generator', '2026-03-14 19:34:16', '2026-03-14 19:34:16', 'Not Applied', 1);

-- --------------------------------------------------------

--
-- Table structure for table `attendance_logs`
--

CREATE TABLE `attendance_logs` (
  `id` int(11) NOT NULL,
  `emp_id` varchar(30) NOT NULL,
  `att_date` datetime NOT NULL COMMENT 'Exact scan timestamp',
  `action` varchar(10) NOT NULL COMMENT 'ENTRY or EXIT',
  `scan_method` varchar(20) DEFAULT 'face_recognition' COMMENT 'How scan was captured',
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `attendance_logs`
--

INSERT INTO `attendance_logs` (`id`, `emp_id`, `att_date`, `action`, `scan_method`, `created_at`) VALUES
(4, 'emp001', '2026-02-23 15:53:09', 'ENTRY', 'face_recognition', '2026-02-23 15:53:09'),
(5, 'emp001', '2026-02-23 15:53:23', 'EXIT', 'face_recognition', '2026-02-23 15:53:23'),
(11, 'emp001', '2026-02-23 17:02:49', 'ENTRY', 'face_recognition', '2026-02-23 17:02:49'),
(12, 'emp001', '2026-02-23 17:03:41', 'EXIT', 'face_recognition', '2026-02-23 17:03:41'),
(13, 'emp003', '2026-02-23 17:08:22', 'ENTRY', 'face_recognition', '2026-02-23 17:08:22'),
(14, 'emp001', '2026-02-24 11:22:52', 'ENTRY', 'face_recognition', '2026-02-24 11:22:52'),
(15, 'emp001', '2026-02-24 12:29:13', 'EXIT', 'face_recognition', '2026-02-24 12:29:13'),
(17, 'emp001', '2026-02-26 11:17:33', 'ENTRY', 'face_recognition', '2026-02-26 11:17:33'),
(18, 'emp003', '2026-02-27 10:15:08', 'ENTRY', 'face_recognition', '2026-02-27 10:15:08'),
(19, 'emp003', '2026-02-27 15:48:09', 'EXIT', 'face_recognition', '2026-02-27 15:48:09'),
(20, 'emp001', '2026-02-27 18:17:46', 'ENTRY', 'face_recognition', '2026-02-27 18:17:46'),
(21, 'emp001', '2026-02-27 18:54:40', 'EXIT', 'face_recognition', '2026-02-27 18:54:40'),
(52, 'emp001', '2026-02-28 12:34:20', 'ENTRY', 'face_recognition', '2026-02-28 12:34:20'),
(53, 'emp001', '2026-02-28 12:41:45', 'EXIT', 'face_recognition', '2026-02-28 12:41:45'),
(54, 'emp001', '2026-02-28 13:13:27', 'ENTRY', 'face_recognition', '2026-02-28 13:13:27'),
(55, 'emp001', '2026-02-28 13:14:36', 'EXIT', 'face_recognition', '2026-02-28 13:14:36'),
(56, 'emp005', '2026-02-28 13:25:33', 'ENTRY', 'face_recognition', '2026-02-28 13:25:33'),
(57, 'emp005', '2026-02-28 13:29:42', 'EXIT', 'face_recognition', '2026-02-28 13:29:42'),
(58, 'emp001', '2026-02-28 18:47:41', 'ENTRY', 'face_recognition', '2026-02-28 18:47:41'),
(59, 'emp001', '2026-02-28 18:49:16', 'EXIT', 'face_recognition', '2026-02-28 18:49:16'),
(60, 'emp001', '2026-02-28 18:50:51', 'ENTRY', 'face_recognition', '2026-02-28 18:50:51'),
(61, 'emp001', '2026-02-28 18:51:31', 'EXIT', 'face_recognition', '2026-02-28 18:51:31'),
(64, 'emp001', '2026-03-01 10:59:40', 'ENTRY', 'face_recognition', '2026-03-01 10:59:40'),
(66, 'emp001', '2026-03-07 19:11:09', 'ENTRY', 'face_recognition', '2026-03-07 19:11:09'),
(67, 'emp005', '2026-03-07 19:12:07', 'ENTRY', 'face_recognition', '2026-03-07 19:12:07'),
(68, 'emp001', '2026-03-08 11:52:30', 'ENTRY', 'face_recognition', '2026-03-08 11:52:30'),
(69, 'emp005', '2026-03-08 11:56:15', 'ENTRY', 'face_recognition', '2026-03-08 11:56:15'),
(70, 'emp001', '2026-03-08 17:51:17', 'EXIT', 'face_recognition', '2026-03-08 17:51:17'),
(71, 'emp005', '2026-03-08 17:52:06', 'EXIT', 'face_recognition', '2026-03-08 17:52:06'),
(72, 'emp001', '2026-03-08 18:10:27', 'ENTRY', 'face_recognition', '2026-03-08 18:10:27'),
(73, 'emp001', '2026-03-08 18:29:57', 'EXIT', 'face_recognition', '2026-03-08 18:29:57'),
(74, 'emp005', '2026-03-08 18:36:51', 'ENTRY', 'face_recognition', '2026-03-08 18:36:51'),
(75, 'emp005', '2026-03-08 18:47:17', 'EXIT', 'face_recognition', '2026-03-08 18:47:17'),
(76, 'emp001', '2026-03-09 10:01:59', 'ENTRY', 'face_recognition', '2026-03-09 10:01:59'),
(77, 'emp006', '2026-03-09 10:09:23', 'ENTRY', 'face_recognition', '2026-03-09 10:09:23'),
(78, 'emp001', '2026-03-09 16:46:36', 'EXIT', 'face_recognition', '2026-03-09 16:46:36'),
(79, 'emp001', '2026-03-10 13:04:59', 'ENTRY', 'face_recognition', '2026-03-10 13:04:59'),
(80, 'emp001', '2026-03-10 13:30:51', 'EXIT', 'face_recognition', '2026-03-10 13:30:51'),
(81, 'emp001', '2026-03-10 18:07:38', 'ENTRY', 'face_recognition', '2026-03-10 18:07:38'),
(82, 'emp002', '2026-03-10 18:08:23', 'ENTRY', 'face_recognition', '2026-03-10 18:08:23'),
(85, 'emp001', '2026-03-13 17:55:30', 'ENTRY', 'face_recognition', '2026-03-13 17:55:30'),
(86, 'emp001', '2026-03-13 18:07:43', 'EXIT', 'face_recognition', '2026-03-13 18:07:43');

-- --------------------------------------------------------

--
-- Table structure for table `employees`
--

CREATE TABLE `employees` (
  `id` int(11) NOT NULL,
  `emp_id` varchar(30) NOT NULL,
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

--
-- Dumping data for table `employees`
--

INSERT INTO `employees` (`id`, `emp_id`, `full_name`, `mobile`, `email`, `designation`, `joining_date`, `address`, `role`, `status`, `created_at`) VALUES
(1, 'emp001', 'Vishwa B. Rathod', '8980360039', 'drashtir.616@gmail.com', 'Frontend Developer', '2026-02-23', 'Kalawad Road, Rajkot-360005.', 'Employee', 'Active', '2026-02-23 07:49:27'),
(2, 'emp002', 'Priya P. Poon', '9924892979', 'poonyesha1@gmail.com', 'iOS App Developer', '2026-02-23', 'Racecourse Ring Road, Rajkot.', 'Employee', 'Active', '2026-02-23 08:07:37'),
(6, 'emp005', 'Asha S. Shah', '7862954879', 'ashas@gmail.com', 'Android App Developer', '2026-02-25', 'Kuvadava Road, Rajkot-360003.', 'Employee', 'Active', '2026-02-24 23:07:10'),
(12, 'emp006', 'Mansi Varu', '9712940709', 'manc.21@gmail.com', 'UI/UX Designer', '2026-03-09', 'Rajkot, Gujarat.', 'Employee', 'Active', '2026-03-09 09:01:22');

-- --------------------------------------------------------

--
-- Table structure for table `employee_credentials`
--

CREATE TABLE `employee_credentials` (
  `id` int(11) NOT NULL,
  `emp_id` varchar(30) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `must_change_password` tinyint(1) NOT NULL DEFAULT 1,
  `last_login_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `employee_credentials`
--

INSERT INTO `employee_credentials` (`id`, `emp_id`, `password_hash`, `is_active`, `must_change_password`, `last_login_at`, `created_at`) VALUES
(1, 'emp001', '$2b$12$6P4Ch1eyU7Kl4RGh25qeZ.ZOvTM23eyj.pkMuP.2evWqxXSSBEJre', 1, 0, '2026-03-14 19:35:18', '2026-02-23 07:49:28'),
(2, 'emp002', '$2b$12$6mPapQF/kwAX22f7h1QNBuPWHUAEZgCFouXJXMBFmjmneFfg9oKTS', 1, 0, '2026-03-10 18:09:54', '2026-02-23 08:07:37'),
(6, 'emp005', '$2b$12$.OYPkx3/qgwuQa/1MOHJB.RFNQWrRVh5rQLZexwip5.yCqyeF/w82', 1, 0, '2026-03-12 23:31:11', '2026-02-24 23:07:10'),
(12, 'emp006', '$2b$12$MDc8KQgm6VCiyCtlZijIuOcCSHd7kKsecozXLdzqTsvKeIiTPY6N6', 1, 0, '2026-03-10 22:58:09', '2026-03-09 09:01:22');

-- --------------------------------------------------------

--
-- Table structure for table `face_profiles`
--

CREATE TABLE `face_profiles` (
  `id` int(11) NOT NULL,
  `emp_id` varchar(30) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT NULL,
  `face_image_path` varchar(500) DEFAULT NULL,
  `profile_pic_path` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `face_profiles`
--

INSERT INTO `face_profiles` (`id`, `emp_id`, `created_at`, `updated_at`, `face_image_path`, `profile_pic_path`) VALUES
(1, 'emp001', '2026-02-23 07:49:27', '2026-02-23 07:50:38', 'faces/images/emp001.jpg', 'faces/uploads/emp001.jpg'),
(2, 'emp002', '2026-02-23 08:07:37', NULL, 'faces/images/emp002.jpg', NULL),
(6, 'emp005', '2026-02-24 23:07:10', '2026-02-24 23:09:26', 'faces/images/emp005.jpg', 'faces/uploads/emp005.jpg'),
(12, 'emp006', '2026-03-09 09:01:22', '2026-03-09 09:07:47', 'faces/images/emp006.jpg', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `leave_applications`
--

CREATE TABLE `leave_applications` (
  `id` int(11) NOT NULL,
  `emp_id` varchar(30) NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `leave_type` varchar(30) NOT NULL,
  `reason` text DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Pending' COMMENT 'Pending|Approved|Rejected',
  `reviewed_by` varchar(30) DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `auto_overridden` tinyint(1) DEFAULT 0 COMMENT 'TRUE if employee came in on leave day',
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `leave_applications`
--

INSERT INTO `leave_applications` (`id`, `emp_id`, `from_date`, `to_date`, `leave_type`, `reason`, `status`, `reviewed_by`, `reviewed_at`, `auto_overridden`, `created_at`) VALUES
(1, 'emp002', '2026-02-24', '2026-02-26', 'Sick', 'I am currently admitted in hospital, because I am suffering from Malaria', 'Approved', 'admin', '2026-02-23 08:25:50', 0, '2026-02-23 08:14:25'),
(2, 'emp001', '2026-02-27', '2026-03-01', 'Casual', 'I have to attend one family function, for that I have to go out of state.', 'Rejected', 'admin', '2026-02-23 08:32:24', 0, '2026-02-23 08:32:01'),
(3, 'emp005', '2026-03-06', '2026-03-10', 'Sick', 'I have got injured by car accident and currently in hospital so grant me a leave.', 'Approved', 'admin', '2026-03-05 22:11:43', 0, '2026-03-05 22:11:07'),
(14, 'emp005', '2026-03-13', '2026-03-15', 'Casual', 'I have to attend family function.', 'Rejected', 'admin', '2026-03-12 23:31:03', 0, '2026-03-12 23:21:17'),
(15, 'emp005', '2026-04-01', '2026-04-03', 'Casual', 'I have to attend family function.', 'Approved', 'admin', '2026-03-12 23:30:58', 0, '2026-03-12 23:28:39');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_emp_date` (`emp_id`,`att_date`),
  ADD KEY `idx_att_date` (`att_date`),
  ADD KEY `idx_att_status` (`status`);

--
-- Indexes for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_log_emp_date` (`emp_id`),
  ADD KEY `idx_log_datetime` (`att_date`);

--
-- Indexes for table `employees`
--
ALTER TABLE `employees`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `emp_id` (`emp_id`);

--
-- Indexes for table `employee_credentials`
--
ALTER TABLE `employee_credentials`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `emp_id` (`emp_id`);

--
-- Indexes for table `face_profiles`
--
ALTER TABLE `face_profiles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `emp_id` (`emp_id`);

--
-- Indexes for table `leave_applications`
--
ALTER TABLE `leave_applications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_leave_emp` (`emp_id`),
  ADD KEY `idx_leave_dates` (`from_date`,`to_date`,`status`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `attendance`
--
ALTER TABLE `attendance`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=302;

--
-- AUTO_INCREMENT for table `attendance_logs`
--
ALTER TABLE `attendance_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=87;

--
-- AUTO_INCREMENT for table `employees`
--
ALTER TABLE `employees`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `employee_credentials`
--
ALTER TABLE `employee_credentials`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `face_profiles`
--
ALTER TABLE `face_profiles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `leave_applications`
--
ALTER TABLE `leave_applications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `attendance`
--
ALTER TABLE `attendance`
  ADD CONSTRAINT `fk_att_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE;

--
-- Constraints for table `employee_credentials`
--
ALTER TABLE `employee_credentials`
  ADD CONSTRAINT `fk_creds_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE;

--
-- Constraints for table `face_profiles`
--
ALTER TABLE `face_profiles`
  ADD CONSTRAINT `fk_face_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE;

--
-- Constraints for table `leave_applications`
--
ALTER TABLE `leave_applications`
  ADD CONSTRAINT `fk_leave_emp` FOREIGN KEY (`emp_id`) REFERENCES `employees` (`emp_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
