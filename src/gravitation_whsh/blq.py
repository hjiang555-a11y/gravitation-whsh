"""BLQ parsing and principal-constituent ocean-loading prediction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
from typing import Iterable

import numpy as np

CONSTITUENTS = ("M2", "S2", "N2", "K2", "K1", "O1", "P1", "Q1", "MF", "MM", "SSA")

# Doodson multipliers for (tau, s, h, p, N', ps), in BLQ column order.
DOODSON = np.asarray(
    [
        (2, 0, 0, 0, 0, 0),
        (2, 2, -2, 0, 0, 0),
        (2, -1, 0, 1, 0, 0),
        (2, 2, 0, 0, 0, 0),
        (1, 1, 0, 0, 0, 0),
        (1, -1, 0, 0, 0, 0),
        (1, 1, -2, 0, 0, 0),
        (1, -2, 0, 1, 0, 0),
        (0, 2, 0, 0, 0, 0),
        (0, 1, 0, -1, 0, 0),
        (0, 0, 2, 0, 0, 0),
    ],
    dtype=float,
)


@dataclass(frozen=True)
class BlqStation:
    """Ocean-loading amplitudes and phase lags in standard BLQ order."""

    name: str
    amplitudes_m: np.ndarray
    phases_deg: np.ndarray

    @property
    def radial_amplitudes_m(self) -> np.ndarray:
        return self.amplitudes_m[0]

    @property
    def radial_phases_deg(self) -> np.ndarray:
        return self.phases_deg[0]


def _numeric_row(line: str) -> list[float] | None:
    try:
        values = [float(value) for value in line.split()]
    except ValueError:
        return None
    return values if len(values) == len(CONSTITUENTS) else None


def read_blq(path: str | Path) -> dict[str, BlqStation]:
    """Read one or more six-row station records from a BLQ file."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    stations: dict[str, BlqStation] = {}
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line.startswith(("$$", "#")) or _numeric_row(line) is not None:
            index += 1
            continue

        rows: list[list[float]] = []
        cursor = index + 1
        while cursor < len(lines) and len(rows) < 6:
            candidate = lines[cursor].strip()
            if candidate and not candidate.startswith(("$$", "#")):
                row = _numeric_row(candidate)
                if row is None:
                    break
                rows.append(row)
            cursor += 1

        if len(rows) == 6:
            key = line.split()[0].upper()
            stations[key] = BlqStation(
                name=key,
                amplitudes_m=np.asarray(rows[:3], dtype=float),
                phases_deg=np.asarray(rows[3:], dtype=float),
            )
            index = cursor
        else:
            index += 1

    if not stations:
        raise ValueError(f"No valid six-row BLQ station record found in {path}")
    return stations


def _julian_dates(datetimes: Iterable[datetime]) -> np.ndarray:
    unix_seconds = np.asarray(
        [
            value.astimezone(timezone.utc).timestamp()
            if value.tzinfo
            else value.replace(tzinfo=timezone.utc).timestamp()
            for value in datetimes
        ],
        dtype=float,
    )
    return unix_seconds / 86400.0 + 2440587.5


def astronomical_arguments(datetimes: Iterable[datetime]) -> np.ndarray:
    """Return Doodson fundamental arguments in degrees.

    UT1 is approximated by UTC; the resulting phase error is below 0.01 degrees
    for the requested dates.
    """
    jd = _julian_dates(datetimes)
    centuries = (jd - 2451545.0) / 36525.0

    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * centuries**2
        - centuries**3 / 38710000.0
    )
    moon = (
        218.31664563
        + 481267.88194 * centuries
        - 0.0014663889 * centuries**2
        + centuries**3 / 540000.0
    )
    sun = 280.46645 + 36000.7697489 * centuries + 0.00030322222 * centuries**2
    perigee = (
        83.35324312
        + 4069.01363525 * centuries
        - 0.01032172222 * centuries**2
        - centuries**3 / 80053.0
    )
    ascending_node = (
        125.04455501
        - 1934.13626197 * centuries
        + 0.00207561111 * centuries**2
        + centuries**3 / 467441.0
    )
    solar_perigee = 282.93734098 + 1.71945766667 * centuries + 0.00045688889 * centuries**2
    tau = gmst + 180.0 - moon
    return np.column_stack((tau, moon, sun, perigee, -ascending_node, solar_perigee)) % 360.0


def radial_displacement(station: BlqStation, datetimes: Iterable[datetime]) -> np.ndarray:
    """Predict radial loading displacement from the 11 principal BLQ tides."""
    arguments = astronomical_arguments(datetimes)
    constituent_phase = arguments @ DOODSON.T
    lag = station.radial_phases_deg[np.newaxis, :]
    amplitude = station.radial_amplitudes_m[np.newaxis, :]
    return np.sum(amplitude * np.cos(np.deg2rad(constituent_phase - lag)), axis=1)


def normal_gravity(latitude_deg: float, height_m: float) -> float:
    """Somigliana normal gravity with the free-air height correction."""
    latitude = math.radians(latitude_deg)
    sin2 = math.sin(latitude) ** 2
    equatorial = 9.7803253359
    k = 0.00193185265241
    eccentricity2 = 0.00669437999013
    surface = equatorial * (1.0 + k * sin2) / math.sqrt(1.0 - eccentricity2 * sin2)
    return surface - 3.086e-6 * height_m
