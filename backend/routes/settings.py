"""
Settings API routes
"""
from fastapi import APIRouter, Header
from schemas import SettingsResponse, SettingsUpdate
import database as db

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(x_trip_id: str = Header(...)):
    """Get current settings"""
    return db.get_settings(x_trip_id)


@router.put("")
def update_settings(data: SettingsUpdate, x_trip_id: str = Header(...)):
    """Update settings"""
    db.update_settings(
        trip_id=x_trip_id,
        default_buffer_rate=data.default_buffer_rate,
        trip_name=data.trip_name
    )
    return {"message": "Settings updated", "data": db.get_settings(x_trip_id)}
