import database as db
import sqlite3

def clean():
    # Find UserA
    users = db.get_all_participants()
    user_a = next((u for u in users if u['name'] == 'UserA'), None)
    if not user_a:
        print("UserA not found")
        return

    pid = user_a['id']
    print(f"Cleaning user {pid} (UserA)")

    # Delete Receipts
    receipts = db.get_previous_receipts(pid)
    for r in receipts:
        try:
            db.delete_receipt(r['id'])
            print(f"Deleted receipt {r['id']}")
        except Exception as e:
            print(f"Error deleting receipt {r['id']}: {e}")

    # Delete Invoices
    invoices = db.get_previous_invoices(pid)
    for i in invoices:
        try:
            db.delete_invoice(i['id'])
            print(f"Deleted invoice {i['id']}")
        except Exception as e:
             # If invoice is already deleted or something
            print(f"Error deleting invoice {i['id']}: {e}")

    # Delete Expenses (Find expenses where UserA is a participant)
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT expense_id FROM expense_participants WHERE participant_id = ?", (pid,))
        exps = [row[0] for row in cursor.fetchall()]
        
        for eid in exps:
            try:
                db.delete_expense(eid) 
                print(f"Deleted expense {eid}")
            except Exception as e:
                print(f"Error deleting expense {eid}: {e}")

    # Delete Participant
    db.delete_participant(pid)
    print("Deleted participant")

if __name__ == "__main__":
    clean()
