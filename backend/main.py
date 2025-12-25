"""
Trip Expense Manager - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional
import os

# Import routers
from routes import settings, participants, expenses, invoices, refunds, receipts, export, import_db, trips

# Import database to initialize on startup
import database

# Import auth module
from auth import ADMIN_TOKEN, verify_admin_token


# Import version
from version import APP_VERSION

class LoginRequest(BaseModel):
    token: str


app = FastAPI(
    title="Trip Expense Manager",
    description="API for managing group travel expenses with currency conversion and PDF invoices",
    version=APP_VERSION
)


# Authentication middleware to protect mutating endpoints
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow all GET and HEAD requests (read-only)
        if request.method in ["GET", "HEAD"]:
            return await call_next(request)
        
        # Allow auth endpoints
        if request.url.path.startswith("/api/auth"):
            return await call_next(request)
        
        # Allow OPTIONS for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # For mutating operations:
        
        # 1. Allow if valid Global Admin Token
        token = request.headers.get("X-Admin-Token")
        if verify_admin_token(token):
            return await call_next(request)
            
        # 2. Allow if X-Trip-ID is present (Capability URL access)
        if request.headers.get("X-Trip-ID"):
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required. Please provide a Trip ID or Admin Token."}
        )
        
        return await call_next(request)


# Add auth middleware BEFORE CORS
app.add_middleware(AuthMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(settings.router)
app.include_router(participants.router)
app.include_router(expenses.router)

app.include_router(invoices.router)
app.include_router(refunds.router)
app.include_router(receipts.router)
app.include_router(trips.router)
app.include_router(export.router)
app.include_router(import_db.router)


# ========================
# Authentication Endpoints
# ========================
@app.post("/api/auth/login")
def login(request: LoginRequest):
    """Validate admin token and return success status"""
    if request.token == ADMIN_TOKEN:
        return {"success": True, "message": "Login successful"}
    return JSONResponse(
        status_code=401,
        content={"success": False, "detail": "Invalid token"}
    )


@app.post("/api/auth/verify")
def verify_token(x_admin_token: Optional[str] = Header(None)):
    """Verify if current token is still valid"""
    if verify_admin_token(x_admin_token):
        return {"valid": True}
    return {"valid": False}


# Mount PDF files directory for direct access
pdf_dir = os.path.join(os.path.dirname(__file__), "data", "pdfs")
os.makedirs(pdf_dir, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=pdf_dir), name="pdfs")

# Mount static frontend files (CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    """Serve the frontend index.html"""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "Trip Expense Manager API",
        "version": "1.0.0",
        "message": "Frontend not found. API is running."
    }


@app.get("/admin")
def serve_admin():
    """Serve SPA for admin dashboard"""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"message": "Frontend not found"})


@app.get("/t/{full_path:path}")
def serve_spa(full_path: str):
    """Serve SPA for trip routes"""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"message": "Frontend not found"})


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")

