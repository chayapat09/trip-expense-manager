"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


# === Settings ===

class SettingsResponse(BaseModel):
    id: int
    default_buffer_rate: float
    trip_name: str


class SettingsUpdate(BaseModel):
    default_buffer_rate: Optional[float] = None
    trip_name: Optional[str] = None


# === Participants ===

class ParticipantResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[str] = None


class ParticipantCreate(BaseModel):
    name: str


# === Expenses ===

class ExpenseCreate(BaseModel):
    name: str
    amount: float
    currency: str  # 'JPY' or 'THB'
    buffer_rate: float
    participant_ids: List[int]


class ExpenseUpdate(BaseModel):
    name: str
    amount: float
    currency: str
    buffer_rate: float
    participant_ids: List[int]


class ExpenseStatusUpdate(BaseModel):
    status: str  # 'pending' or 'collected'


class ExpenseResponse(BaseModel):
    id: int
    name: str
    amount: float
    currency: str
    buffer_rate: float
    status: str
    collected_thb: float
    per_person_thb: float
    participants: List[str]
    participant_ids: List[int] = []
    invoices: List[int] = []
    is_invoiced: bool = False
    
    # Actuals Info
    is_paid: bool = False
    actual_date: Optional[str] = None
    actual_method: Optional[str] = None
    actual_amount: Optional[float] = None
    actual_currency: Optional[str] = None
    actual_thb: Optional[float] = None
    
    created_at: Optional[str] = None


class LogPaymentRequest(BaseModel):
    date: str
    method: Optional[str] = None
    actual_amount: float
    actual_currency: str
    actual_thb: float


# === Actuals ===

class ActualCreate(BaseModel):
    expense_id: int
    date: str  # YYYY-MM-DD
    payment_method: str
    actual_amount: float
    actual_currency: str
    actual_thb: float


class ActualResponse(BaseModel):
    id: int
    expense_id: int
    expense_name: Optional[str] = None
    date: str
    payment_method: Optional[str] = None
    actual_amount: float
    actual_currency: str
    actual_thb: float
    created_at: Optional[str] = None
    # Calculated field
    real_rate: Optional[float] = None


# === Invoices ===

class InvoiceExpenseItem(BaseModel):
    expense_id: int
    name: str
    original_amount: float
    currency: str
    buffer_rate: float
    share: str  # e.g., "1/5"
    your_share_thb: float


class InvoiceData(BaseModel):
    participant_name: str
    version: int
    generated_at: str
    previous_invoices: List[dict] = []
    new_expenses: List[InvoiceExpenseItem] = []
    this_invoice_total: float
    grand_total: float
    has_new_expenses: bool


class InvoiceGenerationRequest(BaseModel):
    expense_ids: Optional[List[int]] = None


# === Refunds ===

class RefundCollectedItem(BaseModel):
    expense_name: str
    original_amount: float
    currency: str
    buffer_rate: Optional[float] = None
    share: str
    collected_thb: float


class RefundActualItem(BaseModel):
    expense_name: str
    paid_amount: float
    paid_currency: str
    actual_thb: float
    share: str
    your_cost_thb: float


class RefundData(BaseModel):
    participant_name: str
    generated_at: str
    trip_name: str
    collected_items: List[RefundCollectedItem]
    actual_items: List[RefundActualItem]
    total_collected: float
    total_actual: float
    refund_amount: float  # Positive = refund to participant, Negative = owes more


# === Reconciliation ===

class ReconciliationItem(BaseModel):
    participant_name: str
    total_collected: float
    total_actual: float
    surplus_deficit: float  # Positive = surplus (to refund)


# === Receipts ===

class ReceiptItem(BaseModel):
    expense_name: str
    original_amount: float
    currency: str
    buffer_rate: Optional[float] = None
    share: str
    amount_paid: float


class ReceiptData(BaseModel):
    participant_name: str
    receipt_number: int
    generated_at: str
    trip_name: str
    items: List[ReceiptItem]
    total_paid: float
    payment_method: Optional[str] = None


class ReceiptGenerationRequest(BaseModel):
    payment_method: str = "Cash"
    invoice_ids: List[int]

