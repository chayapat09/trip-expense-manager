"""
Refunds API routes - reconciliation and refund PDF generation
"""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import Response
from datetime import datetime
from typing import List
from schemas import RefundData, RefundCollectedItem, RefundActualItem, ReconciliationItem
import database as db
from pdf_generator import pdf_generator

router = APIRouter(prefix="/api/refunds", tags=["refunds"])


def calculate_participant_refund(trip_id: str, participant_id: int, participant_name: str) -> RefundData:
    """Calculate detailed refund data for a participant"""
    settings = db.get_settings(trip_id)
    
    # Get all expenses for participant
    expenses = db.get_participant_expenses(participant_id)
    
    # Build collected items
    collected_items: List[RefundCollectedItem] = []
    total_collected = 0.0
    
    for expense in expenses:
        amount = expense['amount']
        currency = expense['currency']
        buffer_rate = expense['buffer_rate']
        total_participants = expense['total_participants']
        
        if currency == 'JPY':
            total_expense_thb = amount * buffer_rate
        else:
            total_expense_thb = amount
        
        your_share = total_expense_thb / total_participants
        total_collected += your_share
        
        collected_items.append(RefundCollectedItem(
            expense_name=expense['name'],
            original_amount=amount,
            currency=currency,
            buffer_rate=buffer_rate if currency == 'JPY' else None,
            share=f"1/{total_participants}",
            collected_thb=round(your_share, 2)
        ))
    
    # Get actuals for this participant
    actuals = db.get_participant_actuals(participant_id)
    
    # Build actual items
    actual_items: List[RefundActualItem] = []
    total_actual = 0.0
    
    for actual in actuals:
        total_participants = actual['total_participants']
        your_cost = actual['actual_thb'] / total_participants
        total_actual += your_cost
        
        actual_items.append(RefundActualItem(
            expense_name=actual['expense_name'],
            paid_amount=actual['actual_amount'],
            paid_currency=actual['actual_currency'],
            actual_thb=actual['actual_thb'],
            share=f"1/{total_participants}",
            your_cost_thb=round(your_cost, 2)
        ))
    
    refund_amount = total_collected - total_actual
    
    return RefundData(
        participant_name=participant_name,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        trip_name=settings['trip_name'],
        collected_items=collected_items,
        actual_items=actual_items,
        total_collected=round(total_collected, 2),
        total_actual=round(total_actual, 2),
        refund_amount=round(refund_amount, 2)
    )


@router.get("/reconciliation")
def get_reconciliation(x_trip_id: str = Header(...)) -> List[ReconciliationItem]:
    """Get reconciliation summary for all participants"""
    participants = db.get_all_participants(x_trip_id)
    results = []
    
    for p in participants:
        refund_data = calculate_participant_refund(x_trip_id, p['id'], p['name'])
        results.append(ReconciliationItem(
            participant_name=p['name'],
            total_collected=refund_data.total_collected,
            total_actual=refund_data.total_actual,
            surplus_deficit=refund_data.refund_amount
        ))
    
    return results


@router.get("/{participant_name}")
def get_refund_data(participant_name: str, x_trip_id: str = Header(...)) -> RefundData:
    """Get detailed refund data for a participant"""
    participant = db.get_participant_by_name(x_trip_id, participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    return calculate_participant_refund(x_trip_id, participant['id'], participant_name)


@router.post("/{participant_name}/pdf")
def generate_refund_pdf_endpoint(participant_name: str, x_trip_id: str = Header(...)):
    """Generate refund statement PDF data for a participant"""
    participant = db.get_participant_by_name(x_trip_id, participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    refund_data = calculate_participant_refund(x_trip_id, participant['id'], participant_name)
    
    return {
        "message": f"Refund statement ready for {participant_name}",
        "refund_amount": refund_data.refund_amount
    }


@router.get("/{participant_name}/pdf/download")
def download_refund_pdf(participant_name: str, trip_id: str = None, x_trip_id: str = Header(None)):
    """Generate and download refund PDF directly - on-the-fly
    
    Accepts trip_id via query parameter (for window.open() calls) or X-Trip-Id header.
    Query parameter takes precedence since window.open() can't send headers.
    """
    # Use query param if provided, otherwise fall back to header
    effective_trip_id = trip_id or x_trip_id
    if not effective_trip_id:
        raise HTTPException(status_code=400, detail="trip_id query parameter or X-Trip-Id header required")
    
    participant = db.get_participant_by_name(effective_trip_id, participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    refund_data = calculate_participant_refund(effective_trip_id, participant['id'], participant_name)
    pdf_bytes = pdf_generator.generate_refund_pdf(refund_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=refund_{participant_name}.pdf"
        }
    )

