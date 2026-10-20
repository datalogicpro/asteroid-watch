"""Shared test setup: saved JPL replies, trimmed to a few records each.

They let every test run with no real calls to NASA/JPL.
"""

import json
from pathlib import Path
from typing import Any

import pytest

DATA = Path(__file__).parent / "data"


def load(name: str) -> dict[str, Any]:
    reply: dict[str, Any] = json.loads((DATA / f"{name}.json").read_text())
    return reply


@pytest.fixture
def cad_reply() -> dict[str, Any]:
    """3 close passes. The second has a measured diameter added for the tests,
    and the third has its brightness removed."""
    return load("cad")


@pytest.fixture
def sentry_reply() -> dict[str, Any]:
    """3 objects from the impact-risk list."""
    return load("sentry")


@pytest.fixture
def fireball_reply() -> dict[str, Any]:
    """3 fireballs: one south-west, one with no speed, one north-east."""
    return load("fireball")
