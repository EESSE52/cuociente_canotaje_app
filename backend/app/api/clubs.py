"""
Clubs API endpoints
SuperAdmin manages clubs (full CRUD)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import Club, User, UserRole, ClubStatus, Member, GeneratedFee, Payment, MemberStatus, FeeStatus, PaymentStatus
from app.schemas.schemas import (
    ClubCreate, ClubUpdate, ClubResponse, PaginationParams
)
from app.core.security import get_current_user, RoleChecker

router = APIRouter()


@router.post("/", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club(
    club_data: ClubCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN]))
):
    """
    Create a new club (SuperAdmin only)
    """
    # Check if club name already exists
    existing_club = db.query(Club).filter(Club.name == club_data.name).first()
    if existing_club:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Club name already exists"
        )
    
    # Create new club
    new_club = Club(**club_data.model_dump())
    db.add(new_club)
    db.commit()
    db.refresh(new_club)
    
    return ClubResponse.model_validate(new_club)


@router.get("/", response_model=List[ClubResponse])
async def list_clubs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: ClubStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN]))
):
    """
    List all clubs with pagination (SuperAdmin only)
    """
    query = db.query(Club)
    
    if status_filter:
        query = query.filter(Club.status == status_filter)
    
    # Pagination
    offset = (page - 1) * page_size
    clubs = query.offset(offset).limit(page_size).all()
    
    return [ClubResponse.model_validate(club) for club in clubs]


@router.get("/{club_id}", response_model=ClubResponse)
async def get_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific club by ID
    SuperAdmin can access any club
    Other users can only access their own club
    """
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    # Check access permissions
    if current_user.role != UserRole.SUPERADMIN and current_user.club_id != club_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this club"
        )
    
    return ClubResponse.model_validate(club)


@router.put("/{club_id}", response_model=ClubResponse)
async def update_club(
    club_id: int,
    club_data: ClubUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN]))
):
    """
    Update a club (SuperAdmin only)
    """
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    # Update fields
    update_data = club_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(club, field, value)
    
    db.commit()
    db.refresh(club)
    
    return ClubResponse.model_validate(club)


@router.delete("/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN]))
):
    """
    Delete a club (SuperAdmin only)
    Note: This will cascade delete all related entities
    """
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    db.delete(club)
    db.commit()
    
    return None


@router.get("/{club_id}/stats")
async def get_club_stats(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get club statistics
    """
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    # Check access
    if current_user.role != UserRole.SUPERADMIN and current_user.club_id != club_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Calculate statistics
    total_members = db.query(Member).filter(Member.club_id == club_id).count()
    active_members = db.query(Member).filter(
        Member.club_id == club_id,
        Member.status == MemberStatus.ACTIVE
    ).count()
    
    pending_fees = db.query(GeneratedFee).filter(
        GeneratedFee.club_id == club_id,
        GeneratedFee.status == FeeStatus.PENDING
    ).count()
    
    total_payments = db.query(Payment).filter(
        Payment.club_id == club_id,
        Payment.status == PaymentStatus.APPROVED
    ).count()
    
    return {
        "club_id": club_id,
        "club_name": club.name,
        "total_members": total_members,
        "active_members": active_members,
        "pending_fees": pending_fees,
        "total_payments": total_payments
    }
