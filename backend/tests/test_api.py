from fastapi.testclient import TestClient
from inevitable.app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_info():
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Inevitable"
    assert data["tagline"] == "Don't trust the patch. Prove it."
    assert "version" in data
    assert "capabilities" in data
    assert isinstance(data["capabilities"], list)

def test_not_found():
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404
