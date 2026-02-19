"""
Database initialization script
Creates initial SuperAdmin user and sample club

⚠️ FOR DEVELOPMENT/TESTING ONLY ⚠️
Do NOT use default passwords in production!
For production, set passwords via environment variables or admin interface.
"""
import sys
import os
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal, engine, Base
from app.models.models import User, Club, UserRole, ClubStatus
from app.core.security import hash_password


def get_password_from_env_or_default(env_var: str, default: str, user_type: str) -> str:
    """Get password from environment variable or use default with warning"""
    password = os.getenv(env_var, default)
    if password == default:
        print(f"  ⚠️  Using default password for {user_type}")
        print(f"  ⚠️  Set {env_var} environment variable for production!")
    return password


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
        
        # Get password from environment or use default
        admin_password = get_password_from_env_or_default(
            'INIT_ADMIN_PASSWORD', 
            'admin123',  # Default for development only
            'SuperAdmin'
        )
        
        # Create SuperAdmin
        superadmin = User(
            email="admin@clubmanagement.com",
            hashed_password=hash_password(admin_password),
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
        if admin_password == 'admin123':
            print(f"  Password: {admin_password} (DEFAULT - CHANGE IN PRODUCTION!)")
        
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
        
        club_admin_password = get_password_from_env_or_default(
            'INIT_CLUB_ADMIN_PASSWORD',
            'club123',  # Default for development only
            'Club Admin'
        )
        
        club_admin = User(
            email="admin@demosportsclub.com",
            hashed_password=hash_password(club_admin_password),
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
        if club_admin_password == 'club123':
            print(f"  Password: {club_admin_password} (DEFAULT - CHANGE IN PRODUCTION!)")
        
        # Create treasurer for sample club
        print("\nCreating treasurer...")
        
        treasurer_password = get_password_from_env_or_default(
            'INIT_TREASURER_PASSWORD',
            'treasurer123',  # Default for development only
            'Treasurer'
        )
        
        treasurer = User(
            email="treasurer@demosportsclub.com",
            hashed_password=hash_password(treasurer_password),
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
        if treasurer_password == 'treasurer123':
            print(f"  Password: {treasurer_password} (DEFAULT)")
        
        print("\n" + "="*60)
        print("✅ Database initialization complete!")
        print("="*60)
        print("\n📝 Login Credentials (for development/testing):")
        print("\n1. SuperAdmin:")
        print("   Email: admin@clubmanagement.com")
        if admin_password == 'admin123':
            print(f"   Password: {admin_password} (DEFAULT)")
        print("\n2. Club Admin:")
        print("   Email: admin@demosportsclub.com")
        if club_admin_password == 'club123':
            print(f"   Password: {club_admin_password} (DEFAULT)")
        print("\n3. Treasurer:")
        print("   Email: treasurer@demosportsclub.com")
        if treasurer_password == 'treasurer123':
            print(f"   Password: {treasurer_password} (DEFAULT)")
        
        print("\n" + "="*60)
        print("⚠️  FOR PRODUCTION DEPLOYMENT:")
        print("="*60)
        print("Set environment variables for secure passwords:")
        print("  - INIT_ADMIN_PASSWORD")
        print("  - INIT_CLUB_ADMIN_PASSWORD")
        print("  - INIT_TREASURER_PASSWORD")
        print("Or change passwords immediately after first login!")
        print("="*60)
        
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
