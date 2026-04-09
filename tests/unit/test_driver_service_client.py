from __future__ import annotations

import httpx
import pytest

from app.integrations.driver_service_client import DriverServiceClient
from app.integrations.errors import UpstreamBadResponseError, UpstreamTimeoutError


def test_driver_service_client_validates_driver_roster_response():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "drivers": [
                    {
                        "driver_id": 7,
                        "driver_name": "Dana Wu",
                        "vehicle_type": "Van",
                        "driver_status": "available",
                    }
                ]
            },
        )
    )
    client = DriverServiceClient(
        base_url="http://driver-service.test",
        drivers_path="/api/drivers",
        http_client=httpx.Client(transport=transport),
        enable_dev_fallback=False,
    )

    drivers = client.list_drivers()

    assert len(drivers) == 1
    assert drivers[0].driver_id == 7
    assert drivers[0].driver_name == "Dana Wu"
    assert drivers[0].driver_status == "available"


def test_driver_service_client_maps_timeout_to_domain_error():
    transport = httpx.MockTransport(lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("boom")))
    client = DriverServiceClient(
        base_url="http://driver-service.test",
        drivers_path="/api/drivers",
        http_client=httpx.Client(transport=transport),
        enable_dev_fallback=False,
    )

    with pytest.raises(UpstreamTimeoutError, match="Driver Service request timed out"):
        client.list_drivers()


def test_driver_service_client_rejects_invalid_driver_payload():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "name": "Legacy Shape",
                    "vehicle_type": "Van",
                    "status": "available",
                }
            ],
        )
    )
    client = DriverServiceClient(
        base_url="http://driver-service.test",
        drivers_path="/api/drivers",
        http_client=httpx.Client(transport=transport),
        enable_dev_fallback=False,
    )

    with pytest.raises(UpstreamBadResponseError, match="invalid driver roster response"):
        client.list_drivers()


def test_driver_service_client_uses_dev_fallback_only_when_explicitly_enabled():
    client = DriverServiceClient(enable_dev_fallback=True)

    drivers = client.list_drivers()

    assert [driver.driver_id for driver in drivers] == [1, 2, 3]
    assert drivers[0].driver_name == "Jordan Lee"
