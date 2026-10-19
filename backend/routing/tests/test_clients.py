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


def test_upstream_error_does_not_leak_the_token(monkeypatch):
    class Unauthorized:
        status_code = 401

        def raise_for_status(self):
            error = geocoding.requests.HTTPError("401 for url: https://x?access_token=pk.test")
            error.response = self
            raise error

    monkeypatch.setattr(geocoding.requests, "get", lambda *a, **k: Unauthorized())
    with pytest.raises(UpstreamError) as info:
        geocoding.geocode("Dallas")
    assert "pk.test" not in str(info.value)
    assert "MAPBOX_TOKEN" in str(info.value)


def _capture_params(monkeypatch):
    captured = {}

    def fake_get(url, params, timeout):
        captured.update(params)
        return FakeResponse({"features": [{"center": [76.2, 10.0], "place_name": "Kochi, India"}]})

    monkeypatch.setattr(geocoding.requests, "get", fake_get)
    return captured


def test_geocoding_is_worldwide_by_default(monkeypatch, settings):
    settings.GEOCODING_COUNTRY = ""
    params = _capture_params(monkeypatch)
    assert geocoding.geocode("Kochi")[2] == "Kochi, India"
    assert "country" not in params


def test_geocoding_can_be_restricted_to_countries(monkeypatch, settings):
    settings.GEOCODING_COUNTRY = "in,us"
    params = _capture_params(monkeypatch)
    geocoding.geocode("Kochi")
    assert params["country"] == "in,us"
