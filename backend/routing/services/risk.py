"""Weather risk rules: classify wind / rain / snow at one checkpoint for a given load.

Pure functions, no I/O, so every threshold can be unit tested.
"""
from dataclasses import dataclass

LOW, MODERATE, HIGH, SEVERE, NO_TRAVEL = range(5)
LEVEL_NAMES = ["Low", "Moderate", "High", "Severe", "No Travel"]

# Upper bounds of Low, Moderate, High, Severe. Anything above the last bound is No Travel.
WIND_BOUNDS = (25, 35, 45, 55)  # mph
RAIN_BOUNDS = (0.10, 0.25, 0.50, 1.00)  # in/hr
SNOW_BOUNDS = (0.5, 1.0, 2.0, 3.0)  # in/hr


@dataclass(frozen=True)
class Risk:
    level: int
    reason: str

    @property
    def label(self) -> str:
        return LEVEL_NAMES[self.level]


def _level(value: float, bounds: tuple, no_travel_inclusive: bool) -> int:
    """Map a reading to a level.

    A value sitting exactly on a bound goes to the higher (safer-to-assume) level,
    e.g. wind 25 mph is Moderate. The last bound differs per the table:
    wind ">= 55" is No Travel, while rain "> 1.00" and snow "> 3.0" are No Travel.
    """
    last = len(bounds) - 1
    for level, bound in enumerate(bounds):
        if level == last and not no_travel_inclusive:
            if value <= bound:
                return level
        elif value < bound:
            return level
    return NO_TRAVEL


def wind_level(mph: float) -> int:
    return _level(mph, WIND_BOUNDS, no_travel_inclusive=True)


def rain_level(in_per_hr: float) -> int:
    return _level(in_per_hr, RAIN_BOUNDS, no_travel_inclusive=False)


def snow_level(in_per_hr: float) -> int:
    return _level(in_per_hr, SNOW_BOUNDS, no_travel_inclusive=False)


def assess(wind_mph: float, rain_in_hr: float, snow_in_hr: float, load_lb: float) -> Risk:
    """Overall risk = worst of wind, rain, snow, then escalated by the load rules."""
    candidates = [
        (wind_level(wind_mph), f"Wind {wind_mph:.0f} mph"),
        (rain_level(rain_in_hr), f"Rain {rain_in_hr:.2f} in/hr"),
        (snow_level(snow_in_hr), f"Snow {snow_in_hr:.2f} in/hr"),
    ]
    level, reason = max(candidates, key=lambda c: c[0])
    if level == LOW:
        return Risk(LOW, "Conditions clear")

    # Load rules only ever raise the risk.
    if 45 <= wind_mph < 55 and load_lb > 30_000 and level < NO_TRAVEL:
        return Risk(NO_TRAVEL, f"Wind {wind_mph:.0f} mph with load over 30,000 lb")
    if 35 <= wind_mph < 45 and load_lb > 40_000 and level < SEVERE:
        return Risk(SEVERE, f"Wind {wind_mph:.0f} mph with load over 40,000 lb")
    return Risk(level, reason)
