"""Weather heatmap along the trip corridor: one intensity value per grid point per forecast hour."""
from datetime import timedelta
from math import cos, radians

from . import weather
from .risk import NO_TRAVEL, assess
from .sampling import haversine_miles, thin_polyline

MAX_POINTS = 200
MIN_BUFFER_MILES = 20


def corridor_grid(polylines: list[list], max_points: int = MAX_POINTS) -> list[tuple[float, float]]:
    """Regular lat/lng grid, keeping only cells close to at least one route."""
    vertices = [p for line in polylines for p in thin_polyline(line, 100)]
    lats = [p[0] for p in vertices]
    lngs = [p[1] for p in vertices]
    min_lat, max_lat, min_lng, max_lng = min(lats), max(lats), min(lngs), max(lngs)

    # ~15 cells across the larger side of the bounding box (never finer than ~7 miles).
    step_lat = max(0.1, max(max_lat - min_lat, max_lng - min_lng) / 15)
    step_lng = step_lat / max(cos(radians((min_lat + max_lat) / 2)), 0.2)
    buffer_miles = max(MIN_BUFFER_MILES, step_lat * 69)

    grid = []
    lat = min_lat
    while lat <= max_lat + step_lat:
        lng = min_lng
        while lng <= max_lng + step_lng:
            if any(haversine_miles((lat, lng), v) <= buffer_miles for v in vertices):
                grid.append((round(lat, 3), round(lng, 3)))
            lng += step_lng
        lat += step_lat
    return grid[:max_points]


def build_heatmap(polylines: list[list], departure, load_lb: int, hours: int = 48) -> dict:
    """Frames for hour 0..`hours` after departure. Intensity = risk level / 4 (0 clear, 1 No Travel)."""
    points = corridor_grid(polylines)
    first_hour = weather.floor_to_hour(departure)
    forecasts = weather.fetch_forecasts(points, first_hour, hours + 1)

    frames = []
    for h in range(hours + 1):
        when = first_hour + timedelta(hours=h)
        frame = []
        for p in points:
            wx = forecasts[p].at(when)
            level = assess(wx.wind_mph, wx.rain_in_hr, wx.snow_in_hr, load_lb).level
            frame.append(level / NO_TRAVEL)
        frames.append(frame)

    return {
        "start_time": first_hour.isoformat(),
        "hours": hours,
        "points": [list(p) for p in points],
        "frames": frames,
    }
