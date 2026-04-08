from app.api.routes import drivers
from app.schemas.driver import DriverSummaryResponse
from tests.conftest import client


def test_list_drivers(monkeypatch):
    monkeypatch.setattr(
        drivers.service.client,
        "list_drivers",
        lambda: [
            DriverSummaryResponse(
                driver_id=1,
                driver_name="Jordan Lee",
                vehicle_type="Van",
                driver_status="available",
            )
        ],
    )

    response = client.get("/api/drivers/")
    assert response.status_code == 200
    assert response.json() == [
        {
            "driver_id": 1,
            "driver_name": "Jordan Lee",
            "vehicle_type": "Van",
            "driver_status": "available",
        }
    ]
