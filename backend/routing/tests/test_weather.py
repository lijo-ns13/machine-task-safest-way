from datetime import datetime, timezone

import pytest
from django.core.cache import cache

from routing.services import weather
from routing.services.errors import UpstreamError

START = datetime(2026, 10, 19, 8, 30, tzinfo=timezone.utc)


def _hourly(wind):
    times = [f"2026-10-19T{h:02d}:00" for h in range(24)] + [f"2026-10-20T{h:02d}:00" for h in range(24)]
    n = len(times)
    return {
        "time": times,
        "wind_speed_10m": [wind] * n,
        "rain": [0.1] * n,
        "showers": [0.05] * n,
        "snowfall": [None] * n,
    }


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


def test_multiple_points_are_batched_into_one_call(monkeypatch):
    calls = []

    def fake_get(url, params, timeout):
        calls.append(params)
        return FakeResponse([{"hourly": _hourly(10)}, {"hourly": _hourly(20)}])

    monkeypatch.setattr(weather.requests, "get", fake_get)
    forecasts = weather.fetch_forecasts([(30.0, -97.0), (31.0, -97.0)], START, hours=24)

    assert len(calls) == 1
    assert calls[0]["wind_speed_unit"] == "mph" and calls[0]["precipitation_unit"] == "inch"
    assert forecasts[(30.0, -97.0)].at(START).wind_mph == 10
    assert forecasts[(31.0, -97.0)].at(START).wind_mph == 20


def test_rain_is_rain_plus_showers_and_null_snow_is_zero(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda *a, **k: FakeResponse({"hourly": _hourly(5)}))
    wx = weather.fetch_forecasts([(30.0, -97.0)], START, 24)[(30.0, -97.0)].at(START)
    assert wx.rain_in_hr == pytest.approx(0.15)
    assert wx.snow_in_hr == 0


def test_lookup_uses_nearest_hour_and_clamps():
    hours = [weather.Weather(w, 0, 0) for w in range(24)]
    fc = weather.Forecast(datetime(2026, 10, 19, tzinfo=timezone.utc), hours)
    assert fc.at(datetime(2026, 10, 19, 8, 20, tzinfo=timezone.utc)).wind_mph == 8
    assert fc.at(datetime(2026, 10, 19, 8, 40, tzinfo=timezone.utc)).wind_mph == 9
    assert fc.at(datetime(2030, 1, 1, tzinfo=timezone.utc)).wind_mph == 23


def test_results_are_cached(monkeypatch):
    calls = []

    def fake_get(*a, **k):
        calls.append(1)
        return FakeResponse({"hourly": _hourly(5)})

    monkeypatch.setattr(weather.requests, "get", fake_get)
    weather.fetch_forecasts([(30.0, -97.0)], START, 24)
    weather.fetch_forecasts([(30.001, -97.001)], START, 24)  # rounds to the same point
    assert len(calls) == 1


def test_upstream_failure_is_wrapped(monkeypatch):
    def boom(*a, **k):
        raise weather.requests.ConnectionError("down")

    monkeypatch.setattr(weather.requests, "get", boom)
    with pytest.raises(UpstreamError):
        weather.fetch_forecasts([(30.0, -97.0)], START, 24)


def test_429_is_retried_then_succeeds(monkeypatch):
    monkeypatch.setattr(weather.time, "sleep", lambda s: None)
    calls = []

    def fake_get(url, params, timeout):
        calls.append(1)
        if len(calls) < 3:
            return FakeResponse({}, status_code=429)
        return FakeResponse({"hourly": _hourly(5)})

    monkeypatch.setattr(weather.requests, "get", fake_get)
    weather.fetch_forecasts([(1.0, 2.0)], START, 24)
    assert len(calls) == 3
