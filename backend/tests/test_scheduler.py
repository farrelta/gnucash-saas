import pytest
from datetime import datetime, timedelta
from database import SessionLocal
from models import Session
import scheduler

def test_cleanup_idle_sessions(client, mock_docker, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # Create a session
    res = client.post("/api/sessions", headers=headers)
    session_id = res.json()["id"]
    
    # Manually backdate last_activity in database to simulate idle timeout
    db = SessionLocal()
    db_session = db.query(Session).filter(Session.id == session_id).first()
    db_session.last_activity = datetime.utcnow() - timedelta(minutes=65)
    db.commit()
    db.close()
    
    # Trigger scheduler job manually
    scheduler.cleanup_idle_sessions()
    
    # Verify session is now STOPPED
    db = SessionLocal()
    updated_session = db.query(Session).filter(Session.id == session_id).first()
    assert updated_session.status == "STOPPED"
    db.close()

def test_active_sessions_not_cleaned_up(client, mock_docker, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # Create a session
    res = client.post("/api/sessions", headers=headers)
    session_id = res.json()["id"]
    
    # Trigger scheduler job
    scheduler.cleanup_idle_sessions()
    
    # Verify session is still RUNNING
    db = SessionLocal()
    updated_session = db.query(Session).filter(Session.id == session_id).first()
    assert updated_session.status == "RUNNING"
    db.close()
