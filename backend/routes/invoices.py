"""
Invoices API routes - versioned invoices with PDF generation
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from typing import List
from schemas import InvoiceData, InvoiceExpenseItem, InvoiceGenerationRequest
import database as db
from pdf_generator import pdf_generator

router = APIRouter(prefix="/api/invoices", tags=["invoices"])




@router.get("/")
def get_invoices():
    """Get all invoices for list view"""
    return {
        "invoices": db.get_all_invoices_with_status()
    }


@router.get("/details/{invoice_id}")
def get_invoice_details(invoice_id: int):
    """Get detailed data for a specific past invoice"""
    # 1. Get basic info
    invoice = db.get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # 2. Get expenses included in this invoice
    expenses = db.get_invoice_expenses(invoice_id)
    
    # 3. Calculate share items (reusing existing logic)
    items = [calculate_expense_share(e, invoice['participant_id']) for e in expenses]
    
    # 4. No previous invoices (Decoupled)
    previous = []
    
    # 5. Calculate totals
    grand_total = invoice['total_thb']
    
    return {
        "id": invoice_id,
        "participant_name": invoice['participant_name'],
        "version": invoice['version'],
        "generated_at": invoice['created_at'],
        "previous_invoices": previous,
        "new_expenses": items,
        "this_invoice_total": invoice['total_thb'],
        "grand_total": grand_total,
        "pdf_path": invoice['pdf_path'] # exposing for frontend to offer download too
    }


@router.get("/overview/all")
def get_overview():
    """Get all invoices, receipts, and stats for overview page"""
    return {
        "stats": db.get_overview_stats(),
        "invoices": db.get_all_invoices_with_status(),
        "receipts": db.get_all_receipts()
    }


@router.get("/download/{invoice_id}")
def download_invoice_by_id(invoice_id: int):
    """Download invoice PDF by ID"""
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, p.name as participant_name 
            FROM invoices i 
            JOIN participants p ON i.participant_id = p.id 
            WHERE i.id = ?
        """, (invoice_id,))
        invoice = cursor.fetchone()
        
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice = dict(invoice)
    if not invoice['pdf_path']:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        invoice['pdf_path'],
        media_type="application/pdf",
        filename=f"invoice_{invoice['participant_name']}_v{invoice['version']}.pdf"
    )


def calculate_expense_share(expense: dict, participant_id: int) -> InvoiceExpenseItem:
    """Calculate participant's share for an expense"""
    amount = expense['amount']
    currency = expense['currency']
    buffer_rate = expense['buffer_rate']
    total_participants = expense['total_participants']
    
    # Calculate collected THB for this expense
    if currency == 'JPY':
        total_collected = amount * buffer_rate
    else:
        total_collected = amount
    
    your_share = total_collected / total_participants
    
    return InvoiceExpenseItem(
        expense_id=expense['id'],
        name=expense['name'],
        original_amount=amount,
        currency=currency,
        buffer_rate=buffer_rate,
        share=f"1/{total_participants}",
        your_share_thb=round(your_share, 2)
    )


@router.get("/{participant_name}")
def get_invoice_data(participant_name: str) -> InvoiceData:
    """Get invoice data for a participant (without generating PDF)"""
    participant = db.get_participant_by_name(participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    participant_id = participant['id']
    
    # Get all expenses for this participant
    all_expenses = db.get_participant_expenses(participant_id)
    
    # Get already invoiced expense IDs
    invoiced_ids = set(db.get_invoiced_expense_ids(participant_id))
    
    # Find new expenses (not yet invoiced)
    new_expenses = [e for e in all_expenses if e['id'] not in invoiced_ids]
    
    # Calculate new expense items
    new_expense_items = [calculate_expense_share(e, participant_id) for e in new_expenses]
    
    # Previous invoices decoupling
    previous_invoices = []
    
    # Calculate totals
    this_invoice_total = sum(item.your_share_thb for item in new_expense_items)
    grand_total = this_invoice_total
    
    next_version = db.get_next_invoice_version(participant_id)
    
    return InvoiceData(
        participant_name=participant_name,
        version=next_version,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        previous_invoices=previous_invoices,
        new_expenses=new_expense_items,
        this_invoice_total=round(this_invoice_total, 2),
        grand_total=round(grand_total, 2),
        has_new_expenses=len(new_expense_items) > 0
    )


@router.post("/{participant_name}/generate")
def generate_invoice(participant_name: str, request: InvoiceGenerationRequest = None):
    """Generate and save a new invoice version, returning PDF download link"""
    invoice_data = get_invoice_data(participant_name)
    
    if not invoice_data.has_new_expenses:
        raise HTTPException(status_code=400, detail="No new expenses to invoice")
    
    # Filter expenses if specific IDs provided
    if request and request.expense_ids:
        selected_expenses = [e for e in invoice_data.new_expenses if e.expense_id in request.expense_ids]
        if not selected_expenses:
            raise HTTPException(status_code=400, detail="No matching expenses found")
        # Recalculate total for selected expenses only
        selected_total = sum(e.your_share_thb for e in selected_expenses)
        invoice_data = InvoiceData(
            participant_name=invoice_data.participant_name,
            version=invoice_data.version,
            generated_at=invoice_data.generated_at,
            previous_invoices=invoice_data.previous_invoices,
            new_expenses=selected_expenses,
            this_invoice_total=round(selected_total, 2),
            grand_total=round(selected_total, 2),
            has_new_expenses=True
        )
    
    participant = db.get_participant_by_name(participant_name)
    settings = db.get_settings()
    
    # Generate PDF
    pdf_path = pdf_generator.generate_invoice_pdf(invoice_data, settings['trip_name'])
    
    # Save invoice record
    expense_ids = [item.expense_id for item in invoice_data.new_expenses]
    db.create_invoice(
        participant_id=participant['id'],
        version=invoice_data.version,
        total_thb=invoice_data.this_invoice_total,
        pdf_path=pdf_path,
        expense_ids=expense_ids
    )
    
    return {
        "message": f"Invoice #{invoice_data.version} generated for {participant_name}",
        "pdf_path": pdf_path,
        "total": invoice_data.this_invoice_total,
        "grand_total": invoice_data.grand_total
    }


@router.get("/{participant_name}/pdf")
def download_latest_invoice(participant_name: str):
    """Download the latest invoice PDF for a participant"""
    participant = db.get_participant_by_name(participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    invoices = db.get_previous_invoices(participant['id'])
    if not invoices:
        raise HTTPException(status_code=404, detail="No invoices found for this participant")
    
    latest = invoices[-1]
    if not latest['pdf_path']:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        latest['pdf_path'],
        media_type="application/pdf",
        filename=f"invoice_{participant_name}_v{latest['version']}.pdf"
    )


@router.get("/{participant_name}/history")
def get_invoice_history(participant_name: str):
    """Get all previous invoices for a participant"""
    participant = db.get_participant_by_name(participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    return db.get_previous_invoices(participant['id'])


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int):
    """Delete (cancel) an invoice"""
    try:
        db.delete_invoice(invoice_id)
        return {"message": "Invoice cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))





