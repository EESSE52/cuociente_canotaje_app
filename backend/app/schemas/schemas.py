"""
Pydantic schemas for request/response validation
Organized by entity
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.models.models import (
    UserRole, ClubStatus, MemberType, MemberStatus,
    FeeStatus, PaymentStatus, PaymentMethod, SpecialFeeType, Periodicity
)


# ==================== BASE SCHEMAS ====================

class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at timestamps"""
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==================== CLUB SCHEMAS ====================

class ClubBase(BaseModel):
    """Base club schema"""
    name: str = Field(..., max_length=200)
    contact_email: EmailStr
    commission_percentage: Decimal = Field(default=5.0, ge=0, le=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ClubCreate(ClubBase):
    """Schema for creating a new club"""
    pass


class ClubUpdate(BaseModel):
    """Schema for updating a club"""
    name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[EmailStr] = None
    commission_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    status: Optional[ClubStatus] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ClubResponse(ClubBase, TimestampMixin):
    """Schema for club response"""
    id: int
    status: ClubStatus
    registration_date: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., max_length=200)
    role: UserRole = UserRole.MEMBER


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8)
    club_id: Optional[int] = None
    member_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=200)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response"""
    id: int
    club_id: Optional[int]
    member_id: Optional[int]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== MEMBER SCHEMAS ====================

class MemberBase(BaseModel):
    """Base member schema"""
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    member_number: Optional[str] = Field(None, max_length=50)
    member_type: MemberType = MemberType.REGULAR
    join_date: date
    notes: Optional[str] = None


class MemberCreate(MemberBase):
    """Schema for creating a new member"""
    club_id: int


class MemberUpdate(BaseModel):
    """Schema for updating a member"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    member_number: Optional[str] = Field(None, max_length=50)
    member_type: Optional[MemberType] = None
    status: Optional[MemberStatus] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class MemberResponse(MemberBase, TimestampMixin):
    """Schema for member response"""
    id: int
    club_id: int
    status: MemberStatus
    end_date: Optional[date]
    
    model_config = ConfigDict(from_attributes=True)


# ==================== FEE PLAN SCHEMAS ====================

class RecurringFeePlanBase(BaseModel):
    """Base fee plan schema"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    periodicity: Periodicity = Periodicity.MONTHLY
    due_day_of_month: int = Field(default=5, ge=1, le=31)
    discount_percentage: Decimal = Field(default=0, ge=0, le=100)


class RecurringFeePlanCreate(RecurringFeePlanBase):
    """Schema for creating a fee plan"""
    club_id: int


class RecurringFeePlanUpdate(BaseModel):
    """Schema for updating a fee plan"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    periodicity: Optional[Periodicity] = None
    due_day_of_month: Optional[int] = Field(None, ge=1, le=31)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class RecurringFeePlanResponse(RecurringFeePlanBase, TimestampMixin):
    """Schema for fee plan response"""
    id: int
    club_id: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


# ==================== GENERATED FEE SCHEMAS ====================

class GeneratedFeeBase(BaseModel):
    """Base generated fee schema"""
    amount: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    final_amount: Decimal = Field(..., ge=0)
    period_start: date
    period_end: date
    due_date: date


class GeneratedFeeCreate(GeneratedFeeBase):
    """Schema for creating a generated fee"""
    club_id: int
    member_id: int
    fee_plan_id: int


class GeneratedFeeUpdate(BaseModel):
    """Schema for updating a generated fee"""
    status: Optional[FeeStatus] = None
    due_date: Optional[date] = None


class GeneratedFeeResponse(GeneratedFeeBase, TimestampMixin):
    """Schema for generated fee response"""
    id: int
    club_id: int
    member_id: int
    fee_plan_id: int
    status: FeeStatus
    paid_amount: Decimal
    
    model_config = ConfigDict(from_attributes=True)


# ==================== SPECIAL FEE SCHEMAS ====================

class SpecialFeeBase(BaseModel):
    """Base special fee schema"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    fee_type: SpecialFeeType
    amount: Decimal = Field(..., gt=0)
    due_date: date


class SpecialFeeCreate(SpecialFeeBase):
    """Schema for creating a special fee"""
    club_id: int
    member_id: int
    event_id: Optional[int] = None


class SpecialFeeUpdate(BaseModel):
    """Schema for updating a special fee"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    due_date: Optional[date] = None
    status: Optional[FeeStatus] = None


class SpecialFeeResponse(SpecialFeeBase, TimestampMixin):
    """Schema for special fee response"""
    id: int
    club_id: int
    member_id: int
    event_id: Optional[int]
    status: FeeStatus
    paid_amount: Decimal
    
    model_config = ConfigDict(from_attributes=True)


# ==================== PAYMENT SCHEMAS ====================

class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating a payment"""
    club_id: int
    member_id: int
    fee_ids: List[int] = Field(default_factory=list)
    special_fee_ids: List[int] = Field(default_factory=list)
    payment_date: Optional[datetime] = None


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    status: Optional[PaymentStatus] = None
    receipt_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class PaymentResponse(PaymentBase, TimestampMixin):
    """Schema for payment response"""
    id: int
    club_id: int
    member_id: int
    status: PaymentStatus
    payment_date: datetime
    receipt_url: Optional[str]
    processed_by_user_id: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)


# ==================== COMMISSION SCHEMAS ====================

class CommissionResponse(BaseModel):
    """Schema for commission response"""
    id: int
    club_id: int
    payment_id: int
    payment_amount: Decimal
    commission_percentage: Decimal
    commission_amount: Decimal
    club_net_amount: Decimal
    calculated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== EVENT SCHEMAS ====================

class EventBase(BaseModel):
    """Base event schema"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    event_date: datetime
    location: Optional[str] = Field(None, max_length=300)
    registration_fee: Optional[Decimal] = Field(None, ge=0)
    auto_generate_fee: bool = False


class EventCreate(EventBase):
    """Schema for creating an event"""
    club_id: int


class EventUpdate(BaseModel):
    """Schema for updating an event"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=300)
    registration_fee: Optional[Decimal] = Field(None, ge=0)
    auto_generate_fee: Optional[bool] = None
    is_active: Optional[bool] = None


class EventResponse(EventBase, TimestampMixin):
    """Schema for event response"""
    id: int
    club_id: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


# ==================== CLUB NEWS SCHEMAS ====================

class ClubNewsBase(BaseModel):
    """Base news schema"""
    title: str = Field(..., max_length=300)
    content: str


class ClubNewsCreate(ClubNewsBase):
    """Schema for creating news"""
    club_id: int
    attachment_url: Optional[str] = Field(None, max_length=500)
    publish_date: Optional[datetime] = None


class ClubNewsUpdate(BaseModel):
    """Schema for updating news"""
    title: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = None
    is_published: Optional[bool] = None
    publish_date: Optional[datetime] = None
    attachment_url: Optional[str] = Field(None, max_length=500)


class ClubNewsResponse(ClubNewsBase, TimestampMixin):
    """Schema for news response"""
    id: int
    club_id: int
    author_id: Optional[int]
    is_published: bool
    publish_date: Optional[datetime]
    attachment_url: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# ==================== PAGINATION ====================

class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[BaseModel]
    total: int
    page: int
    page_size: int
    total_pages: int
