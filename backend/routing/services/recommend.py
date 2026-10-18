"""Turn checkpoint risks into route statistics, then rank routes."""
from dataclasses import dataclass

from .risk import HIGH, LEVEL_NAMES, NO_TRAVEL, SEVERE


@dataclass(frozen=True)
class RouteStats:
    miles_by_level: tuple  # miles spent at Low, Moderate, High, Severe, No Travel
    avg_risk: float  # mile-weighted average level, 0 (Low) .. 4 (No Travel)
    max_level: int

    @property
    def no_travel_miles(self) -> float:
        return self.miles_by_level[NO_TRAVEL]

    @property
    def severe_miles(self) -> float:
        return self.miles_by_level[SEVERE]

    @property
    def high_miles(self) -> float:
        return self.miles_by_level[HIGH]


def summarize(checkpoint_miles: list[float], levels: list[int], total_miles: float) -> RouteStats:
    """Each checkpoint 'owns' the stretch halfway to its neighbours.

    Example: checkpoints at miles 0, 50, 100 own [0-25], [25-75], [75-100].
    """
    miles_by_level = [0.0] * len(LEVEL_NAMES)
    for i, (mile, level) in enumerate(zip(checkpoint_miles, levels)):
        start = 0.0 if i == 0 else (checkpoint_miles[i - 1] + mile) / 2
        end = total_miles if i == len(levels) - 1 else (mile + checkpoint_miles[i + 1]) / 2
        miles_by_level[level] += max(end - start, 0.0)

    weighted = sum(level * miles for level, miles in enumerate(miles_by_level))
    avg = weighted / total_miles if total_miles else 0.0
    return RouteStats(
        miles_by_level=tuple(round(m, 1) for m in miles_by_level),
        avg_risk=round(avg, 2),
        max_level=max(levels) if levels else 0,
    )


@dataclass(frozen=True)
class Candidate:
    route_id: str
    stats: RouteStats
    duration_hours: float


# Ranking criteria in priority order. No Travel miles come first because No Travel
# is worse than Severe; the rest follow the brief: Severe, High, average risk, time.
_CRITERIA = [
    ("No Travel miles", lambda c: c.stats.no_travel_miles),
    ("Severe miles", lambda c: c.stats.severe_miles),
    ("High miles", lambda c: c.stats.high_miles),
    ("average risk", lambda c: c.stats.avg_risk),
    ("travel time", lambda c: round(c.duration_hours, 2)),
]


def recommend(candidates: list[Candidate]) -> tuple[str, str]:
    """Return (best route id, human readable reason)."""
    ranked = sorted(candidates, key=lambda c: tuple(fn(c) for _, fn in _CRITERIA))
    best = ranked[0]
    if len(ranked) == 1:
        return best.route_id, "Only one route available"

    for name, fn in _CRITERIA:
        values = [fn(c) for c in candidates]
        if len(set(values)) > 1 and fn(best) == min(values):
            others = ", ".join(str(v) for v in sorted(v for v in values if v != fn(best)))
            return best.route_id, f"Lowest {name} ({fn(best)} vs {others})"
    return best.route_id, "Routes are equivalent; picked the first"
