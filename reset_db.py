from app import app, db
from models import User, Project, Bid, FreelancerProfile, Milestone, Review
from werkzeug.security import generate_password_hash

def reset_database():
    with app.app_context():
        # Drop all tables
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating new tables...")
        db.create_all()
        
        # Create sample data
        print("Creating sample data...")
        
        # Create users
        client = User(
            Name='Alice Client',
            Email='alice@example.com',
            Password=generate_password_hash('alice123'),
            Role='client'
        )
        
        freelancer = User(
            Name='Bob Freelancer', 
            Email='bob@example.com',
            Password=generate_password_hash('bob123'),
            Role='freelancer'
        )
        
        admin = User(
            Name='Charlie Admin',
            Email='charlie@example.com', 
            Password=generate_password_hash('charlie123'),
            Role='admin'
        )
        
        db.session.add_all([client, freelancer, admin])
        db.session.commit()
        
        # Create freelancer profile
        profile = FreelancerProfile(
            FreelancerID=freelancer.UserID,
            Skills='Python, Flask, SQL',
            Experience='3 years experience in web development',
            PortfolioURL='http://portfolio-bob.com'
        )
        db.session.add(profile)
        
        # Create project
        project = Project(
            ClientID=client.UserID,
            Title='Build a Freelance Management System',
            Description='A system to manage projects, bids, and reviews.',
            Budget=5000.00,
            Status='open'
        )
        db.session.add(project)
        db.session.commit()
        
        # Create bid (with CoverLetter column)
        bid = Bid(
            ProjectID=project.ProjectID,
            FreelancerID=freelancer.UserID,
            BidAmount=4500.00,
            CoverLetter='I have built similar systems before and can deliver quality.'
        )
        db.session.add(bid)
        
        # Create milestone
        milestone = Milestone(
            ProjectID=project.ProjectID,
            Title='Database Setup',
            Description='Design and implement database schema.',
            Status='pending',
            DueDate='2025-10-15'
        )
        db.session.add(milestone)
        
        # Create review
        review = Review(
            ReviewerID=client.UserID,
            RevieweeID=freelancer.UserID,
            ProjectID=project.ProjectID,
            Rating=5,
            Comment='Great work, delivered on time!'
        )
        db.session.add(review)
        
        db.session.commit()
        
        print("✅ Database reset successfully!")
        print("\nSample users created:")
        print("Client: alice@example.com / alice123")
        print("Freelancer: bob@example.com / bob123") 
        print("Admin: charlie@example.com / charlie123")

if __name__ == '__main__':
    reset_database()