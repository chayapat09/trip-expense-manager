"""
Invoices API routes - versioned invoices with PDF generation
"""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import Response
from datetime import datetime
from typing import List
from schemas import InvoiceData, InvoiceExpenseItem, InvoiceGenerationRequest
import database as db
from pdf_generator import pdf_generator

router = APIRouter(prefix="/api/invoices", tags=["invoices"])




@router.get("/")
def get_invoices(x_trip_id: str = Header(...)):
    """Get all invoices for list view"""
    return {
        "invoices": db.get_all_invoices_with_status(x_trip_id)
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
def get_overview(x_trip_id: str = Header(...)):
    """Get all invoices, receipts, and stats for overview page"""
    return {
        "stats": db.get_overview_stats(x_trip_id),
        "cash_flow": db.get_cash_flow_stats(x_trip_id),
        "financial_dashboard": db.get_financial_dashboard_data(x_trip_id),
        "expense_breakdown": db.get_expense_breakdown(x_trip_id),
        "invoices": db.get_all_invoices_with_status(x_trip_id),
        "receipts": db.get_all_receipts(x_trip_id)
    }


@router.get("/download/{invoice_id}")
def download_invoice_by_id(invoice_id: int):
    """Download invoice PDF by ID - generated on-the-fly"""
    # Get invoice with participant info
    invoice = db.get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get expenses for this invoice
    expenses = db.get_invoice_expenses(invoice_id)
    
    # Get trip settings
    trip_id = invoice.get('trip_id')
    if not trip_id:
        # Fallback: get trip_id from participant
        with db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT trip_id FROM participants WHERE id = ?", (invoice['participant_id'],))
            row = cursor.fetchone()
            trip_id = row[0] if row else None
    
    settings = db.get_settings(trip_id) if trip_id else {'trip_name': 'Trip'}
    
    # Build invoice data
    items = [calculate_expense_share(e, invoice['participant_id']) for e in expenses]
    
    invoice_data = InvoiceData(
        participant_name=invoice['participant_name'],
        version=invoice['version'],
        generated_at=invoice['created_at'],
        previous_invoices=[],
        new_expenses=items,
        this_invoice_total=invoice['total_thb'],
        grand_total=invoice['total_thb'],
        has_new_expenses=len(items) > 0
    )
    
    # Generate PDF bytes on-the-fly
    pdf_bytes = pdf_generator.generate_invoice_pdf(invoice_data, settings['trip_name'])
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice['participant_name']}_v{invoice['version']}.pdf"
        }
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
def get_invoice_data(participant_name: str, x_trip_id: str = Header(...)) -> InvoiceData:
    """Get invoice data for a participant (without generating PDF)"""
    participant = db.get_participant_by_name(x_trip_id, participant_name)
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
    
    grand_total = this_invoice_total
    
    # Use global ID for preview (estimate)
    next_version = db.get_next_global_invoice_id()
    
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
def generate_invoice(participant_name: str, request: InvoiceGenerationRequest = None, x_trip_id: str = Header(...)):
    """Generate and save a new invoice version, returning PDF download link"""
    invoice_data = get_invoice_data(participant_name, x_trip_id)
    
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
    
    participant = db.get_participant_by_name(x_trip_id, participant_name)
    settings = db.get_settings(x_trip_id)
    
    # 1. create placeholder invoice to get ID
    expense_ids = [item.expense_id for item in invoice_data.new_expenses]
    
    # We pass 0 as temporary version, and empty PDF path
    invoice_id = db.create_invoice(
        trip_id=x_trip_id,
        participant_id=participant['id'],
        version=0, 
        total_thb=invoice_data.this_invoice_total,
        pdf_path="",
        expense_ids=expense_ids
    )
    
    # 2. Update data with actual ID
    invoice_data = InvoiceData(
        participant_name=invoice_data.participant_name,
        version=invoice_id, # Use ID as version
        generated_at=invoice_data.generated_at,
        previous_invoices=invoice_data.previous_invoices,
        new_expenses=invoice_data.new_expenses,
        this_invoice_total=invoice_data.this_invoice_total,
        grand_total=invoice_data.grand_total,
        has_new_expenses=invoice_data.has_new_expenses
    )
    
    # 3. Update version in record (no PDF storage needed - generated on-the-fly)
    db.update_invoice_pdf(invoice_id, "", invoice_id)
    
    return {
        "message": f"Invoice #{invoice_data.version} generated for {participant_name}",
        "invoice_id": invoice_id,
        "total": invoice_data.this_invoice_total,
        "grand_total": invoice_data.grand_total
    }


@router.get("/{participant_name}/pdf")
def download_latest_invoice(participant_name: str, x_trip_id: str = Header(...)):
    """Download the latest invoice PDF for a participant - generated on-the-fly"""
    participant = db.get_participant_by_name(x_trip_id, participant_name)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    invoices = db.get_previous_invoices(participant['id'])
    if not invoices:
        raise HTTPException(status_code=404, detail="No invoices found for this participant")
    
    latest = invoices[-1]
    
    # Generate on-the-fly using download_invoice_by_id
    return download_invoice_by_id(latest['id'])


@router.get("/{participant_name}/history")
def get_invoice_history(participant_name: str, x_trip_id: str = Header(...)):
    """Get all previous invoices for a participant"""
    participant = db.get_participant_by_name(x_trip_id, participant_name)
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





