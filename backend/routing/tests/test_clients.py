import pytest

from routing.services import geocoding, routing
from routing.services.errors import LocationNotFound, NoRouteFound, UpstreamError


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def token(settings):
    settings.MAPBOX_TOKEN = "pk.test"


def test_geocode_returns_lat_lng_and_name(monkeypatch):
    payload = {"features": [{"center": [-96.8, 32.78], "place_name": "Dallas, Texas"}]}
    monkeypatch.setattr(geocoding.requests, "get", lambda *a, **k: FakeResponse(payload))
    assert geocoding.geocode("Dallas") == (32.78, -96.8, "Dallas, Texas")


def test_geocode_unknown_place(monkeypatch):
    monkeypatch.setattr(geocoding.requests, "get", lambda *a, **k: FakeResponse({"features": []}))
    with pytest.raises(LocationNotFound):
        geocoding.geocode("asdfghjkl")


def test_missing_token_is_reported(settings):
    settings.MAPBOX_TOKEN = ""
    with pytest.raises(UpstreamError):
        geocoding.geocode("Dallas")


def test_routes_are_parsed_and_limited_to_three(monkeypatch):
    route = {
        "distance": 160934.4,  # 100 miles
        "duration": 7200,
        "legs": [{"summary": "I-35 N"}],
        "geometry": {"coordinates": [[-97.0, 30.0], [-97.0, 31.0]]},
    }
    monkeypatch.setattr(routing.requests, "get", lambda *a, **k: FakeResponse({"routes": [route] * 4}))
    result = routing.get_routes((30.0, -97.0), (31.0, -97.0))
    assert [r.id for r in result] == ["r1", "r2", "r3"]
    assert result[0].distance_miles == 100.0
    assert result[0].summary == "via I-35 N"
    assert result[0].polyline == [(30.0, -97.0), (31.0, -97.0)]  # flipped to lat,lng


def test_no_routes(monkeypatch):
    monkeypatch.setattr(routing.requests, "get", lambda *a, **k: FakeResponse({"routes": []}))
    with pytest.raises(NoRouteFound):
        routing.get_routes((0, 0), (1, 1))
