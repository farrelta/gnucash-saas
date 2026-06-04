"""
File management API router.

Provides upload, download, list, and delete operations for user GnuCash
data files.  All endpoints are scoped to the authenticated user's
private directory.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from auth import get_current_user
from models import User
from schemas import FileInfo, MessageResponse

router = APIRouter(prefix="/api/files", tags=["files"])

USER_DATA_PATH: str = os.getenv("USER_DATA_PATH", "/opt/gnucash-data")

ALLOWED_EXTENSIONS: set = {".gnucash", ".qif", ".ofx", ".csv"}
MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_user_dir(user_id: int) -> Path:
    """Return the data directory for *user_id*, creating it if needed."""
    user_dir = Path(USER_DATA_PATH) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def validate_filename(filename: str) -> str:
    """Sanitise *filename* and ensure the extension is allowed.

    Raises ``HTTPException(400)`` on path-traversal attempts or
    disallowed extensions.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Block path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal not allowed",
        )

    # Validate extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File extension '{ext}' not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    return filename


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=FileInfo, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
) -> FileInfo:
    """Upload a GnuCash-compatible file to the user's data directory."""
    filename = validate_filename(file.filename or "")

    # Read content and enforce size limit
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    user_dir = get_user_dir(current_user.id)
    filepath = user_dir / filename
    filepath.write_bytes(content)

    stat = filepath.stat()
    return FileInfo(
        filename=filename,
        size=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
    )


@router.get("/", response_model=List[FileInfo])
async def list_files(
    current_user: User = Depends(get_current_user),
) -> List[FileInfo]:
    """List all files in the authenticated user's data directory."""
    user_dir = get_user_dir(current_user.id)
    files: List[FileInfo] = []

    for entry in user_dir.iterdir():
        if entry.is_file():
            stat = entry.stat()
            files.append(
                FileInfo(
                    filename=entry.name,
                    size=stat.st_size,
                    modified_at=datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ),
                )
            )

    return files


@router.get("/download/{filename}")
async def download_file(
    filename: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download a specific file from the user's data directory."""
    safe_name = validate_filename(filename)
    filepath = get_user_dir(current_user.id) / safe_name

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{safe_name}' not found",
        )

    return FileResponse(
        path=str(filepath),
        filename=safe_name,
        media_type="application/octet-stream",
    )


@router.delete("/{filename}", response_model=MessageResponse)
async def delete_file(
    filename: str,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Delete a file from the user's data directory."""
    safe_name = validate_filename(filename)
    filepath = get_user_dir(current_user.id) / safe_name

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{safe_name}' not found",
        )

    filepath.unlink()
    return MessageResponse(message=f"File '{safe_name}' deleted successfully")
