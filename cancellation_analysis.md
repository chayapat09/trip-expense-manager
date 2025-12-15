# Cancellation Logic Analysis & Implementation Plan

## 🎯 Objective
To correctly handle the cancellation (deletion/voiding) of **Expenses**, **Invoices**, and **Actuals**, ensuring data integrity across the application.

## 🔗 Dependency Chain
The data flows in a strict hierarchy:
1.  **Expenses** (Base Layer) -> Linked to Participants.
2.  **Actuals** (Payment Layer) -> Linked to Expenses.
3.  **Invoices** (Collection Layer) -> Groups Expenses for a Participant.
4.  **Receipts** (Confirmation Layer) -> Groups Invoices for Payment.

## 🛑 Current Risks
*   **Deleting an Expense** that is already Invoiced:
    *   *Result*: The Invoice becomes corrupt (missing line item), but the Participant still owes the Total Amount (if stored statically) or the Total Amount recalculates and mismatches the generated PDF.
    *   *Constraint*: Database Foreign Keys should block this, but application logic should handle it gracefully.
*   **Deleting an Invoice** that is already Paid (Receipted):
    *   *Result*: The Receipt points to a non-existent Invoice. The "Paid Amount" statistics become invalid.
*   **Deleting an Actual** linked to an Expense:
    *   *Result*: The Reconciliation logic assumes the expense hasn't been paid for, potentially leading to incorrect surpluses.

## 🛡️ Proposed Safe Cancellation Flow
We must enforce a **"Reverse Order Deletion"** policy:

### 1. Receipt Cancellation (Voiding)
*   **Action**: User deletes a Receipt.
*   **Consequence**: The linked Invoices are released. They revert from `Paid` to `Unpaid` status.
*   **Logic**:
    1.  Delete rows in `receipt_items` (unlink invoices).
    2.  Delete row in `receipts`.
    3.  *Effect*: Invoices reappear in the "Pending Payment" list.

### 2. Invoice Cancellation
*   **Action**: User deletes an Invoice.
*   **Constraint**: **Cannot delete** if linked to a Receipt. (Must void Receipt first).
*   **Consequence**: The linked Expenses are released. They revert from `Invoiced` to `Pending` status.
*   **Logic**:
    1.  Check if Invoice is in `receipt_items`. If yes -> **Error: Invoice is Paid**.
    2.  Delete rows in `invoice_items` (unlink expenses).
    3.  Delete row in `invoices`.
    4.  *Effect*: Expenses reappear in the "Generate Invoice" list.

### 3. Expense Deletion
*   **Action**: User deletes an Expense.
*   **Constraint**: **Cannot delete** if linked to an Invoice. (Must cancel Invoice first).
*   **Consequence**: The Expense is removed permanently.
*   **Actuals Handling**:
    *   If `Actuals` exist for this expense, they should also be deleted (Cascade) OR the user should be warned.
    *   *Decision*: **Cascade Delete Actuals** ensures no orphaned payment records.
*   **Logic**:
    1.  Check if Expense is in `invoice_items`. If yes -> **Error: Expense is Invoiced**.
    2.  Delete linked `actuals`.
    3.  Delete linked `expense_participants` (handled by DB cascade).
    4.  Delete row in `expenses`.

### 4. Actual Deletion
*   **Action**: User deletes an Actual payment record.
*   **Constraint**: None.
*   **Consequence**: Reconciliation recalculates real rates/totals.

## 💻 Implementation Plan

### Database (`database.py`)
- [ ] Add `check_expense_usage(expense_id)`: Return true if invoiced.
- [ ] Update `delete_expense`: Block if used. Cascade delete actuals.
- [ ] Add `delete_invoice(invoice_id)`: Block if paid. Unlink expenses.
- [ ] Add `delete_receipt(receipt_id)`: Unlink invoices.

### Frontend (`app.js`)
- [ ] **Expenses Tab**: existing delete button is fine, just need to handle the new error message "Cannot delete invoiced expense".
- [ ] **Invoices Tab**: Add "Delete/Cancel" button to Invoice History table.
    *   Only show for *Unpaid* invoices? Or allow delete for Paid but show error? -> **Only show for Unpaid** is better UX.
- [ ] **Overview Tab**: Add "Void" button to Receipt History?
    *   Or in a detailed view. For now, Receipt History in Overview is the best place.

## 📊 Summary of Consequence
| Action | Pre-condition | Post-condition |
|:---|:---|:---|
| **Delete Receipt** | None | Invoices become `Unpaid`. |
| **Delete Invoice** | Must be `Unpaid` | Expenses become `Pending`. |
| **Delete Expense** | Must be `NotInvoiced` | Expense & Actuals removed. |

This implementation ensures strict data integrity and predictable behavior for the user.
