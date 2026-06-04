import pytest
from models import User, AuditLog
from database import SessionLocal

def test_register(client):
    response = client.post("/api/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()

    # Attempt to register again
    response_dup = client.post("/api/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123"
    })
    assert response_dup.status_code == 409

def test_login(client):
    client.post("/api/register", json={
        "email": "loginuser@example.com",
        "password": "loginpass123"
    })
    
    response = client.post("/api/login", json={
        "email": "loginuser@example.com",
        "password": "loginpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid(client):
    response = client.post("/api/login", json={
        "email": "nonexistent@example.com",
        "password": "wrong"
    })
    assert response.status_code == 401

def test_get_me(client, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.get("/api/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user["email"]

def test_unauthorized_access(client):
    response = client.get("/api/me")
    assert response.status_code == 401
