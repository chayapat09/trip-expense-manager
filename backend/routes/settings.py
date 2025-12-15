"""
Settings API routes
"""
from fastapi import APIRouter
from schemas import SettingsResponse, SettingsUpdate
import database as db

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings():
    """Get current settings"""
    return db.get_settings()


@router.put("")
def update_settings(data: SettingsUpdate):
    """Update settings"""
    db.update_settings(
        default_buffer_rate=data.default_buffer_rate,
        trip_name=data.trip_name
    )
    return {"message": "Settings updated", "data": db.get_settings()}
