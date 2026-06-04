import pytest

def test_create_session(client, mock_docker, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/api/sessions", headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "RUNNING"
    assert data["session_token"] is not None
    assert f"/session/{data['session_token']}" == data["url"]

def test_reuse_existing_session(client, mock_docker, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    # Create first session
    res1 = client.post("/api/sessions", headers=headers)
    assert res1.status_code == 201
    
    # Try creating again, should return the same active session
    res2 = client.post("/api/sessions", headers=headers)
    assert res2.status_code == 201
    
    assert res1.json()["id"] == res2.json()["id"]
    assert res1.json()["session_token"] == res2.json()["session_token"]

def test_get_sessions(client, mock_docker, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.get("/api/sessions", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_heartbeat_session(client, mock_docker, test_user):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    # Create a session
    res = client.post("/api/sessions", headers=headers)
    session_id = res.json()["id"]
    
    # Send heartbeat
    hb_res = client.post(f"/api/sessions/{session_id}/heartbeat", headers=headers)
    assert hb_res.status_code == 200
    assert hb_res.json()["message"] == "Heartbeat received"

def test_cross_user_access(client, mock_docker, test_user):
    headers1 = {"Authorization": f"Bearer {test_user['token']}"}
    
    # Create user 2
    client.post("/api/register", json={"email": "user2@example.com", "password": "pwd"})
    res2 = client.post("/api/login", json={"email": "user2@example.com", "password": "pwd"})
    headers2 = {"Authorization": f"Bearer {res2.json()['access_token']}"}
    
    # User 1 creates session
    s1 = client.post("/api/sessions", headers=headers1)
    s1_id = s1.json()["id"]
    
    # User 2 tries to access User 1's session
    acc_res = client.get(f"/api/sessions/{s1_id}", headers=headers2)
    assert acc_res.status_code == 403
    
    # User 2 tries to heartbeat User 1's session
    hb_res = client.post(f"/api/sessions/{s1_id}/heartbeat", headers=headers2)
    assert hb_res.status_code == 403
