"""Tests for calling NASA/JPL. Nothing here makes a real call."""

import logging
from datetime import date
from typing import Any, cast

import pytest
import requests
from requests.adapters import HTTPAdapter

import jpl


class FakeResponse:
    def __init__(self, reply: Any, status: int = 200) -> None:
        self.reply = reply
        self.status = status

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise requests.HTTPError(f"{self.status} error")

    def json(self) -> Any:
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


class FakeSession:
    """Stands in for requests.Session: records each call and answers with a
    prepared reply."""

    def __init__(self, response: FakeResponse | Exception) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def as_session(fake: FakeSession) -> requests.Session:
    """Let the type checker accept the fake where a real session is expected."""
    return cast(requests.Session, fake)


def test_session_retries_busy_server_replies() -> None:
    session = jpl.make_session()

    adapter = session.get_adapter("https://ssd-api.jpl.nasa.gov")
    assert isinstance(adapter, HTTPAdapter)
    retry = adapter.max_retries
    assert retry.total == 3
    assert retry.backoff_factor == 1
    assert set(retry.status_forcelist or []) == {429, 500, 502, 503, 504}
    session.close()


def test_close_approaches_asks_for_the_right_data(cad_reply: dict[str, Any]) -> None:
    session = FakeSession(FakeResponse(cad_reply))

    reply = jpl.close_approaches(
        as_session(session), date(2026, 10, 20), date(2026, 12, 19), 0.05
    )

    assert reply["count"] == 3
    call = session.calls[0]
    assert call["url"] == "https://ssd-api.jpl.nasa.gov/cad.api"
    assert call["params"]["date-min"] == "2026-10-20"
    assert call["params"]["date-max"] == "2026-12-19"
    assert call["params"]["dist-max"] == "0.05"
    assert call["params"]["sort"] == "dist"
    assert call["timeout"] == jpl.TIMEOUT


def test_impact_risks(sentry_reply: dict[str, Any]) -> None:
    session = FakeSession(FakeResponse(sentry_reply))

    reply = jpl.impact_risks(as_session(session))

    assert len(reply["data"]) == 3
    assert session.calls[0]["url"] == "https://ssd-api.jpl.nasa.gov/sentry.api"


def test_fireballs_asks_for_located_fireballs_newest_first(
    fireball_reply: dict[str, Any],
) -> None:
    session = FakeSession(FakeResponse(fireball_reply))

    jpl.fireballs(as_session(session), date(2026, 1, 1))

    params = session.calls[0]["params"]
    assert params == {"date-min": "2026-01-01", "req-loc": "true", "sort": "-date"}


def test_calls_are_logged_with_a_request_id(
    caplog: pytest.LogCaptureFixture, sentry_reply: dict[str, Any]
) -> None:
    session = FakeSession(FakeResponse(sentry_reply))

    with caplog.at_level(logging.INFO):
        jpl.impact_risks(as_session(session))

    assert "request_id=" in caplog.text
    assert "OK count=3" in caplog.text


def test_a_changed_api_version_is_logged(
    caplog: pytest.LogCaptureFixture, sentry_reply: dict[str, Any]
) -> None:
    sentry_reply["signature"]["version"] = "3.0"
    session = FakeSession(FakeResponse(sentry_reply))

    jpl.impact_risks(as_session(session))

    assert "sentry.api version is 3.0, written for 2.0" in caplog.text


@pytest.mark.parametrize(
    "response",
    [
        requests.ConnectionError("no connection"),
        FakeResponse({}, status=503),
    ],
)
def test_failed_calls_raise_a_clear_error(
    response: FakeResponse | Exception, caplog: pytest.LogCaptureFixture
) -> None:
    session = FakeSession(response)

    with pytest.raises(jpl.JplError, match="didn't answer"):
        jpl.impact_risks(as_session(session))

    assert "failed" in caplog.text


@pytest.mark.parametrize("reply", [ValueError("not JSON"), ["not", "a", "dict"]])
def test_unreadable_replies_raise_a_clear_error(reply: Any) -> None:
    session = FakeSession(FakeResponse(reply))

    with pytest.raises(jpl.JplError, match="couldn't be read"):
        jpl.impact_risks(as_session(session))
