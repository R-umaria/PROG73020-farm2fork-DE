from tests.conftest import client


def test_tracking_status():
    response = client.get("/api/delivery-status/ORD-100")
    assert response.status_code == 200
    assert response.json() == {
        "order_id": "ORD-100",
        "delivery_status": "scheduled",
    }
