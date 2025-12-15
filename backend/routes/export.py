import csv
import io
import os
import sqlite3
import zipfile
from fastapi import APIRouter, Header, HTTPException, Response
from database import get_db_connection
from auth import verify_admin_token
from typing import Optional

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/db")
def export_database(x_admin_token: Optional[str] = Header(None)):
    """
    Export the entire database as a ZIP file containing CSVs for each table.
    Requires admin authentication.
    """
    if not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row['name'] for row in cursor.fetchall() if not row['name'].startswith('sqlite_')]

    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if not rows and cursor.description:
                # Handle empty tables - just headers
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer)
                headers = [description[0] for description in cursor.description]
                csv_writer.writerow(headers)
                zip_file.writestr(f"{table}.csv", csv_buffer.getvalue())
                continue
            
            if rows:
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer)
                
                # Write headers
                headers = rows[0].keys()
                csv_writer.writerow(headers)
                
                # Write data
                for row in rows:
                    csv_writer.writerow(list(row))
                
                zip_file.writestr(f"{table}.csv", csv_buffer.getvalue())
    
    conn.close()
    
    # Seek to beginning
    zip_buffer.seek(0)
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=trip_expenses_backup.zip"
        }
    )
