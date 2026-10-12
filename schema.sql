-- SQL Schema for Email Automation Application
-- Target Database: MySQL 8.0+

CREATE DATABASE IF NOT EXISTS `harish`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `harish`;

-- Table: email_campaigns
-- Stores summary analytics for each bulk email campaign execution
CREATE TABLE IF NOT EXISTS `email_campaigns` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `subject` VARCHAR(255) NOT NULL,
    `total_attempted` INT NOT NULL,
    `successful` INT NOT NULL,
    `failed` INT NOT NULL,
    INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
