class LocationNotFound(Exception):
    """A place name could not be geocoded."""


class UpstreamError(Exception):
    """A third-party API (Mapbox / Open-Meteo) failed or is misconfigured."""


class NoRouteFound(Exception):
    """The routing API returned no drivable route."""
