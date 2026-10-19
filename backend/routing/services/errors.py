def describe(exc: Exception) -> str:
    """Short error text that never includes the request URL (it contains the API token)."""
    response = getattr(exc, "response", None)
    if response is not None:
        hint = " - check MAPBOX_TOKEN" if response.status_code == 401 else ""
        return f"HTTP {response.status_code}{hint}"
    return type(exc).__name__


class LocationNotFound(Exception):
    """A place name could not be geocoded."""


class UpstreamError(Exception):
    """A third-party API (Mapbox / Open-Meteo) failed or is misconfigured."""


class NoRouteFound(Exception):
    """The routing API returned no drivable route."""
