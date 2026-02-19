"""
SQLAlchemy models for multi-tenant SaaS platform
All tables include club_id for tenant isolation (except Club table itself)
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Text, Enum, Numeric, Index, CheckConstraint, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.db.database import Base


# ==================== ENUMS ====================

class UserRole(str, enum.Enum):
    """User roles in the system"""
    SUPERADMIN = "superadmin"  # Platform provider
    CLUB_ADMIN = "club_admin"  # Club administrator
    TREASURER = "treasurer"  # Club treasurer
    BOARD = "board"  # Board member
    MEMBER = "member"  # Regular member


class ClubStatus(str, enum.Enum):
    """Club status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class MemberType(str, enum.Enum):
    """Member types"""
    REGULAR = "regular"
    FOUNDING_CONTRIBUTOR = "founding_contributor"
    EXEMPT = "exempt"


class MemberStatus(str, enum.Enum):
    """Member status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class FeeStatus(str, enum.Enum):
    """Fee payment status"""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIALLY_PAID = "partially_paid"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    """Payment methods"""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ONLINE_GATEWAY = "online_gateway"
    OTHER = "other"


class SpecialFeeType(str, enum.Enum):
    """Special fee types"""
    EVENT_REGISTRATION = "event_registration"
    TRANSPORT = "transport"
    FOOD = "food"
    FOUNDING_CONTRIBUTOR = "founding_contributor"
    EXTRAORDINARY = "extraordinary"
    DONATION = "donation"
    OTHER = "other"


class Periodicity(str, enum.Enum):
    """Fee periodicity"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BIANNUAL = "biannual"
    ANNUAL = "annual"


# ==================== MODELS ====================

class Club(Base):
    """
    Club entity - each club is a tenant
    SuperAdmin manages clubs
    """
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    contact_email = Column(String(255), nullable=False)
    commission_percentage = Column(Numeric(5, 2), nullable=False, default=5.0)  # Platform commission %
    status = Column(Enum(ClubStatus), nullable=False, default=ClubStatus.ACTIVE)
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Contact information
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Settings
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="club", cascade="all, delete-orphan")
    members = relationship("Member", back_populates="club", cascade="all, delete-orphan")
    fee_plans = relationship("RecurringFeePlan", back_populates="club", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="club", cascade="all, delete-orphan")
    news = relationship("ClubNews", back_populates="club", cascade="all, delete-orphan")


class User(Base):
    """
    User accounts - can have different roles
    Multi-tenant: belongs to a specific club (except SuperAdmin)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True)  # Null for SuperAdmin
    
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Optional link to member (if user is also a club member)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    club = relationship("Club", back_populates="users")
    member = relationship("Member", foreign_keys=[member_id])
    
    # Indexes for multi-tenant queries
    __table_args__ = (
        Index('idx_user_club_email', 'club_id', 'email'),
        Index('idx_user_club_role', 'club_id', 'role'),
    )


class Member(Base):
    """
    Club members - people who pay fees
    Multi-tenant: isolated by club_id
    """
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    
    # Member info
    member_number = Column(String(50), nullable=True)
    member_type = Column(Enum(MemberType), nullable=False, default=MemberType.REGULAR)
    status = Column(Enum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE)
    
    # Dates
    join_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    
    # Additional info
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    club = relationship("Club", back_populates="members")
    fees = relationship("GeneratedFee", back_populates="member", cascade="all, delete-orphan")
    special_fees = relationship("SpecialFee", back_populates="member", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="member", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_member_club_status', 'club_id', 'status'),
        Index('idx_member_club_email', 'club_id', 'email'),
    )


class RecurringFeePlan(Base):
    """
    Recurring fee plans (monthly, quarterly, etc.)
    Multi-tenant: isolated by club_id
    """
    __tablename__ = "recurring_fee_plans"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    amount = Column(Numeric(10, 2), nullable=False)
    periodicity = Column(Enum(Periodicity), nullable=False, default=Periodicity.MONTHLY)
    
    # Due date configuration
    due_day_of_month = Column(Integer, nullable=False, default=5)  # Day of month when fee is due
    
    # Discount settings
    discount_percentage = Column(Numeric(5, 2), nullable=True, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    club = relationship("Club", back_populates="fee_plans")
    generated_fees = relationship("GeneratedFee", back_populates="fee_plan", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount >= 0', name='check_amount_positive'),
        CheckConstraint('due_day_of_month >= 1 AND due_day_of_month <= 31', name='check_due_day'),
        Index('idx_feeplan_club_active', 'club_id', 'is_active'),
    )


class GeneratedFee(Base):
    """
    Generated fee instances from recurring plans
    Each member gets a fee generated periodically
    Multi-tenant: isolated by club_id
    """
    __tablename__ = "generated_fees"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    fee_plan_id = Column(Integer, ForeignKey("recurring_fee_plans.id", ondelete="RESTRICT"), nullable=False)
    
    # Fee details
    amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    final_amount = Column(Numeric(10, 2), nullable=False)
    
    # Dates
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Payment tracking
    status = Column(Enum(FeeStatus), nullable=False, default=FeeStatus.PENDING)
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    member = relationship("Member", back_populates="fees")
    fee_plan = relationship("RecurringFeePlan", back_populates="generated_fees")
    payments = relationship("Payment", secondary="payment_fees", back_populates="fees")
    
    # Indexes
    __table_args__ = (
        CheckConstraint('final_amount >= 0', name='check_final_amount_positive'),
        CheckConstraint('paid_amount >= 0', name='check_paid_amount_positive'),
        Index('idx_fee_club_member', 'club_id', 'member_id'),
        Index('idx_fee_club_status', 'club_id', 'status'),
        Index('idx_fee_due_date', 'due_date'),
    )


class SpecialFee(Base):
    """
    Special/one-time fees (events, donations, etc.)
    Multi-tenant: isolated by club_id
    """
    __tablename__ = "special_fees"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=True)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    fee_type = Column(Enum(SpecialFeeType), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Payment tracking
    status = Column(Enum(FeeStatus), nullable=False, default=FeeStatus.PENDING)
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    member = relationship("Member", back_populates="special_fees")
    event = relationship("Event", back_populates="special_fees")
    payments = relationship("Payment", secondary="payment_special_fees", back_populates="special_fees")
    
    # Indexes
    __table_args__ = (
        CheckConstraint('amount >= 0', name='check_special_amount_positive'),
        Index('idx_special_fee_club_member', 'club_id', 'member_id'),
        Index('idx_special_fee_club_status', 'club_id', 'status'),
    )


class Payment(Base):
    """
    Payment records - can pay multiple fees at once
    Supports partial payments
    Multi-tenant: isolated by club_id
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Reference information
    reference_number = Column(String(100), nullable=True)
    receipt_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Who processed
    processed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    member = relationship("Member", back_populates="payments")
    fees = relationship("GeneratedFee", secondary="payment_fees", back_populates="payments")
    special_fees = relationship("SpecialFee", secondary="payment_special_fees", back_populates="payments")
    commission = relationship("Commission", back_populates="payment", uselist=False)
    
    # Indexes
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_payment_amount_positive'),
        Index('idx_payment_club_member', 'club_id', 'member_id'),
        Index('idx_payment_club_status', 'club_id', 'status'),
        Index('idx_payment_date', 'payment_date'),
    )


# Association table for Payment-GeneratedFee many-to-many
class PaymentFee(Base):
    """Association between payments and generated fees"""
    __tablename__ = "payment_fees"
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    generated_fee_id = Column(Integer, ForeignKey("generated_fees.id", ondelete="CASCADE"), nullable=False)
    amount_applied = Column(Numeric(10, 2), nullable=False)  # How much of payment applied to this fee
    
    __table_args__ = (
        Index('idx_payment_fee', 'payment_id', 'generated_fee_id'),
    )


# Association table for Payment-SpecialFee many-to-many
class PaymentSpecialFee(Base):
    """Association between payments and special fees"""
    __tablename__ = "payment_special_fees"
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    special_fee_id = Column(Integer, ForeignKey("special_fees.id", ondelete="CASCADE"), nullable=False)
    amount_applied = Column(Numeric(10, 2), nullable=False)
    
    __table_args__ = (
        Index('idx_payment_special_fee', 'payment_id', 'special_fee_id'),
    )


class Commission(Base):
    """
    Platform commission records - generated automatically from payments
    Immutable for accounting purposes
    """
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    
    # Commission calculation
    payment_amount = Column(Numeric(10, 2), nullable=False)
    commission_percentage = Column(Numeric(5, 2), nullable=False)
    commission_amount = Column(Numeric(10, 2), nullable=False)
    club_net_amount = Column(Numeric(10, 2), nullable=False)
    
    # Calculation date
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    payment = relationship("Payment", back_populates="commission")
    
    # Indexes
    __table_args__ = (
        Index('idx_commission_club', 'club_id'),
        Index('idx_commission_date', 'calculated_at'),
    )


class Event(Base):
    """
    Club events - can generate special fees automatically
    Multi-tenant: isolated by club_id
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Event details
    event_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(300), nullable=True)
    
    # Fee generation settings
    registration_fee = Column(Numeric(10, 2), nullable=True)
    auto_generate_fee = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    club = relationship("Club", back_populates="events")
    special_fees = relationship("SpecialFee", back_populates="event", cascade="all, delete-orphan")
    attendances = relationship("EventAttendance", back_populates="event", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_club_date', 'club_id', 'event_date'),
    )


class EventAttendance(Base):
    """Track member attendance confirmations for events"""
    __tablename__ = "event_attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    
    confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="attendances")
    
    __table_args__ = (
        Index('idx_attendance_event_member', 'event_id', 'member_id'),
    )


class ClubNews(Base):
    """
    Club news/announcements
    Multi-tenant: isolated by club_id
    """
    __tablename__ = "club_news"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    
    # Author
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Publishing
    is_published = Column(Boolean, default=False)
    publish_date = Column(DateTime(timezone=True), nullable=True)
    
    # Attachments
    attachment_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    club = relationship("Club", back_populates="news")
    
    # Indexes
    __table_args__ = (
        Index('idx_news_club_published', 'club_id', 'is_published'),
        Index('idx_news_publish_date', 'publish_date'),
    )


class AuditLog(Base):
    """
    Audit log for sensitive operations
    Records user actions for compliance and security
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False)  # e.g., "create_payment", "delete_member"
    entity_type = Column(String(50), nullable=False)  # e.g., "payment", "member"
    entity_id = Column(Integer, nullable=True)
    
    # Changes (JSON)
    changes = Column(Text, nullable=True)
    
    # Request info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_club_created', 'club_id', 'created_at'),
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_action', 'action'),
    )
