"""Tests for the close-pass chart and the fireball map."""

from datetime import date
from typing import Any

import pytest

from charts import approach_chart, fireball_map
from space import parse_close_approaches, parse_fireballs


def test_approach_chart(cad_reply: dict[str, Any]) -> None:
    figure = approach_chart(
        parse_close_approaches(cad_reply), date(2026, 10, 20), date(2026, 12, 19)
    )

    dots = figure.data[0]
    assert list(dots.text) == ["(2025 UK9)", "(2017 WJ2)", "(2019 XF2)"]
    assert dots.y[0] == pytest.approx(0.82, abs=0.01)
    # The axis says what a Moon distance is
    assert figure.layout.yaxis.title.text == "Moon distances (1 = 384,399 km)"
    # A dashed line marks the Moon's orbit, 1 Moon distance away
    moon_line = figure.layout.shapes[0]
    assert (moon_line.y0, moon_line.y1) == (1, 1)
    assert moon_line.line.dash == "dash"
    # Big dots that are easy to click, with labels that show from nearby
    assert dots.marker.size == 12
    assert figure.layout.hoverdistance == 30
    # The bottom covers every day picked, through the end of the last one
    assert list(figure.layout.xaxis.range) == ["2026-10-20", "2026-12-20"]


def test_fireball_map(fireball_reply: dict[str, Any]) -> None:
    figure = fireball_map(parse_fireballs(fireball_reply))

    dots = figure.data[0]
    assert list(dots.lat) == [-41.8, -37.6, 46.6]
    assert list(dots.lon) == [-173.1, -161.6, 133.1]
    assert dots.text[0] == "Oct 04, 2026 03:14 UTC<br>0.18 kilotons"
    assert dots.marker.size == 12
    assert figure.layout.hoverdistance == 30
    # The whole world shows once, not repeated side by side
    assert figure.layout.geo.projection.type == "natural earth"
