import csv
import io
import json
import zipfile
import sqlite3
from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Response
from database import get_db_connection
from auth import verify_admin_token
from typing import Optional
from version import APP_VERSION

router = APIRouter(prefix="/api/import", tags=["import"])

@router.post("/db")
async def import_database(
    file: UploadFile = File(...),
    x_admin_token: Optional[str] = Header(None)
):
    """
    Import database from a ZIP backup.
    WARNING: This completely overwrites the current database.
    Requires admin authentication and version match.
    """
    if not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")

    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a ZIP file.")

    content = await file.read()
    
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
            # 1. Check Metadata & Version
            if "metadata.json" not in zip_file.namelist():
                raise HTTPException(status_code=400, detail="Invalid backup: Missing metadata.json")
            
            with zip_file.open("metadata.json") as f:
                metadata = json.load(f)
                backup_version = metadata.get("version")
                
            if backup_version != APP_VERSION:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Version mismatch. Backup version ({backup_version}) does not match current App version ({APP_VERSION}). Import rejected to prevent data corruption."
                )

            # 2. Perform Restoration
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Disable FK for bulk insert (safe because we are importing consistent state)
            # Actually, let's keep it ON but delete in correct order, then insert in correct order.
            # OR just disable it for simplicity during restore.
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            try:
                cursor.execute("BEGIN TRANSACTION")
                
                # Tables to process in specific order (dependency wise)
                # We will delete everything first.
                # Include 'trips' for multi-trip support
                all_tables = [
                    "receipt_items", "invoice_items", "expense_participants", 
                    "receipts", "invoices", "refunds", "expenses", "participants", "settings",
                    "trips"
                ]
                
                for table in all_tables:
                    cursor.execute(f"DELETE FROM {table}")
                    
                # Now insert data (Order mostly doesn't matter with FK keys OFF, but let's be nice)
                # Include 'trips' for multi-trip support
                tables_to_import = [
                    "trips", "settings", "participants", "expenses", "refunds", 
                    "invoices", "receipts", "expense_participants", "invoice_items", "receipt_items"
                ]
                
                for table in tables_to_import:
                    filename = f"{table}.csv"
                    if filename in zip_file.namelist():
                        with zip_file.open(filename) as f:
                            # Read CSV
                            csv_content = io.TextIOWrapper(f, encoding='utf-8', newline='')
                            reader = csv.DictReader(csv_content)
                            
                            # Insert rows
                            rows_to_insert = []
                            for row in reader:
                                # Convert empty strings to None (NULL) for optional fields
                                cleaned_row = {k: (None if v == '' else v) for k, v in row.items()}
                                rows_to_insert.append(cleaned_row)
                                
                            if rows_to_insert:
                                columns = rows_to_insert[0].keys()
                                placeholders = ", ".join(["?"] * len(columns))
                                col_names = ", ".join(columns)
                                sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                                
                                for row in rows_to_insert:
                                    cursor.execute(sql, list(row.values()))
                                    
                cursor.execute("COMMIT")
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise HTTPException(status_code=500, detail=f"Database restoration failed: {str(e)}")
            finally:
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.close()
            
            # Run migration to handle orphaned data (NULL trip_id)
            # This creates Legacy Trip if needed and assigns orphaned records
            from database import init_db
            init_db()
                
            return {"success": True, "message": "Database successfully restored from backup."}
            
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
