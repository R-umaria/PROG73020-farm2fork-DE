from __future__ import annotations

from unittest.mock import MagicMock

import httpx

from app.core.config import settings
from app.integrations.osrm_client import OsrmClient
from app.integrations.valhalla_client import RouteLeg, RouteResult
from app.schemas.routing import RouteCoordinate
from app.services.planning_service import PlanningService


def test_osrm_client_uses_lon_lat_url_order_and_returns_route_result():
    captured_url: str | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_url
        captured_url = str(request.url)
        return httpx.Response(
            200,
            json={
                "code": "Ok",
                "routes": [
                    {
                        "geometry": "_p~iF~ps|U_ulLnnqC_mqNvxq`@",
                        "distance": 2300.0,
                        "duration": 420.0,
                    }
                ],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    osrm = OsrmClient(base_url="https://router.test", http_client=client)

    result = osrm.route([(43.4700, -80.5200), (43.4800, -80.5300)])

    assert captured_url is not None
    assert "/route/v1/driving/-80.52,43.47;-80.53,43.48" in captured_url
    assert result.total_distance_km == 2.3
    assert result.total_duration_seconds == 420.0
    assert result.encoded_polylines == ["_p~iF~ps|U_ulLnnqC_mqNvxq`@"]
    assert result.raw_payload is not None
    assert result.raw_payload["provider"] == "osrm"
    assert result.raw_payload["trip"]["legs"][0]["summary"]["length"] == 2.3


def test_planning_service_routes_with_osrm_when_valhalla_fails(monkeypatch):
    monkeypatch.setattr(settings, "valhalla_enable_routing", True)
    monkeypatch.setattr(settings, "osrm_enable_routing", True)

    valhalla = MagicMock()
    valhalla.optimized_route.side_effect = RuntimeError("valhalla unavailable")

    osrm = MagicMock()
    osrm.route.return_value = RouteResult(
        total_distance_km=4.2,
        total_duration_seconds=605.0,
        legs=[
            RouteLeg(sequence=1, duration_seconds=605.0, distance_km=4.2, eta_offset_seconds=605.0),
        ],
        raw_payload={"provider": "osrm", "trip": {"summary": {"length": 4.2, "time": 605.0}, "legs": []}},
        encoded_polylines=["abc"],
    )

    service = PlanningService(valhalla_client=valhalla, osrm_client=osrm)
    result = service._route_locations([(43.47, -80.52), (43.48, -80.53)])

    assert result is not None
    assert result.total_distance_km == 4.2
    valhalla.optimized_route.assert_called_once()
    osrm.route.assert_called_once()


def test_decode_route_payload_leg_supports_osrm_style_payload():
    payload = {
        "provider": "osrm",
        "trip": {
            "summary": {"length": 4.2, "time": 605.0},
            "legs": [
                {
                    "shape": "abc123",
                    "summary": {"length": 4.2, "time": 605.0},
                }
            ],
        },
    }

    original_decoder = PlanningService._decode_polyline_coordinates
    PlanningService._decode_polyline_coordinates = staticmethod(lambda encoded: [RouteCoordinate(latitude=43.47, longitude=-80.52)] if encoded == "abc123" else [])
    try:
        encoded, points, distance_km, duration_min, duration_seconds = PlanningService._decode_route_payload_leg(payload, 1)
    finally:
        PlanningService._decode_polyline_coordinates = original_decoder

    assert encoded == "abc123"
    assert points == [RouteCoordinate(latitude=43.47, longitude=-80.52)]
    assert distance_km == 4.2
    assert duration_seconds == 605.0
    assert duration_min == 10
