import pytest

from routing.services.recommend import Candidate, recommend, summarize
from routing.services.risk import HIGH, LOW, MODERATE, NO_TRAVEL, SEVERE


def test_summarize_splits_miles_halfway_between_checkpoints():
    stats = summarize([0, 50, 100], [LOW, SEVERE, LOW], total_miles=100)
    # LOW owns 0-25 and 75-100, SEVERE owns 25-75.
    assert stats.miles_by_level == (50.0, 0.0, 0.0, 50.0, 0.0)
    assert stats.severe_miles == 50.0
    assert stats.avg_risk == pytest.approx(1.5)
    assert stats.max_level == SEVERE


def test_summarize_miles_add_up_to_total():
    stats = summarize([0, 10, 20, 27.5], [LOW, MODERATE, HIGH, NO_TRAVEL], total_miles=27.5)
    assert sum(stats.miles_by_level) == pytest.approx(27.5, abs=0.2)


def _cand(route_id, levels, hours, miles=(0, 50, 100)):
    return Candidate(route_id, summarize(list(miles), levels, 100), hours)


def test_fewest_severe_miles_beats_faster_route():
    fast_but_severe = _cand("fast", [LOW, SEVERE, LOW], hours=5)
    slow_but_safe = _cand("safe", [LOW, MODERATE, LOW], hours=9)
    best, reason = recommend([fast_but_severe, slow_but_safe])
    assert best == "safe"
    assert "Severe miles" in reason


def test_no_travel_is_avoided_before_anything_else():
    no_travel = _cand("a", [LOW, NO_TRAVEL, LOW], hours=4)
    severe = _cand("b", [SEVERE, SEVERE, SEVERE], hours=8)
    assert recommend([no_travel, severe])[0] == "b"


def test_high_miles_break_severe_tie():
    a = _cand("a", [HIGH, HIGH, HIGH], hours=5)
    b = _cand("b", [MODERATE, HIGH, MODERATE], hours=7)
    assert recommend([a, b])[0] == "b"


def test_average_risk_breaks_tie_when_no_severe_or_high():
    a = _cand("a", [MODERATE, MODERATE, MODERATE], hours=5)
    b = _cand("b", [LOW, MODERATE, LOW], hours=7)
    best, reason = recommend([a, b])
    assert best == "b"
    assert "average risk" in reason


def test_shortest_time_is_last_tie_break():
    a = _cand("a", [LOW, LOW, LOW], hours=6)
    b = _cand("b", [LOW, LOW, LOW], hours=5)
    best, reason = recommend([a, b])
    assert best == "b"
    assert "travel time" in reason


def test_single_route():
    assert recommend([_cand("only", [LOW, LOW, LOW], 5)])[0] == "only"
