"""Turn JPL's raw replies into clean records with everyday units.

JPL sends numbers as text and uses astronomy units, so each record here
converts them: distances to km, miles, and Moon distances, sizes to meters, and
fireball locations to signed latitude and longitude for a map.
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

AU_KM = 149_597_870.7  # 1 au, the average Earth-Sun distance
MOON_DISTANCE_KM = 384_399  # the average Earth-Moon distance
KM_PER_MILE = 1.609344

# How shiny an asteroid's surface is. Dark ones reflect about 5% of sunlight
# and shiny ones about 25%, so a size from brightness alone is a range.
DARK_ALBEDO = 0.05
SHINY_ALBEDO = 0.25


def au_to_km(au: float) -> float:
    return au * AU_KM


def km_to_miles(km: float) -> float:
    return km / KM_PER_MILE


def km_to_moon_distances(km: float) -> float:
    return km / MOON_DISTANCE_KM


def moon_distances_to_au(moon_distances: float) -> float:
    return moon_distances * MOON_DISTANCE_KM / AU_KM


def diameter_m(h: float, albedo: float) -> float:
    """Size in meters from brightness (H), using the standard formula."""
    return 1329 / math.sqrt(albedo) * 10 ** (-h / 5) * 1000


def size_range_m(h: float) -> tuple[float, float]:
    """The likely size range in meters: shiny (smaller) to dark (larger)."""
    return diameter_m(h, SHINY_ALBEDO), diameter_m(h, DARK_ALBEDO)


# What an impact could do, by size. A rough guide only: real effects also
# depend on speed, angle, and what the object is made of.
IMPACT_EFFECTS = [
    (10, "Burns up high in the air"),
    (40, "Air blast, like Chelyabinsk in 2013"),
    (140, "Could flatten a forest or city, like Tunguska in 1908"),
    (1000, "Regional damage"),
]
GLOBAL_EFFECTS = "Global effects"


def impact_effect(size_m: float | None) -> str | None:
    """What a hit by an object this size could do, or None when unknown."""
    if size_m is None:
        return None
    for limit, effect in IMPACT_EFFECTS:
        if size_m < limit:
            return effect
    return GLOBAL_EFFECTS


def number(value: Any) -> float | None:
    """A number from JPL's text, or None when it is missing."""
    return None if value is None else float(value)


def rows(reply: dict[str, Any]) -> list[dict[str, Any]]:
    """Pair each row's values with the field names JPL sends with them."""
    fields = reply.get("fields", [])
    return [dict(zip(fields, row, strict=True)) for row in reply.get("data", [])]


@dataclass(frozen=True)
class CloseApproach:
    name: str
    time: datetime
    distance_au: float
    speed_km_s: float
    h: float | None
    diameter_km: float | None

    @property
    def distance_km(self) -> float:
        return au_to_km(self.distance_au)

    @property
    def distance_miles(self) -> float:
        return km_to_miles(self.distance_km)

    @property
    def moon_distances(self) -> float:
        return km_to_moon_distances(self.distance_km)

    @property
    def size_m(self) -> tuple[float, float] | None:
        """Measured size when known, otherwise the range from brightness."""
        if self.diameter_km is not None:
            size = self.diameter_km * 1000
            return size, size
        if self.h is None:
            return None
        return size_range_m(self.h)

    @property
    def typical_size_m(self) -> float | None:
        """One size for sorting and labels: the middle of the size range."""
        if self.size_m is None:
            return None
        smallest, largest = self.size_m
        return math.sqrt(smallest * largest)


def parse_close_approaches(reply: dict[str, Any]) -> list[CloseApproach]:
    return [
        CloseApproach(
            name=(row.get("fullname") or row["des"]).strip(),
            time=datetime.strptime(row["cd"], "%Y-%b-%d %H:%M"),
            distance_au=float(row["dist"]),
            speed_km_s=float(row["v_rel"]),
            h=number(row.get("h")),
            diameter_km=number(row.get("diameter")),
        )
        for row in rows(reply)
    ]


@dataclass(frozen=True)
class ImpactRisk:
    name: str
    years: str
    impact_probability: float
    palermo: float
    torino: int | None
    diameter_km: float | None
    possible_impacts: int

    @property
    def size_m(self) -> float | None:
        return None if self.diameter_km is None else self.diameter_km * 1000

    @property
    def odds(self) -> str:
        """The impact chance as '1 in N', which is easier to read."""
        if self.impact_probability <= 0:
            return "none"
        return f"1 in {round(1 / self.impact_probability):,}"


def parse_impact_risks(reply: dict[str, Any]) -> list[ImpactRisk]:
    """Every Sentry object, highest risk first by the Palermo scale."""
    risks = [
        ImpactRisk(
            name=item["fullname"].strip(),
            years=item["range"],
            impact_probability=float(item["ip"]),
            palermo=float(item["ps_cum"]),
            torino=None if item.get("ts_max") is None else int(item["ts_max"]),
            diameter_km=number(item.get("diameter")),
            possible_impacts=int(item["n_imp"]),
        )
        for item in reply.get("data", [])
    ]
    return sorted(risks, key=lambda risk: risk.palermo, reverse=True)


@dataclass(frozen=True)
class Fireball:
    time: datetime
    latitude: float
    longitude: float
    altitude_km: float | None
    speed_km_s: float | None
    impact_energy_kt: float


def signed(value: str, direction: str, negative: str) -> float:
    """South and west become negative, as maps expect."""
    degrees = float(value)
    return -degrees if direction == negative else degrees


def parse_fireballs(reply: dict[str, Any]) -> list[Fireball]:
    return [
        Fireball(
            time=datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S"),
            latitude=signed(row["lat"], row["lat-dir"], "S"),
            longitude=signed(row["lon"], row["lon-dir"], "W"),
            altitude_km=number(row.get("alt")),
            speed_km_s=number(row.get("vel")),
            impact_energy_kt=float(row["impact-e"]),
        )
        for row in rows(reply)
    ]
