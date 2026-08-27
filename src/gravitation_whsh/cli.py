"""Command-line interface."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import math
from pathlib import Path

from skyfield.api import Loader

from .blq import read_blq
from .calculator import Site, calculate, load_ephemeris
from .harpos import read_harpos

# Station coordinates from IGS20 SINEX (epoch 2015.0, ITRF2020) and IGS site logs.
# Source: https://files.igs.org/pub/station/general/igs.snx
#         https://files.igs.org/pub/station/log/shao00chn_20230306.log
WUHAN = Site("WUHN", 30.531653, 114.357261, 28.2)
SHANGHAI = Site("SHAO", 31.099642, 121.200445, 22.09)
DEFAULT_START = datetime(2026, 6, 20, tzinfo=timezone.utc)
DEFAULT_END = datetime(2026, 8, 26, 23, 59, tzinfo=timezone.utc)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate minute tidal geopotential difference: SHAO minus WUHN"
    )
    parser.add_argument("--blq", type=Path, help="BLQ file containing WUHN and SHAO")
    parser.add_argument(
        "--harpos",
        type=Path,
        help="HARPOS file containing WUHN and SHAO ocean-loading coefficients",
    )
    parser.add_argument(
        "--allow-no-ocean",
        action="store_true",
        help="produce an explicitly incomplete solid-tide-only result",
    )
    parser.add_argument("--ephemeris", type=Path, help="local JPL SPK file (default: bundled DE440s)")
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
    parser.add_argument(
        "--plot",
        type=Path,
        help="SVG plot path (default: the output CSV path with an .svg suffix)",
    )
    return parser


def _write_csv(path: Path, result) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "elapsed_minutes",
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
                    index,
                    timestamp.isoformat().replace("+00:00", "Z"),
                    f"{result.generating_delta[index]:.9f}",
                    f"{result.induced_delta[index]:.9f}",
                    f"{result.solid_effective_delta[index]:.9f}",
                    ocean,
                    f"{result.total_delta[index]:.9f}",
                    f"{result.total_delta[index]:.9f}",
                )
            )


def _write_svg(path: Path, result) -> None:
    width, height = 1200, 700
    left, right, top, bottom = 100, 50, 55, 85
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = result.total_delta
    minimum = float(values.min())
    maximum = float(values.max())
    padding = max((maximum - minimum) * 0.05, 1e-9)
    y_min, y_max = minimum - padding, maximum + padding

    def x_position(index: int) -> float:
        return left + plot_width * index / (len(values) - 1)

    def y_position(value: float) -> float:
        return top + plot_height * (y_max - value) / (y_max - y_min)

    bucket_size = max(1, math.ceil(len(values) / plot_width))
    points: list[tuple[int, float]] = []
    for start in range(0, len(values), bucket_size):
        stop = min(start + bucket_size, len(values))
        bucket = values[start:stop]
        low = start + int(bucket.argmin())
        high = start + int(bucket.argmax())
        for index in sorted((low, high)):
            if not points or points[-1][0] != index:
                points.append((index, float(values[index])))
    polyline = " ".join(f"{x_position(i):.2f},{y_position(v):.2f}" for i, v in points)

    x_ticks = []
    for tick in range(0, 6):
        index = round((len(values) - 1) * tick / 5)
        x = x_position(index)
        stamp = result.timestamps[index]
        x_ticks.append(
            f'<line x1="{x:.2f}" y1="{height-bottom}" x2="{x:.2f}" '
            f'y2="{height-bottom+6}" stroke="black"/>'
            f'<text x="{x:.2f}" y="{height-bottom+24}" text-anchor="middle" '
            f'font-size="12">{stamp.strftime("%Y-%m-%d")}</text>'
            f'<text x="{x:.2f}" y="{height-bottom+40}" text-anchor="middle" '
            f'font-size="12">{stamp.strftime("%H:%M")}</text>'
        )
    y_ticks = []
    for tick in range(0, 6):
        value = y_min + (y_max - y_min) * tick / 5
        y = y_position(value)
        y_ticks.append(
            f'<line x1="{left-6}" y1="{y:.2f}" x2="{width-right}" '
            f'y2="{y:.2f}" stroke="#dddddd"/>'
            f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end">{value:.4f}</text>'
        )

    ocean_note = "" if result.ocean_loading_delta is not None else " (solid tide only)"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/>
<text x="{width/2}" y="30" text-anchor="middle" font-size="20">Wuhan–Shanghai tidal geopotential difference{ocean_note}</text>
<g font-family="sans-serif" font-size="13">
{''.join(y_ticks)}
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="black"/>
<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="black"/>
{''.join(x_ticks)}
<polyline points="{polyline}" fill="none" stroke="#0969da" stroke-width="1.3"/>
<text x="{left+plot_width/2}" y="{height-20}" text-anchor="middle">Time (UTC)</text>
<text x="22" y="{top+plot_height/2}" text-anchor="middle" transform="rotate(-90 22 {top+plot_height/2})">SHAO − WUHN geopotential difference (m²/s²)</text>
</g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.blq is None and args.harpos is None and not args.allow_no_ocean:
        _parser().error(
            "--blq or --harpos is required unless --allow-no-ocean is explicitly set"
        )

    def find_station(stations, code):
        return next((station for key, station in stations.items() if key.startswith(code)), None)

    wuhan_blq = shanghai_blq = None
    if args.blq is not None:
        stations = read_blq(args.blq)
        wuhan_blq = find_station(stations, WUHAN.code)
        shanghai_blq = find_station(stations, SHANGHAI.code)
        missing = [
            site.code
            for site, station in ((WUHAN, wuhan_blq), (SHANGHAI, shanghai_blq))
            if station is None
        ]
        if missing:
            raise SystemExit(f"BLQ file is missing station(s): {', '.join(missing)}")

    wuhan_harpos = shanghai_harpos = None
    if args.harpos is not None:
        stations = read_harpos(args.harpos)
        wuhan_harpos = find_station(stations, WUHAN.code)
        shanghai_harpos = find_station(stations, SHANGHAI.code)
        missing = [
            site.code
            for site, station in ((WUHAN, wuhan_harpos), (SHANGHAI, shanghai_harpos))
            if station is None
        ]
        if missing:
            raise SystemExit(f"HARPOS file is missing station(s): {', '.join(missing)}")

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
        wuhan_harpos,
        shanghai_harpos,
    )
    _write_csv(args.output, result)
    plot_path = args.plot or args.output.with_suffix(".svg")
    _write_svg(plot_path, result)
    print(f"Wrote {len(result.timestamps):,} epochs to {args.output}")
    print(f"Wrote plot to {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
