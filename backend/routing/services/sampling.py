"""Place checkpoints along a route and estimate when the truck reaches each one."""
from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_MILES = 3958.8

LatLng = tuple[float, float]


@dataclass(frozen=True)
class Checkpoint:
    mile: float
    lat: float
    lng: float
    eta: datetime


def haversine_miles(a: LatLng, b: LatLng) -> float:
    lat1, lng1, lat2, lng2 = map(radians, (*a, *b))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * asin(sqrt(h))


def auto_interval(distance_miles: float) -> int:
    """Short trips get denser sampling: 10 mi up to 100 mi, 25 mi up to 300 mi, else 50 mi."""
    if distance_miles <= 100:
        return 10
    if distance_miles <= 300:
        return 25
    return 50


def sample_checkpoints(
    polyline: list[LatLng],
    distance_miles: float,
    duration_seconds: float,
    departure: datetime,
    interval_miles: int,
) -> list[Checkpoint]:
    """Checkpoints at mile 0, every `interval_miles`, and at the destination.

    The routing API gives total distance and duration only, so we assume a constant
    average speed: the ETA at a point is `departure + duration * (fraction of route done)`.
    """
    cumulative = [0.0]
    for prev, cur in zip(polyline, polyline[1:]):
        cumulative.append(cumulative[-1] + haversine_miles(prev, cur))
    line_length = cumulative[-1]

    miles = [m for m in _frange(0, distance_miles, interval_miles)] + [distance_miles]
    checkpoints = []
    for mile in miles:
        fraction = mile / distance_miles if distance_miles else 0.0
        lat, lng = _point_at(polyline, cumulative, fraction * line_length)
        eta = departure + timedelta(seconds=duration_seconds * fraction)
        checkpoints.append(Checkpoint(round(mile, 1), lat, lng, eta))
    return checkpoints


def _frange(start: float, stop: float, step: float):
    value = start
    while value < stop - 1e-9:
        yield value
        value += step


def _point_at(polyline: list[LatLng], cumulative: list[float], target: float) -> LatLng:
    """Interpolate the coordinate `target` miles along the polyline."""
    if target <= 0 or len(polyline) == 1:
        return polyline[0]
    if target >= cumulative[-1]:
        return polyline[-1]
    i = bisect_right(cumulative, target) - 1
    seg = cumulative[i + 1] - cumulative[i]
    t = (target - cumulative[i]) / seg if seg else 0.0
    (lat1, lng1), (lat2, lng2) = polyline[i], polyline[i + 1]
    return lat1 + (lat2 - lat1) * t, lng1 + (lng2 - lng1) * t


def thin_polyline(polyline: list[LatLng], max_points: int = 800) -> list[LatLng]:
    """Reduce points so the JSON payload and the map stay light. Keeps first and last."""
    if len(polyline) <= max_points:
        return polyline
    step = len(polyline) / max_points
    thinned = [polyline[int(i * step)] for i in range(max_points)]
    thinned[-1] = polyline[-1]
    return thinned
