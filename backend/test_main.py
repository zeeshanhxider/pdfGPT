import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_upload_invalid_file():
    """Test upload with invalid file type."""
    # Create a fake non-PDF file
    files = {"file": ("test.txt", b"fake content", "text/plain")}
    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400

def test_chat_without_document():
    """Test chat without uploading document."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello, what's in this document?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "couldn't find relevant information" in data["response"].lower()

def test_status_endpoint():
    """Test system status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

if __name__ == "__main__":
    pytest.main([__file__])
