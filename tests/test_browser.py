"""Browser test: runs the real page in Chrome and clicks a dot on the chart.

The page talks to a small stand-in JPL server here that sends the saved
replies, so this test never calls NASA/JPL.
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from collections.abc import Iterator
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page, expect

APP_FILE = str(Path(__file__).parent.parent / "app.py")
DATA = Path(__file__).parent / "data"
START_SECONDS = 60
# Puts the saved passes inside the page's default 60 days ahead
DAYS_AHEAD = (3, 8, 15)


def load(name: str) -> Any:
    return json.loads((DATA / f"{name}.json").read_text())


def upcoming_cad_reply() -> Any:
    """The saved close passes, moved to dates in the next few days."""
    reply = load("cad")
    for row, days in zip(reply["data"], DAYS_AHEAD, strict=True):
        row[3] = f"{date.today() + timedelta(days=days):%Y-%b-%d} 02:35"
    return reply


class FakeJpl(BaseHTTPRequestHandler):
    """Answers each JPL API with its saved reply, whatever is asked."""

    def do_GET(self) -> None:
        api = self.path.split("?")[0].strip("/")
        replies = {
            "cad.api": upcoming_cad_reply,
            "sentry.api": lambda: load("sentry"),
            "fireball.api": lambda: load("fireball"),
        }
        if api not in replies:
            self.send_error(404)
            return
        body = json.dumps(replies[api]()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Keep the test output quiet."""


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port: int = s.getsockname()[1]
        return port


def wait_for(url: str) -> None:
    """Wait until the page answers, or fail after START_SECONDS."""
    deadline = time.monotonic() + START_SECONDS
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except OSError:
            time.sleep(0.5)
    pytest.fail(f"The page didn't start within {START_SECONDS} seconds")


@pytest.fixture(scope="module")
def page_url() -> Iterator[str]:
    """Start the stand-in JPL server and the real page, then stop both."""
    jpl_server = ThreadingHTTPServer(("127.0.0.1", 0), FakeJpl)
    threading.Thread(target=jpl_server.serve_forever, daemon=True).start()
    port = free_port()
    app = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            APP_FILE,
            "--server.headless=true",
            f"--server.port={port}",
            "--server.fileWatcherType=none",
            "--browser.gatherUsageStats=false",
        ],
        env={
            **os.environ,
            "JPL_BASE_URL": f"http://127.0.0.1:{jpl_server.server_port}",
        },
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        wait_for(url)
        yield url
    finally:
        app.terminate()
        app.wait(timeout=10)
        jpl_server.shutdown()
        jpl_server.server_close()


def test_clicking_a_dot_shows_its_details(page: Page, page_url: str) -> None:
    page.goto(page_url)
    hint = page.get_by_text("Click a dot on the chart to see its details here.")
    expect(hint.first).to_be_visible(timeout=30_000)

    # The first dot on the Upcoming chart is (2025 UK9)
    chart = page.locator(".js-plotly-plot").first
    dot = chart.locator(".scatterlayer .point").first
    expect(dot).to_be_visible()
    # The mouse can only reach what's on the screen
    dot.scroll_into_view_if_needed()
    box = dot.bounding_box()
    assert box is not None
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2

    # Plotly only counts a click on a dot once the mouse is over it and its
    # label shows, the same as a person would do
    page.mouse.move(x, y)
    expect(chart.locator(".hoverlayer .hovertext").first).to_be_visible()
    page.mouse.click(x, y)

    details = page.get_by_text("0.82 Moon distances, or 314,648 km (195,513 miles)")
    expect(details.first).to_be_visible()
    expect(page.get_by_role("heading", name="(2025 UK9)").first).to_be_visible()
