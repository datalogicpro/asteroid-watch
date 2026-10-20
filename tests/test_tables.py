"""Tests for the table rows and the details text."""

from datetime import datetime
from typing import Any

from space import parse_close_approaches, parse_fireballs, parse_impact_risks
from tables import (
    BIGGEST_FIRST,
    CLOSEST_FIRST,
    fireball_table,
    pass_details,
    risk_table,
    size_text,
    sort_passes,
)


def test_size_text() -> None:
    assert size_text(None) is None
    assert size_text((240.0, 240.0)) == "240"
    assert size_text((2.94, 6.41)) == "2.9–6.4"
    assert size_text((12.3, 27.8)) == "12–28"


def test_risk_table(sentry_reply: dict[str, Any]) -> None:
    top = risk_table(parse_impact_risks(sentry_reply))[0]

    assert top == {
        "Object": "29075 (1950 DA)",
        "Years": "2880-2880",
        "Impact chance": "1 in 2,753",
        "Palermo scale": -0.95,
        "Torino scale": None,
        "Size (m)": 1300,
        "If it hit": "Global effects",
        "Possible impacts": 1,
    }


def test_fireball_table(fireball_reply: dict[str, Any]) -> None:
    first = fireball_table(parse_fireballs(fireball_reply))[0]

    assert first["Date (UTC)"] == datetime(2026, 10, 4, 3, 14, 45)
    assert (first["Latitude"], first["Longitude"]) == (-41.8, -173.1)


def test_sort_passes(cad_reply: dict[str, Any]) -> None:
    passes = parse_close_approaches(cad_reply)

    closest = [p.name for p in sort_passes(passes, CLOSEST_FIRST)]
    biggest = [p.name for p in sort_passes(passes, BIGGEST_FIRST)]

    assert closest == ["(2025 UK9)", "(2019 XF2)", "(2017 WJ2)"]
    # The one with no known size goes last
    assert biggest == ["(2017 WJ2)", "(2025 UK9)", "(2019 XF2)"]


def test_pass_details(cad_reply: dict[str, Any]) -> None:
    known, _, unknown = parse_close_approaches(cad_reply)

    assert pass_details(known) == [
        "**Date:** October 31, 2026 at 02:35 (TDB)",
        "**Distance:** 0.82 Moon distances, or 314,648 km (195,513 miles)",
        "**Speed:** 7.8 km/s",
        "**Size:** 2.9–6.4 m",
        "**If it hit:** Burns up high in the air",
    ]
    assert pass_details(unknown)[3:] == [
        "**Size:** unknown",
        "**If it hit:** unknown",
    ]
