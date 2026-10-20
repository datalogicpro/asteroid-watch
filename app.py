"""Asteroid Watch: asteroids and comets passing near Earth, impact risks,
and fireballs, from NASA/JPL.

Run it with:  uv run streamlit run app.py

This file is the page itself: the tabs, the sliders and other choices, and
the calls to NASA/JPL. The charts are in charts.py, and the table rows and
details text are in tables.py.

Each NASA/JPL reply is saved for an hour, so the page doesn't call NASA on
every click.
"""

import logging
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

import streamlit as st

import jpl
from charts import approach_chart, fireball_map
from space import (
    CloseApproach,
    moon_distances_to_au,
    parse_close_approaches,
    parse_fireballs,
    parse_impact_risks,
)
from tables import (
    BIGGEST_FIRST,
    CLOSEST_FIRST,
    approach_table,
    fireball_table,
    pass_details,
    risk_table,
    size_text,
    sort_passes,
)

CACHE_SECONDS = 60 * 60
MAX_PAST_DAYS = 366
MOON_NOTE = (
    "Distances are in Moon distances. 1 Moon distance is how far the Moon is "
    "from Earth: 384,399 km, or 238,855 miles. A pass at 0.5 Moon distances "
    "comes halfway to the Moon."
)
EFFECT_NOTE = (
    '"If it hit" is a rough guide from size alone; real effects also depend '
    "on speed, angle, and what the object is made of."
)
CREDIT = (
    "Data: NASA/JPL Center for Near Earth Object Studies (CNEOS), "
    "through JPL's Solar System Dynamics APIs."
)
# Big numbers get thousands separators, like 314,648
COMMAS = st.column_config.NumberColumn(format="localized")


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Asking NASA/JPL...")
def load_close_approaches(
    start: date, end: date, max_au: float, hazardous_only: bool
) -> dict[str, Any]:
    with jpl.make_session() as session:
        return jpl.close_approaches(session, start, end, max_au, hazardous_only)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Asking NASA/JPL...")
def load_impact_risks() -> dict[str, Any]:
    with jpl.make_session() as session:
        return jpl.impact_risks(session)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Asking NASA/JPL...")
def load_fireballs(start: date) -> dict[str, Any]:
    with jpl.make_session() as session:
        return jpl.fireballs(session, start)


def selected_pass(
    passes: list[CloseApproach], selection: Mapping[str, Any]
) -> CloseApproach | None:
    """The pass whose dot was clicked on the chart, or None."""
    indices = selection.get("point_indices") or []
    if not indices:
        return None
    index = int(indices[0])
    return passes[index] if index < len(passes) else None


def show_details(p: CloseApproach | None) -> None:
    """The clicked pass in large text, so nothing is hidden under the mouse."""
    if p is None:
        st.caption("Click a dot on the chart to see its details here.")
        return
    with st.container(border=True):
        st.subheader(p.name)
        st.markdown("  \n".join(pass_details(p)))


def pass_filters(key: str) -> tuple[float, bool, str]:
    """The distance, hazardous-only, and sort choices for a close-pass tab."""
    closer_than = st.slider(
        "Closer than (Moon distances, 1 = 384,399 km)",
        min_value=1,
        max_value=50,
        value=10,
        key=f"{key}_distance",
    )
    hazardous_only = st.checkbox(
        "Only potentially hazardous asteroids (about 140 m or larger, with "
        "orbits that come close to Earth's)",
        key=f"{key}_hazardous",
    )
    order = st.radio(
        "Sort by",
        [CLOSEST_FIRST, BIGGEST_FIRST],
        horizontal=True,
        key=f"{key}_order",
    )
    return moon_distances_to_au(closer_than), hazardous_only, order or CLOSEST_FIRST


def show_close_approaches(
    passes: list[CloseApproach], start: date, end: date, order: str, key: str
) -> None:
    """Counts, a chart, and a table for the close passes from start to end.

    The key keeps the upcoming and past charts and tables apart when they
    show the same passes.
    """
    if not passes:
        st.info("No close passes match. Try more days or a larger distance.")
        return

    closest = min(passes, key=lambda p: p.distance_au)
    count, near, big = st.columns(3)
    count.metric("Close passes", len(passes))
    near.metric(
        f"Closest: {closest.name}", f"{closest.moon_distances:.2f} Moon distances"
    )
    sized = [p for p in passes if p.typical_size_m is not None]
    if sized:
        biggest = max(sized, key=lambda p: p.typical_size_m or 0)
        big.metric(f"Biggest: {biggest.name}", f"{size_text(biggest.size_m)} m")

    # Clicking a dot shows its details below the chart
    chart = st.plotly_chart(
        approach_chart(passes, start, end),
        key=f"{key}_chart",
        on_select="rerun",
        selection_mode="points",
    )
    show_details(selected_pass(passes, chart.selection))
    st.dataframe(
        approach_table(sort_passes(passes, order)),
        hide_index=True,
        placeholder="—",
        column_config={"Distance (km)": COMMAS, "Distance (miles)": COMMAS},
        key=f"{key}_table",
    )
    st.caption(
        "Sizes are a range when only the object's brightness is known. Dates "
        "are in TDB, within about a minute of UTC. " + EFFECT_NOTE
    )


def upcoming_tab(today: date) -> None:
    st.caption(MOON_NOTE)
    days = st.slider("Days ahead", min_value=7, max_value=365, value=60)
    max_au, hazardous_only, order = pass_filters("upcoming")
    end = today + timedelta(days=days)
    reply = load_close_approaches(today, end, max_au, hazardous_only)
    show_close_approaches(
        parse_close_approaches(reply), today, end, order, key="upcoming"
    )


def past_tab(today: date) -> None:
    st.caption(MOON_NOTE)
    picked = st.date_input(
        "Dates",
        value=(today - timedelta(days=30), today),
        max_value=today,
    )
    dates = list(picked) if isinstance(picked, tuple) else []
    if len(dates) != 2:
        st.info("Pick a start date and an end date.")
        return
    start, end = dates
    if (end - start).days > MAX_PAST_DAYS:
        st.warning("Pick a range of one year or less.")
        return
    max_au, hazardous_only, order = pass_filters("past")
    reply = load_close_approaches(start, end, max_au, hazardous_only)
    show_close_approaches(parse_close_approaches(reply), start, end, order, key="past")


def risk_tab() -> None:
    risks = parse_impact_risks(load_impact_risks())
    if not risks:
        st.info("The impact-risk list is empty right now.")
        return

    count, highest, rated = st.columns(3)
    count.metric("Objects on the list", f"{len(risks):,}")
    highest.metric("Highest Palermo scale", risks[0].palermo)
    rated.metric(
        "Torino 1 or higher",
        sum(1 for r in risks if r.torino is not None and r.torino >= 1),
    )
    st.dataframe(
        risk_table(risks),
        hide_index=True,
        placeholder="—",
        column_config={"Size (m)": COMMAS},
    )
    st.caption(
        "Highest risk first. Palermo scale: below -2 is no concern; -2 to 0 "
        "is worth watching. Torino scale: 0 is no hazard, 10 is a certain "
        "collision with global effects; it only covers the next 100 years. "
        + EFFECT_NOTE
    )


def fireball_tab(today: date) -> None:
    years = st.slider("Years back", min_value=1, max_value=10, value=1)
    fireballs = parse_fireballs(load_fireballs(today - timedelta(days=365 * years)))
    if not fireballs:
        st.info("No fireballs with a known location in this time.")
        return

    count, biggest = st.columns(2)
    count.metric("Fireballs", len(fireballs))
    biggest.metric(
        "Largest",
        f"{max(f.impact_energy_kt for f in fireballs):,} kilotons",
    )
    st.plotly_chart(fireball_map(fireballs))
    st.dataframe(fireball_table(fireballs), hide_index=True, placeholder="—")
    st.caption(
        "Space rocks that burned up in the sky, newest first. Energy is the "
        "estimated total impact energy in kilotons of TNT."
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    st.set_page_config(page_title="Asteroid Watch", layout="wide")
    st.title("Asteroid Watch")
    st.write(
        "Asteroids and comets passing near Earth, the objects with a chance of "
        "hitting it, and the space rocks that burned up in the sky."
    )

    today = date.today()
    upcoming, past, risk, fireball = st.tabs(
        ["Upcoming close passes", "Past close passes", "Impact risk", "Fireballs"]
    )
    for tab, show in [
        (upcoming, lambda: upcoming_tab(today)),
        (past, lambda: past_tab(today)),
        (risk, risk_tab),
        (fireball, lambda: fireball_tab(today)),
    ]:
        with tab:
            try:
                show()
            except jpl.JplError as exc:
                st.error(str(exc))

    st.caption(CREDIT)


if __name__ == "__main__":
    main()
