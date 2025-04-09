-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 08, 2025 at 12:18 PM
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
(1, 'hhhh', 'jhhghhgh hhhh hhhh hhhhhh', 133.00, 'portrait, landscape, digital, minimalist', 'static/uploads\\WOWW.png', 2, '2c9ceecd717904cc3c4f84c9a380631fda18db683893729e744dc1c3c3c94b96', '7e9e003800313830', 'painting', NULL, 2, 0, 1, '2025-04-07 12:40:55'),
(2, 'hhhhh', 'hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh', 12.00, 'portrait, landscape, digital, minimalist', 'static/uploads\\diagram-export-01-04-2025-19_13_03.png', 2, 'afc8977317fbeabed74192d15308f8a0b58723b529fa5bbdea5a65d4de190000', '18b4f4303f0d040c', 'painting', NULL, 0, 0, 1, '2025-04-07 12:53:29'),
(18, 'tg', 'gfbg', 455.00, 'fdvv', 'static/uploads\\rwee-removebg.png', 2, 'b4dc0d91fe841f29f1a0422e82d464e7d9387d2952e934c18446cad046e89f94', NULL, 'other', NULL, 0, 0, 1, '2025-03-27 17:05:23'),
(20, 'win', 'Win for winnerssssss', 20.00, 'modern, portrait, landscape', 'static/uploads\\Takatsamwa_Riddim_Demo_Dankillah_Records_263778909032__Ethical_Records_263774293061.mp3', 10, 'f2426cbacfe28b2c382482312f45f4056619ee65a9f0c16215a2fb785567e318', NULL, 'music', NULL, 0, 0, 1, '2025-03-29 12:42:45'),
(21, 'testtest', 'No story to tell now', 2.00, 'landscape, digital, minimalist, surreal', 'static/uploads\\image3.jpeg', 10, 'db4af2ebddf82b492490e21e48c414f7803ee9bae8b84bb971e98c5a1715fb61', NULL, 'other', NULL, 0, 0, 1, '2025-03-29 12:44:30'),
(22, 'artwork', 'test artwork for etc', 30.00, 'abstract, modern, portrait, landscape', 'static/uploads\\WhatsApp_Image_2025-01-23_at_22.23.51.jpeg', 2, '3c37d7ad649a1dfdec8f24a89d9ca684bdd7b43525cac8e781bec9528a7cef45', NULL, 'digital', NULL, 0, 0, 1, '2025-03-31 22:57:26'),
(25, 'myown', 'lets see how it goes hmmmmmmm', 20.00, 'abstract, modern, portrait, landscape', 'static/uploads\\diagram-export-01-04-2025-17_16_10.png', 2, '0e3eacad8e59e260dfefa0bf4f6a17e2ed5033961ada6622e9206528783015fc', NULL, 'painting', NULL, 0, 0, 1, '2025-04-02 02:13:08'),
(26, 'ggg', 'ghzthngn ckui76 jrdii', 23.00, 'portrait, landscape, digital, minimalist', 'static/uploads\\Zimbabwe.png', 2, '2c9ceecd717904cc3c4f84c9a380631fda18db683893729e744dc1c3c3c94b96', NULL, 'digital', NULL, 0, 0, 1, '2025-04-02 02:14:28'),
(27, 'ttt', 't65gy5bbhmkdhngdkl gkt5mktrnbkrtb', 34.00, 'modern, portrait, landscape, digital, minimalist', 'static/uploads\\diagram-export-01-04-2025-19_08_13.png', 2, '8c00f95a3b8b93dec9ca45b199b2a438a838eef60b1a9cade386a2a104a651a6', NULL, 'painting', NULL, 0, 0, 1, '2025-04-03 19:34:58'),
(28, 'tnjumn5mn', ' hojonm 0ulthbp[f\" 0hmormnb[', 43.00, 'landscape, digital, minimalist', 'static/uploads\\P_W_-_Kwaari_kuApplyer_kwacho_vachaonerera.mp4', 2, '9e5b8f9b85f319ef350f7e4b5dbc8e9fef38426b3d822d92048e67ab27beec9a', NULL, 'painting', NULL, 0, 0, 1, '2025-04-03 19:57:48'),
(29, 'Test Art', 'Test description', 100.00, 'test, art', 'static/uploads\\fail.wav', 15, '9cbc1b707ece0190d16b34e0690d62a628f391990bc229506e8449d5ba9eb245', NULL, 'Digital', NULL, 0, 0, 1, '2025-04-06 14:16:17'),
(30, 'Test Art', 'Test description', 100.00, 'test, art', 'static/uploads\\ashesi_drawing_sample.png', 15, '32b83e7a236d5ed63377b5ceec46cd8bf0ff30393102557ec699e77b731c31df', NULL, 'Digital', NULL, 0, 0, 1, '2025-04-06 14:18:00'),
(31, 'Test Art', 'Test description', 100.00, 'test, art', 'static/uploads\\image4.jpeg', 15, '907126b4770227cfc061206d498abf0992535bb4672c375df8f63794f9000f32', NULL, 'Digital', NULL, 0, 0, 1, '2025-04-06 14:18:27');

-- --------------------------------------------------------

--
-- Table structure for table `artwork_ownership`
--

CREATE TABLE `artwork_ownership` (
  `id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `is_original_owner` tinyint(1) DEFAULT 0,
  `purchase_proof` varchar(255) DEFAULT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `artwork_tags`
--

CREATE TABLE `artwork_tags` (
  `artwork_id` int(11) NOT NULL,
  `tag_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `artwork_upload_history`
--

CREATE TABLE `artwork_upload_history` (
  `id` int(11) NOT NULL,
  `artwork_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `upload_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `backups`
--

CREATE TABLE `backups` (
  `id` int(11) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `backup_type` varchar(20) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `created_by` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
(1, 'Nature Photography', 'Capture the beauty of nature in your own style.', '2025-09-26', 50),
(2, 'Abstract Art.', 'Create an abstract piece using bold colors.', '2025-04-15', 300),
(3, 'Digital Illustration', 'Design a digital artwork based on a theme of your choice.', '2025-05-30', 500),
(5, 'singing', 'sing', '2025-04-02', 200);

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
(1, 'tyno25', 531, '2025-03-23 19:16:56'),
(2, 'treble3', 1473, '2025-03-23 19:19:24'),
(3, 'smuggerteey', 20, '2025-03-23 19:46:07'),
(4, 'onemore', 331, '2025-03-28 08:11:15');

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

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `message` text NOT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `notification_type` enum('system','artwork','message','purchase','challenge') NOT NULL,
  `related_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `payment`
--

CREATE TABLE `payment` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `currency` varchar(3) DEFAULT NULL,
  `payment_method` varchar(50) NOT NULL,
  `transaction_id` varchar(100) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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

CREATE TABLE `tag` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `slug` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `usernotificationsettings`
--

CREATE TABLE `usernotificationsettings` (
  `user_id` int(11) NOT NULL,
  `email_notifications` tinyint(1) DEFAULT 1,
  `push_notifications` tinyint(1) DEFAULT 1,
  `in_app_notifications` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
  `email_verified` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `first_name`, `last_name`, `phone`, `role`, `address`, `points`, `badges`, `bio`, `profile_picture`, `is_admin`, `created_at`, `last_login`, `status`, `email_verified`) VALUES
(1, 'admin', 'admin@example.com', 'admin123', 'Tinotenda', 'Chagaka', '0203419613', 'Regular User', '12 Address', 0, '', 'Wow!!', 'profile_pics/user_1_1743795431.jpeg', 1, '2025-04-05 15:29:02', NULL, 'active', 0),
(2, 'treble3', 'tryy@gmail.com', 'scrypt:32768:8:1$DBndxQITUVsuW40M$53f901f911738b2dcfe11da08f7b5bd887bbebd22c9e97f9f957e99961f45493dba3ff71f131fb48d02ede9e006999aca81aa69a39cdd7d68e937217c013de18', 'Tamika', 'Chasira', '1234567891', 'Artist', '12 Address', 180, '', 'One Two Three', 'profile_pics/user_2_1743759284.jpeg', 0, '2025-04-05 16:03:11', NULL, 'active', 0),
(3, 'tyno25', 'appy@mail.com', 'scrypt:32768:8:1$ggnP4vX6eRUsvGHZ$8d73b563bab5abf9888b0e19a8460c6d620362b19465372276f6c08e86a9aba06727715282ee6f32396d1171e854fd60070dd85fb65bcbbc081eeb87f16e9bd6', 'Happy', 'Tembo', '0203419613', 'Regular User', '12 Address', 0, '', 'oK', 'profile_pics/user_3_1743731562.jpeg', 0, '2025-04-08 10:09:29', NULL, 'active', 0),
(4, 'werr333', 'weeee@gmail.com', 'scrypt:32768:8:1$NRoqguz16PNnql8s$c9cf9b608086b4bd47f3be05ebeb850c64038c057b95f402f299c0fdfedf0af73d77b8441f60bf994b9ab73472331444cdb79a42ec84e3a0413b1851f30c622d', 'Ten', 'Eleven', '0203419613', 'Regular User', 'Accra', 0, '', NULL, NULL, 0, '2025-04-08 10:09:29', NULL, 'active', 0),
(6, 'smuggerteey', 'tynochagka@gmail.com', 'scrypt:32768:8:1$dS5ZOq3wq31nb3np$821fd67a6a9269db3dcf591c832fb33f77c12b05ebd3afc2ce16a60ef0bc17d2c7d18962f13f774a216b5c01b74c5598667672325a6f0fec83e36b68cb0b9a49', 'Teeno', 'Chagaka', '0780660853', 'Artist', 'Harare, Zimbabwe', 0, '', 'wow!!!', 'profile_pics/user_6_1744032152.jpeg', 0, '2025-04-07 13:21:17', NULL, 'active', 0),
(7, 'tamik2', 'tamika@gmail.com', 'scrypt:32768:8:1$KQMCZXnONdEho7il$1bc73732eb06369ce6bd83091db531f7d56f7c03c6267f94280472e99dbc3b2db0d115a93715fa4aabcecfb2b6b30bd6f759ec70c07fc5c9125853331c0c5aa5', 'Tamika', 'Temu', '0780660853', 'Regular User', 'Accra, Ghana', 0, '', 'One Two', 'profile_pics/user_7_1744033005.png', 0, '2025-04-07 13:35:58', NULL, 'active', 0),
(10, 'onemore', 'onemore@gmail.com', 'scrypt:32768:8:1$XZO9IJRAYhhb65KJ$b90411c7218a69523cf84bb673be154408a91388bc3b4ff7aee10a6f4d0d0621f124a70be2957c0ef86ce897f646ee720f81fbbd601f2bc96a792065b9f0bfbd', 'Oney', 'Morey', '660897778', 'Artist', 'Djibout', 0, '', NULL, NULL, 0, '2025-04-08 10:09:29', NULL, 'active', 0),
(11, 'letstry', 'letus@gmail.com', 'scrypt:32768:8:1$ZMM5X2rUupuzoIHK$9f75f592f349afba502894a6e408429b5b784e7496a3a48f899c00a6ac9ffb556c160b7c38e38828ea3958e26f1023c389210880ceb62c3d290bed106965ca86', 'Letus', 'Tryit', '080808008', 'Artist', 'Burundi', 0, '', NULL, NULL, 0, '2025-04-08 10:09:29', NULL, 'active', 0),
(12, 'wangu33', 'welling@gmail.com', 'scrypt:32768:8:1$T2Tx5dqis8Dlh7YM$4a7cbafd9356a1a44ed2b55c43966240509e53d9aa525052096464b5925b68f7e69fe36bc70ea597138f78da0a7cbdedc1af69c8cbf925f72e6014bf2b60aa3e', 'Wellington', 'Mukuuu', '0780660055', 'Artist', 'Harare, Zimbabwe', 0, '', NULL, NULL, 0, '2025-04-08 10:09:29', NULL, 'active', 0),
(13, 'manual2', 'manmakasaa@gmail.com', 'scrypt:32768:8:1$y0q5FZAEd8nwBz32$e66edabd9bcfa2b517c329e3e6054b62186e0e29a07ac492d90253307f7ea8ce159ff32377fdc6e220175e87645bd833ef53e4803a93b7ac35ec8899e86d11f6', 'Manuel', 'Makassa', '203419613', 'Artist', 'Accra, Ghana', 0, '', NULL, NULL, 0, '2025-04-08 10:09:29', NULL, 'active', 0),
(15, 'testuser', 'test@example.com', 'scrypt:32768:8:1$PDeB8V4Szo27Z48J$5473b03fe8476b9f5bb35fc19b6ec12175f35615e434058d59e3b6b483f2a1b5d11ba67e9e74818aec141b055c02d51f8d86cb6b2ac593362c7e7d3ea9e38e90', 'Test', 'User', '1234567890', 'Artist', '123 Test St', 0, '', NULL, NULL, 0, '2025-04-08 10:09:29', NULL, 'active', 0);

-- --------------------------------------------------------

--
-- Table structure for table `user_badges`
--

CREATE TABLE `user_badges` (
  `user_id` int(11) NOT NULL,
  `badge_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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

CREATE TABLE `videos` (
  `id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `video_data` longblob NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `visitor_stats`
--

CREATE TABLE `visitor_stats` (
  `id` int(11) NOT NULL,
  `date` date NOT NULL,
  `visitor_count` int(11) DEFAULT 0,
  `unique_visitors` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
-- Indexes for table `artwork_ownership`
--
ALTER TABLE `artwork_ownership`
  ADD PRIMARY KEY (`id`),
  ADD KEY `artwork_id` (`artwork_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `artwork_upload_history`
--
ALTER TABLE `artwork_upload_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `artwork_id` (`artwork_id`),
  ADD KEY `user_id` (`user_id`);

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
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `artwork`
--
ALTER TABLE `artwork`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `artwork_ownership`
--
ALTER TABLE `artwork_ownership`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `artwork_upload_history`
--
ALTER TABLE `artwork_upload_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `artwork`
--
ALTER TABLE `artwork`
  ADD CONSTRAINT `artwork_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `artwork_ibfk_2` FOREIGN KEY (`original_upload_id`) REFERENCES `artwork` (`id`);

--
-- Constraints for table `artwork_ownership`
--
ALTER TABLE `artwork_ownership`
  ADD CONSTRAINT `artwork_ownership_ibfk_1` FOREIGN KEY (`artwork_id`) REFERENCES `artwork` (`id`),
  ADD CONSTRAINT `artwork_ownership_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `artwork_upload_history`
--
ALTER TABLE `artwork_upload_history`
  ADD CONSTRAINT `artwork_upload_history_ibfk_1` FOREIGN KEY (`artwork_id`) REFERENCES `artwork` (`id`),
  ADD CONSTRAINT `artwork_upload_history_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
