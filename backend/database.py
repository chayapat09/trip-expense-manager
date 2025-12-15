"""
Database models and connection for Trip Expense Manager
Using SQLite with raw SQL for simplicity
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "trip_expenses.db")


def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database with all tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                default_buffer_rate REAL DEFAULT 0.25,
                trip_name TEXT DEFAULT 'Japan Trip 2025'
            )
        """)
        
        # Insert default settings if not exists
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO settings (id, default_buffer_rate, trip_name) VALUES (1, 0.25, 'Japan Trip 2025')"
            )
        
        # Participants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default participants
        default_participants = ['Nine', 'Nam', 'Team', 'Ti', 'Thep']
        for name in default_participants:
            cursor.execute(
                "INSERT OR IGNORE INTO participants (name) VALUES (?)",
                (name,)
            )
        
        # Expenses table (multi-currency + per-transaction rate)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                buffer_rate REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Actuals (Merged)
                actual_date TEXT,
                actual_method TEXT,
                actual_amount REAL,
                actual_currency TEXT,
                actual_thb REAL
            )
        """)
        
        # Check if actual columns actally exist (for migration)
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'actual_date' not in columns:
            print("Migrating schema: Adding actuals columns to expenses...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN actual_date TEXT")
            cursor.execute("ALTER TABLE expenses ADD COLUMN actual_method TEXT")
            cursor.execute("ALTER TABLE expenses ADD COLUMN actual_amount REAL")
            cursor.execute("ALTER TABLE expenses ADD COLUMN actual_currency TEXT")
            cursor.execute("ALTER TABLE expenses ADD COLUMN actual_thb REAL")
        
        
        # Expense-Participant junction
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expense_participants (
                expense_id INTEGER,
                participant_id INTEGER,
                PRIMARY KEY (expense_id, participant_id),
                FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
                FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
            )
        """)
        
        # Actuals table (Deprecated - keeping for data safety until migration complete)
        # We will migrate data from here if it still exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='actuals'")
        if cursor.fetchone():
            print("Checking checking for legacy actuals data to migrate...")
            cursor.execute("SELECT * FROM actuals")
            rows = cursor.fetchall()
            if rows:
                print(f"Migrating {len(rows)} legacy actuals...")
                for row in rows:
                    cursor.execute("""
                        UPDATE expenses 
                        SET actual_date = ?, actual_method = ?, actual_amount = ?, actual_currency = ?, actual_thb = ?, status = 'collected'
                        WHERE id = ?
                    """, (row['date'], row['payment_method'], row['actual_amount'], row['actual_currency'], row['actual_thb'], row['expense_id']))
            
            # Rename/Drop map legacy table to avoid re-migration
            cursor.execute("DROP TABLE actuals")
            print("Legacy actuals table dropped.")
        
        # Refunds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER,
                amount_thb REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
            )
        """)
        
        # Invoices table (versioned)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER,
                version INTEGER NOT NULL,
                total_thb REAL NOT NULL,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
            )
        """)
        
        # Invoice items junction
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                invoice_id INTEGER,
                expense_id INTEGER,
                PRIMARY KEY (invoice_id, expense_id),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
            )
        """)
        
        # Receipts table (payment confirmations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER,
                receipt_number INTEGER NOT NULL,
                total_thb REAL NOT NULL,
                payment_method TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
            )
        """)
        
        # Receipt items junction (which invoiced expenses are paid)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipt_items (
                receipt_id INTEGER,
                invoice_id INTEGER,
                PRIMARY KEY (receipt_id, invoice_id),
                FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            )
        """)


# === Settings Functions ===

def get_settings() -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else {}


def update_settings(default_buffer_rate: Optional[float] = None, trip_name: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if default_buffer_rate is not None:
            cursor.execute("UPDATE settings SET default_buffer_rate = ? WHERE id = 1", (default_buffer_rate,))
        if trip_name is not None:
            cursor.execute("UPDATE settings SET trip_name = ? WHERE id = 1", (trip_name,))


# === Participant Functions ===

def get_all_participants() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM participants ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def add_participant(name: str) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO participants (name) VALUES (?)", (name,))
        return cursor.lastrowid


def delete_participant(participant_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM participants WHERE id = ?", (participant_id,))


# === Expense Functions ===

def get_all_expenses() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, GROUP_CONCAT(DISTINCT p.name) as participant_names, 
                   GROUP_CONCAT(DISTINCT p.id) as participant_ids,
                   GROUP_CONCAT(DISTINCT i.version) as invoice_versions
            FROM expenses e
            LEFT JOIN expense_participants ep ON e.id = ep.expense_id
            LEFT JOIN participants p ON ep.participant_id = p.id
            LEFT JOIN invoice_items ii ON e.id = ii.expense_id
            LEFT JOIN invoices i ON ii.invoice_id = i.id
            GROUP BY e.id
            ORDER BY e.created_at DESC
        """)
        expenses = []
        for row in cursor.fetchall():
            expense = dict(row)
            expense['participants'] = expense['participant_names'].split(',') if expense['participant_names'] else []
            expense['participant_ids'] = [int(x) for x in expense['participant_ids'].split(',')] if expense['participant_ids'] else []
            # Parse invoice versions
            if expense['invoice_versions']:
                expense['invoices'] = [int(v) for v in expense['invoice_versions'].split(',')]
            else:
                expense['invoices'] = []
            
            # Mark as paid if actual info exists
            expense['is_paid'] = expense['status'] == 'collected'
            
            expenses.append(expense)
        return expenses


def get_expense_by_id(expense_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, GROUP_CONCAT(p.name) as participant_names,
                   GROUP_CONCAT(p.id) as participant_ids
            FROM expenses e
            LEFT JOIN expense_participants ep ON e.id = ep.expense_id
            LEFT JOIN participants p ON ep.participant_id = p.id
            WHERE e.id = ?
            GROUP BY e.id
        """, (expense_id,))
        row = cursor.fetchone()
        if row:
            expense = dict(row)
            expense['participants'] = expense['participant_names'].split(',') if expense['participant_names'] else []
            expense['participant_ids'] = [int(x) for x in expense['participant_ids'].split(',')] if expense['participant_ids'] else []
            expense['is_paid'] = expense['status'] == 'collected'
            return expense
        return None


def add_expense(name: str, amount: float, currency: str, buffer_rate: float, participant_ids: List[int]) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (name, amount, currency, buffer_rate, status) VALUES (?, ?, ?, ?, 'pending')",
            (name, amount, currency.upper(), buffer_rate)
        )
        expense_id = cursor.lastrowid
        
        for pid in participant_ids:
            cursor.execute(
                "INSERT INTO expense_participants (expense_id, participant_id) VALUES (?, ?)",
                (expense_id, pid)
            )
        return expense_id


def update_expense(expense_id: int, name: str, amount: float, currency: str, buffer_rate: float, participant_ids: List[int]):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE expenses SET name = ?, amount = ?, currency = ?, buffer_rate = ? WHERE id = ?",
            (name, amount, currency.upper(), buffer_rate, expense_id)
        )
        cursor.execute("DELETE FROM expense_participants WHERE expense_id = ?", (expense_id,))
        for pid in participant_ids:
            cursor.execute(
                "INSERT INTO expense_participants (expense_id, participant_id) VALUES (?, ?)",
                (expense_id, pid)
            )


def update_expense_status(expense_id: int, status: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE expenses SET status = ? WHERE id = ?", (status, expense_id))


def log_expense_payment(expense_id: int, date: str, method: str, actual_amount: float, actual_currency: str, actual_thb: float):
    """Log actual payment details for an expense"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expenses 
            SET actual_date = ?, actual_method = ?, actual_amount = ?, actual_currency = ?, actual_thb = ?, status = 'collected'
            WHERE id = ?
        """, (date, method, actual_amount, actual_currency, actual_thb, expense_id))


def delete_expense(expense_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if invoiced
        cursor.execute("SELECT invoice_id FROM invoice_items WHERE expense_id = ?", (expense_id,))
        if cursor.fetchone():
            raise ValueError("Cannot delete expense that is included in an invoice. Please delete the invoice first.")
            
        # No more 'actuals' table to clean up
        
        # Delete expense (cascade deletes participants)
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


# === Invoice Functions ===

def get_invoiced_expense_ids(participant_id: int) -> List[int]:
    """Get all expense IDs that have been invoiced for a participant"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ii.expense_id
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.participant_id = ?
        """, (participant_id,))
        return [row[0] for row in cursor.fetchall()]


def get_participant_expenses(participant_id: int) -> List[Dict[str, Any]]:
    """Get all expenses for a participant"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, 
                   (SELECT COUNT(*) FROM expense_participants WHERE expense_id = e.id) as total_participants
            FROM expenses e
            JOIN expense_participants ep ON e.id = ep.expense_id
            WHERE ep.participant_id = ?
            ORDER BY e.created_at
        """, (participant_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_next_invoice_version(participant_id: int) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(version) FROM invoices WHERE participant_id = ?",
            (participant_id,)
        )
        result = cursor.fetchone()[0]
        return (result or 0) + 1


def get_previous_invoices(participant_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM invoices 
            WHERE participant_id = ? 
            ORDER BY version
        """, (participant_id,))
        return [dict(row) for row in cursor.fetchall()]


def create_invoice(participant_id: int, version: int, total_thb: float, pdf_path: str, expense_ids: List[int]) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO invoices (participant_id, version, total_thb, pdf_path) VALUES (?, ?, ?, ?)",
            (participant_id, version, total_thb, pdf_path)
        )
        invoice_id = cursor.lastrowid
        
        for eid in expense_ids:
            cursor.execute(
                "INSERT INTO invoice_items (invoice_id, expense_id) VALUES (?, ?)",
                (invoice_id, eid)
            )
        return invoice_id


def get_invoice_by_id(invoice_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, p.name as participant_name
            FROM invoices i
            JOIN participants p ON i.participant_id = p.id
            WHERE i.id = ?
        """, (invoice_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_invoice(invoice_id: int):
    """Delete an invoice if not paid"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if paid
        cursor.execute("SELECT receipt_id FROM receipt_items WHERE invoice_id = ?", (invoice_id,))
        if cursor.fetchone():
            raise ValueError("Cannot delete invoice that has been paid. Please void the receipt first.")
            
        # Delete items (unlinks expenses)
        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        
        # Delete invoice
        cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))


# === Receipt Functions ===

def get_unpaid_invoices(participant_id: int) -> List[Dict[str, Any]]:
    """Get invoices that haven't been receipted yet"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.* FROM invoices i
            WHERE i.participant_id = ?
            AND i.id NOT IN (SELECT invoice_id FROM receipt_items)
            ORDER BY i.version
        """, (participant_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_next_receipt_number(participant_id: int) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(receipt_number) FROM receipts WHERE participant_id = ?",
            (participant_id,)
        )
        result = cursor.fetchone()[0]
        return (result or 0) + 1


def get_previous_receipts(participant_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM receipts 
            WHERE participant_id = ? 
            ORDER BY receipt_number
        """, (participant_id,))
        return [dict(row) for row in cursor.fetchall()]


def create_receipt(participant_id: int, receipt_number: int, total_thb: float, payment_method: str, pdf_path: str, invoice_ids: List[int]) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO receipts (participant_id, receipt_number, total_thb, payment_method, pdf_path) VALUES (?, ?, ?, ?, ?)",
            (participant_id, receipt_number, total_thb, payment_method, pdf_path)
        )
        receipt_id = cursor.lastrowid
        
        for inv_id in invoice_ids:
            cursor.execute(
                "INSERT INTO receipt_items (receipt_id, invoice_id) VALUES (?, ?)",
                (receipt_id, inv_id)
            )
        return receipt_id


def get_receipt_by_id(receipt_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, p.name as participant_name
            FROM receipts r
            JOIN participants p ON r.participant_id = p.id
            WHERE r.id = ?
        """, (receipt_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_receipt_invoices(receipt_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*
            FROM invoices i
            JOIN receipt_items ri ON i.id = ri.invoice_id
            WHERE ri.receipt_id = ?
            ORDER BY i.version
        """, (receipt_id,))
        return [dict(row) for row in cursor.fetchall()]


def delete_receipt(receipt_id: int):
    """Delete (void) a receipt"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Delete items (unlinks invoices)
        cursor.execute("DELETE FROM receipt_items WHERE receipt_id = ?", (receipt_id,))
        
        # Delete receipt
        cursor.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))


def get_invoice_expenses(invoice_id: int) -> List[Dict[str, Any]]:
    """Get all expenses in an invoice"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, 
                   (SELECT COUNT(*) FROM expense_participants WHERE expense_id = e.id) as total_participants
            FROM expenses e
            JOIN invoice_items ii ON e.id = ii.expense_id
            WHERE ii.invoice_id = ?
        """, (invoice_id,))
        return [dict(row) for row in cursor.fetchall()]


# === Reconciliation Functions ===

def get_participant_by_name(name: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM participants WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_participant_actuals(participant_id: int) -> List[Dict[str, Any]]:
    """Get actuals (paid expenses) where participant is involved"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.actual_date as date, e.actual_method as payment_method, e.actual_amount, e.actual_currency, e.actual_thb, e.name as expense_name, e.amount as original_amount, e.currency as original_currency,
                   (SELECT COUNT(*) FROM expense_participants WHERE expense_id = e.id) as total_participants
            FROM expenses e
            JOIN expense_participants ep ON e.id = ep.expense_id
            WHERE ep.participant_id = ? AND e.status = 'collected'
            ORDER BY e.actual_date
        """, (participant_id,))
        return [dict(row) for row in cursor.fetchall()]


# === Overview Functions ===

def get_all_invoices_with_status() -> List[Dict[str, Any]]:
    """Get all invoices with their payment status and receipt info"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, p.name as participant_name,
                   CASE WHEN ri.receipt_id IS NOT NULL THEN 'paid' ELSE 'unpaid' END as status,
                   r.receipt_number
            FROM invoices i
            JOIN participants p ON i.participant_id = p.id
            LEFT JOIN receipt_items ri ON i.id = ri.invoice_id
            LEFT JOIN receipts r ON ri.receipt_id = r.id
            ORDER BY i.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_all_receipts() -> List[Dict[str, Any]]:
    """Get all receipts with linked invoices"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, p.name as participant_name
            FROM receipts r
            JOIN participants p ON r.participant_id = p.id
            ORDER BY r.created_at DESC
        """)
        receipts = [dict(row) for row in cursor.fetchall()]
        
        # Get linked invoices for each receipt
        for receipt in receipts:
            cursor.execute("""
                SELECT i.version FROM invoices i
                JOIN receipt_items ri ON i.id = ri.invoice_id
                WHERE ri.receipt_id = ?
                ORDER BY i.version
            """, (receipt['id'],))
            receipt['invoice_versions'] = [row[0] for row in cursor.fetchall()]
        
        return receipts


# === Overview Functions ===

def get_all_invoices_with_status() -> List[Dict[str, Any]]:
    """Get all invoices with their payment status and receipt info"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, p.name as participant_name,
                   CASE WHEN ri.receipt_id IS NOT NULL THEN 'paid' ELSE 'unpaid' END as status,
                   r.receipt_number
            FROM invoices i
            JOIN participants p ON i.participant_id = p.id
            LEFT JOIN receipt_items ri ON i.id = ri.invoice_id
            LEFT JOIN receipts r ON ri.receipt_id = r.id
            ORDER BY i.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_all_receipts() -> List[Dict[str, Any]]:
    """Get all receipts with linked invoices"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, p.name as participant_name
            FROM receipts r
            JOIN participants p ON r.participant_id = p.id
            ORDER BY r.created_at DESC
        """)
        receipts = [dict(row) for row in cursor.fetchall()]
        
        # Get linked invoices for each receipt
        for receipt in receipts:
            cursor.execute("""
                SELECT i.version FROM invoices i
                JOIN receipt_items ri ON i.id = ri.invoice_id
                WHERE ri.receipt_id = ?
                ORDER BY i.version
            """, (receipt['id'],))
            receipt['invoice_versions'] = [row[0] for row in cursor.fetchall()]
        
        return receipts



def get_overview_stats() -> Dict[str, Any]:
    """Get overview statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total invoices and amount
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_thb), 0) FROM invoices")
        inv_count, inv_total = cursor.fetchone()
        
        # Paid invoices
        cursor.execute("""
            SELECT COUNT(DISTINCT i.id), COALESCE(SUM(i.total_thb), 0)
            FROM invoices i
            JOIN receipt_items ri ON i.id = ri.invoice_id
        """)
        paid_count, paid_total = cursor.fetchone()
        
        # Receipts
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_thb), 0) FROM receipts")
        receipt_count, receipt_total = cursor.fetchone()
        
        return {
            "total_invoices": inv_count,
            "total_invoiced_amount": round(inv_total, 2),
            "paid_invoices": paid_count,
            "paid_amount": round(paid_total, 2),
            "unpaid_invoices": inv_count - paid_count,
            "unpaid_amount": round(inv_total - paid_total, 2),
            "total_receipts": receipt_count,
            "total_received": round(receipt_total, 2)
        }


# Initialize database on import
init_db()
