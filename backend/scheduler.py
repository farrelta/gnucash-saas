"""
Background scheduler for idle-session cleanup.

Uses APScheduler to periodically scan for sessions that have been idle
beyond a configurable timeout, stop and remove their containers, and
record the action in the audit log.
"""

import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session as DbSession

from database import SessionLocal
from docker_manager import remove_container
from models import AuditLog, Session

logger = logging.getLogger(__name__)

IDLE_TIMEOUT_MINUTES: int = int(os.getenv("IDLE_TIMEOUT_MINUTES", "60"))

_scheduler: AsyncIOScheduler | None = None


def cleanup_idle_sessions() -> None:
    """Find and terminate sessions idle longer than *IDLE_TIMEOUT_MINUTES*.

    For each expired session the function:
    1. Calls :func:`docker_manager.remove_container` to stop & remove the
       Docker container.
    2. Sets the session status to ``STOPPED``.
    3. Creates an :class:`AuditLog` entry documenting the cleanup.
    """
    db: DbSession = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=IDLE_TIMEOUT_MINUTES)
        idle_sessions = (
            db.query(Session)
            .filter(Session.status == "RUNNING")
            .filter(Session.last_activity < cutoff)
            .all()
        )

        for session in idle_sessions:
            logger.info(
                "Cleaning up idle session %d (container=%s, user=%d)",
                session.id,
                session.container_id,
                session.user_id,
            )
            try:
                remove_container(session.container_id)
            except Exception:
                logger.exception(
                    "Failed to remove container %s for session %d",
                    session.container_id,
                    session.id,
                )

            session.status = "STOPPED"

            audit = AuditLog(
                user_id=session.user_id,
                action="session_cleanup",
                detail=(
                    f"Idle session {session.id} stopped after "
                    f"{IDLE_TIMEOUT_MINUTES} minutes of inactivity"
                ),
            )
            db.add(audit)

        db.commit()

        if idle_sessions:
            logger.info("Cleaned up %d idle session(s)", len(idle_sessions))
    except Exception:
        db.rollback()
        logger.exception("Error during idle-session cleanup")
    finally:
        db.close()


def start_scheduler() -> None:
    """Create and start the background scheduler.

    Adds a job that runs :func:`cleanup_idle_sessions` every 5 minutes.
    """
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        cleanup_idle_sessions,
        "interval",
        minutes=5,
        id="cleanup_idle_sessions",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Background scheduler started (cleanup every 5 min)")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler if it is running."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped")
