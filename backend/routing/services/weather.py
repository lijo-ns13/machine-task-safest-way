"""Open-Meteo hourly forecast client (free, no API key)."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests
from django.conf import settings
from django.core.cache import cache

from .errors import UpstreamError

URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARS = "wind_speed_10m,rain,showers,snowfall"
BATCH_SIZE = 50  # locations per HTTP call (keeps the URL short)


@dataclass(frozen=True)
class Weather:
    wind_mph: float
    rain_in_hr: float
    snow_in_hr: float


class Forecast:
    """Hourly weather for one location. Look up any time with `at()`."""

    def __init__(self, first_hour: datetime, hours: list[Weather]):
        self.first_hour = first_hour
        self.hours = hours

    def at(self, when: datetime) -> Weather:
        offset = (when - self.first_hour).total_seconds() / 3600
        index = min(max(round(offset), 0), len(self.hours) - 1)
        return self.hours[index]


def floor_to_hour(when: datetime) -> datetime:
    return when.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def fetch_forecasts(points: list[tuple[float, float]], start: datetime, hours: int) -> dict:
    """Fetch forecasts for many points. Returns {(lat, lng): Forecast}.

    Points are rounded to 2 decimals (~1 km, finer than the weather model grid)
    so nearby checkpoints share one request, and results are cached.
    """
    first_hour = floor_to_hour(start)
    last_hour = first_hour + timedelta(hours=hours)
    window = (first_hour.date().isoformat(), last_hour.date().isoformat())

    unique = {_key(p) for p in points}
    result, missing = {}, []
    for key in unique:
        cached = cache.get(_cache_key(key, window))
        if cached is not None:
            result[key] = cached
        else:
            missing.append(key)

    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i : i + BATCH_SIZE]
        for key, forecast in zip(batch, _request(batch, window)):
            cache.set(_cache_key(key, window), forecast, settings.WEATHER_CACHE_SECONDS)
            result[key] = forecast

    return {p: result[_key(p)] for p in points}


def _key(point: tuple[float, float]) -> tuple[float, float]:
    return round(point[0], 2), round(point[1], 2)


def _cache_key(key, window) -> str:
    return f"wx:{key[0]}:{key[1]}:{window[0]}:{window[1]}"


def _request(batch: list[tuple[float, float]], window: tuple[str, str]) -> list[Forecast]:
    params = {
        "latitude": ",".join(str(lat) for lat, _ in batch),
        "longitude": ",".join(str(lng) for _, lng in batch),
        "hourly": HOURLY_VARS,
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "UTC",
        "start_date": window[0],
        "end_date": window[1],
    }
    try:
        resp = requests.get(URL, params=params, timeout=settings.EXTERNAL_API_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise UpstreamError(f"Weather service failed: {exc}") from exc

    # One location returns an object, several return a list.
    items = payload if isinstance(payload, list) else [payload]
    return [_parse(item["hourly"]) for item in items]


def _parse(hourly: dict) -> Forecast:
    first = datetime.fromisoformat(hourly["time"][0]).replace(tzinfo=timezone.utc)
    zero = lambda v: v or 0.0  # Open-Meteo uses null for missing hours
    hours = [
        Weather(zero(wind), zero(rain) + zero(showers), zero(snow))
        for wind, rain, showers, snow in zip(
            hourly["wind_speed_10m"], hourly["rain"], hourly["showers"], hourly["snowfall"]
        )
    ]
    return Forecast(first, hours)
