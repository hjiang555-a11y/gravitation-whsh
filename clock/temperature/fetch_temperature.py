#!/usr/bin/env python3
"""Fetch hourly surface temperature for the clock-comparison link stations.

The 1550 nm transfer link runs Wuhan -> Hefei -> Shanghai. Surface temperature
drives fiber thermal expansion / refractive-index change and thus link delay.
This script pulls hourly 2-m air temperature for the three stations from
Meteostat (https://meteostat.net), saving Beijing-time (UTC+8) CSV files under
clock/temperature/.

Stations (Meteostat id):
    Shanghai   58362  31.4 N, 121.467 E
    Wuhan      57494  30.6167 N, 114.1333 E
    Hefei      58321  31.8667 N, 117.2333 E

Usage:
    python clock/temperature/fetch_temperature.py \
        --start 2026-06-20 --end 2026-08-27
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from meteostat import Parameter, hourly

OUT_DIR = Path(__file__).resolve().parent

STATIONS = [
    ("58362", "shanghai"),
    ("57494", "wuhan"),
    ("58321", "hefei"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-06-20")
    parser.add_argument("--end", default="2026-08-27")
    args = parser.parse_args()

    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end)

    frames = {}
    for station_id, name in STATIONS:
        data = hourly(
            station_id, start, end, timezone="Asia/Shanghai",
            parameters=[Parameter.TEMP],
        )
        df = data.fetch().rename(columns={"temp": f"temp_{name}"})
        frames[name] = df
        path = OUT_DIR / f"temperature_{name}_hourly.csv"
        df.to_csv(path, date_format="%Y-%m-%dT%H:%M:%S%z")
        print(f"{name}: {len(df)} rows -> {path}")

    merged = frames["shanghai"].join(
        [frames["wuhan"], frames["hefei"]], how="outer"
    )
    merged_path = OUT_DIR / "temperature_merged_hourly.csv"
    merged.to_csv(merged_path, date_format="%Y-%m-%dT%H:%M:%S%z")
    print(f"merged: {len(merged)} rows -> {merged_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
