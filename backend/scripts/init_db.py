"""
Database initialization script
Creates initial SuperAdmin user and sample club
"""
import sys
import os
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal, engine, Base
from app.models.models import User, Club, UserRole, ClubStatus
from app.core.security import hash_password


def init_database():
    """Initialize database with tables and seed data"""
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    db = SessionLocal()
    
    try:
        # Check if SuperAdmin already exists
        existing_admin = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        
        if existing_admin:
            print("⚠ SuperAdmin already exists, skipping initialization")
            return
        
        print("\nCreating SuperAdmin user...")
        
        # Create SuperAdmin
        superadmin = User(
            email="admin@clubmanagement.com",
            hashed_password=hash_password("admin123"),  # CHANGE IN PRODUCTION!
            full_name="System Administrator",
            role=UserRole.SUPERADMIN,
            club_id=None,  # SuperAdmin is not tied to any club
            is_active=True,
            is_verified=True
        )
        
        db.add(superadmin)
        db.commit()
        
        print("✓ SuperAdmin created")
        print(f"  Email: admin@clubmanagement.com")
        print(f"  Password: admin123")
        print("  ⚠️  CHANGE PASSWORD IN PRODUCTION!")
        
        # Create a sample club
        print("\nCreating sample club...")
        
        sample_club = Club(
            name="Demo Sports Club",
            contact_email="contact@demosportsclub.com",
            commission_percentage=5.0,
            status=ClubStatus.ACTIVE,
            phone="+1234567890",
            address="123 Sport Street, City, Country",
            primary_color="#0066cc"
        )
        
        db.add(sample_club)
        db.commit()
        db.refresh(sample_club)
        
        print(f"✓ Sample club created (ID: {sample_club.id})")
        print(f"  Name: {sample_club.name}")
        print(f"  Commission: {sample_club.commission_percentage}%")
        
        # Create club admin for sample club
        print("\nCreating club admin...")
        
        club_admin = User(
            email="admin@demosportsclub.com",
            hashed_password=hash_password("club123"),  # CHANGE IN PRODUCTION!
            full_name="Club Administrator",
            role=UserRole.CLUB_ADMIN,
            club_id=sample_club.id,
            is_active=True,
            is_verified=True
        )
        
        db.add(club_admin)
        db.commit()
        
        print("✓ Club admin created")
        print(f"  Email: admin@demosportsclub.com")
        print(f"  Password: club123")
        print("  ⚠️  CHANGE PASSWORD IN PRODUCTION!")
        
        # Create treasurer for sample club
        print("\nCreating treasurer...")
        
        treasurer = User(
            email="treasurer@demosportsclub.com",
            hashed_password=hash_password("treasurer123"),
            full_name="Club Treasurer",
            role=UserRole.TREASURER,
            club_id=sample_club.id,
            is_active=True,
            is_verified=True
        )
        
        db.add(treasurer)
        db.commit()
        
        print("✓ Treasurer created")
        print(f"  Email: treasurer@demosportsclub.com")
        print(f"  Password: treasurer123")
        
        print("\n" + "="*60)
        print("✅ Database initialization complete!")
        print("="*60)
        print("\nYou can now login with:")
        print("1. SuperAdmin: admin@clubmanagement.com / admin123")
        print("2. Club Admin: admin@demosportsclub.com / club123")
        print("3. Treasurer: treasurer@demosportsclub.com / treasurer123")
        print("\n⚠️  Remember to change these passwords in production!")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("Club Management SaaS - Database Initialization")
    print("="*60)
    init_database()
