"""Solid-Earth and ocean-loading tidal geopotential calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

import numpy as np
from skyfield.api import Loader, load_file, wgs84
from skyfield_data import get_skyfield_data_path

from .blq import BlqStation, normal_gravity, radial_displacement
from .harpos import HarposStation, radial_displacement as harpos_radial_displacement

GM_MOON = 4.902800118e12
GM_SUN = 1.327124400419394e20
LOVE_K = {2: 0.30190, 3: 0.093}
LOVE_H = {2: 0.6078, 3: 0.292}


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


def _station_components(site: Site, times, earth, moon, sun) -> tuple[np.ndarray, ...]:
    station = wgs84.latlon(
        latitude_degrees=site.latitude_deg,
        longitude_degrees=site.longitude_deg,
        elevation_m=site.height_m,
    )
    station_position = station.at(times).position.m
    moon_position = (moon - earth).at(times).position.m
    sun_position = (sun - earth).at(times).position.m

    generating = np.zeros(times.shape)
    induced = np.zeros(times.shape)
    effective = np.zeros(times.shape)
    for degree in (2, 3):
        external = _body_potential(station_position, moon_position, GM_MOON, degree)
        external += _body_potential(station_position, sun_position, GM_SUN, degree)
        generating += external
        induced += LOVE_K[degree] * external
        effective += (1.0 + LOVE_K[degree] - LOVE_H[degree]) * external
    return generating, induced, effective


def load_ephemeris(path: str | Path | None, cache_directory: str | Path):
    """Load a local SPK file or the packaged public JPL DE421 ephemeris."""
    if path is not None:
        return load_file(str(path))
    del cache_directory
    return Loader(get_skyfield_data_path())("de421.bsp")


def _ocean_delta(
    wuhan: Site, shanghai: Site, wuh_up: np.ndarray, sha_up: np.ndarray
) -> np.ndarray:
    """Convert radial loading displacements to the SHAO-minus-WUHN geopotential."""
    wuh_potential = -normal_gravity(wuhan.latitude_deg, wuhan.height_m) * wuh_up
    sha_potential = -normal_gravity(shanghai.latitude_deg, shanghai.height_m) * sha_up
    return sha_potential - wuh_potential


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
) -> Calculation:
    """Calculate Shanghai-minus-Wuhan tidal geopotential components."""
    timestamps = minute_epochs(start, end)
    times = timescale.from_datetimes(timestamps)
    earth, moon, sun = ephemeris["earth"], ephemeris["moon"], ephemeris["sun"]

    wuh = _station_components(wuhan, times, earth, moon, sun)
    sha = _station_components(shanghai, times, earth, moon, sun)

    ocean_delta = None
    if (wuhan_blq is None) != (shanghai_blq is None):
        raise ValueError("BLQ coefficients must be supplied for both stations")
    if wuhan_blq is not None and shanghai_blq is not None:
        wuh_up = radial_displacement(wuhan_blq, timestamps)
        sha_up = radial_displacement(shanghai_blq, timestamps)
        ocean_delta = _ocean_delta(wuhan, shanghai, wuh_up, sha_up)

    if wuhan_harpos is not None or shanghai_harpos is not None:
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
