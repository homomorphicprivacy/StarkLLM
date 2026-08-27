from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
from app.core.config import settings
from app.db.session import engine, Base
from app.api import api_router
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Add columns to existing tables if they don't exist
from sqlalchemy import text
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE chats ADD COLUMN folder_id INTEGER REFERENCES chat_folders(id) ON DELETE SET NULL"))
except Exception:
    pass # Column already exists or table doesn't exist

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost",
]

CORS_HEADERS = {
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Expose-Headers": "X-Chat-ID, X-KB-Used, X-KB-Sources, X-WS-Sources, X-Web-Sources, X-Web-Sources-Urls, X-Chat-Renamed",
    "Access-Control-Max-Age": "600",
}

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)


# ---------------------------------------------------------------------------
# Bulletproof CORS middleware — pure ASGI, wraps every response including
# error responses raised by OAuth2PasswordBearer / HTTPException / 500s.
# ---------------------------------------------------------------------------
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")

    # Handle preflight (OPTIONS) immediately — don't even call the route
    if request.method == "OPTIONS":
        if origin in ALLOWED_ORIGINS:
            headers = {**CORS_HEADERS, "Access-Control-Allow-Origin": origin}
        else:
            headers = {}
        return Response(status_code=204, headers=headers)

    # Call the actual route handler
    response = await call_next(request)

    # Inject CORS headers into every response (including 401/403/500)
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "X-Chat-ID, X-KB-Used, X-KB-Sources, X-WS-Sources, X-Web-Sources, X-Web-Sources-Urls, X-Chat-Renamed"

    return response


# Custom HTTPException handler: returns JSON with CORS headers baked in.
# This catches exceptions raised before/outside the middleware chain.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin", "")
    extra_headers = {}
    if origin in ALLOWED_ORIGINS:
        extra_headers["Access-Control-Allow-Origin"] = origin
        extra_headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=extra_headers,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    extra_headers = {}
    if origin in ALLOWED_ORIGINS:
        extra_headers["Access-Control-Allow-Origin"] = origin
        extra_headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=extra_headers,
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME}

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
