from app import app, db
from models import User, Project, Bid, FreelancerProfile, Milestone, Review
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def reset_database():
    with app.app_context():
        try:
            # Drop all tables
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating new tables...")
            db.create_all()
            
            # Create sample data
            print("Creating sample data...")
            
            # Create users
            client1 = User(
                Name='Alice Client',
                Email='alice@example.com',
                Password=generate_password_hash('alice123'),
                Role='client'
            )
            
            client2 = User(
                Name='David Client',
                Email='david@example.com',
                Password=generate_password_hash('david123'),
                Role='client'
            )
            
            freelancer1 = User(
                Name='Bob Freelancer', 
                Email='bob@example.com',
                Password=generate_password_hash('bob123'),
                Role='freelancer'
            )
            
            freelancer2 = User(
                Name='Eva Freelancer', 
                Email='eva@example.com',
                Password=generate_password_hash('eva123'),
                Role='freelancer'
            )
            
            admin = User(
                Name='Charlie Admin',
                Email='charlie@example.com', 
                Password=generate_password_hash('charlie123'),
                Role='admin'
            )
            
            db.session.add_all([client1, client2, freelancer1, freelancer2, admin])
            db.session.commit()
            
            # Create freelancer profiles with phone numbers
            profile1 = FreelancerProfile(
                FreelancerID=freelancer1.UserID,
                Skills='Python, Flask, SQL, Web Development',
                Experience='3 years experience in web development with Flask and Django',
                PortfolioURL='http://portfolio-bob.com',
                PhoneNumber='+1 (555) 123-4567'  # Added phone number
            )
            
            profile2 = FreelancerProfile(
                FreelancerID=freelancer2.UserID,
                Skills='JavaScript, React, Node.js, UI/UX Design',
                Experience='2 years experience in frontend development and design',
                PortfolioURL='http://portfolio-eva.com',
                PhoneNumber='+1 (555) 987-6543'  # Added phone number
            )
            
            db.session.add_all([profile1, profile2])
            
            # Create projects
            project1 = Project(
                ClientID=client1.UserID,
                Title='Build a Freelance Management System',
                Description='A comprehensive system to manage projects, bids, and reviews for freelancers and clients.',
                Budget=5000.00,
                Status='open'
            )
            
            project2 = Project(
                ClientID=client1.UserID,
                Title='E-commerce Website Development',
                Description='Need a responsive e-commerce website with payment integration and admin panel.',
                Budget=3000.00,
                Status='open'
            )
            
            project3 = Project(
                ClientID=client2.UserID,
                Title='Mobile App UI/UX Design',
                Description='Looking for a talented designer to create modern UI/UX for a fitness mobile app.',
                Budget=1500.00,
                Status='in_progress'
            )
            
            db.session.add_all([project1, project2, project3])
            db.session.commit()
            
            # Create bids
            bid1 = Bid(
                ProjectID=project1.ProjectID,
                FreelancerID=freelancer1.UserID,
                BidAmount=4500.00,
                CoverLetter='I have built similar systems before and can deliver quality work on time. I have 3 years of Flask experience.',
                Status='pending'
            )
            
            bid2 = Bid(
                ProjectID=project1.ProjectID,
                FreelancerID=freelancer2.UserID,
                BidAmount=4800.00,
                CoverLetter='I can create a modern, responsive system with great UI/UX. I have experience with both frontend and backend.',
                Status='pending'
            )
            
            bid3 = Bid(
                ProjectID=project2.ProjectID,
                FreelancerID=freelancer1.UserID,
                BidAmount=2800.00,
                CoverLetter='I specialize in e-commerce development and can complete this within 3 weeks.',
                Status='pending'
            )
            
            bid4 = Bid(
                ProjectID=project3.ProjectID,
                FreelancerID=freelancer2.UserID,
                BidAmount=1400.00,
                CoverLetter='I have designed multiple fitness apps and understand the user journey well.',
                Status='accepted'
            )
            
            db.session.add_all([bid1, bid2, bid3, bid4])
            
            # Create milestones with progress updates
            milestone1 = Milestone(
                ProjectID=project3.ProjectID,
                Title='Wireframe Design',
                Description='Create initial wireframes for all app screens',
                Status='completed',
                DueDate=datetime.now().date() - timedelta(days=7),
                Amount=500.00,
                ProgressUpdates="[2025-01-10 14:30]: Started working on wireframe concepts\n\n[2025-01-12 10:15]: Completed initial wireframes for all main screens"
            )
            
            milestone2 = Milestone(
                ProjectID=project3.ProjectID,
                Title='UI Design',
                Description='Design high-fidelity UI for all screens',
                Status='in_progress',
                DueDate=datetime.now().date() + timedelta(days=7),
                Amount=600.00,
                ProgressUpdates="[2025-01-15 14:30]: Started working on the main dashboard screen\n\n[2025-01-16 10:15]: Completed color scheme and typography selections"
            )
            
            milestone3 = Milestone(
                ProjectID=project3.ProjectID,
                Title='Final Delivery',
                Description='Deliver all design assets and style guide',
                Status='pending',
                DueDate=datetime.now().date() + timedelta(days=14),
                Amount=400.00
            )
            
            db.session.add_all([milestone1, milestone2, milestone3])
            
            # Create reviews
            review1 = Review(
                ProjectID=project3.ProjectID,
                ReviewerID=client2.UserID,
                RevieweeID=freelancer2.UserID,
                Rating=5,
                Comment='Excellent work! Very professional and delivered ahead of schedule.',
                CreatedAt=datetime.now() - timedelta(days=1)
            )
            
            review2 = Review(
                ProjectID=project1.ProjectID,
                ReviewerID=client1.UserID,
                RevieweeID=freelancer1.UserID,
                Rating=4,
                Comment='Good work, but there were some delays in communication.',
                CreatedAt=datetime.now() - timedelta(days=10)
            )
            
            db.session.add_all([review1, review2])
            db.session.commit()
            
            print("✅ Database reset successfully!")
            print("\n📋 Sample accounts created:")
            print("   Clients:")
            print("     - alice@example.com / alice123")
            print("     - david@example.com / david123")
            print("   Freelancers:")
            print("     - bob@example.com / bob123 (Phone: +1 (555) 123-4567)") 
            print("     - eva@example.com / eva123 (Phone: +1 (555) 987-6543)")
            print("   Admin: charlie@example.com / charlie123")
            print("\n📊 Sample Data:")
            print("   - 3 Projects (2 open, 1 in progress)")
            print("   - 4 Bids (3 pending, 1 accepted)")
            print("   - 3 Milestones with progress updates")
            print("   - 2 Reviews with ratings")
            print("\n🚀 Run 'python app.py' to start the application!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    reset_database()