-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 27, 2025 at 02:41 PM
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
-- Database: `art_showcase`
--

-- --------------------------------------------------------

--
-- Table structure for table `allowed_file_types`
--

CREATE TABLE `allowed_file_types` (
  `id` int(11) NOT NULL,
  `file_type` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `allowed_file_types`
--

INSERT INTO `allowed_file_types` (`id`, `file_type`) VALUES
(3, 'gif'),
(6, 'jpeg'),
(1, 'jpg'),
(5, 'mp4'),
(4, 'pdf'),
(2, 'png'),
(7, 'svg');

-- --------------------------------------------------------

--
-- Table structure for table `artist_followers`
--

CREATE TABLE `artist_followers` (
  `id` int(11) NOT NULL,
  `artist_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `artist_likes`
--

CREATE TABLE `artist_likes` (
  `id` int(11) NOT NULL,
  `artist_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `artist_ratings`
--

CREATE TABLE `artist_ratings` (
  `id` int(11) NOT NULL,
  `artist_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `rating` tinyint(4) NOT NULL CHECK (`rating` between 1 and 5),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `artist_verification`
--

CREATE TABLE `artist_verification` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `artist_type` varchar(50) DEFAULT NULL,
  `security_question1` varchar(255) DEFAULT NULL,
  `security_answer1` varchar(255) DEFAULT NULL,
  `security_question2` varchar(255) DEFAULT NULL,
  `security_answer2` varchar(255) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `reviewer_id` int(11) DEFAULT NULL,
  `reviewer_notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `artwork`
--

CREATE TABLE `artwork` (
  `id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `tags` text DEFAULT NULL,
  `media` varchar(255) NOT NULL,
  `user_id` int(11) NOT NULL,
  `file_hash` varchar(64) NOT NULL,
  `perceptual_hash` varchar(64) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `original_upload_id` int(11) DEFAULT NULL,
  `duplicate_count` int(11) DEFAULT 0,
  `needs_admin_review` tinyint(1) DEFAULT 0,
  `is_approved` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `artwork`
--

INSERT INTO `artwork` (`id`, `title`, `description`, `price`, `tags`, `media`, `user_id`, `file_hash`, `perceptual_hash`, `category`, `original_upload_id`, `duplicate_count`, `needs_admin_review`, `is_approved`, `created_at`) VALUES
(68, 'Music_Test', 'Uploading an audio for tests', 100.00, 'modern, digital', 'main/static/uploads\\Kumakomoyo_PART1_Riddim_Istrumental_demo.mp3', 10, '506ec6f816bc494c771f17da7bd1e7e8560053f6882326f82d8482dd158ae9fe', NULL, 'music', NULL, 0, 0, 1, '2025-04-27 01:11:16'),
(69, 'Video', 'Video testing', 22.00, 'modern, portrait, landscape', 'main/static/uploads\\Ozwa_WeLiquor_-_Mudhara_Benza_pane_basa__1.mp4', 10, '8202c8424c31e64c434523c232856b09569c0763a584bb2bd1369f89c26072a2', NULL, 'animation', NULL, 0, 0, 1, '2025-04-27 01:12:44'),
(70, 'Image_Test', 'Testing with an image', 33.00, 'portrait, modern, abstract', 'main/static/uploads\\marketplace_1.png', 10, '0cd64467be09ffcc2f5e13fe1af39d2fd9e7e62ca97fb6b615cf63d57f7b2752', 'c7bbbb9b19a4bbfb', 'photography', NULL, 0, 0, 1, '2025-04-27 01:15:05'),
(71, 'Sculpture_Test', 'Uploading a test sculpture', 300.00, 'digital', 'main/static/uploads\\Screenshot_2025-04-27_011710.png', 2, '36a0e2c6e6a4672c6331770cedd2f635caf58caaad90d54147296324a2d2c07f', 'ffffe3c3c3c3c7c7', 'sculpture', NULL, 0, 0, 1, '2025-04-27 01:20:12'),
(72, 'Painting_Test', 'Uploading a painting', 300.00, 'portrait, landscape', 'main/static/uploads\\weeeeeeeeeeeeeeeeeeeeejfjf.png', 2, '1a8e89709578cc91593a7a0985c106936ee6bfceb275f2f38e1352564e95c8b0', 'f8f8fdb060fdf8f0', 'painting', NULL, 0, 0, 1, '2025-04-27 01:22:30'),
(73, 'DigitalArt', 'Test Upload for a digital art in general', 66.00, 'portrait, landscape', 'main/static/uploads\\Zimbabwe_1.png', 10, '2c9ceecd717904cc3c4f84c9a380631fda18db683893729e744dc1c3c3c94b96', '7e9e003800313830', 'digital', NULL, 1, 0, 1, '2025-04-27 01:24:23'),
(74, 'Duplicate_Testing', 'Testing duplicate uploads', 11.00, 'modern, portrait, digital, second-hand', 'main/static/uploads\\WOWW.png', 10, '2c9ceecd717904cc3c4f84c9a380631fda18db683893729e744dc1c3c3c94b96', '7e9e003800313830', 'other', 73, 1, 0, 1, '2025-04-27 01:25:16');

-- --------------------------------------------------------

--
-- Table structure for table `artwork_ownership`
--
-- Error reading structure for table art_showcase.artwork_ownership: #1932 - Table 'art_showcase.artwork_ownership' doesn't exist in engine
-- Error reading data for table art_showcase.artwork_ownership: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`artwork_ownership`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `artwork_tags`
--
-- Error reading structure for table art_showcase.artwork_tags: #1932 - Table 'art_showcase.artwork_tags' doesn't exist in engine
-- Error reading data for table art_showcase.artwork_tags: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`artwork_tags`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `artwork_upload_history`
--
-- Error reading structure for table art_showcase.artwork_upload_history: #1932 - Table 'art_showcase.artwork_upload_history' doesn't exist in engine
-- Error reading data for table art_showcase.artwork_upload_history: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`artwork_upload_history`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `backups`
--
-- Error reading structure for table art_showcase.backups: #1932 - Table 'art_showcase.backups' doesn't exist in engine
-- Error reading data for table art_showcase.backups: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`backups`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `badge`
--

CREATE TABLE `badge` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `description` text DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `points_required` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `challenges`
--

CREATE TABLE `challenges` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `deadline` date DEFAULT NULL,
  `points_reward` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `challenges`
--

INSERT INTO `challenges` (`id`, `name`, `description`, `deadline`, `points_reward`) VALUES
(1, 'Nature Photography', 'Capture the beauty of nature in your own style.', '2025-09-26', 230),
(2, 'Abstract Art.', 'Create an abstract piece using bold colors.', '2025-04-15', 300),
(3, 'Digital Illustration', 'Design a digital artwork based on a theme of your choice.', '2025-05-30', 500),
(5, 'singing', 'sing', '2025-04-25', 305);

-- --------------------------------------------------------

--
-- Table structure for table `challenge_submission`
--

CREATE TABLE `challenge_submission` (
  `id` int(11) NOT NULL,
  `challenge_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `is_approved` tinyint(1) DEFAULT NULL,
  `points_awarded` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `comments`
--

CREATE TABLE `comments` (
  `id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `content` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `drawings`
--

CREATE TABLE `drawings` (
  `id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `image_data` longblob NOT NULL,
  `points` int(11) NOT NULL,
  `mode` varchar(50) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `favorites`
--

CREATE TABLE `favorites` (
  `user_id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `insights`
--

CREATE TABLE `insights` (
  `id` int(11) NOT NULL,
  `views` int(11) DEFAULT 0,
  `likes` int(11) DEFAULT 0,
  `shares` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `insights`
--

INSERT INTO `insights` (`id`, `views`, `likes`, `shares`) VALUES
(2, 5230, 320, 150);

-- --------------------------------------------------------

--
-- Table structure for table `leaderboard`
--

CREATE TABLE `leaderboard` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `score` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `leaderboard`
--

INSERT INTO `leaderboard` (`id`, `username`, `score`, `created_at`) VALUES
(1, 'tyno25', 936, '2025-03-23 19:16:56'),
(2, 'treble3', 2385, '2025-03-23 19:19:24'),
(3, 'smuggerteey', 469, '2025-03-23 19:46:07'),
(4, 'onemore', 1662, '2025-03-28 08:11:15'),
(0, 'first22', 447, '2025-04-20 18:16:53');

-- --------------------------------------------------------

--
-- Table structure for table `like`
--

CREATE TABLE `like` (
  `id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `username` varchar(50) DEFAULT NULL,
  `room` varchar(50) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `username`, `room`, `message`, `timestamp`) VALUES
(12, 'smuggerteey', 'general', 'HI', '2025-02-09 15:47:14'),
(15, 'treble3', 'general', 'People', '2025-02-09 15:54:31');

-- --------------------------------------------------------

--
-- Table structure for table `notes`
--

CREATE TABLE `notes` (
  `id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `content` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--
-- Error reading structure for table art_showcase.notifications: #1932 - Table 'art_showcase.notifications' doesn't exist in engine
-- Error reading data for table art_showcase.notifications: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`notifications`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `payment`
--
-- Error reading structure for table art_showcase.payment: #1932 - Table 'art_showcase.payment' doesn't exist in engine
-- Error reading data for table art_showcase.payment: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`payment`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `purchases`
--

CREATE TABLE `purchases` (
  `id` int(11) NOT NULL,
  `buyer_id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `purchase_date` datetime DEFAULT current_timestamp(),
  `price` decimal(10,2) DEFAULT NULL,
  `payment_method` varchar(50) DEFAULT NULL,
  `transaction_id` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `purchases`
--

INSERT INTO `purchases` (`id`, `buyer_id`, `artwork_id`, `purchase_date`, `price`, `payment_method`, `transaction_id`) VALUES
(56, 2, 69, '2025-04-27 01:49:53', 22.00, 'credit_card', '7L57YX8DWIT9ON1J'),
(57, 10, 72, '2025-04-27 09:25:02', 300.00, 'credit_card', 'BU6JQSHGLX7T0GH0');

-- --------------------------------------------------------

--
-- Table structure for table `receipts`
--

CREATE TABLE `receipts` (
  `id` int(11) NOT NULL,
  `purchase_id` int(11) NOT NULL,
  `receipt_number` varchar(50) NOT NULL,
  `generated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `receipts`
--

INSERT INTO `receipts` (`id`, `purchase_id`, `receipt_number`, `generated_at`) VALUES
(1, 1, 'RCPT-20250418-000001', '2025-04-18 18:02:14'),
(2, 2, 'RCPT-20250418-000002', '2025-04-18 18:02:50'),
(3, 3, 'RCPT-20250418-000003', '2025-04-18 18:03:29'),
(4, 4, 'RCPT-20250418-000004', '2025-04-18 18:09:05'),
(5, 5, 'RCPT-20250418-000005', '2025-04-18 18:09:48'),
(6, 6, 'RCPT-20250418-000006', '2025-04-18 18:09:56'),
(7, 7, 'RCPT-20250418-000007', '2025-04-18 18:12:39'),
(8, 8, 'RCPT-20250418-000008', '2025-04-18 18:12:56'),
(9, 9, 'RCPT-20250418-000009', '2025-04-18 18:13:13'),
(10, 10, 'RCPT-20250418-000010', '2025-04-18 18:13:34'),
(11, 11, 'RCPT-20250418-000011', '2025-04-18 18:14:59'),
(12, 12, 'RCPT-20250418-000012', '2025-04-18 18:15:34'),
(13, 13, 'RCPT-20250418-000013', '2025-04-18 18:17:33'),
(14, 14, 'RCPT-20250418-000014', '2025-04-18 18:24:15'),
(15, 15, 'RCPT-20250418-000015', '2025-04-18 18:25:10'),
(16, 16, 'RCPT-20250418-000016', '2025-04-18 18:25:56'),
(17, 17, 'RCPT-20250418-000017', '2025-04-18 18:45:47'),
(18, 18, 'RCPT-20250418-000018', '2025-04-18 19:08:14'),
(19, 19, 'RCPT-20250418-000019', '2025-04-18 19:35:07'),
(20, 20, 'RCPT-20250418-000020', '2025-04-18 19:36:49'),
(21, 21, 'RCPT-20250418-000021', '2025-04-18 19:43:29'),
(22, 22, 'RCPT-20250418-000022', '2025-04-18 19:49:05'),
(23, 23, 'RCPT-20250418-000023', '2025-04-18 19:49:29'),
(24, 24, 'RCPT-20250418-000024', '2025-04-18 19:55:01'),
(25, 25, 'RCPT-20250418-000025', '2025-04-18 20:53:45'),
(26, 26, 'RCPT-20250418-000026', '2025-04-18 20:56:25'),
(27, 27, 'RCPT-20250418-000027', '2025-04-18 20:56:37'),
(28, 28, 'RCPT-20250418-000028', '2025-04-18 21:05:19'),
(29, 29, 'RCPT-20250418-000029', '2025-04-18 21:06:11'),
(30, 30, 'RCPT-20250418-000030', '2025-04-18 21:07:38'),
(31, 31, 'RCPT-20250418-000031', '2025-04-18 21:08:44'),
(32, 32, 'RCPT-20250418-000032', '2025-04-18 21:15:08'),
(33, 33, 'RCPT-20250418-000033', '2025-04-18 21:16:28'),
(34, 34, 'RCPT-20250418-000034', '2025-04-18 21:16:56'),
(35, 35, 'RCPT-20250418-000035', '2025-04-18 21:41:30'),
(36, 36, 'RCPT-20250418-000036', '2025-04-18 21:42:40'),
(37, 37, 'RCPT-20250418-000037', '2025-04-18 21:44:37'),
(38, 38, 'RCPT-20250418-000038', '2025-04-18 21:46:04'),
(39, 39, 'RCPT-20250418-000039', '2025-04-18 22:48:44'),
(40, 40, 'RCPT-20250419-000040', '2025-04-19 00:33:45'),
(41, 41, 'RCPT-20250419-000041', '2025-04-19 10:28:46'),
(42, 42, 'RCPT-20250419-000042', '2025-04-19 10:29:28'),
(43, 43, 'RCPT-20250419-000043', '2025-04-19 18:35:51'),
(44, 44, 'RCPT-20250420-000044', '2025-04-20 02:12:00'),
(45, 45, 'RCPT-20250420-000045', '2025-04-20 10:35:15'),
(46, 46, 'RCPT-20250420-000046', '2025-04-20 10:36:44'),
(47, 47, 'RCPT-20250420-000047', '2025-04-20 10:37:18'),
(48, 48, 'RCPT-20250420-000048', '2025-04-20 17:08:56'),
(49, 49, 'RCPT-20250420-000049', '2025-04-20 17:28:38'),
(50, 50, 'RCPT-20250420-000050', '2025-04-20 18:13:26'),
(51, 51, 'RCPT-20250423-000051', '2025-04-23 09:26:21'),
(52, 52, 'RCPT-20250425-000052', '2025-04-25 03:15:33'),
(53, 53, 'RCPT-20250425-000053', '2025-04-25 03:28:46'),
(54, 54, 'RCPT-20250425-000054', '2025-04-25 03:31:22'),
(55, 55, 'RCPT-20250425-000055', '2025-04-25 10:32:01'),
(56, 56, 'RCPT-20250427-000056', '2025-04-27 01:49:53'),
(57, 57, 'RCPT-20250427-000057', '2025-04-27 09:25:02');

-- --------------------------------------------------------

--
-- Table structure for table `recordings`
--

CREATE TABLE `recordings` (
  `id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `audio_data` longblob NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `id` int(11) NOT NULL,
  `reporter_id` int(11) NOT NULL,
  `reported_artwork_id` int(11) NOT NULL,
  `type` varchar(50) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `status` enum('pending','reviewed','resolved','dismissed') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `role_permissions`
--

CREATE TABLE `role_permissions` (
  `id` int(11) NOT NULL,
  `role` varchar(50) NOT NULL,
  `permission` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `role_permissions`
--

INSERT INTO `role_permissions` (`id`, `role`, `permission`) VALUES
(1, 'Admin', 'create_content'),
(3, 'Admin', 'delete_content'),
(2, 'Admin', 'edit_content'),
(4, 'Admin', 'manage_users'),
(5, 'Admin', 'system_settings'),
(6, 'Moderator', 'create_content'),
(8, 'Moderator', 'delete_content'),
(7, 'Moderator', 'edit_content'),
(9, 'User', 'create_content');

-- --------------------------------------------------------

--
-- Table structure for table `room_message`
--

CREATE TABLE `room_message` (
  `id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `content` text NOT NULL,
  `timestamp` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `system_info`
--

CREATE TABLE `system_info` (
  `id` int(11) NOT NULL,
  `version` varchar(50) NOT NULL,
  `last_backup` datetime DEFAULT NULL,
  `last_optimization` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `system_info`
--

INSERT INTO `system_info` (`id`, `version`, `last_backup`, `last_optimization`) VALUES
(1, '1.0.0', '2025-04-02 16:13:13', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `system_settings`
--

CREATE TABLE `system_settings` (
  `id` int(11) NOT NULL,
  `setting_name` varchar(100) NOT NULL,
  `setting_value` text NOT NULL,
  `category` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `system_settings`
--

INSERT INTO `system_settings` (`id`, `setting_name`, `setting_value`, `category`) VALUES
(1, 'site_name', 'Creative Showcase', 'general'),
(2, 'site_url', 'http://localhost:5000', 'general'),
(3, 'timezone', 'UTC', 'general'),
(4, 'date_format', 'YYYY-MM-DD', 'general'),
(5, 'maintenance_mode', '0', 'general'),
(6, 'user_registration', '1', 'general'),
(7, 'email_verification', '1', 'users'),
(8, 'admin_approval', '0', 'users'),
(9, 'captcha_registration', '1', 'users'),
(10, 'pre_moderation', '1', 'content'),
(11, 'auto_purge', '0', 'content'),
(12, 'max_file_size', '10', 'content'),
(13, 'items_per_page', '12', 'content'),
(14, 'brute_force_protection', '1', 'security'),
(15, 'two_factor_auth', '0', 'security'),
(16, 'failed_attempts', '5', 'security'),
(17, 'lockout_time', '30', 'security'),
(18, 'strong_passwords', '1', 'security'),
(19, 'min_password_length', '8', 'security'),
(20, 'password_expiry', '90', 'security'),
(21, 'smtp_host', '', 'email'),
(22, 'smtp_port', '587', 'email'),
(23, 'smtp_ssl', '1', 'email'),
(24, 'from_email', 'noreply@creativeshowcase.com', 'email'),
(25, 'from_name', 'Creative Showcase', 'email');

-- --------------------------------------------------------

--
-- Table structure for table `tag`
--
-- Error reading structure for table art_showcase.tag: #1932 - Table 'art_showcase.tag' doesn't exist in engine
-- Error reading data for table art_showcase.tag: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`tag`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `usernotificationsettings`
--
-- Error reading structure for table art_showcase.usernotificationsettings: #1932 - Table 'art_showcase.usernotificationsettings' doesn't exist in engine
-- Error reading data for table art_showcase.usernotificationsettings: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`usernotificationsettings`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `role` enum('Admin','Artist','Regular User') NOT NULL DEFAULT 'Regular User',
  `address` text DEFAULT NULL,
  `points` int(11) NOT NULL DEFAULT 0,
  `badges` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `bio` text DEFAULT NULL,
  `profile_picture` varchar(255) DEFAULT 'default_profile.png',
  `is_admin` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `last_login` datetime DEFAULT NULL,
  `status` enum('active','suspended','pending') NOT NULL DEFAULT 'active',
  `email_verified` tinyint(1) NOT NULL DEFAULT 0,
  `instagram` varchar(255) DEFAULT NULL,
  `twitter` varchar(255) DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `first_name`, `last_name`, `phone`, `role`, `address`, `points`, `badges`, `bio`, `profile_picture`, `is_admin`, `created_at`, `last_login`, `status`, `email_verified`, `instagram`, `twitter`, `website`) VALUES
(2, 'treble3', 'tryy@gmail.com', 'scrypt:32768:8:1$DBndxQITUVsuW40M$53f901f911738b2dcfe11da08f7b5bd887bbebd22c9e97f9f957e99961f45493dba3ff71f131fb48d02ede9e006999aca81aa69a39cdd7d68e937217c013de18', 'Tamika', 'Chasira', '1234567891', 'Artist', '12 Address', 180, '', 'One Two Three', 'profile_pics/user_2_1745232206.jpg', 0, '2025-04-05 16:03:11', NULL, 'active', 0, NULL, NULL, NULL),
(3, 'tyno25', 'appy@mail.com', 'scrypt:32768:8:1$ggnP4vX6eRUsvGHZ$8d73b563bab5abf9888b0e19a8460c6d620362b19465372276f6c08e86a9aba06727715282ee6f32396d1171e854fd60070dd85fb65bcbbc081eeb87f16e9bd6', 'Happy', 'Tembo', '0203419613', 'Regular User', '12 Address', 0, '', 'oK', 'profile_pics/user_3_1743731562.jpeg', 0, '2025-04-08 10:09:29', NULL, 'active', 0, NULL, NULL, NULL),
(6, 'smuggerteey', 'tynochagka@gmail.com', 'scrypt:32768:8:1$dS5ZOq3wq31nb3np$821fd67a6a9269db3dcf591c832fb33f77c12b05ebd3afc2ce16a60ef0bc17d2c7d18962f13f774a216b5c01b74c5598667672325a6f0fec83e36b68cb0b9a49', 'Teeno', 'Chagaka', '0780660853', 'Admin', 'Harare, Zimbabwe', 0, '', 'wow!!!', 'profile_pics/user_6_1744032152.jpeg', 0, '2025-04-07 13:21:17', NULL, 'active', 0, NULL, NULL, NULL),
(10, 'onemore', 'onemore@gmail.com', 'scrypt:32768:8:1$XZO9IJRAYhhb65KJ$b90411c7218a69523cf84bb673be154408a91388bc3b4ff7aee10a6f4d0d0621f124a70be2957c0ef86ce897f646ee720f81fbbd601f2bc96a792065b9f0bfbd', 'Oney', 'Morey', '660897778', 'Artist', 'Djibout', 0, '', 'Welcomes You', 'profile_pics/user_10_1745747708.png', 0, '2025-04-08 10:09:29', NULL, 'active', 0, NULL, NULL, NULL),
(18, 'first22', 'weeejjjf@gmail.com', 'scrypt:32768:8:1$ethCs2OsVJ440J2v$11f660e463de2451724f38c7bb7e57912c0b9c979f099f25ff178698e45a58f22caa44015addc156dfb93e0b1d2b60dde011389b9ef7181919cf6f3ae6ab927d', 'First', 'Trial', '123567899', 'Regular User', '12 Accra', 0, '', 'None', 'profile_pics/user_18_1745231704.jpeg', 0, '2025-04-20 17:33:20', NULL, 'active', 0, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `user_badges`
--
-- Error reading structure for table art_showcase.user_badges: #1932 - Table 'art_showcase.user_badges' doesn't exist in engine
-- Error reading data for table art_showcase.user_badges: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`user_badges`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `user_interactions`
--

CREATE TABLE `user_interactions` (
  `id` int(11) NOT NULL,
  `user_id` varchar(100) DEFAULT NULL,
  `page_name` varchar(255) DEFAULT NULL,
  `interaction_type` varchar(50) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_interactions`
--

INSERT INTO `user_interactions` (`id`, `user_id`, `page_name`, `interaction_type`, `timestamp`) VALUES
(1, 'guest', 'Home Page', 'visit', '2025-03-24 14:37:35'),
(2, 'guest', 'Home Page', 'visit', '2025-03-24 14:40:50'),
(3, 'guest', 'Home Page', 'visit', '2025-03-26 23:45:37'),
(4, 'guest', 'Home Page', 'visit', '2025-03-27 03:43:34'),
(5, 'guest', 'Home Page', 'visit', '2025-03-28 12:31:07'),
(6, 'guest', 'Home Page', 'visit', '2025-03-29 11:22:00'),
(7, 'guest', 'Home Page', 'visit', '2025-03-30 21:20:40'),
(8, 'guest', 'Home Page', 'visit', '2025-03-30 21:20:45'),
(9, 'guest', 'Home Page', 'visit', '2025-03-31 14:06:59'),
(10, 'guest', 'Home Page', 'visit', '2025-03-31 14:07:27'),
(11, 'guest', 'Home Page', 'visit', '2025-03-31 14:08:42'),
(12, 'guest', 'Home Page', 'visit', '2025-03-31 14:10:03'),
(13, 'guest', 'Home Page', 'visit', '2025-03-31 15:47:09'),
(14, 'guest', 'Home Page', 'visit', '2025-03-31 15:55:52'),
(15, 'guest', 'Analytics Page', 'visit', '2025-03-31 15:56:16'),
(16, 'guest', 'Analytics Page', 'visit', '2025-03-31 15:56:56'),
(17, 'guest', 'Analytics Page', 'visit', '2025-03-31 16:03:35'),
(18, 'guest', 'Analytics Page', 'visit', '2025-03-31 16:04:16'),
(1, 'guest', 'Home Page', 'visit', '2025-03-24 14:37:35'),
(2, 'guest', 'Home Page', 'visit', '2025-03-24 14:40:50'),
(3, 'guest', 'Home Page', 'visit', '2025-03-26 23:45:37'),
(4, 'guest', 'Home Page', 'visit', '2025-03-27 03:43:34'),
(5, 'guest', 'Home Page', 'visit', '2025-03-28 12:31:07'),
(6, 'guest', 'Home Page', 'visit', '2025-03-29 11:22:00'),
(7, 'guest', 'Home Page', 'visit', '2025-03-30 21:20:40'),
(8, 'guest', 'Home Page', 'visit', '2025-03-30 21:20:45'),
(9, 'guest', 'Home Page', 'visit', '2025-03-31 14:06:59'),
(10, 'guest', 'Home Page', 'visit', '2025-03-31 14:07:27'),
(11, 'guest', 'Home Page', 'visit', '2025-03-31 14:08:42'),
(12, 'guest', 'Home Page', 'visit', '2025-03-31 14:10:03'),
(13, 'guest', 'Home Page', 'visit', '2025-03-31 15:47:09'),
(14, 'guest', 'Home Page', 'visit', '2025-03-31 15:55:52'),
(15, 'guest', 'Analytics Page', 'visit', '2025-03-31 15:56:16'),
(16, 'guest', 'Analytics Page', 'visit', '2025-03-31 15:56:56'),
(17, 'guest', 'Analytics Page', 'visit', '2025-03-31 16:03:35'),
(18, 'guest', 'Analytics Page', 'visit', '2025-03-31 16:04:16');

-- --------------------------------------------------------

--
-- Table structure for table `videos`
--
-- Error reading structure for table art_showcase.videos: #1932 - Table 'art_showcase.videos' doesn't exist in engine
-- Error reading data for table art_showcase.videos: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`videos`' at line 1

-- --------------------------------------------------------

--
-- Table structure for table `views`
--

CREATE TABLE `views` (
  `id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `view_date` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `visitor_stats`
--
-- Error reading structure for table art_showcase.visitor_stats: #1932 - Table 'art_showcase.visitor_stats' doesn't exist in engine
-- Error reading data for table art_showcase.visitor_stats: #1064 - You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'FROM `art_showcase`.`visitor_stats`' at line 1

--
-- Indexes for dumped tables
--

--
-- Indexes for table `allowed_file_types`
--
ALTER TABLE `allowed_file_types`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `file_type` (`file_type`);

--
-- Indexes for table `artist_followers`
--
ALTER TABLE `artist_followers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `artist_id` (`artist_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `artist_likes`
--
ALTER TABLE `artist_likes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_like` (`artist_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `artist_ratings`
--
ALTER TABLE `artist_ratings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_rating` (`artist_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `artist_verification`
--
ALTER TABLE `artist_verification`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`),
  ADD KEY `reviewer_id` (`reviewer_id`);

--
-- Indexes for table `artwork`
--
ALTER TABLE `artwork`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `original_upload_id` (`original_upload_id`);

--
-- Indexes for table `purchases`
--
ALTER TABLE `purchases`
  ADD PRIMARY KEY (`id`),
  ADD KEY `buyer_id` (`buyer_id`),
  ADD KEY `artwork_id` (`artwork_id`);

--
-- Indexes for table `receipts`
--
ALTER TABLE `receipts`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `receipt_number` (`receipt_number`),
  ADD KEY `purchase_id` (`purchase_id`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `reporter_id` (`reporter_id`),
  ADD KEY `reported_artwork_id` (`reported_artwork_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_role` (`role`),
  ADD KEY `idx_status` (`status`);
ALTER TABLE `users` ADD FULLTEXT KEY `ft_search` (`username`,`email`,`first_name`,`last_name`);

--
-- Indexes for table `views`
--
ALTER TABLE `views`
  ADD PRIMARY KEY (`id`),
  ADD KEY `artwork_id` (`artwork_id`),
  ADD KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `artist_followers`
--
ALTER TABLE `artist_followers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `artist_likes`
--
ALTER TABLE `artist_likes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `artist_ratings`
--
ALTER TABLE `artist_ratings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `artwork`
--
ALTER TABLE `artwork`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=76;

--
-- AUTO_INCREMENT for table `purchases`
--
ALTER TABLE `purchases`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=58;

--
-- AUTO_INCREMENT for table `receipts`
--
ALTER TABLE `receipts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=58;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `views`
--
ALTER TABLE `views`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `artist_followers`
--
ALTER TABLE `artist_followers`
  ADD CONSTRAINT `artist_followers_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `artist_followers_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `artist_likes`
--
ALTER TABLE `artist_likes`
  ADD CONSTRAINT `artist_likes_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `artist_likes_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `artist_ratings`
--
ALTER TABLE `artist_ratings`
  ADD CONSTRAINT `artist_ratings_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `artist_ratings_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `artwork`
--
ALTER TABLE `artwork`
  ADD CONSTRAINT `artwork_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `artwork_ibfk_2` FOREIGN KEY (`original_upload_id`) REFERENCES `artwork` (`id`);

--
-- Constraints for table `purchases`
--
ALTER TABLE `purchases`
  ADD CONSTRAINT `purchases_ibfk_1` FOREIGN KEY (`buyer_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `purchases_ibfk_2` FOREIGN KEY (`artwork_id`) REFERENCES `artwork` (`id`);

--
-- Constraints for table `receipts`
--
ALTER TABLE `receipts`
  ADD CONSTRAINT `receipts_ibfk_1` FOREIGN KEY (`purchase_id`) REFERENCES `purchases` (`id`);

--
-- Constraints for table `reports`
--
ALTER TABLE `reports`
  ADD CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`reporter_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `reports_ibfk_2` FOREIGN KEY (`reported_artwork_id`) REFERENCES `artworks` (`id`);

--
-- Constraints for table `views`
--
ALTER TABLE `views`
  ADD CONSTRAINT `views_ibfk_1` FOREIGN KEY (`artwork_id`) REFERENCES `artwork` (`id`),
  ADD CONSTRAINT `views_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
