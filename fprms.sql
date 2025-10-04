-- Create database
CREATE DATABASE IF NOT EXISTS fprms;
USE fprms;

-- Create Users table
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Role ENUM('client','freelancer','admin') NOT NULL
);

-- Create Projects table
CREATE TABLE Projects (
    ProjectID INT AUTO_INCREMENT PRIMARY KEY,
    ClientID INT NOT NULL,
    Title VARCHAR(200) NOT NULL,
    Description TEXT,
    Budget DECIMAL(10,2),
    Status ENUM('open','in-progress','completed') DEFAULT 'open',
    FOREIGN KEY (ClientID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Create Bids table
CREATE TABLE Bids (
    BidID INT AUTO_INCREMENT PRIMARY KEY,
    ProjectID INT NOT NULL,
    FreelancerID INT NOT NULL,
    BidAmount DECIMAL(10,2) NOT NULL,
    CoverLetter TEXT,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    FOREIGN KEY (FreelancerID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Create Milestones table
CREATE TABLE Milestones (
    MilestoneID INT AUTO_INCREMENT PRIMARY KEY,
    ProjectID INT NOT NULL,
    Title VARCHAR(200),
    Description TEXT,
    Status ENUM('pending','completed') DEFAULT 'pending',
    DueDate DATE,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE
);

-- Create Reviews table


-- Create default admin user
INSERT INTO Users (Name, Email, Password, Role)
VALUES ('Admin', 'admin@fprms.com', 
        '$pbkdf2:sha256$29000$z2sAfi5sF3Zqk3gC5PITcQ$G0c5c6ljFfN84Xf3iB5ZV7CqOULFMLqL5QH5Fl9f1Uk', 
        'admin');
-- (Password is hashed for "admin123")