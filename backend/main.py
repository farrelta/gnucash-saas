from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from pydantic import BaseModel

from database import engine
from database import SessionLocal

from models import Base
from models import Session

from docker_manager import (
    create_container,
    stop_container
)

Base.metadata.create_all(bind=engine)

app = FastAPI()


class SessionRequest(BaseModel):
    user_id: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/sessions")
def create_session(req: SessionRequest):

    db = SessionLocal()

    result = create_container(req.user_id)

    session = Session(
        user_id=req.user_id,
        container_id=result["container_id"],
        container_name=result["container_name"],
        internal_host=result["internal_host"],
    	internal_port=result["internal_port"],
	status="RUNNING"
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "url": f"/session/{session.container_name}"
    }


@app.get("/sessions")
def list_sessions():

    db = SessionLocal()

    sessions = db.query(Session).all()

    return sessions


@app.delete("/sessions/{session_id}")
def delete_session(session_id: int):

    db = SessionLocal()

    session = db.query(Session).filter(
        Session.id == session_id
    ).first()

    if not session:
        return {"error": "session not found"}

    stop_container(session.container_id)

    session.status = "STOPPED"

    db.commit()

    return {"message": "session stopped"}


@app.get("/session/{session_id}")
def open_session(session_id: int):

    db = SessionLocal()

    session = db.query(Session).filter(
        Session.id == session_id
    ).first()

    if not session:
        return {"error": "session not found"}

    return RedirectResponse(
    	url=f"/proxy/{session.id}"
    )

@app.get("/session/{session_id}/target")
def get_session_target(session_id: int):

    db = SessionLocal()

    session = db.query(Session).filter(
        Session.id == session_id
    ).first()

    if not session:
        return {"error": "not found"}

    return {
        "host": session.internal_host,
        "port": session.internal_port
    }


@app.get("/internal/session/{session_id}")
def get_session_target(session_id: int):

    db = SessionLocal()

    session = db.query(Session).filter(
        Session.id == session_id
    ).first()

    if not session:
        return {"error": "not found"}

    return {
        "host": session.internal_host,
        "port": session.internal_port
    }
