from unittest.mock import MagicMock
from app.integrations.valhalla_client import ValhallaClient, RouteResult, RouteLeg

mock_valhalla = MagicMock(spec=ValhallaClient)
mock_valhalla.optimized_route.return_value = RouteResult(
    total_distance_km=12.5,
    total_duration_seconds=1800,
    legs=[
        RouteLeg(sequence=2, duration_seconds=900, distance_km=6.0, eta_offset_seconds=900),
        RouteLeg(sequence=3, duration_seconds=900, distance_km=6.5, eta_offset_seconds=1800),
    ],
)
service = PlanningService(db=test_db, valhalla_client=mock_valhalla)