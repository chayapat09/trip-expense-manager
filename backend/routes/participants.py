"""
Participants API routes
"""
from fastapi import APIRouter, Header, HTTPException
from typing import List
from schemas import ParticipantResponse, ParticipantCreate
import database as db

router = APIRouter(prefix="/api/participants", tags=["participants"])


@router.get("", response_model=List[ParticipantResponse])
def get_participants(x_trip_id: str = Header(...)):
    """Get all participants"""
    return db.get_all_participants(x_trip_id)


@router.post("", response_model=ParticipantResponse)
def add_participant(data: ParticipantCreate, x_trip_id: str = Header(...)):
    """Add a new participant"""
    try:
        participant_id = db.add_participant(x_trip_id, data.name)
        return {"id": participant_id, "name": data.name}
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=400, detail="Participant already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{participant_id}")
def delete_participant(participant_id: int):
    """Delete a participant"""
    db.delete_participant(participant_id)
    return {"message": "Participant deleted"}
