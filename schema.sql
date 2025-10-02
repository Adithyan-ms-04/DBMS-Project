-- Drop database if it exists (optional, for clean setup)
DROP DATABASE IF EXISTS fprms;

-- Create database
CREATE DATABASE fprms;

-- Use database
USE fprms;

-- ==========================
-- USERS TABLE
-- ==========================
CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Role ENUM('freelancer','client','admin') NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- FREELANCER PROFILE
-- ==========================
CREATE TABLE Freelancer_Profile (
    FreelancerID INT PRIMARY KEY,
    Skills TEXT NOT NULL,
    Experience TEXT NULL,
    PortfolioURL VARCHAR(255) NULL,
    FOREIGN KEY (FreelancerID) REFERENCES Users(UserID)
);

-- ==========================
-- PROJECTS TABLE
-- ==========================
CREATE TABLE Projects (
    ProjectID INT PRIMARY KEY AUTO_INCREMENT,
    ClientID INT,
    Title VARCHAR(150) NOT NULL,
    Description TEXT NOT NULL,
    Budget DECIMAL(10,2) NOT NULL,
    Status ENUM('open','in_progress','completed','cancelled') DEFAULT 'open',
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ClientID) REFERENCES Users(UserID)
);

-- ==========================
-- BIDS TABLE
-- ==========================
CREATE TABLE Bids (
    BidID INT PRIMARY KEY AUTO_INCREMENT,
    ProjectID INT,
    FreelancerID INT,
    BidAmount DECIMAL(10,2) NOT NULL,
    CoverLetter TEXT NULL,
    BidDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
    FOREIGN KEY (FreelancerID) REFERENCES Users(UserID)
);

-- ==========================
-- MILESTONES TABLE
-- ==========================
CREATE TABLE Milestones (
    MilestoneID INT PRIMARY KEY AUTO_INCREMENT,
    ProjectID INT,
    Title VARCHAR(150) NOT NULL,
    Description TEXT NULL,
    Status ENUM('pending','submitted','approved','rejected') DEFAULT 'pending',
    DueDate DATE NULL,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
);

-- ==========================
-- REVIEWS TABLE
-- ==========================
CREATE TABLE Reviews (
    ReviewID INT PRIMARY KEY AUTO_INCREMENT,
    ReviewerID INT,
    RevieweeID INT,
    ProjectID INT,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    Comment TEXT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ReviewerID) REFERENCES Users(UserID),
    FOREIGN KEY (RevieweeID) REFERENCES Users(UserID),
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
);

-- ==========================
-- SAMPLE DATA (Optional)
-- ==========================
INSERT INTO Users (Name, Email, Password, Role) VALUES
('Alice Client', 'alice@example.com', 'alice123', 'client'),
('Bob Freelancer', 'bob@example.com', 'bob123', 'freelancer'),
('Charlie Admin', 'charlie@example.com', 'charlie123', 'admin');

INSERT INTO Freelancer_Profile (FreelancerID, Skills, Experience, PortfolioURL) VALUES
(2, 'Python, Flask, SQL', '3 years experience in web development', 'http://portfolio-bob.com');

INSERT INTO Projects (ClientID, Title, Description, Budget, Status) VALUES
(1, 'Build a Freelance Management System', 'A system to manage projects, bids, and reviews.', 5000.00, 'open');

INSERT INTO Bids (ProjectID, FreelancerID, BidAmount, CoverLetter) VALUES
(1, 2, 4500.00, 'I have built similar systems before and can deliver quality.');

INSERT INTO Milestones (ProjectID, Title, Description, Status, DueDate) VALUES
(1, 'Database Setup', 'Design and implement database schema.', 'pending', '2025-10-15');

INSERT INTO Reviews (ReviewerID, RevieweeID, ProjectID, Rating, Comment) VALUES
(1, 2, 1, 5, 'Great work, delivered on time!');
