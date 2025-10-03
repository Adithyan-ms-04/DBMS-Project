from app import app, db
from models import User, Project, Bid, Milestone

def migrate_database():
    with app.app_context():
        try:
            print("Starting database migration...")
            
            # Check if columns exist and add them if they don't
            from sqlalchemy import text
            
            # Add Deadline to Projects if it doesn't exist
            try:
                db.session.execute(text("SELECT Deadline FROM Projects LIMIT 1"))
                print("✅ Projects.Deadline column already exists")
            except Exception as e:
                if "Unknown column" in str(e):
                    print("Adding Deadline column to Projects table...")
                    db.session.execute(text("ALTER TABLE Projects ADD COLUMN Deadline DATE NULL"))
                    print("✅ Added Deadline column to Projects")
            
            # Add DeliveryTime to Bids if it doesn't exist
            try:
                db.session.execute(text("SELECT DeliveryTime FROM Bids LIMIT 1"))
                print("✅ Bids.DeliveryTime column already exists")
            except Exception as e:
                if "Unknown column" in str(e):
                    print("Adding DeliveryTime column to Bids table...")
                    db.session.execute(text("ALTER TABLE Bids ADD COLUMN DeliveryTime VARCHAR(50) NULL"))
                    print("✅ Added DeliveryTime column to Bids")
            
            # Add Status to Bids if it doesn't exist
            try:
                db.session.execute(text("SELECT Status FROM Bids LIMIT 1"))
                print("✅ Bids.Status column already exists")
            except Exception as e:
                if "Unknown column" in str(e):
                    print("Adding Status column to Bids table...")
                    db.session.execute(text("ALTER TABLE Bids ADD COLUMN Status VARCHAR(20) DEFAULT 'pending'"))
                    print("✅ Added Status column to Bids")
            
            # Add Amount to Milestones if it doesn't exist
            try:
                db.session.execute(text("SELECT Amount FROM Milestones LIMIT 1"))
                print("✅ Milestones.Amount column already exists")
            except Exception as e:
                if "Unknown column" in str(e):
                    print("Adding Amount column to Milestones table...")
                    db.session.execute(text("ALTER TABLE Milestones ADD COLUMN Amount DECIMAL(10,2) NULL"))
                    print("✅ Added Amount column to Milestones")
            
            db.session.commit()
            print("🎉 Database migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration error: {e}")

if __name__ == '__main__':
    migrate_database()