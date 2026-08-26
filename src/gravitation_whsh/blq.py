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
DOODSON_WARBURG_DEG = np.where(
    DOODSON[:, 0] == 0.0, 180.0, np.where(DOODSON[:, 0] == 1.0, 90.0, 0.0)
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
    """Return IERS HARDISP Doodson fundamental arguments in degrees.

    TT is approximated by UTC when evaluating the slowly varying Delaunay
    arguments. The sub-minute offset has a negligible effect here.
    """
    jd = _julian_dates(datetimes)
    centuries = (jd - 2451545.0) / 36525.0
    lunar_anomaly = (
        134.96340251
        + centuries
        * (
            477198.8675605
            + centuries
            * (0.0088553333 + centuries * (0.0000143431 - centuries * 0.000000068))
        )
    )
    solar_anomaly = (
        357.5291091806
        + centuries
        * (
            35999.0502911389
            + centuries
            * (-0.0001536667 + centuries * (0.0000000378 - centuries * 0.0000000032))
        )
    )
    lunar_latitude = (
        93.27209062
        + centuries
        * (
            483202.0174577222
            + centuries
            * (-0.003542 + centuries * (-0.0000002881 + centuries * 0.0000000012))
        )
    )
    lunar_elongation = (
        297.8501954694
        + centuries
        * (
            445267.1114469445
            + centuries
            * (-0.0017696111 + centuries * (0.0000018314 - centuries * 0.0000000088))
        )
    )
    ascending_node = (
        125.04455501
        + centuries
        * (
            -1934.1362619722
            + centuries
            * (0.0020756111 + centuries * (0.0000021394 - centuries * 0.0000000165))
        )
    )
    utc_day_fraction = (jd + 0.5) % 1.0

    doodson_1 = 360.0 * utc_day_fraction - lunar_elongation
    doodson_2 = lunar_latitude + ascending_node
    doodson_3 = doodson_2 - lunar_elongation
    doodson_4 = doodson_2 - lunar_anomaly
    doodson_5 = -ascending_node
    doodson_6 = doodson_3 - solar_anomaly
    return np.column_stack(
        (doodson_1, doodson_2, doodson_3, doodson_4, doodson_5, doodson_6)
    ) % 360.0


def radial_displacement(station: BlqStation, datetimes: Iterable[datetime]) -> np.ndarray:
    """Predict radial loading displacement from the 11 principal BLQ tides."""
    arguments = astronomical_arguments(datetimes)
    constituent_phase = arguments @ DOODSON.T + DOODSON_WARBURG_DEG
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
