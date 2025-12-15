"""
Expenses API routes
"""
from fastapi import APIRouter, HTTPException
from typing import List
from schemas import ExpenseCreate, ExpenseUpdate, ExpenseStatusUpdate, ExpenseResponse, LogPaymentRequest
import database as db

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def calculate_expense_amounts(expense: dict) -> dict:
    """Add calculated fields to expense"""
    amount = expense['amount']
    currency = expense['currency']
    buffer_rate = expense['buffer_rate']
    num_participants = len(expense.get('participants', [])) or 1
    
    # Calculate collected THB
    if currency == 'JPY':
        collected_thb = amount * buffer_rate
    else:  # THB
        collected_thb = amount
    
    expense['collected_thb'] = round(collected_thb, 2)
    expense['per_person_thb'] = round(collected_thb / num_participants, 2)
    
    # Check if invoiced (invoices list comes from DB query)
    expense['is_invoiced'] = len(expense.get('invoices', [])) > 0
    
    return expense


@router.get("", response_model=List[ExpenseResponse])
def get_expenses():
    """Get all expenses with calculated amounts"""
    expenses = db.get_all_expenses()
    return [calculate_expense_amounts(e) for e in expenses]


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int):
    """Get a single expense by ID"""
    expense = db.get_expense_by_id(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return calculate_expense_amounts(expense)


@router.post("", response_model=ExpenseResponse)
def create_expense(data: ExpenseCreate):
    """Create a new expense"""
    if not data.participant_ids:
        raise HTTPException(status_code=400, detail="At least one participant required")
    
    expense_id = db.add_expense(
        name=data.name,
        amount=data.amount,
        currency=data.currency,
        buffer_rate=data.buffer_rate,
        participant_ids=data.participant_ids
    )
    
    expense = db.get_expense_by_id(expense_id)
    return calculate_expense_amounts(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, data: ExpenseUpdate):
    """Update an expense"""
    existing = db.get_expense_by_id(expense_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.update_expense(
        expense_id=expense_id,
        name=data.name,
        amount=data.amount,
        currency=data.currency,
        buffer_rate=data.buffer_rate,
        participant_ids=data.participant_ids
    )
    
    expense = db.get_expense_by_id(expense_id)
    return calculate_expense_amounts(expense)


@router.patch("/{expense_id}/status")
def update_status(expense_id: int, data: ExpenseStatusUpdate):
    """Update expense status (pending/collected)"""
    if data.status not in ['pending', 'collected']:
        raise HTTPException(status_code=400, detail="Status must be 'pending' or 'collected'")
    
    db.update_expense_status(expense_id, data.status)
    return {"message": f"Status updated to {data.status}"}


@router.post("/{expense_id}/payment", response_model=ExpenseResponse)
def log_payment(expense_id: int, data: LogPaymentRequest):
    """Log an actual payment for an expense"""
    existing = db.get_expense_by_id(expense_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    db.log_expense_payment(
        expense_id=expense_id,
        date=data.date,
        method=data.method,
        actual_amount=data.actual_amount,
        actual_currency=data.actual_currency,
        actual_thb=data.actual_thb
    )
    
    expense = db.get_expense_by_id(expense_id)
    return calculate_expense_amounts(expense)


@router.delete("/{expense_id}")
def delete_expense(expense_id: int):
    """Delete an expense"""
    try:
        db.delete_expense(expense_id)
        return {"message": "Expense deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
