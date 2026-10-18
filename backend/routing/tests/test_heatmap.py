from datetime import datetime, timezone

from routing.services import heatmap, weather
from routing.services.weather import Forecast, Weather

DEPARTURE = datetime(2026, 10, 19, 8, 30, tzinfo=timezone.utc)
LINE = [(30.0, -97.0), (33.0, -97.0)]


def test_grid_stays_near_route_and_under_cap():
    grid = heatmap.corridor_grid([LINE])
    assert 0 < len(grid) <= heatmap.MAX_POINTS
    for lat, lng in grid:
        assert abs(lng - (-97.0)) < 1.0  # within roughly the corridor buffer


def test_grid_for_tiny_trip_is_not_empty():
    assert heatmap.corridor_grid([[(30.0, -97.0), (30.05, -97.0)]])


def test_frames_cover_zero_to_48_hours_with_risk_intensity(monkeypatch):
    def fake_forecasts(points, start, hours):
        # Calm for the first 24h, 40 mph wind afterwards.
        series = [Weather(5, 0, 0)] * 24 + [Weather(40, 0, 0)] * (hours - 23)
        return {p: Forecast(start, series) for p in points}

    monkeypatch.setattr(weather, "fetch_forecasts", fake_forecasts)
    result = heatmap.build_heatmap([LINE], DEPARTURE, load_lb=45_000, hours=48)

    assert result["start_time"] == "2026-10-19T08:00:00+00:00"
    assert len(result["frames"]) == 49
    assert all(len(f) == len(result["points"]) for f in result["frames"])
    assert set(result["frames"][0]) == {0.0}  # calm -> Low
    assert set(result["frames"][48]) == {0.75}  # 40 mph + heavy load -> Severe (3/4)
