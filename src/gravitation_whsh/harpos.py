"""HARPOS-format ocean-loading displacement parsing and prediction.

HARPOS (Harmonic Positions) files describe site displacements as a sum of
harmonic components. Each constituent contributes

    d_up = A_c * cos(arg) + A_s * sin(arg)

where ``arg = phase + freq*(t - t0) + 0.5*accel*(t - t0)**2``, with ``t``
expressed in TDT (terrestrial) seconds and ``t0`` the J2000.0 epoch
(2000-01-01 12:00 TDT). We therefore evaluate the argument on the TT
timescale returned by Skyfield rather than on UTC.

Sources of such files include the International Mass Loading Service
(https://massloading.net), which ships precomputed ocean-tide-loading
displacements for IGS stations in this format.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

J2000_TT = 2451545.0  # Julian date of the J2000.0 reference epoch (TT)


@dataclass(frozen=True)
class HarposStation:
    """Ocean-loading radial displacement as cos/sin harmonic amplitudes."""

    name: str
    phases_rad: np.ndarray
    freqs_rad_s: np.ndarray
    accels_rad_s2: np.ndarray
    up_cos: np.ndarray
    up_sin: np.ndarray

    def __post_init__(self) -> None:
        size = self.phases_rad.shape[0]
        for field in (self.freqs_rad_s, self.accels_rad_s2, self.up_cos, self.up_sin):
            if field.shape[0] != size:
                raise ValueError("HARPOS harmonic arrays must share a common length")


def _float(value: str) -> float:
    return float(value.replace("D", "E").replace("d", "e"))


def read_harpos(path: str | Path) -> dict[str, HarposStation]:
    """Read site displacement records from a HARPOS file.

    Only the radial (Up) component is retained; the tangential East/North
    components are irrelevant for the geopotential calculation.
    """
    harmonics: dict[str, tuple[float, float, float]] = {}
    rows: dict[str, list[tuple[float, float, float, float, float]]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        tokens = line.split()
        if not tokens:
            continue
        tag = tokens[0]
        if tag == "H":
            harmonics[tokens[1]] = (_float(tokens[2]), _float(tokens[3]), _float(tokens[4]))
        elif tag == "D":
            name, site = tokens[1], tokens[2]
            up_cos = _float(tokens[3])
            up_sin = _float(tokens[6])
            phase, freq, accel = harmonics[name]
            rows.setdefault(site, []).append((phase, freq, accel, up_cos, up_sin))

    stations: dict[str, HarposStation] = {}
    for site, site_rows in rows.items():
        stations[site] = HarposStation(
            name=site,
            phases_rad=np.asarray([r[0] for r in site_rows]),
            freqs_rad_s=np.asarray([r[1] for r in site_rows]),
            accels_rad_s2=np.asarray([r[2] for r in site_rows]),
            up_cos=np.asarray([r[3] for r in site_rows]),
            up_sin=np.asarray([r[4] for r in site_rows]),
        )
    if not stations:
        raise ValueError(f"No valid HARPOS station records found in {path}")
    return stations


def radial_displacement(station: HarposStation, datetimes, timescale) -> np.ndarray:
    """Predict radial (Up) loading displacement in metres at the given times."""
    times = timescale.from_datetimes(list(datetimes))
    dt = (times.tt - J2000_TT) * 86400.0  # seconds since J2000.0 (TT)
    argument = (
        station.phases_rad[np.newaxis, :]
        + station.freqs_rad_s[np.newaxis, :] * dt[:, np.newaxis]
        + 0.5 * station.accels_rad_s2[np.newaxis, :] * dt[:, np.newaxis] ** 2
    )
    contribution = (
        station.up_cos[np.newaxis, :] * np.cos(argument)
        + station.up_sin[np.newaxis, :] * np.sin(argument)
    )
    return np.sum(contribution, axis=1)
