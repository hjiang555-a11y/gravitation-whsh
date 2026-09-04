"""Solid-Earth and ocean-loading tidal geopotential calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

import numpy as np
from skyfield.api import load_file, wgs84

from .blq import BlqStation, astronomical_arguments, normal_gravity, radial_displacement
from .frequency_dependence import frequency_correction
from .harpos import HarposStation, radial_displacement as harpos_radial_displacement

GM_MOON = 4.902800118e12
GM_SUN = 1.327124400419394e20

# IERS Conventions (2010), Table 6.3: the degree-2 potential Love number k2 is
# order-dependent (m=0 zonal, m=1 diurnal, m=2 semidiurnal). Values are the
# anelastic real parts.
K2_ORDER = {0: 0.30190, 1: 0.29830, 2: 0.30102}
K3 = 0.093
H2 = 0.6078
H3 = 0.292

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Site:
    code: str
    latitude_deg: float
    longitude_deg: float
    height_m: float


@dataclass(frozen=True)
class Calculation:
    timestamps: Sequence[datetime]
    generating_delta: np.ndarray
    induced_delta: np.ndarray
    solid_effective_delta: np.ndarray
    ocean_loading_delta: np.ndarray | None

    @property
    def total_delta(self) -> np.ndarray:
        if self.ocean_loading_delta is None:
            return self.solid_effective_delta.copy()
        return self.solid_effective_delta + self.ocean_loading_delta


def minute_epochs(start: datetime, end: datetime) -> list[datetime]:
    """Build an inclusive UTC minute grid."""
    start = _as_utc(start)
    end = _as_utc(end)
    if start.second or start.microsecond or end.second or end.microsecond:
        raise ValueError("start and end must be aligned to whole minutes")
    if end < start:
        raise ValueError("end must not precede start")
    count = int((end - start).total_seconds() // 60) + 1
    return [start + timedelta(minutes=index) for index in range(count)]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _legendre(degree: int, cosine: np.ndarray) -> np.ndarray:
    if degree == 2:
        return 0.5 * (3.0 * cosine**2 - 1.0)
    if degree == 3:
        return 0.5 * (5.0 * cosine**3 - 3.0 * cosine)
    raise ValueError(f"Unsupported degree: {degree}")


def _body_potential(
    station_position_m: np.ndarray,
    body_position_m: np.ndarray,
    gm: float,
    degree: int,
) -> np.ndarray:
    station_radius = np.linalg.norm(station_position_m, axis=0)
    body_radius = np.linalg.norm(body_position_m, axis=0)
    cosine = np.sum(station_position_m * body_position_m, axis=0) / (
        station_radius * body_radius
    )
    return (
        gm
        / body_radius
        * (station_radius / body_radius) ** degree
        * _legendre(degree, cosine)
    )


def _degree2_order_potential(
    station_xyz: np.ndarray,
    body_xyz: np.ndarray,
    gm: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Degree-2 tidal potential split into zonal/diurnal/sectorial orders.

    Evaluated in the terrestrial frame via the spherical-harmonic addition
    theorem so each order m receives its own Love number k2m.
    """
    station_radius = np.linalg.norm(station_xyz, axis=0)
    body_radius = np.linalg.norm(body_xyz, axis=0)
    sin_station = station_xyz[2] / station_radius
    sin_body = body_xyz[2] / body_radius
    dlon = np.arctan2(station_xyz[1], station_xyz[0]) - np.arctan2(
        body_xyz[1], body_xyz[0]
    )
    factor = gm / body_radius * (station_radius / body_radius) ** 2

    p2_station = 0.5 * (3.0 * sin_station**2 - 1.0)
    p2_body = 0.5 * (3.0 * sin_body**2 - 1.0)
    p21_station = 3.0 * sin_station * np.sqrt(1.0 - sin_station**2)
    p21_body = 3.0 * sin_body * np.sqrt(1.0 - sin_body**2)
    p22_station = 3.0 * (1.0 - sin_station**2)
    p22_body = 3.0 * (1.0 - sin_body**2)

    m0 = factor * p2_station * p2_body
    m1 = factor * 2.0 * (1.0 / 6.0) * p21_station * p21_body * np.cos(dlon)
    m2 = factor * 2.0 * (1.0 / 24.0) * p22_station * p22_body * np.cos(2.0 * dlon)
    return m0, m1, m2


def _station_components(site: Site, times, earth, moon, sun) -> tuple[np.ndarray, ...]:
    station = wgs84.latlon(
        latitude_degrees=site.latitude_deg,
        longitude_degrees=site.longitude_deg,
        elevation_m=site.height_m,
    )
    station_xyz = station.at(times).itrf_xyz().m
    moon_xyz = (moon - earth).at(times).itrf_xyz().m
    sun_xyz = (sun - earth).at(times).itrf_xyz().m

    generating = np.zeros(times.shape)
    induced = np.zeros(times.shape)
    effective = np.zeros(times.shape)

    for body_xyz, gm in ((moon_xyz, GM_MOON), (sun_xyz, GM_SUN)):
        m0, m1, m2 = _degree2_order_potential(station_xyz, body_xyz, gm)
        generating += m0 + m1 + m2
        induced += K2_ORDER[0] * m0 + K2_ORDER[1] * m1 + K2_ORDER[2] * m2
        effective += (
            (1.0 + K2_ORDER[0] - H2) * m0
            + (1.0 + K2_ORDER[1] - H2) * m1
            + (1.0 + K2_ORDER[2] - H2) * m2
        )

    for body_xyz, gm in ((moon_xyz, GM_MOON), (sun_xyz, GM_SUN)):
        external = _body_potential(station_xyz, body_xyz, gm, 3)
        generating += external
        induced += K3 * external
        effective += (1.0 + K3 - H3) * external

    datetimes = times.utc_datetime()
    arguments = astronomical_arguments(datetimes)
    longitude = np.radians(site.longitude_deg)
    m0_total, m1_total, m2_total = _degree2_orders(station_xyz, moon_xyz, sun_xyz)
    for order, potential, k2_nominal in (
        (0, m0_total, K2_ORDER[0]),
        (1, m1_total, K2_ORDER[1]),
        (2, m2_total, K2_ORDER[2]),
    ):
        d_induced, d_effective = frequency_correction(
            potential, arguments, longitude, order, k2_nominal, H2
        )
        induced += d_induced
        effective += d_effective

    return generating, induced, effective


def _degree2_orders(
    station_xyz: np.ndarray, moon_xyz: np.ndarray, sun_xyz: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sum the degree-2 order potential over the Moon and Sun."""
    m0 = np.zeros(station_xyz.shape[1])
    m1 = np.zeros(station_xyz.shape[1])
    m2 = np.zeros(station_xyz.shape[1])
    for body_xyz, gm in ((moon_xyz, GM_MOON), (sun_xyz, GM_SUN)):
        a0, a1, a2 = _degree2_order_potential(station_xyz, body_xyz, gm)
        m0 += a0
        m1 += a1
        m2 += a2
    return m0, m1, m2


def load_ephemeris(path: str | Path | None, cache_directory: str | Path):
    """Load a local SPK file or the bundled JPL DE440s ephemeris."""
    if path is not None:
        return load_file(str(path))
    del cache_directory
    return load_file(str(DATA_DIR / "de440s.bsp"))


def _ocean_delta(
    wuhan: Site, shanghai: Site, wuh_up: np.ndarray, sha_up: np.ndarray
) -> np.ndarray:
    """Convert radial loading displacements to the loading geopotential difference.

    A positive radial loading displacement ``up`` raises the surface, so the
    geopotential change is ``delta_W = -g * up``. The returned difference is
    ``sha_potential - wuh_potential = -g_sha*sha_up + g_wuh*wuh_up``, i.e. the
    Shanghai-minus-Wuhan (SHAO − WUHN) convention, consistent with the solid-tide
    output and with the numerical direction of the professionally supplied
    "海潮之差" column (whose xlsx label "CAS − SHA" is a sign-convention artifact;
    the values are empirically Shanghai-minus-Wuhan — Shanghai's coastal loading
    far exceeds inland Wuhan's).
    """
    wuh_potential = -normal_gravity(wuhan.latitude_deg, wuhan.height_m) * wuh_up
    sha_potential = -normal_gravity(shanghai.latitude_deg, shanghai.height_m) * sha_up
    return sha_potential - wuh_potential


def load_professional_ocean(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load an authoritative ocean-loading ΔW series (30-second UTC grid).

    The file is a CSV with ``timestamp_utc`` and ``ocean_loading_delta_m2_s2``
    columns, derived from the professionally supplied Wuhan–Shanghai tidal
    results (海潮之差 column). Returns ``(epoch_seconds, delta_W)`` where
    ``epoch_seconds`` is seconds since the Unix epoch (UTC, float).
    """
    import csv as _csv

    with Path(path).open(encoding="utf-8") as handle:
        rows = list(_csv.DictReader(handle))
    epochs = np.array(
        [
            datetime.fromisoformat(r["timestamp_utc"].replace("Z", "+00:00")).timestamp()
            for r in rows
        ]
    )
    delta_w = np.array([float(r["ocean_loading_delta_m2_s2"]) for r in rows])
    return epochs, delta_w


def calculate(
    start: datetime,
    end: datetime,
    wuhan: Site,
    shanghai: Site,
    ephemeris,
    timescale,
    wuhan_blq: BlqStation | None = None,
    shanghai_blq: BlqStation | None = None,
    wuhan_harpos: HarposStation | None = None,
    shanghai_harpos: HarposStation | None = None,
    professional_ocean_csv: str | Path | None = None,
) -> Calculation:
    """Calculate Shanghai-minus-Wuhan tidal geopotential components.

    The ocean-loading term may be supplied from three sources. When more than
    one is given the priority is: ``professional_ocean_csv`` (authoritative
    interpolated series) > ``*_harpos`` > ``*_blq``.
    """
    timestamps = minute_epochs(start, end)
    times = timescale.from_datetimes(timestamps)
    earth, moon, sun = ephemeris["earth"], ephemeris["moon"], ephemeris["sun"]

    wuh = _station_components(wuhan, times, earth, moon, sun)
    sha = _station_components(shanghai, times, earth, moon, sun)

    ocean_delta = None
    if professional_ocean_csv is not None:
        prof_epochs, prof_dw = load_professional_ocean(professional_ocean_csv)
        minute_epoch_values = np.array(
            [ts.replace(tzinfo=timezone.utc).timestamp() for ts in timestamps]
        )
        ocean_delta = np.interp(minute_epoch_values, prof_epochs, prof_dw)
    elif (wuhan_blq is None) != (shanghai_blq is None):
        raise ValueError("BLQ coefficients must be supplied for both stations")
    elif wuhan_blq is not None and shanghai_blq is not None:
        wuh_up = radial_displacement(wuhan_blq, timestamps)
        sha_up = radial_displacement(shanghai_blq, timestamps)
        ocean_delta = _ocean_delta(wuhan, shanghai, wuh_up, sha_up)

    if ocean_delta is None and (wuhan_harpos is not None or shanghai_harpos is not None):
        if wuhan_harpos is None or shanghai_harpos is None:
            raise ValueError("HARPOS coefficients must be supplied for both stations")
        wuh_up = harpos_radial_displacement(wuhan_harpos, timestamps, timescale)
        sha_up = harpos_radial_displacement(shanghai_harpos, timestamps, timescale)
        ocean_delta = _ocean_delta(wuhan, shanghai, wuh_up, sha_up)

    return Calculation(
        timestamps=timestamps,
        generating_delta=sha[0] - wuh[0],
        induced_delta=sha[1] - wuh[1],
        solid_effective_delta=sha[2] - wuh[2],
        ocean_loading_delta=ocean_delta,
    )
