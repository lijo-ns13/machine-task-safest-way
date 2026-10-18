from datetime import datetime, timedelta, timezone

import pytest

from routing.services.sampling import (
    auto_interval, haversine_miles, sample_checkpoints, thin_polyline,
)

START = datetime(2026, 10, 19, 8, 0, tzinfo=timezone.utc)
# Straight line due north, roughly 69 miles per degree of latitude.
LINE = [(30.0, -97.0), (31.0, -97.0), (32.0, -97.0)]


def test_haversine_one_degree_latitude_is_about_69_miles():
    assert haversine_miles((30, -97), (31, -97)) == pytest.approx(69.1, abs=0.2)


@pytest.mark.parametrize("miles,expected", [(50, 10), (100, 10), (101, 25), (300, 25), (301, 50)])
def test_auto_interval(miles, expected):
    assert auto_interval(miles) == expected


def test_checkpoints_include_start_every_interval_and_end():
    cps = sample_checkpoints(LINE, distance_miles=138, duration_seconds=7200, departure=START, interval_miles=50)
    assert [c.mile for c in cps] == [0, 50, 100, 138]
    assert cps[0].eta == START
    assert cps[-1].eta == START + timedelta(hours=2)
    assert (cps[0].lat, cps[0].lng) == LINE[0]
    assert (cps[-1].lat, cps[-1].lng) == LINE[-1]


def test_eta_is_proportional_to_distance():
    cps = sample_checkpoints(LINE, 100, 3600, START, 25)
    assert [c.eta - START for c in cps] == [timedelta(minutes=m) for m in (0, 15, 30, 45, 60)]


def test_checkpoint_position_is_interpolated():
    cps = sample_checkpoints(LINE, 138, 7200, START, 69)
    assert cps[1].lat == pytest.approx(31.0, abs=0.01)


def test_no_duplicate_when_distance_is_exact_multiple():
    cps = sample_checkpoints(LINE, 100, 3600, START, 50)
    assert [c.mile for c in cps] == [0, 50, 100]


def test_thin_polyline_keeps_endpoints():
    line = [(i / 1000, i / 1000) for i in range(5000)]
    thinned = thin_polyline(line, 800)
    assert len(thinned) == 800
    assert thinned[0] == line[0] and thinned[-1] == line[-1]
