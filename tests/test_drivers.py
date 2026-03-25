from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_drivers():
    response = client.get("/api/drivers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
