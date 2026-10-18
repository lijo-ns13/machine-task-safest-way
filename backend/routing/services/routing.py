"""Mapbox Directions: origin/destination -> up to 3 alternative routes."""
from dataclasses import dataclass

import requests
from django.conf import settings

from .errors import NoRouteFound, UpstreamError

URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
METERS_PER_MILE = 1609.344


@dataclass(frozen=True)
class RouteOption:
    id: str
    summary: str
    distance_miles: float
    duration_seconds: float
    polyline: list  # [(lat, lng), ...]


def get_routes(origin: tuple[float, float], destination: tuple[float, float]) -> list[RouteOption]:
    if not settings.MAPBOX_TOKEN:
        raise UpstreamError("MAPBOX_TOKEN is not configured on the server")
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"  # Mapbox wants lng,lat
    try:
        resp = requests.get(
            URL.format(coords=coords),
            params={
                "access_token": settings.MAPBOX_TOKEN,
                "alternatives": "true",
                "geometries": "geojson",
                "overview": "full",
            },
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise UpstreamError(f"Routing service failed: {exc}") from exc

    routes = resp.json().get("routes", [])[:3]
    if not routes:
        raise NoRouteFound("No drivable route found between these locations")

    return [
        RouteOption(
            id=f"r{i + 1}",
            summary=_summary(route, i),
            distance_miles=round(route["distance"] / METERS_PER_MILE, 1),
            duration_seconds=route["duration"],
            polyline=[(lat, lng) for lng, lat in route["geometry"]["coordinates"]],
        )
        for i, route in enumerate(routes)
    ]


def _summary(route: dict, index: int) -> str:
    legs = route.get("legs") or [{}]
    name = legs[0].get("summary")
    return f"via {name}" if name else f"Route {index + 1}"
