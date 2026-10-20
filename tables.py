"""Rows for the dashboard's tables, and the text in the details box.

Nothing here draws anything; each function turns records from space.py into
the plain values the page shows.
"""

from typing import Any

from space import CloseApproach, Fireball, ImpactRisk, impact_effect

# A Moon distance is its own unit, so every label that uses it says what it is
MOON_DISTANCES = "Moon distances (1 = 384,399 km)"
CLOSEST_FIRST = "Closest first"
BIGGEST_FIRST = "Biggest first"


def size_text(size: tuple[float, float] | None) -> str | None:
    """'240' for a measured size, '2.9–6.4' for a range, None when unknown."""
    if size is None:
        return None
    smallest, largest = size
    if smallest == largest:
        return f"{smallest:,.0f}"
    places = 1 if largest < 10 else 0
    return f"{smallest:,.{places}f}–{largest:,.{places}f}"


def approach_table(passes: list[CloseApproach]) -> list[dict[str, Any]]:
    return [
        {
            "Object": p.name,
            "Date": p.time,
            MOON_DISTANCES: round(p.moon_distances, 2),
            "Distance (km)": round(p.distance_km),
            "Distance (miles)": round(p.distance_miles),
            "Speed (km/s)": round(p.speed_km_s, 1),
            "Size (m)": size_text(p.size_m),
            "If it hit": impact_effect(p.typical_size_m),
        }
        for p in passes
    ]


def sort_passes(passes: list[CloseApproach], order: str) -> list[CloseApproach]:
    """Closest first, or biggest first with unknown sizes last."""
    if order == BIGGEST_FIRST:
        return sorted(passes, key=lambda p: -(p.typical_size_m or 0))
    return sorted(passes, key=lambda p: p.distance_au)


def pass_details(p: CloseApproach) -> list[str]:
    """Everything about one pass, one line each, for the box under the chart."""
    size = size_text(p.size_m)
    return [
        f"**Date:** {p.time:%B %d, %Y at %H:%M} (TDB)",
        f"**Distance:** {p.moon_distances:.2f} Moon distances, or "
        f"{p.distance_km:,.0f} km ({p.distance_miles:,.0f} miles)",
        f"**Speed:** {p.speed_km_s:.1f} km/s",
        f"**Size:** {size} m" if size else "**Size:** unknown",
        f"**If it hit:** {impact_effect(p.typical_size_m) or 'unknown'}",
    ]


def risk_table(risks: list[ImpactRisk]) -> list[dict[str, Any]]:
    return [
        {
            "Object": r.name,
            "Years": r.years,
            "Impact chance": r.odds,
            "Palermo scale": r.palermo,
            "Torino scale": r.torino,
            "Size (m)": None if r.size_m is None else round(r.size_m),
            "If it hit": impact_effect(r.size_m),
            "Possible impacts": r.possible_impacts,
        }
        for r in risks
    ]


def fireball_table(fireballs: list[Fireball]) -> list[dict[str, Any]]:
    return [
        {
            "Date (UTC)": f.time,
            "Latitude": f.latitude,
            "Longitude": f.longitude,
            "Altitude (km)": f.altitude_km,
            "Speed (km/s)": f.speed_km_s,
            "Energy (kilotons)": f.impact_energy_kt,
        }
        for f in fireballs
    ]
