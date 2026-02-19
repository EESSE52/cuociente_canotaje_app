"""
Payments API endpoints
Payment processing with commission calculation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.db.database import get_db
from app.models.models import (
    Payment, User, UserRole, PaymentStatus, GeneratedFee, 
    SpecialFee, Commission, Club, PaymentFee, PaymentSpecialFee, FeeStatus
)
from app.schemas.schemas import PaymentCreate, PaymentUpdate, PaymentResponse
from app.core.security import get_current_user, verify_club_access, RoleChecker

router = APIRouter()


def calculate_and_create_commission(db: Session, payment: Payment) -> Commission:
    """
    Calculate and create commission record for a payment
    Called when payment is approved
    """
    # Get club's commission percentage
    club = db.query(Club).filter(Club.id == payment.club_id).first()
    commission_pct = club.commission_percentage
    
    # Calculate amounts
    commission_amount = payment.amount * (commission_pct / Decimal('100'))
    club_net_amount = payment.amount - commission_amount
    
    # Create commission record
    commission = Commission(
        club_id=payment.club_id,
        payment_id=payment.id,
        payment_amount=payment.amount,
        commission_percentage=commission_pct,
        commission_amount=commission_amount,
        club_net_amount=club_net_amount
    )
    
    db.add(commission)
    return commission


def distribute_payment_to_fees(db: Session, payment: Payment, fee_ids: List[int], special_fee_ids: List[int]):
    """
    Distribute payment amount to specified fees
    Updates fee paid_amount and status
    """
    remaining_amount = payment.amount
    
    # Process regular fees
    for fee_id in fee_ids:
        if remaining_amount <= 0:
            break
        
        fee = db.query(GeneratedFee).filter(GeneratedFee.id == fee_id).first()
        if not fee:
            continue
        
        # Calculate amount to apply
        amount_owed = fee.final_amount - fee.paid_amount
        amount_to_apply = min(remaining_amount, amount_owed)
        
        # Update fee
        fee.paid_amount += amount_to_apply
        if fee.paid_amount >= fee.final_amount:
            fee.status = FeeStatus.PAID
        else:
            fee.status = FeeStatus.PARTIALLY_PAID
        
        # Create payment-fee association
        payment_fee = PaymentFee(
            payment_id=payment.id,
            generated_fee_id=fee.id,
            amount_applied=amount_to_apply
        )
        db.add(payment_fee)
        
        remaining_amount -= amount_to_apply
    
    # Process special fees
    for fee_id in special_fee_ids:
        if remaining_amount <= 0:
            break
        
        fee = db.query(SpecialFee).filter(SpecialFee.id == fee_id).first()
        if not fee:
            continue
        
        # Calculate amount to apply
        amount_owed = fee.amount - fee.paid_amount
        amount_to_apply = min(remaining_amount, amount_owed)
        
        # Update fee
        fee.paid_amount += amount_to_apply
        if fee.paid_amount >= fee.amount:
            fee.status = FeeStatus.PAID
        else:
            fee.status = FeeStatus.PARTIALLY_PAID
        
        # Create payment-special_fee association
        payment_special_fee = PaymentSpecialFee(
            payment_id=payment.id,
            special_fee_id=fee.id,
            amount_applied=amount_to_apply
        )
        db.add(payment_special_fee)
        
        remaining_amount -= amount_to_apply


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN, UserRole.TREASURER]))
):
    """
    Create a new payment
    Initially in 'pending' status
    """
    verify_club_access(current_user, payment_data.club_id)
    
    # Create payment
    payment_dict = payment_data.model_dump(exclude={'fee_ids', 'special_fee_ids'})
    if not payment_dict.get('payment_date'):
        payment_dict['payment_date'] = datetime.utcnow()
    
    new_payment = Payment(
        **payment_dict,
        processed_by_user_id=current_user.id
    )
    
    db.add(new_payment)
    db.flush()  # Get payment ID
    
    # Distribute payment to fees
    if payment_data.fee_ids or payment_data.special_fee_ids:
        distribute_payment_to_fees(
            db, 
            new_payment, 
            payment_data.fee_ids,
            payment_data.special_fee_ids
        )
    
    db.commit()
    db.refresh(new_payment)
    
    return PaymentResponse.model_validate(new_payment)


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    club_id: Optional[int] = None,
    member_id: Optional[int] = None,
    status_filter: Optional[PaymentStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List payments with filtering and pagination
    """
    query = db.query(Payment)
    
    # Multi-tenant filtering
    if current_user.role == UserRole.SUPERADMIN:
        if club_id:
            query = query.filter(Payment.club_id == club_id)
    else:
        query = query.filter(Payment.club_id == current_user.club_id)
    
    # Additional filters
    if member_id:
        query = query.filter(Payment.member_id == member_id)
    
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    # Order by date descending
    query = query.order_by(Payment.payment_date.desc())
    
    # Pagination
    offset = (page - 1) * page_size
    payments = query.offset(offset).limit(page_size).all()
    
    return [PaymentResponse.model_validate(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific payment by ID
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    verify_club_access(current_user, payment.club_id)
    
    return PaymentResponse.model_validate(payment)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN, UserRole.TREASURER]))
):
    """
    Update a payment
    Limited fields can be updated after creation
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    verify_club_access(current_user, payment.club_id)
    
    # Update fields
    update_data = payment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)
    
    db.commit()
    db.refresh(payment)
    
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/approve", response_model=PaymentResponse)
async def approve_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN, UserRole.TREASURER]))
):
    """
    Approve a payment
    This triggers commission calculation
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    verify_club_access(current_user, payment.club_id)
    
    if payment.status == PaymentStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is already approved"
        )
    
    # Update status
    payment.status = PaymentStatus.APPROVED
    
    # Calculate and create commission
    calculate_and_create_commission(db, payment)
    
    db.commit()
    db.refresh(payment)
    
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.SUPERADMIN, UserRole.CLUB_ADMIN]))
):
    """
    Cancel a payment
    Requires SUPERADMIN or CLUB_ADMIN role
    Reverts fee statuses if payment was approved
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    verify_club_access(current_user, payment.club_id)
    
    if payment.status == PaymentStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is already cancelled"
        )
    
    # Revert fee amounts if payment was approved
    if payment.status == PaymentStatus.APPROVED:
        # Get associated fees
        payment_fees = db.query(PaymentFee).filter(PaymentFee.payment_id == payment.id).all()
        for pf in payment_fees:
            fee = db.query(GeneratedFee).filter(GeneratedFee.id == pf.generated_fee_id).first()
            if fee:
                fee.paid_amount -= pf.amount_applied
                if fee.paid_amount <= 0:
                    fee.status = FeeStatus.PENDING
                else:
                    fee.status = FeeStatus.PARTIALLY_PAID
        
        payment_special_fees = db.query(PaymentSpecialFee).filter(PaymentSpecialFee.payment_id == payment.id).all()
        for psf in payment_special_fees:
            fee = db.query(SpecialFee).filter(SpecialFee.id == psf.special_fee_id).first()
            if fee:
                fee.paid_amount -= psf.amount_applied
                if fee.paid_amount <= 0:
                    fee.status = FeeStatus.PENDING
                else:
                    fee.status = FeeStatus.PARTIALLY_PAID
    
    # Update payment status
    payment.status = PaymentStatus.CANCELLED
    if reason:
        payment.notes = f"{payment.notes or ''}\nCancellation reason: {reason}"
    
    db.commit()
    db.refresh(payment)
    
    return PaymentResponse.model_validate(payment)


@router.get("/reports/summary")
async def get_payment_reports(
    club_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment summary reports
    """
    query = db.query(Payment).filter(Payment.status == PaymentStatus.APPROVED)
    
    # Multi-tenant filtering
    if current_user.role == UserRole.SUPERADMIN:
        if club_id:
            query = query.filter(Payment.club_id == club_id)
    else:
        query = query.filter(Payment.club_id == current_user.club_id)
    
    # Date filtering
    if start_date:
        query = query.filter(Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(Payment.payment_date <= end_date)
    
    payments = query.all()
    
    total_amount = sum(p.amount for p in payments)
    total_count = len(payments)
    
    # Get commissions
    commission_query = db.query(Commission)
    if current_user.role != UserRole.SUPERADMIN:
        commission_query = commission_query.filter(Commission.club_id == current_user.club_id)
    elif club_id:
        commission_query = commission_query.filter(Commission.club_id == club_id)
    
    commissions = commission_query.all()
    total_commission = sum(c.commission_amount for c in commissions)
    total_club_net = sum(c.club_net_amount for c in commissions)
    
    return {
        "total_payments": total_count,
        "total_amount": float(total_amount),
        "total_commission": float(total_commission),
        "total_club_net": float(total_club_net),
        "average_payment": float(total_amount / total_count) if total_count > 0 else 0
    }
