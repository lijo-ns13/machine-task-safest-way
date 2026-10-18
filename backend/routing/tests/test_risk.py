import pytest

from routing.services.risk import (
    HIGH, LOW, MODERATE, NO_TRAVEL, SEVERE,
    assess, rain_level, snow_level, wind_level,
)


@pytest.mark.parametrize("mph,expected", [
    (0, LOW), (24.9, LOW), (25, MODERATE), (34.9, MODERATE),
    (35, HIGH), (44.9, HIGH), (45, SEVERE), (54.9, SEVERE),
    (55, NO_TRAVEL), (80, NO_TRAVEL),
])
def test_wind_thresholds(mph, expected):
    assert wind_level(mph) == expected


@pytest.mark.parametrize("rate,expected", [
    (0, LOW), (0.09, LOW), (0.10, MODERATE), (0.24, MODERATE),
    (0.25, HIGH), (0.49, HIGH), (0.50, SEVERE), (1.00, SEVERE),
    (1.01, NO_TRAVEL),
])
def test_rain_thresholds(rate, expected):
    assert rain_level(rate) == expected


@pytest.mark.parametrize("rate,expected", [
    (0, LOW), (0.4, LOW), (0.5, MODERATE), (0.9, MODERATE),
    (1.0, HIGH), (1.9, HIGH), (2.0, SEVERE), (3.0, SEVERE),
    (3.1, NO_TRAVEL),
])
def test_snow_thresholds(rate, expected):
    assert snow_level(rate) == expected


def test_overall_risk_is_worst_factor():
    risk = assess(wind_mph=10, rain_in_hr=0.3, snow_in_hr=0.6, load_lb=10_000)
    assert risk.level == HIGH
    assert "Rain" in risk.reason


def test_clear_weather_is_low():
    assert assess(5, 0, 0, 80_000).level == LOW


def test_wind_55_is_no_travel_for_any_load():
    assert assess(55, 0, 0, 0).level == NO_TRAVEL


def test_wind_45_to_54_light_load_is_severe():
    assert assess(50, 0, 0, 30_000).level == SEVERE  # exactly 30,000 is not "> 30,000"


def test_wind_45_to_54_heavy_load_is_no_travel():
    risk = assess(50, 0, 0, 30_001)
    assert risk.level == NO_TRAVEL
    assert "30,000" in risk.reason


def test_wind_35_to_44_heavy_load_is_severe():
    assert assess(40, 0, 0, 40_000).level == HIGH  # exactly 40,000 is not "> 40,000"
    assert assess(40, 0, 0, 40_001).level == SEVERE


def test_load_rules_never_lower_risk():
    # Rain already makes this No Travel; light-load wind rule must not reduce it.
    assert assess(40, 1.5, 0, 50_000).level == NO_TRAVEL
