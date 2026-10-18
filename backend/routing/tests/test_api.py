from datetime import datetime, timedelta, timezone

import pytest
from rest_framework.test import APIClient

from routing.services import analyzer, geocoding, routing
from routing.services.errors import LocationNotFound, UpstreamError
from routing.services.weather import Forecast, Weather

URL = "/api/routes/analyze"


def _payload(**overrides):
    body = {
        "origin": "Austin, TX",
        "destination": "Dallas, TX",
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
        "load_weight_lb": 45_000,
    }
    return {**body, **overrides}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def fake_services(monkeypatch):
    """Two routes along the same corridor; every checkpoint sees 40 mph wind."""
    monkeypatch.setattr(geocoding, "geocode", lambda q: (30.0, -97.0, q) if "Austin" in q else (33.0, -97.0, q))
    options = [
        routing.RouteOption("r1", "via I-35", 207.0, 3 * 3600, [(30.0, -97.0), (33.0, -97.0)]),
        routing.RouteOption("r2", "via US-281", 215.0, 4 * 3600, [(30.0, -97.0), (33.0, -97.0)]),
    ]
    monkeypatch.setattr(routing, "get_routes", lambda o, d: options)

    def fake_forecasts(points, start, hours):
        return {p: Forecast(start.replace(minute=0, second=0, microsecond=0), [Weather(40, 0, 0)] * (hours + 1)) for p in points}

    monkeypatch.setattr(analyzer.weather, "fetch_forecasts", fake_forecasts)


def test_success_shape(client, fake_services):
    resp = client.post(URL, _payload(), format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["routes"]) == 2
    route = body["routes"][0]
    assert {"id", "summary", "distance_miles", "duration_hours", "eta", "geometry", "stats", "checkpoints"} <= route.keys()
    cp = route["checkpoints"][0]
    assert {"mile", "lat", "lng", "eta", "weather", "risk", "reason"} <= cp.keys()
    assert body["recommended_route_id"] in {"r1", "r2"}
    assert body["recommendation_reason"]
    assert len(body["heatmap"]["frames"]) == 49


def test_heavy_load_in_40mph_wind_is_severe(client, fake_services):
    body = client.post(URL, _payload(load_weight_lb=45_000), format="json").json()
    assert body["routes"][0]["stats"]["max_risk"] == "Severe"


def test_light_load_in_40mph_wind_is_high(client, fake_services):
    body = client.post(URL, _payload(load_weight_lb=20_000), format="json").json()
    assert body["routes"][0]["stats"]["max_risk"] == "High"


def test_validation_errors_are_per_field(client):
    resp = client.post(URL, {"origin": "", "load_weight_lb": 999_999}, format="json")
    assert resp.status_code == 400
    assert {"origin", "destination", "departure_time", "load_weight_lb"} <= resp.json().keys()


def test_past_departure_rejected(client):
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    resp = client.post(URL, _payload(departure_time=past), format="json")
    assert resp.status_code == 400
    assert "departure_time" in resp.json()


def test_same_origin_and_destination_rejected(client):
    resp = client.post(URL, _payload(origin="Dallas", destination="dallas"), format="json")
    assert resp.status_code == 400


def test_unknown_location_returns_422(client, monkeypatch):
    def not_found(q):
        raise LocationNotFound("nope")

    monkeypatch.setattr(geocoding, "geocode", not_found)
    assert client.post(URL, _payload(), format="json").status_code == 422


def test_upstream_failure_returns_502(client, monkeypatch):
    def down(q):
        raise UpstreamError("down")

    monkeypatch.setattr(geocoding, "geocode", down)
    assert client.post(URL, _payload(), format="json").status_code == 502
