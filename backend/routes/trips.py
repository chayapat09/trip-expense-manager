from fastapi import APIRouter, HTTPException, Body, Header
from typing import List, Dict
import database as db

router = APIRouter(prefix="/api/trips", tags=["trips"])

@router.post("")
def create_trip(name: str = Body(..., embed=True)):
    """Create a new trip"""
    trip_id = db.create_trip(name)
    return {"id": trip_id, "name": name}

@router.get("/{trip_id}")
def get_trip(trip_id: str):
    """Get trip details"""
    trip = db.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.get("")
def list_trips():
    """List all trips"""
    return db.list_trips()


@router.get("/admin/dashboard")
def get_admin_dashboard(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """Get admin dashboard stats. Requires Admin Token."""
    # Simple check against the env var or hardcoded token from main.py?
    # Actually main.py defines the ADMIN_TOKEN. Ideally we import it.
    # But for now, let's look at how auth is handled.
    # It is handled in middleware.
    # But since GET is open by default in middleware, we must enforce it here.
    # We need to know the ADMIN_TOKEN.
    # It takes it from os.environ or defaults to "admin123".
    import os
    expected_token = os.getenv("ADMIN_TOKEN", "admin123")
    if x_admin_token != expected_token:
         raise HTTPException(status_code=401, detail="Invalid Admin Token")
    
    return db.get_admin_dashboard_stats()
