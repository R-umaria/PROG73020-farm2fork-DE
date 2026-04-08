from tests.conftest import client


def test_tracking_status():
    response = client.get("/api/delivery-status/100")
    assert response.status_code == 200
    assert response.json() == {
        "order_id": 100,
        "delivery_status": "scheduled",
    }
