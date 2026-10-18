"""Orchestrates one analysis: geocode -> routes -> checkpoints -> weather -> risk -> recommendation."""
from datetime import datetime
from math import ceil

from . import geocoding, heatmap, routing, weather
from .recommend import Candidate, recommend, summarize
from .risk import LEVEL_NAMES, NO_TRAVEL, assess
from .sampling import auto_interval, sample_checkpoints, thin_polyline

FORECAST_HOURS = 48  # heatmap slider range


def analyze(
    origin: str,
    destination: str,
    departure: datetime,
    load_lb: int,
    interval_miles: int | None = None,
) -> dict:
    start = geocoding.geocode(origin)
    end = geocoding.geocode(destination)
    options = routing.get_routes(start[:2], end[:2])

    # Sample every route, then fetch weather for ALL checkpoints in one batch.
    sampled = {}
    for opt in options:
        interval = interval_miles or auto_interval(opt.distance_miles)
        sampled[opt.id] = sample_checkpoints(
            opt.polyline, opt.distance_miles, opt.duration_seconds, departure, interval
        )

    longest_trip_hours = max(o.duration_seconds for o in options) / 3600
    window_hours = ceil(max(FORECAST_HOURS, longest_trip_hours)) + 1
    points = [(c.lat, c.lng) for cps in sampled.values() for c in cps]
    forecasts = weather.fetch_forecasts(points, departure, window_hours)

    routes, candidates = [], []
    for opt in options:
        route, stats = _build_route(opt, sampled[opt.id], forecasts, departure, load_lb)
        routes.append(route)
        candidates.append(Candidate(opt.id, stats, opt.duration_seconds / 3600))

    best_id, reason = recommend(candidates)
    result = {
        "origin": _place(start),
        "destination": _place(end),
        "departure_time": departure.isoformat(),
        "load_weight_lb": load_lb,
        "recommended_route_id": best_id,
        "recommendation_reason": reason,
        "routes": routes,
        "warnings": _warnings(options, routes, best_id),
        "heatmap": heatmap.build_heatmap([o.polyline for o in options], departure, load_lb, FORECAST_HOURS),
    }
    return result


def _build_route(opt, checkpoints, forecasts, departure, load_lb):
    levels, checkpoint_json = [], []
    for cp in checkpoints:
        wx = forecasts[(cp.lat, cp.lng)].at(cp.eta)
        risk = assess(wx.wind_mph, wx.rain_in_hr, wx.snow_in_hr, load_lb)
        levels.append(risk.level)
        checkpoint_json.append({
            "mile": cp.mile,
            "lat": round(cp.lat, 5),
            "lng": round(cp.lng, 5),
            "eta": cp.eta.isoformat(),
            "weather": {
                "wind_mph": round(wx.wind_mph, 1),
                "rain_in_hr": round(wx.rain_in_hr, 2),
                "snow_in_hr": round(wx.snow_in_hr, 2),
            },
            "risk": risk.label,
            "risk_level": risk.level,
            "reason": risk.reason,
        })

    stats = summarize([c.mile for c in checkpoints], levels, opt.distance_miles)
    route = {
        "id": opt.id,
        "summary": opt.summary,
        "distance_miles": opt.distance_miles,
        "duration_hours": round(opt.duration_seconds / 3600, 2),
        "eta": checkpoints[-1].eta.isoformat(),
        "geometry": [[round(lat, 5), round(lng, 5)] for lat, lng in thin_polyline(opt.polyline)],
        "stats": {
            "miles_by_risk": dict(zip(LEVEL_NAMES, stats.miles_by_level)),
            "no_travel_miles": stats.no_travel_miles,
            "severe_miles": stats.severe_miles,
            "high_miles": stats.high_miles,
            "avg_risk": stats.avg_risk,
            "max_risk": LEVEL_NAMES[stats.max_level],
            "no_travel": stats.max_level == NO_TRAVEL,
        },
        "checkpoints": checkpoint_json,
    }
    return route, stats


def _place(geocoded):
    lat, lng, name = geocoded
    return {"name": name, "lat": lat, "lng": lng}


def _warnings(options, routes, best_id) -> list[str]:
    warnings = []
    if len(options) < 3:
        warnings.append(f"Only {len(options)} route(s) available for this trip")
    best = next(r for r in routes if r["id"] == best_id)
    if best["stats"]["no_travel"]:
        warnings.append("Every route crosses No Travel conditions; consider delaying departure")
    return warnings
