import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Override DB URL to use a temp sqlite database for testing
test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_file.name}"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["USER_DATA_PATH"] = tempfile.mkdtemp()

from main import app
from database import Base, engine, get_db

# Create a fresh test engine
test_engine = create_engine(
    f"sqlite:///{test_db_file.name}", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    os.unlink(test_db_file.name)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_docker(monkeypatch):
    """Mock the docker_manager create/stop/remove functions to avoid needing Docker daemon in tests."""
    import docker_manager

    def mock_create(user_id, session_token):
        return {
            "container_id": f"mock-container-{session_token}",
            "container_name": f"gnucash-{session_token}",
            "internal_host": f"gnucash-{session_token}",
            "internal_port": 14500
        }

    monkeypatch.setattr(docker_manager, "create_container", mock_create)
    monkeypatch.setattr(docker_manager, "stop_container", lambda cid: None)
    monkeypatch.setattr(docker_manager, "remove_container", lambda cid: None)

@pytest.fixture
def test_user(client):
    """Register and login a test user, returning the auth token."""
    email = "test@example.com"
    password = "password123"
    
    # Ignore 409 if already exists in module scope
    client.post("/api/register", json={"email": email, "password": password})
    
    response = client.post("/api/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"email": email, "token": token}
