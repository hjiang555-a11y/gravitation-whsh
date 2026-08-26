"""Command-line interface."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from skyfield.api import Loader

from .blq import read_blq
from .calculator import Site, calculate, load_ephemeris

WUHAN = Site("WUHN", 30.531653, 114.357261, 28.2)
SHANGHAI = Site("SHAO", 31.099370, 121.200250, 26.0)
DEFAULT_START = datetime(2026, 6, 20, tzinfo=timezone.utc)
DEFAULT_END = datetime(2026, 8, 26, 23, 59, tzinfo=timezone.utc)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate minute tidal geopotential difference: SHAO minus WUHN"
    )
    parser.add_argument("--blq", type=Path, help="BLQ file containing WUHN and SHAO")
    parser.add_argument(
        "--allow-no-ocean",
        action="store_true",
        help="produce an explicitly incomplete solid-tide-only result",
    )
    parser.add_argument("--ephemeris", type=Path, help="local JPL SPK file (default: DE421)")
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path.home() / ".cache" / "gravitation-whsh",
        help="download cache directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("wuhan_shanghai_20260620_20260826.csv"),
    )
    return parser


def _write_csv(path: Path, result) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "timestamp_utc",
                "tide_generating_delta_m2_s2",
                "solid_induced_delta_m2_s2",
                "solid_effective_delta_m2_s2",
                "ocean_loading_delta_m2_s2",
                "total_tidal_delta_m2_s2",
                "energy_change_per_kg_j",
            )
        )
        for index, timestamp in enumerate(result.timestamps):
            ocean = (
                ""
                if result.ocean_loading_delta is None
                else f"{result.ocean_loading_delta[index]:.9f}"
            )
            writer.writerow(
                (
                    timestamp.isoformat().replace("+00:00", "Z"),
                    f"{result.generating_delta[index]:.9f}",
                    f"{result.induced_delta[index]:.9f}",
                    f"{result.solid_effective_delta[index]:.9f}",
                    ocean,
                    f"{result.total_delta[index]:.9f}",
                    f"{result.total_delta[index]:.9f}",
                )
            )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.blq is None and not args.allow_no_ocean:
        _parser().error("--blq is required unless --allow-no-ocean is explicitly set")

    wuhan_blq = shanghai_blq = None
    if args.blq is not None:
        stations = read_blq(args.blq)

        def find_station(code):
            return next((station for key, station in stations.items() if key.startswith(code)), None)

        wuhan_blq = find_station(WUHAN.code)
        shanghai_blq = find_station(SHANGHAI.code)
        missing = [
            site.code
            for site, station in ((WUHAN, wuhan_blq), (SHANGHAI, shanghai_blq))
            if station is None
        ]
        if missing:
            raise SystemExit(f"BLQ file is missing station(s): {', '.join(missing)}")

    ephemeris = load_ephemeris(args.ephemeris, args.cache)
    timescale = Loader(str(args.cache)).timescale()
    result = calculate(
        DEFAULT_START,
        DEFAULT_END,
        WUHAN,
        SHANGHAI,
        ephemeris,
        timescale,
        wuhan_blq,
        shanghai_blq,
    )
    _write_csv(args.output, result)
    print(f"Wrote {len(result.timestamps):,} epochs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
