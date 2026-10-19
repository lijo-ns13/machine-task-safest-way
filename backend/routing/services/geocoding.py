"""Mapbox geocoding: place name -> coordinates."""
from urllib.parse import quote

import requests
from django.conf import settings

from .errors import LocationNotFound, UpstreamError, describe

URL = "https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"


def geocode(query: str) -> tuple[float, float, str]:
    """Return (lat, lng, display name) for the best US match."""
    if not settings.MAPBOX_TOKEN:
        raise UpstreamError("MAPBOX_TOKEN is not configured on the server")
    try:
        resp = requests.get(
            URL.format(query=quote(query, safe="")),
            params={"access_token": settings.MAPBOX_TOKEN, "limit": 1, "country": "us"},
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise UpstreamError(f"Geocoding service failed: {describe(exc)}") from exc

    features = resp.json().get("features", [])
    if not features:
        raise LocationNotFound(f"Could not find a US location for '{query}'")
    lng, lat = features[0]["center"]  # Mapbox returns [lng, lat]
    return lat, lng, features[0]["place_name"]
