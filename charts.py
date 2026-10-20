"""The dashboard's Plotly charts: close passes by date, and the fireball map."""

from datetime import date, timedelta

import plotly.graph_objects as go

from space import CloseApproach, Fireball
from tables import MOON_DISTANCES

REPORT_COLOR = "#1F4E78"
# Big enough dots to click, with labels that show when the mouse is near one
DOT_SIZE = 12
HOVER_DISTANCE = 30  # pixels


def approach_chart(passes: list[CloseApproach], start: date, end: date) -> go.Figure:
    """Distance by date, one dot per pass, with the name and date on hover.

    The dates along the bottom cover the whole time picked, through the end
    of the last day, not just the days that have passes.
    """
    figure = go.Figure(
        go.Scatter(
            x=[p.time for p in passes],
            y=[p.moon_distances for p in passes],
            text=[p.name for p in passes],
            mode="markers",
            marker={"color": REPORT_COLOR, "size": DOT_SIZE},
            hovertemplate=(
                "%{text}<br>%{x|%b %d, %Y %H:%M}<br>"
                "%{y:.2f} Moon distances<extra></extra>"
            ),
        )
    )
    # Dots below this line pass closer than the Moon
    figure.add_hline(
        y=1,
        line_dash="dash",
        line_color="#888888",
        annotation_text="Moon's orbit",
        annotation_position="top left",
    )
    figure.update_layout(
        height=320,
        margin={"t": 10, "b": 10},
        hovermode="closest",
        hoverdistance=HOVER_DISTANCE,
        xaxis={
            "tickformat": "%b %d",
            "range": [start.isoformat(), (end + timedelta(days=1)).isoformat()],
        },
        yaxis={"title": MOON_DISTANCES, "rangemode": "tozero"},
    )
    return figure


def fireball_map(fireballs: list[Fireball]) -> go.Figure:
    """One world map with a dot where each fireball burned up."""
    figure = go.Figure(
        go.Scattergeo(
            lat=[f.latitude for f in fireballs],
            lon=[f.longitude for f in fireballs],
            text=[
                f"{f.time:%b %d, %Y %H:%M} UTC<br>{f.impact_energy_kt:,} kilotons"
                for f in fireballs
            ],
            mode="markers",
            marker={"color": REPORT_COLOR, "size": DOT_SIZE},
            hoverinfo="text",
        )
    )
    figure.update_geos(
        projection_type="natural earth",
        showcountries=True,
        countrycolor="#C4C4C4",
        landcolor="#EEF1F4",
    )
    figure.update_layout(
        height=450,
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        hoverdistance=HOVER_DISTANCE,
    )
    return figure
