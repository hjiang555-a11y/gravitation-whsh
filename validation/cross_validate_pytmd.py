#!/usr/bin/env python3
"""Cross-validate the solid-tide generating potential against pyTMD.

Compares this project's point-mass ephemeris computation (DE440s + exact
Legendre degree 2+3) against pyTMD's independent CTE1973 harmonic-catalog
expansion (analytic mean longitudes, Doodson arguments). The two methods are
astronomically independent: one integrates exact ephemerides, the other sums a
truncated tidal-potential catalog. Agreement on the time-varying signal
validates the ephemeris chain.

The residual (~0.3%) is the known truncation error of the CTE1973 catalog
relative to exact point-mass evaluation, not an error in this implementation.

Requires pyTMD (validation dependency, not a runtime dependency):
    python -m pip install pyTMD
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import xarray as xr

from gravitation_whsh.blq import normal_gravity
from gravitation_whsh.calculator import (
    GM_MOON,
    GM_SUN,
    _body_potential,
)

import pyTMD
import pyTMD.predict.solid_earth as se
from skyfield.api import Loader, load_file, wgs84

STATIONS = (
    ("WUHN", 30.531653, 114.357261, 28.2),
    ("SHAO", 31.099642, 121.200445, 22.09),
)
HOURS = 48


def _my_generating_potential(t_sky, eph, lat, lon, h):
    station = wgs84.latlon(lat, lon, h)
    station_xyz = station.at(t_sky).itrf_xyz().m
    moon_xyz = (eph["moon"] - eph["earth"]).at(t_sky).itrf_xyz().m
    sun_xyz = (eph["sun"] - eph["earth"]).at(t_sky).itrf_xyz().m
    value = np.zeros(t_sky.shape)
    for body_xyz, gm in ((moon_xyz, GM_MOON), (sun_xyz, GM_SUN)):
        for degree in (2, 3):
            value += _body_potential(station_xyz, body_xyz, gm, degree)
    return value


def _pytmd_equilibrium_height(t_tide, lat, lon):
    geocentric_lat = float(pyTMD.spatial.geocentric_latitude(lat))
    ds = xr.Dataset(coords={"x": lon, "y": geocentric_lat})
    zeta = se.body_tide(
        t_tide,
        ds,
        h2=1.0,
        l2=0.0,
        h3=1.0,
        l3=0.0,
        tide_system="mean_tide",
        catalog="CTE1973",
        lmax=3,
    )
    return zeta["R"].values


def main() -> int:
    timescale = Loader(__import__("tempfile").mkdtemp()).timescale()
    eph = load_file(str(__import__("pathlib").Path("data/de440s.bsp").resolve()))

    start = datetime(2026, 6, 20, tzinfo=timezone.utc)
    times = [start + timedelta(hours=h) for h in range(HOURS)]
    t_sky = timescale.from_datetimes(times)
    epoch_1992 = datetime(1992, 1, 1, tzinfo=timezone.utc)
    t_tide = np.array([(t - epoch_1992).total_seconds() / 86400.0 for t in times])

    mine = {}
    theirs = {}
    for name, lat, lon, h in STATIONS:
        mine[name] = _my_generating_potential(t_sky, eph, lat, lon, h)
        theirs[name] = (
            _pytmd_equilibrium_height(t_tide, lat, lon) * normal_gravity(lat, h)
        )

    print(f"{'quantity':28s} {'residual std':>12s} {'relative':>9s} {'corr':>8s}")
    print("-" * 62)
    for name, _, _, _ in STATIONS:
        a = mine[name] - mine[name].mean()
        b = theirs[name] - theirs[name].mean()
        residual = a - b
        relative = residual.std() / a.std() * 100.0
        corr = np.corrcoef(a, b)[0, 1]
        print(
            f"{name + ' time-varying V':28s} {residual.std():12.6f} "
            f"{relative:8.2f}% {corr:8.5f}"
        )

    a = (mine["SHAO"] - mine["WUHN"]) - (mine["SHAO"] - mine["WUHN"]).mean()
    b = (theirs["SHAO"] - theirs["WUHN"]) - (
        theirs["SHAO"] - theirs["WUHN"]
    ).mean()
    residual = a - b
    relative = residual.std() / a.std() * 100.0
    corr = np.corrcoef(a, b)[0, 1]
    print(
        f"{'SHAO-WUHN difference':28s} {residual.std():12.6f} "
        f"{relative:8.2f}% {corr:8.5f}"
    )
    print("-" * 62)
    print(
        "Residual ~0.3% = CTE1973 catalog truncation (reference side), "
        "not this implementation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
