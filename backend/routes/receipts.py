"""
Receipt routes - Payment confirmation PDFs
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from typing import Optional

import database
from schemas import ReceiptData, ReceiptItem, ReceiptGenerationRequest
from pdf_generator import pdf_generator

router = APIRouter(prefix="/api/receipts", tags=["receipts"])



@router.get("/")
def get_receipts():
    """Get all receipts for list view"""
    return {
        "receipts": database.get_all_receipts()
    }


@router.get("/details/{receipt_id}")
def get_receipt_details(receipt_id: int):
    """Get detailed data for a specific receipt"""
    # 1. Get basic info
    receipt = database.get_receipt_by_id(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # 2. Get linked invoices
    invoices = database.get_receipt_invoices(receipt_id)
    
    # 3. Build item list (aggregating expenses from all linked invoices)
    # This logic mirrors generate_receipt but for past data
    items = []
    for invoice in invoices:
        expenses = database.get_invoice_expenses(invoice['id'])
        for expense in expenses:
            total_participants = expense['total_participants']
            # Re-calculate share 
            share_thb = expense['amount'] * expense['buffer_rate'] / total_participants if expense['currency'] == 'JPY' else expense['amount'] / total_participants
            
            items.append({
                "expense_name": expense['name'],
                "original_amount": expense['amount'],
                "currency": expense['currency'],
                "buffer_rate": expense['buffer_rate'] if expense['currency'] == 'JPY' else None,
                "share": f"1/{total_participants}",
                "amount_paid": round(share_thb, 2)
            })
            
    return {
        "id": receipt_id,
        "participant_name": receipt['participant_name'],
        "receipt_number": receipt['receipt_number'],
        "generated_at": receipt['created_at'],
        "payment_method": receipt['payment_method'],
        "items": items,
        "total_paid": receipt['total_thb'],
        "invoices": invoices,
        "pdf_path": receipt['pdf_path'] # for download
    }


@router.get("/download/{receipt_id}")
def download_receipt_by_id(receipt_id: int):
    """Download receipt PDF by ID"""
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, p.name as participant_name 
            FROM receipts r 
            JOIN participants p ON r.participant_id = p.id 
            WHERE r.id = ?
        """, (receipt_id,))
        receipt = cursor.fetchone()
        
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    receipt = dict(receipt)
    if not receipt['pdf_path']:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        receipt['pdf_path'],
        media_type="application/pdf",
        filename=f"receipt_{receipt['participant_name']}_r{receipt['receipt_number']}.pdf"
    )


@router.get("/{participant_name}")
def get_receipt_data(participant_name: str, payment_method: Optional[str] = None):
    """Get receipt data for unpaid invoices"""
    participant = database.get_participant_by_name(participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    participant_id = participant['id']
    settings = database.get_settings()
    
    # Get unpaid invoices
    unpaid_invoices = database.get_unpaid_invoices(participant_id)
    
    if not unpaid_invoices:
        return {
            "participant_name": participant_name,
            "has_unpaid_invoices": False,
            "message": "No unpaid invoices",
            "items": [],
            "total": 0
        }
    
    # Build receipt items from all unpaid invoices
    items = []
    total = 0
    
    for invoice in unpaid_invoices:
        expenses = database.get_invoice_expenses(invoice['id'])
        for expense in expenses:
            total_participants = expense['total_participants']
            share_thb = expense['amount'] * expense['buffer_rate'] / total_participants if expense['currency'] == 'JPY' else expense['amount'] / total_participants
            
            items.append({
                "expense_name": expense['name'],
                "original_amount": expense['amount'],
                "currency": expense['currency'],
                "buffer_rate": expense['buffer_rate'] if expense['currency'] == 'JPY' else None,
                "share": f"1/{total_participants}",
                "amount_paid": round(share_thb, 2)
            })
            total += share_thb
    
    return {
        "participant_name": participant_name,
        "has_unpaid_invoices": True,
        "receipt_number": database.get_next_receipt_number(participant_id),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "trip_name": settings['trip_name'],
        "items": items,
        "total": round(total, 2),
        "total": round(total, 2),
        "unpaid_invoices": [dict(inv) for inv in unpaid_invoices]
    }


@router.post("/{participant_name}/generate")
def generate_receipt(participant_name: str, request: ReceiptGenerationRequest):
    """Generate receipt PDF for selected unpaid invoices"""
    participant = database.get_participant_by_name(participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    participant_id = participant['id']
    settings = database.get_settings()
    
    # Get all unpaid invoices
    all_unpaid = database.get_unpaid_invoices(participant_id)
    
    # Filter by user selection
    target_invoices = [inv for inv in all_unpaid if inv['id'] in request.invoice_ids]
    
    if not target_invoices:
        raise HTTPException(status_code=400, detail="No matching unpaid invoices found for selection")
    
    # Build receipt data
    items = []
    total = 0
    invoice_ids = []
    
    for invoice in target_invoices:
        invoice_ids.append(invoice['id'])
        expenses = database.get_invoice_expenses(invoice['id'])
        for expense in expenses:
            total_participants = expense['total_participants']
            share_thb = expense['amount'] * expense['buffer_rate'] / total_participants if expense['currency'] == 'JPY' else expense['amount'] / total_participants
            
            items.append(ReceiptItem(
                expense_name=expense['name'],
                original_amount=expense['amount'],
                currency=expense['currency'],
                buffer_rate=expense['buffer_rate'] if expense['currency'] == 'JPY' else None,
                share=f"1/{total_participants}",
                amount_paid=round(share_thb, 2)
            ))
            total += share_thb
    
    receipt_number = database.get_next_receipt_number(participant_id)
    
    receipt_data = ReceiptData(
        participant_name=participant_name,
        receipt_number=receipt_number,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        trip_name=settings['trip_name'],
        items=items,
        total_paid=round(total, 2),
        payment_method=request.payment_method
    )
    
    # Generate PDF
    pdf_path = pdf_generator.generate_receipt_pdf(receipt_data, settings['trip_name'])
    
    # Save receipt to database
    database.create_receipt(
        participant_id=participant_id,
        receipt_number=receipt_number,
        total_thb=round(total, 2),
        payment_method=request.payment_method,
        pdf_path=pdf_path,
        invoice_ids=invoice_ids
    )
    
    return {
        "message": f"Receipt #{receipt_number} generated for {participant_name}",
        "pdf_path": pdf_path,
        "total": round(total, 2)
    }


@router.get("/{participant_name}/pdf")
def download_receipt(participant_name: str):
    """Download the latest receipt PDF"""
    participant = database.get_participant_by_name(participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    receipts = database.get_previous_receipts(participant['id'])
    if not receipts:
        raise HTTPException(status_code=404, detail="No receipts found")
    
    latest = receipts[-1]
    return FileResponse(
        path=latest['pdf_path'],
        media_type='application/pdf',
        filename=f"receipt_{participant_name}_r{latest['receipt_number']}.pdf"
    )


@router.get("/{participant_name}/history")
def get_receipt_history(participant_name: str):
    """Get receipt history for a participant"""
    participant = database.get_participant_by_name(participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    return database.get_previous_receipts(participant['id'])


@router.delete("/{receipt_id}")
def delete_receipt(receipt_id: int):
    """Delete (void) a receipt"""
    try:
        database.delete_receipt(receipt_id)
        return {"message": "Receipt voided successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



