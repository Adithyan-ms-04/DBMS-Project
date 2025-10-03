from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.String(20), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_id(self):
        return str(self.UserID)

class FreelancerProfile(db.Model):
    __tablename__ = 'Freelancer_Profile'
    FreelancerID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), primary_key=True)
    Skills = db.Column(db.Text, nullable=False)
    Experience = db.Column(db.Text)
    PortfolioURL = db.Column(db.String(255))

class Project(db.Model):
    __tablename__ = 'Projects'
    ProjectID = db.Column(db.Integer, primary_key=True)
    ClientID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    Title = db.Column(db.String(150), nullable=False)
    Description = db.Column(db.Text, nullable=False)
    Budget = db.Column(db.Numeric(10, 2), nullable=False)
    Status = db.Column(db.String(20), default='open')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Deadline = db.Column(db.Date, nullable=True)
    
    # Relationships
    client = db.relationship('User', foreign_keys=[ClientID])
    bids = db.relationship('Bid', backref='project', lazy=True)
    milestones = db.relationship('Milestone', backref='project', lazy=True)

class Bid(db.Model):
    __tablename__ = 'Bids'
    BidID = db.Column(db.Integer, primary_key=True)
    ProjectID = db.Column(db.Integer, db.ForeignKey('Projects.ProjectID'), nullable=False)
    FreelancerID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    BidAmount = db.Column(db.Numeric(10, 2), nullable=False)
    CoverLetter = db.Column(db.Text)
    DeliveryTime = db.Column(db.String(50))  # e.g., "2 weeks", "1 month"
    BidDate = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    
    # Relationships
    freelancer = db.relationship('User', foreign_keys=[FreelancerID])

class Milestone(db.Model):
    __tablename__ = 'Milestones'
    MilestoneID = db.Column(db.Integer, primary_key=True)
    ProjectID = db.Column(db.Integer, db.ForeignKey('Projects.ProjectID'), nullable=False)
    Title = db.Column(db.String(150), nullable=False)
    Description = db.Column(db.Text)
    Amount = db.Column(db.Numeric(10, 2), nullable=False)
    Status = db.Column(db.String(20), default='pending')
    DueDate = db.Column(db.Date)

class Review(db.Model):
    __tablename__ = 'Reviews'
    ReviewID = db.Column(db.Integer, primary_key=True)
    ReviewerID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    RevieweeID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    ProjectID = db.Column(db.Integer, db.ForeignKey('Projects.ProjectID'), nullable=False)
    Rating = db.Column(db.Integer, nullable=False)
    Comment = db.Column(db.Text)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[ReviewerID])
    reviewee = db.relationship('User', foreign_keys=[RevieweeID])
    project = db.relationship('Project', foreign_keys=[ProjectID])