from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_deliveries():
    response = client.get("/api/deliveries/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
