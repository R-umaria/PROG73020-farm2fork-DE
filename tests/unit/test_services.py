#command: docker-compose exec app pytest tests/unit/test_services.py

import unittest
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, call
from uuid import uuid4


@dataclass
class RouteLeg:
    sequence: int
    duration_seconds: float
    distance_km: float
    eta_offset_seconds: float


@dataclass
class RouteResult:
    total_distance_km: float
    total_duration_seconds: float
    legs: list
    raw_payload: dict | None = None



def apply_valhalla_result(route_group, valid_stops, result, update_group_fn, update_stop_fn):

    update_group_fn(
        route_group_id=route_group["id"],
        estimated_distance_km=result.total_distance_km,
        estimated_duration_min=int(result.total_duration_seconds // 60),
        route_payload=result.raw_payload,
    )

    base_time = valid_stops[0]["estimated_arrival"]
    if base_time is not None and base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=timezone.utc)

    if base_time is not None:
        for leg in result.legs:
            idx = leg.sequence - 1
            if idx < len(valid_stops):
                eta = base_time + timedelta(seconds=leg.eta_offset_seconds)
                update_stop_fn(
                    route_stop_id=valid_stops[idx]["id"],
                    estimated_arrival=eta,
                )




class TestValhallaResultApplication(unittest.TestCase):

    def _make_stops(self, n, base_time):
        return [
            {"id": uuid4(), "sequence": i + 1, "estimated_arrival": base_time}
            for i in range(n)
        ]

    def test_route_group_summary_is_saved(self):
        group = {"id": uuid4()}
        base = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        stops = self._make_stops(3, base)

        result = RouteResult(
            total_distance_km=14.7,
            total_duration_seconds=1800,
            legs=[
                RouteLeg(sequence=2, duration_seconds=900, distance_km=7.0, eta_offset_seconds=900),
                RouteLeg(sequence=3, duration_seconds=900, distance_km=7.7, eta_offset_seconds=1800),
            ],
            raw_payload={"trip": {"summary": {"length": 14.7, "time": 1800}}},
        )

        update_group = MagicMock()
        update_stop = MagicMock()

        apply_valhalla_result(group, stops, result, update_group, update_stop)

        update_group.assert_called_once_with(
            route_group_id=group["id"],
            estimated_distance_km=14.7,
            estimated_duration_min=30,
            route_payload=result.raw_payload,
        )

    def test_stop_etas_are_offset_correctly(self):
        group = {"id": uuid4()}
        base = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        stops = self._make_stops(3, base)

        result = RouteResult(
            total_distance_km=14.7,
            total_duration_seconds=1800,
            legs=[
                RouteLeg(sequence=2, duration_seconds=900, distance_km=7.0, eta_offset_seconds=900),
                RouteLeg(sequence=3, duration_seconds=900, distance_km=7.7, eta_offset_seconds=1800),
            ],
        )

        update_group = MagicMock()
        update_stop = MagicMock()

        apply_valhalla_result(group, stops, result, update_group, update_stop)

        calls = update_stop.call_args_list
        self.assertEqual(len(calls), 2)

        # stop 2 
        self.assertEqual(calls[0].kwargs["route_stop_id"], stops[1]["id"])
        self.assertEqual(calls[0].kwargs["estimated_arrival"], base + timedelta(seconds=900))

        # stop 3 
        self.assertEqual(calls[1].kwargs["route_stop_id"], stops[2]["id"])
        self.assertEqual(calls[1].kwargs["estimated_arrival"], base + timedelta(seconds=1800))

    def test_first_stop_eta_is_not_changed(self):
        """Stop 1 is the departure point — Valhalla legs start from stop 2."""
        group = {"id": uuid4()}
        base = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        stops = self._make_stops(2, base)

        result = RouteResult(
            total_distance_km=5.0,
            total_duration_seconds=600,
            legs=[
                RouteLeg(sequence=2, duration_seconds=600, distance_km=5.0, eta_offset_seconds=600),
            ],
        )

        update_group = MagicMock()
        update_stop = MagicMock()

        apply_valhalla_result(group, stops, result, update_group, update_stop)

        updated_ids = [c.kwargs["route_stop_id"] for c in update_stop.call_args_list]
        self.assertNotIn(stops[0]["id"], updated_ids)

    def test_naive_base_time_gets_utc_attached(self):
        group = {"id": uuid4()}
        naive_base = datetime(2024, 1, 15, 9, 0)  # no tzinfo
        stops = self._make_stops(2, naive_base)

        result = RouteResult(
            total_distance_km=5.0,
            total_duration_seconds=600,
            legs=[
                RouteLeg(sequence=2, duration_seconds=600, distance_km=5.0, eta_offset_seconds=600),
            ],
        )

        update_group = MagicMock()
        update_stop = MagicMock()

        apply_valhalla_result(group, stops, result, update_group, update_stop)

        eta = update_stop.call_args.kwargs["estimated_arrival"]
        self.assertIsNotNone(eta.tzinfo)

#only one stop means no legs
    def test_single_stop_skips_eta_updates(self):
        group = {"id": uuid4()}
        base = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        stops = self._make_stops(1, base)

        result = RouteResult(
            total_distance_km=0,
            total_duration_seconds=0,
            legs=[],
        )

        update_group = MagicMock()
        update_stop = MagicMock()

        apply_valhalla_result(group, stops, result, update_group, update_stop)

        update_stop.assert_not_called()


class TestValhallaClientParsing(unittest.TestCase):

    def _make_client(self):
        from app.integrations.valhalla_client import ValhallaClient
        client = ValhallaClient.__new__(ValhallaClient)
        return client

    def test_parse_route_extracts_summary(self):
        client = self._make_client()
        payload = {
            "trip": {
                "summary": {"length": 14.7, "time": 1842.0},
                "legs": [
                    {"summary": {"time": 920.0, "length": 7.2}},
                    {"summary": {"time": 922.0, "length": 7.5}},
                ],
                "locations": [],
            }
        }
        result = client._parse_route(payload)
        self.assertAlmostEqual(result.total_distance_km, 14.7)
        self.assertAlmostEqual(result.total_duration_seconds, 1842.0)

    def test_parse_route_cumulative_eta_offsets(self):
        client = self._make_client()
        payload = {
            "trip": {
                "summary": {"length": 14.7, "time": 1842.0},
                "legs": [
                    {"summary": {"time": 900.0, "length": 7.2}},
                    {"summary": {"time": 942.0, "length": 7.5}},
                ],
                "locations": [],
            }
        }
        result = client._parse_route(payload)
        self.assertEqual(result.legs[0].eta_offset_seconds, 900.0)
        self.assertAlmostEqual(result.legs[1].eta_offset_seconds, 1842.0)

    def test_parse_route_stores_raw_payload(self):
        client = self._make_client()
        payload = {
            "trip": {
                "summary": {"length": 5.0, "time": 600.0},
                "legs": [{"summary": {"time": 600.0, "length": 5.0}}],
                "locations": [],
            }
        }
        result = client._parse_route(payload)
        self.assertEqual(result.raw_payload, payload)


if __name__ == "__main__":
    unittest.main()