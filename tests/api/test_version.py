from tests.conftest import client

def test_version():
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.json()
