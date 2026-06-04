"""
GnuCash SaaS API — main FastAPI application.

Provides user registration/login, container-session lifecycle management,
file operations, and internal Traefik routing endpoints.
"""

from dotenv import load_dotenv

load_dotenv()

import logging
import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session as DbSession

from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from database import Base, engine, get_db
from docker_manager import create_container, remove_container
from file_manager import router as file_router
from models import AuditLog, Session, User
from scheduler import start_scheduler, stop_scheduler
from schemas import (
    MessageResponse,
    SessionResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
RATE_LIMIT_REGISTER: str = os.getenv("RATE_LIMIT_REGISTER", "3/minute")
RATE_LIMIT_LOGIN: str = os.getenv("RATE_LIMIT_LOGIN", "5/minute")

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    # Startup
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GnuCash SaaS API",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach rate-limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
CORS_ORIGINS: List[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include sub-routers
app.include_router(file_router)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _session_to_response(session: Session) -> SessionResponse:
    """Convert a :class:`Session` ORM instance to a response schema."""
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        session_token=session.session_token,
        container_name=session.container_name,
        status=session.status,
        created_at=session.created_at,
        last_activity=session.last_activity,
        url=f"/session/{session.session_token}" if session.session_token else None,
    )


# ===================================================================
# AUTH ENDPOINTS
# ===================================================================


@app.post(
    "/api/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    body: UserRegister,
    db: DbSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user account and return a JWT."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(
        AuditLog(
            user_id=user.id,
            action="register",
            detail=f"User registered with email {user.email}",
        )
    )
    db.commit()

    token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=token)


@app.post("/api/login", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    body: UserLogin,
    db: DbSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user and return a JWT."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    db.add(
        AuditLog(
            user_id=user.id,
            action="login",
            detail=f"User {user.email} logged in",
        )
    )
    db.commit()

    token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=token)


@app.get("/api/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


# ===================================================================
# SESSION ENDPOINTS
# ===================================================================


@app.post(
    "/api/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> SessionResponse:
    """Create a new GnuCash container session (or return an existing one)."""
    # Check for an already-running session
    existing = (
        db.query(Session)
        .filter(Session.user_id == current_user.id, Session.status == "RUNNING")
        .first()
    )
    if existing:
        return _session_to_response(existing)

    # Spin up a new container
    session_token = str(uuid.uuid4())
    result = create_container(current_user.id, session_token)

    session = Session(
        user_id=current_user.id,
        session_token=session_token,
        container_id=result["container_id"],
        container_name=result["container_name"],
        internal_host=result["internal_host"],
        internal_port=result["internal_port"],
        status="RUNNING",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="session_create",
            detail=f"Created session {session.id} (container={session.container_name})",
        )
    )
    db.commit()

    return _session_to_response(session)


@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> List[SessionResponse]:
    """List all sessions for the current user, newest first."""
    sessions = (
        db.query(Session)
        .filter(Session.user_id == current_user.id)
        .order_by(Session.created_at.desc())
        .all()
    )
    return [_session_to_response(s) for s in sessions]


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> SessionResponse:
    """Return details for a single session owned by the current user."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    return _session_to_response(session)


@app.post("/api/sessions/{session_id}/heartbeat", response_model=MessageResponse)
async def heartbeat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> MessageResponse:
    """Update the last_activity timestamp for a running session."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if session.status != "RUNNING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not running")

    session.last_activity = datetime.utcnow()
    db.commit()
    return MessageResponse(message="Heartbeat received")


@app.delete("/api/sessions/{session_id}", response_model=MessageResponse)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> MessageResponse:
    """Stop and remove a container session."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    remove_container(session.container_id)
    session.status = "STOPPED"

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="session_delete",
            detail=f"Stopped session {session.id} (container={session.container_name})",
        )
    )
    db.commit()

    return MessageResponse(message="Session stopped successfully")


# ===================================================================
# HEALTH ENDPOINT
# ===================================================================


@app.get("/api/health")
async def health_check() -> dict:
    """Unauthenticated health-check endpoint."""
    return {"status": "healthy"}


# ===================================================================
# INTERNAL / TRAEFIK ENDPOINTS  (no auth — used by reverse proxy)
# ===================================================================


@app.get("/session/{session_name}")
def open_session_redirect(session_name: str, db: DbSession = Depends(get_db)):
    """Redirect to the proxied Xpra session."""
    session = (
        db.query(Session)
        .filter(
            (Session.session_token == session_name)
            | (Session.id == _safe_int(session_name))
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return RedirectResponse(url=f"/session/{session.session_token}/")


@app.get("/session/{session_name}/target")
def get_session_target(session_name: str, db: DbSession = Depends(get_db)):
    """Return the internal host/port for Traefik forwarding."""
    session = (
        db.query(Session)
        .filter(
            (Session.session_token == session_name)
            | (Session.id == _safe_int(session_name))
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return {"host": session.internal_host, "port": session.internal_port}


@app.get("/internal/session/{session_name}")
def internal_session_info(session_name: str, db: DbSession = Depends(get_db)):
    """Internal endpoint for Traefik — returns host/port."""
    session = (
        db.query(Session)
        .filter(
            (Session.session_token == session_name)
            | (Session.id == _safe_int(session_name))
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return {"host": session.internal_host, "port": session.internal_port}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _safe_int(value: str) -> int:
    """Try to parse *value* as int; return ``-1`` on failure so the OR
    filter never accidentally matches a real row."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return -1
