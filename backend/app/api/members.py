"""
Members API endpoints
CRUD operations for club members with multi-tenant filtering
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.database import get_db
from app.models.models import Member, User, UserRole, MemberStatus, FeeStatus, PaymentStatus
from app.schemas.schemas import (
    MemberCreate, MemberUpdate, MemberResponse
)
from app.core.security import get_current_user, verify_club_access, RoleChecker

router = APIRouter()


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    member_data: MemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN, UserRole.TREASURER]))
):
    """
    Create a new member
    Requires: SUPERADMIN, CLUB_ADMIN, or TREASURER role
    """
    # Verify club access
    verify_club_access(current_user, member_data.club_id)
    
    # Check if member email already exists in this club
    if member_data.email:
        existing = db.query(Member).filter(
            Member.club_id == member_data.club_id,
            Member.email == member_data.email
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A member with this email already exists in this club"
            )
    
    # Create member
    new_member = Member(**member_data.model_dump())
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    return MemberResponse.model_validate(new_member)


@router.get("/", response_model=List[MemberResponse])
async def list_members(
    club_id: Optional[int] = None,
    status_filter: Optional[MemberStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List members with filtering and pagination
    - SuperAdmin can specify any club_id or see all
    - Other users see only their club's members
    """
    query = db.query(Member)
    
    # Multi-tenant filtering
    if current_user.role == UserRole.SUPERADMIN:
        if club_id:
            query = query.filter(Member.club_id == club_id)
    else:
        # Non-superadmin users can only see their club
        query = query.filter(Member.club_id == current_user.club_id)
    
    # Status filter
    if status_filter:
        query = query.filter(Member.status == status_filter)
    
    # Pagination
    offset = (page - 1) * page_size
    members = query.offset(offset).limit(page_size).all()
    
    return [MemberResponse.model_validate(m) for m in members]


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific member by ID
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Verify access
    verify_club_access(current_user, member.club_id)
    
    return MemberResponse.model_validate(member)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int,
    member_data: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN, UserRole.TREASURER]))
):
    """
    Update a member
    Requires: SUPERADMIN, CLUB_ADMIN, or TREASURER role
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Verify access
    verify_club_access(current_user, member.club_id)
    
    # Update fields
    update_data = member_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    
    db.commit()
    db.refresh(member)
    
    return MemberResponse.model_validate(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN]))
):
    """
    Delete a member
    Requires: SUPERADMIN or CLUB_ADMIN role
    Note: This will cascade delete related fees and payments
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Verify access
    verify_club_access(current_user, member.club_id)
    
    db.delete(member)
    db.commit()
    
    return None


@router.get("/{member_id}/account")
async def get_member_account_status(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get member's account status including fees and payments
    """
    from app.models.models import GeneratedFee, SpecialFee, Payment
    from decimal import Decimal
    
    member = db.query(Member).filter(Member.id == member_id).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Verify access (members can see their own account)
    if current_user.role == UserRole.MEMBER:
        if current_user.member_id != member_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own account"
            )
    else:
        verify_club_access(current_user, member.club_id)
    
    # Calculate account status
    pending_fees = db.query(GeneratedFee).filter(
        GeneratedFee.member_id == member_id,
        GeneratedFee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE])
    ).all()
    
    pending_special_fees = db.query(SpecialFee).filter(
        SpecialFee.member_id == member_id,
        SpecialFee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE])
    ).all()
    
    total_pending = sum(f.final_amount - f.paid_amount for f in pending_fees)
    total_pending += sum(f.amount - f.paid_amount for f in pending_special_fees)
    
    recent_payments = db.query(Payment).filter(
        Payment.member_id == member_id,
        Payment.status == PaymentStatus.APPROVED
    ).order_by(Payment.payment_date.desc()).limit(10).all()
    
    return {
        "member": MemberResponse.model_validate(member),
        "total_pending": float(total_pending),
        "pending_fees_count": len(pending_fees) + len(pending_special_fees),
        "recent_payments_count": len(recent_payments),
        "account_status": "current" if total_pending == 0 else "overdue" if any(f.status == FeeStatus.OVERDUE for f in pending_fees + pending_special_fees) else "pending"
    }


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_members(
    club_id: int,
    members_data: List[MemberCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN, UserRole.TREASURER]))
):
    """
    Bulk create multiple members at once
    Useful for importing from CSV/Excel
    """
    verify_club_access(current_user, club_id)
    
    created_members = []
    errors = []
    
    for idx, member_data in enumerate(members_data):
        try:
            # Ensure club_id matches
            if member_data.club_id != club_id:
                member_data.club_id = club_id
            
            new_member = Member(**member_data.model_dump())
            db.add(new_member)
            created_members.append(new_member)
        except Exception as e:
            errors.append({
                "index": idx,
                "data": member_data.model_dump(),
                "error": str(e)
            })
    
    if created_members:
        db.commit()
        for member in created_members:
            db.refresh(member)
    
    return {
        "created_count": len(created_members),
        "error_count": len(errors),
        "members": [MemberResponse.model_validate(m) for m in created_members],
        "errors": errors
    }
