"""
Simple token-based authentication for Trip Expense Manager
"""
import os
from fastapi import HTTPException, Header
from typing import Optional

# Get admin token from environment, default for development
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "admin123")


def verify_admin_token(token: Optional[str]) -> bool:
    """Verify the admin token"""
    if not token:
        return False
    return token == ADMIN_TOKEN


def require_admin(x_admin_token: Optional[str] = Header(None)):
    """Dependency that requires valid admin token"""
    if not verify_admin_token(x_admin_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin token"
        )
