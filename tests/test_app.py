"""Tests for the dashboard page. Nothing here calls NASA/JPL."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import jpl
from app import selected_pass, show_details
from space import parse_close_approaches
from tables import BIGGEST_FIRST

APP_FILE = str(Path(__file__).parent.parent / "app.py")

# The first run imports Streamlit, which can take a while
TIMEOUT = 30


class FakeJpl:
    """The three JPL calls, answered with saved replies."""

    def __init__(self, cad: Any, sentry: Any, fireball: Any) -> None:
        self.close_approaches = MagicMock(return_value=cad)
        self.impact_risks = MagicMock(return_value=sentry)
        self.fireballs = MagicMock(return_value=fireball)


@pytest.fixture
def fake_jpl(
    cad_reply: dict[str, Any],
    sentry_reply: dict[str, Any],
    fireball_reply: dict[str, Any],
) -> Iterator[FakeJpl]:
    """Swap in the saved replies, and start each test with nothing saved."""
    fake = FakeJpl(cad_reply, sentry_reply, fireball_reply)
    st.cache_data.clear()
    with (
        patch.object(jpl, "close_approaches", fake.close_approaches),
        patch.object(jpl, "impact_risks", fake.impact_risks),
        patch.object(jpl, "fireballs", fake.fireballs),
    ):
        yield fake
    st.cache_data.clear()


def run_page() -> AppTest:
    return AppTest.from_file(APP_FILE, default_timeout=TIMEOUT).run()


def metric_values(app: AppTest) -> list[str]:
    return [metric.value for metric in app.metric]


def test_selected_pass(cad_reply: dict[str, Any]) -> None:
    passes = parse_close_approaches(cad_reply)

    assert selected_pass(passes, {"point_indices": [1]}) == passes[1]
    # Nothing clicked yet
    assert selected_pass(passes, {"point_indices": []}) is None
    assert selected_pass(passes, {}) is None
    # A click left over from a different list of passes is ignored
    assert selected_pass(passes, {"point_indices": [9]}) is None


def test_show_details(cad_reply: dict[str, Any]) -> None:
    clicked = parse_close_approaches(cad_reply)[0]

    with (
        patch.object(st, "caption") as caption,
        patch.object(st, "subheader") as subheader,
        patch.object(st, "markdown") as markdown,
    ):
        show_details(None)
        show_details(clicked)

    caption.assert_called_once_with("Click a dot on the chart to see its details here.")
    subheader.assert_called_once_with("(2025 UK9)")
    assert "0.82 Moon distances" in markdown.call_args.args[0]


def test_page_shows_every_tab(fake_jpl: FakeJpl) -> None:
    app = run_page()

    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Upcoming close passes",
        "Past close passes",
        "Impact risk",
        "Fireballs",
    ]
    close_passes = ["3", "0.82 Moon distances", "240 m"]
    assert metric_values(app) == [
        *close_passes,  # upcoming
        *close_passes,  # past
        "3",
        "-0.95",
        "0",
        "3",
        "0.18 kilotons",
    ]
    assert app.metric[1].label == "Closest: (2025 UK9)"
    assert app.metric[2].label == "Biggest: (2017 WJ2)"
    # Both close-pass tabs explain what a Moon distance is at the top
    notes = [c.value for c in app.caption if c.value.startswith("Distances are in")]
    assert len(notes) == 2
    assert "384,399 km, or 238,855 miles" in notes[0]
    assert "CNEOS" in app.caption[-1].value


def test_upcoming_asks_for_the_next_60_days(fake_jpl: FakeJpl) -> None:
    run_page()

    start, end, max_au, hazardous_only = fake_jpl.close_approaches.call_args_list[
        0
    ].args[1:]
    assert (end - start).days == 60
    # 10 Moon distances
    assert max_au == pytest.approx(0.0257, abs=0.0001)
    assert hazardous_only is False


def test_hazardous_only_is_sent_to_nasa(fake_jpl: FakeJpl) -> None:
    app = run_page()

    app.checkbox(key="upcoming_hazardous").check().run()

    assert not app.exception
    assert fake_jpl.close_approaches.call_args.args[4] is True


def test_biggest_first(fake_jpl: FakeJpl) -> None:
    app = run_page()

    app.radio(key="upcoming_order").set_value(BIGGEST_FIRST).run()

    assert not app.exception
    table = app.dataframe[0].value
    assert list(table["Object"]) == ["(2017 WJ2)", "(2025 UK9)", "(2019 XF2)"]
    assert list(table.columns) == [
        "Object",
        "Date",
        "Moon distances (1 = 384,399 km)",
        "Distance (km)",
        "Distance (miles)",
        "Speed (km/s)",
        "Size (m)",
        "If it hit",
    ]


def test_no_biggest_when_no_sizes_are_known(
    fake_jpl: FakeJpl, cad_reply: dict[str, Any]
) -> None:
    for row in cad_reply["data"]:
        row[10] = row[11] = None  # no brightness and no measured size
    fake_jpl.close_approaches.return_value = cad_reply

    app = run_page()

    assert not app.exception
    labels = [metric.label for metric in app.metric]
    assert not any(label.startswith("Biggest") for label in labels)


def test_replies_are_saved_between_runs(fake_jpl: FakeJpl) -> None:
    app = run_page()
    app.run()

    assert fake_jpl.impact_risks.call_count == 1


def test_past_needs_two_dates(fake_jpl: FakeJpl) -> None:
    app = run_page()

    app.date_input[0].set_value((date(2026, 1, 1),)).run()

    assert not app.exception
    assert "Pick a start date and an end date." in [i.value for i in app.info]


def test_past_allows_one_year_at_most(fake_jpl: FakeJpl) -> None:
    app = run_page()

    app.date_input[0].set_value((date(2024, 1, 1), date(2026, 1, 1))).run()

    assert not app.exception
    assert app.warning[0].value == "Pick a range of one year or less."


def test_empty_replies_explain_what_to_do(fake_jpl: FakeJpl) -> None:
    fake_jpl.close_approaches.return_value = {"count": 0}
    fake_jpl.impact_risks.return_value = {"count": "0"}
    fake_jpl.fireballs.return_value = {"count": "0"}

    app = run_page()

    assert not app.exception
    assert not app.metric
    assert len(app.info) == 4


def test_nasa_errors_show_a_message_in_that_tab(fake_jpl: FakeJpl) -> None:
    fake_jpl.impact_risks.side_effect = jpl.JplError("NASA/JPL's servers didn't answer")

    app = run_page()

    assert not app.exception
    assert app.error[0].value == "NASA/JPL's servers didn't answer"
    # The other tabs still work
    assert len(app.metric) == 8
