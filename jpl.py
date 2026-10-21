"""Get data from NASA/JPL's Solar System Dynamics (SSD) APIs.

The three APIs used here need no key:
- Close-Approach Data: asteroids and comets passing near Earth
- Sentry: objects with a chance of hitting Earth
- Fireball: space rocks that burned up in the sky

Busy-server replies are retried with backoff, and every request is logged
with its own ID so a failure can be traced in the logs.
"""

import logging
import os
import uuid
from datetime import date
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# JPL_BASE_URL can point the app at a stand-in server, as the browser test does
BASE_URL = os.environ.get("JPL_BASE_URL", "https://ssd-api.jpl.nasa.gov")
TIMEOUT = 30  # seconds

# The API versions this code was written against. JPL asks callers to check
# the version in each reply, since format changes are not otherwise flagged.
API_VERSIONS = {"cad.api": "1.5", "sentry.api": "2.0", "fireball.api": "1.2"}

# Replies that mean "try again later"
RETRY_STATUSES = (429, 500, 502, 503, 504)

log = logging.getLogger(__name__)


class JplError(Exception):
    """NASA/JPL's servers could not be reached or sent a bad reply."""


def make_session() -> requests.Session:
    """A session that retries busy-server replies: after 1, 2, then 4 seconds."""
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def get_json(
    session: requests.Session, path: str, params: dict[str, str]
) -> dict[str, Any]:
    """Call one JPL API and return its reply.

    Raises JplError when the call fails, so the page can show a clear message.
    """
    request_id = uuid.uuid4().hex[:8]
    log.info("request_id=%s GET %s params=%s", request_id, path, params)
    try:
        response = session.get(f"{BASE_URL}/{path}", params=params, timeout=TIMEOUT)
        response.raise_for_status()
        reply = response.json()
    except requests.RequestException as exc:
        log.error("request_id=%s failed: %s", request_id, exc)
        raise JplError(
            f"NASA/JPL's servers didn't answer (request {request_id}). "
            "Please try again in a few minutes."
        ) from exc
    except ValueError as exc:
        log.error("request_id=%s sent a reply that isn't JSON", request_id)
        raise JplError(
            f"NASA/JPL sent a reply that couldn't be read (request {request_id})."
        ) from exc

    if not isinstance(reply, dict):
        log.error("request_id=%s sent an unexpected reply", request_id)
        raise JplError(
            f"NASA/JPL sent a reply that couldn't be read (request {request_id})."
        )

    version = reply.get("signature", {}).get("version")
    if version != API_VERSIONS[path]:
        log.warning(
            "request_id=%s %s version is %s, written for %s",
            request_id,
            path,
            version,
            API_VERSIONS[path],
        )
    log.info("request_id=%s OK count=%s", request_id, reply.get("count"))
    return reply


def close_approaches(
    session: requests.Session,
    start: date,
    end: date,
    max_distance_au: float,
    hazardous_only: bool = False,
) -> dict[str, Any]:
    """Close passes by asteroids and comets between two dates, closest first.

    hazardous_only keeps only NASA's "potentially hazardous asteroids":
    about 140 m or larger, with orbits that come close to Earth's.
    """
    params = {
        "date-min": start.isoformat(),
        "date-max": end.isoformat(),
        "dist-max": str(max_distance_au),
        "sort": "dist",
        "diameter": "true",
        "fullname": "true",
    }
    if hazardous_only:
        params["pha"] = "true"
    return get_json(session, "cad.api", params)


def impact_risks(session: requests.Session) -> dict[str, Any]:
    """Every object on NASA's Sentry impact-risk list."""
    return get_json(session, "sentry.api", {})


def fireballs(session: requests.Session, start: date) -> dict[str, Any]:
    """Fireballs since a date that have a known location, newest first."""
    params = {"date-min": start.isoformat(), "req-loc": "true", "sort": "-date"}
    return get_json(session, "fireball.api", params)
