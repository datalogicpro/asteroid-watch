"""Tests for turning JPL's replies into clean records."""

from datetime import datetime
from typing import Any

import pytest

from space import (
    ImpactRisk,
    au_to_km,
    diameter_m,
    km_to_moon_distances,
    moon_distances_to_au,
    parse_close_approaches,
    parse_fireballs,
    parse_impact_risks,
    size_range_m,
)


def test_unit_conversions() -> None:
    assert au_to_km(1) == 149_597_870.7
    assert km_to_moon_distances(384_399) == 1
    assert moon_distances_to_au(1) == pytest.approx(0.00257, abs=0.00001)


def test_size_from_brightness() -> None:
    # H = 18 with an albedo of 0.25 works out to about 0.67 km across
    assert diameter_m(18, 0.25) == pytest.approx(667, abs=1)
    smallest, largest = size_range_m(29.83)
    assert smallest == pytest.approx(2.9, abs=0.1)
    assert largest == pytest.approx(6.4, abs=0.1)


def test_parse_close_approaches(cad_reply: dict[str, Any]) -> None:
    passes = parse_close_approaches(cad_reply)

    first = passes[0]
    assert len(passes) == 3
    # The padding JPL puts in front of names is trimmed
    assert first.name == "(2025 UK9)"
    assert first.time == datetime(2026, 10, 31, 2, 35)
    assert first.distance_km == pytest.approx(314_648, abs=1)
    assert first.moon_distances == pytest.approx(0.82, abs=0.01)
    assert first.speed_km_s == pytest.approx(7.83, abs=0.01)


def test_close_approach_sizes(cad_reply: dict[str, Any]) -> None:
    estimated, measured, unknown = parse_close_approaches(cad_reply)

    # No measured size, so it's a range from brightness
    assert estimated.size_m == pytest.approx((2.9, 6.4), abs=0.1)
    # The sample file gives this one a measured diameter of 0.24 km
    assert measured.size_m == (240, 240)
    # No measured size and no brightness, so the size is unknown
    assert unknown.size_m is None


def test_parse_impact_risks_puts_the_highest_risk_first(
    sentry_reply: dict[str, Any],
) -> None:
    risks = parse_impact_risks(sentry_reply)

    assert [risk.name for risk in risks] == [
        "29075 (1950 DA)",
        "(2008 JL3)",
        "(2011 TO)",
    ]
    top = risks[0]
    assert top.years == "2880-2880"
    assert top.palermo == -0.95
    # The Torino scale only covers the next 100 years
    assert top.torino is None
    assert top.diameter_km == 1.3
    assert top.odds == "1 in 2,753"
    assert risks[1].torino == 0
    assert risks[1].possible_impacts == 44


def test_odds_when_there_is_no_chance() -> None:
    risk = ImpactRisk("Test", "2100-2100", 0.0, -9.0, 0, None, 0)

    assert risk.odds == "none"


def test_parse_fireballs(fireball_reply: dict[str, Any]) -> None:
    south_west, no_speed, north_east = parse_fireballs(fireball_reply)

    assert south_west.time == datetime(2026, 10, 4, 3, 14, 45)
    # South and west become negative
    assert (south_west.latitude, south_west.longitude) == (-41.8, -173.1)
    assert south_west.altitude_km == 26.9
    assert south_west.speed_km_s == 13.8
    assert south_west.impact_energy_kt == 0.18
    assert no_speed.speed_km_s is None
    assert (north_east.latitude, north_east.longitude) == (46.6, 133.1)


def test_empty_replies() -> None:
    assert parse_close_approaches({"count": 0}) == []
    assert parse_impact_risks({"count": "0"}) == []
    assert parse_fireballs({"count": "0"}) == []
