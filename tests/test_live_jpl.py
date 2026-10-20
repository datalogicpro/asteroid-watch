"""Live check: calls the real NASA/JPL APIs to catch changes to their replies.

These are left out of the normal test run. GitHub runs them once a day, and
they can be run by hand with:  uv run python -m pytest -m live --no-cov

Each test reads a real reply the same way the page does, so a renamed or
missing field, or a new API version, makes it fail.
"""

from collections.abc import Iterator
from datetime import date, timedelta

import pytest
import requests

import jpl
from space import (
    moon_distances_to_au,
    parse_close_approaches,
    parse_fireballs,
    parse_impact_risks,
)

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def session() -> Iterator[requests.Session]:
    with jpl.make_session() as s:
        yield s


def test_close_approach_api(session: requests.Session) -> None:
    today = date.today()
    reply = jpl.close_approaches(
        session, today, today + timedelta(days=60), moon_distances_to_au(10)
    )

    assert reply["signature"]["version"] == jpl.API_VERSIONS["cad.api"]
    # There are always some passes this close in the next 60 days
    assert parse_close_approaches(reply)


def test_impact_risk_api(session: requests.Session) -> None:
    reply = jpl.impact_risks(session)

    assert reply["signature"]["version"] == jpl.API_VERSIONS["sentry.api"]
    assert parse_impact_risks(reply)


def test_fireball_api(session: requests.Session) -> None:
    reply = jpl.fireballs(session, date.today() - timedelta(days=365))

    assert reply["signature"]["version"] == jpl.API_VERSIONS["fireball.api"]
    assert parse_fireballs(reply)
