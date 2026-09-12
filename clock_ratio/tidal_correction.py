#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "typer"]
# ///
# How to run (existing environment; no installs needed):
#   python clock_ratio/tidal_correction.py [--output-dir /independent/destination]
"""Write only additive raw/theory/empirical tidal-correction comparison tables."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Annotated, Final, TypedDict

import numpy as np
import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock import shared
from clock_ratio.tidal_analysis import (
    SCENARIOS, AnalysisError, SegmentResult, TideGrid, analyze_segment, select_segments,
)
from clock_ratio.tidal_stability import continuous_runs, duration_summary, oadev, tau_grid

DEFAULT_OUTPUT: Final = Path(__file__).resolve().parent / "tidal_correction"
FILENAMES: Final = ("ratio_scenarios.csv", "stability.csv", "summary.json")
RATIO_FIELDS: Final = (
    "scenario", "coefficient", "group", "n_valid", "t_start_beijing", "t_end_beijing",
    "t_start_utc", "t_end_utc", "rem_start", "rem_end", "duration_s", "elapsed_span_s",
    "n_continuous_runs", "longest_run_s", "global_median_beat_hz", "raw_mean_beat_hz",
    "mean_dm_raw_hz", "mean_tide_beat_hz", "mean_dff", "mean_dff_1e18", "shift_a",
    "mean_dm_corrected_hz", "R", "delta_R", "delta_fractional_1e18",
    "fractional_std", "beat_std_hz",
)
STABILITY_FIELDS: Final = (
    "scenario", "coefficient", "group", "tau_s", "n_pairs", "sigma_y", "sigma_factor_vs_raw",
)
CsvValue = str | int | float | None
app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


class ScenarioDocument(TypedDict):
    coefficient: str
    R_duration: str
    total_samples: int
    nsegments: int
    duration_s: int
    delta_R: str
    delta_fractional_1e18: str


class Metadata(TypedDict):
    decimal_precision: int
    sources: dict[str, str]
    conventions: dict[str, str]
    formulas: dict[str, str]
    processing: dict[str, str]
    limitations: list[str]


class SummaryDocument(TypedDict):
    scenarios: dict[str, ScenarioDocument]
    metadata: Metadata


def validate_output_dir(output_dir: Path) -> Path:
    """Allow the new analysis tree or an external directory, never legacy roots."""
    target = output_dir.resolve()
    if target.is_relative_to(shared.REPO_ROOT) and not target.is_relative_to(DEFAULT_OUTPUT):
        raise AnalysisError(f"protected repository source/legacy output directory: {target}")
    if target.exists() and not target.is_dir():
        raise AnalysisError(f"output directory is not a directory: {target}")
    for filename in FILENAMES:
        path = target / filename
        if path.is_symlink():
            raise AnalysisError(f"output filename is a symlink: {path}")
        if path.exists() and (not path.is_file() or path.stat().st_nlink > 1):
            raise AnalysisError(f"output filename is not an independent regular file: {path}")
    return target


def build_summary(results: tuple[SegmentResult, ...]) -> SummaryDocument:
    """Serialize Decimal centers explicitly; no float conversion of a ratio."""
    scenarios: dict[str, ScenarioDocument] = {}
    for scenario in SCENARIOS:
        aggregate = duration_summary(tuple(r for r in results if r.scenario == scenario))
        scenarios[scenario.key] = {
            "coefficient": str(scenario.coefficient), "R_duration": str(aggregate.ratio),
            "total_samples": aggregate.total_samples, "nsegments": aggregate.nsegments,
            "duration_s": aggregate.total_samples, "delta_R": str(aggregate.delta_r),
            "delta_fractional_1e18": str(aggregate.delta_fractional_1e18),
        }
    return {"scenarios": scenarios, "metadata": {
        "decimal_precision": 80,
        "sources": {"beat": str(shared.DATA_DIR), "tide": str(shared.RESULTS_CSV),
                    "tide_column": shared.TIDAL_COLUMN, "parameters": str(shared.PARAMS_JSON)},
        "conventions": {
            "delta_w": "W(Wuhan)-W(Shanghai), m^2/s^2",
            "coefficient": "A is the beat RESPONSE coefficient in b_raw=noise+A*h; fixed, not fitted here",
            "time": "Raw Beijing timestamps minus UTC_OFFSET (8 hours) yield UTC",
            "bounds": "First and last actual retained sample timestamps, after BOTH endpoint trims",
            "dff": "mean_dff=mean(h)/F_1550 is tidal deltaW/c^2, NOT exact ratio normalization",
        },
        "formulas": {
            "template": "h=F_1550*deltaW/C^2",
            "correction": "b_corr=b_raw-A*h (negative A adds the undemeaned template)",
            "mean_ratio": "mean_raw_dec=to_dec(float(b_kept.mean())); mean_dm_corr=mean_raw_dec-m_dec-A*to_dec(float(h.mean())); R=full_ratio(mean_dm_corr,SHIFT_A[k],m_dec)",
            "normalization": "G=1+DELTA_G; S0=G/R0; den_k=((1+SHIFT_A[k])/2)/N1397*(N1550+7/25+1/25); K=(COEF1156/N1156)/(FREF*DIV20*den_k)",
            "fractional": "R0=RAW segment ratio for every scenario; e=(b-raw_float_mean)-float(A)*h; q=float(K/S0)*e; y=-q/(1+q)",
            "oadev": "sigma_y=sqrt(sum_runs sum_i (mean(y[i+m:i+2m])-mean(y[i:i+m]))^2/(2*n_pairs)); i=0..N_run-2m",
            "duration": "R_duration=sum(n_valid_i*R_i)/sum(n_valid_i), same weights for all scenarios",
            "changes": "delta_R=R-R_raw; delta_fractional_1e18=(R/R_raw-1)*1e18",
        },
        "processing": {
            "selection": "Unchanged shared loaders, inclusive exclusions, global plausible median; group [start,end), 30MHz<b<40MHz, abs(b-group_median)<10Hz; longest_valid_span then raw endpoint_screen; never re-screen corrections",
            "interpolation": "Finite sorted unique UTC 30s grid; linear interpolation; no clamping, extrapolation or bridging missing >30s intervals",
            "stability": "Break at every non-1s timestamp step, including duplicates; pool squared differences/counts within each segment only",
            "taus": "Per segment: dyadic seconds plus 600,1200,3600,7200, capped at one quarter of its longest continuous raw run; identical grid across scenarios",
            "centering": "Numerical centering only before prefix sums; no detrending or tide demeaning",
            "std": "Sample fractional and beat standard deviations, ddof=1; CSV empty if n<2",
            "n_pairs": "Overlapping pair count, not independent degrees of freedom",
            "zero_sigma": "Corrected/raw OADEV factor is empty when raw sigma is zero or unavailable; unavailable OADEV is empty, never NaN",
            "duration": "duration_s=n_valid*1s (weight); elapsed_span_s=last-first+1s may include gaps",
        },
        "limitations": [
            "Conditional comparison for fixed exact Decimal A=-1 and A=-0.54, not coefficient estimates.",
            "No coefficient, tide-model or systematic uncertainty is propagated.",
            "Raw baseline intentionally inherits the legacy float64 raw mean (converted via repr), then Decimal80 arithmetic; raw quantization is not recovered.",
            "Segment ratio is inversion after averaging corrected linear beat, not the mean of instantaneous ratios.",
            "OADEV and sample std are not SEM; no WLS uncertainty or significance claim is manufactured.",
        ],
    }}


def ratio_row(result: SegmentResult) -> tuple[CsvValue, ...]:
    """Export actual kept bounds, explicit units and full Decimal strings."""
    segment = result.segment
    times = segment.times
    runs = continuous_runs(times)
    longest = max(stop - start for start, stop in runs)
    return (
        result.scenario.key, str(result.scenario.coefficient), segment.group, len(segment.beat),
        str(times[0]), str(times[-1]), str(times[0] - shared.UTC_OFFSET),
        str(times[-1] - shared.UTC_OFFSET), segment.rem_start, segment.rem_end,
        len(segment.beat), float((times[-1] - times[0]) / np.timedelta64(1, "s")) + 1,
        len(runs), longest, str(segment.m_dec), str(shared.to_dec(segment.raw_mean)),
        str(result.mean_dm_raw), result.mean_tide_beat_hz,
        result.mean_tide_beat_hz / shared.F_1550, result.mean_tide_beat_hz / shared.F_1550 * 1e18,
        str(segment.shift_a), str(result.mean_dm_corrected), str(result.ratio),
        str(result.delta_r), str(result.delta_fractional_1e18), result.fractional_std,
        result.beat_std_hz,
    )


def write_outputs(results: tuple[SegmentResult, ...], output_dir: Path) -> None:
    """Compute compact outputs first, then write only the three named artifacts."""
    target = validate_output_dir(output_dir)
    summary_text = json.dumps(build_summary(results), indent=2, ensure_ascii=False, allow_nan=False)
    curves = [(r, oadev(r.segment.times, r.fluctuations,
                       tau_grid(max(stop - start for start, stop in continuous_runs(r.segment.times)))))
              for r in results]
    raw_sigmas = {(r.segment.group, p.tau_s): p.sigma_y
                  for r, points in curves if r.scenario == SCENARIOS[0] for p in points}
    stability_rows: list[tuple[CsvValue, ...]] = []
    for result, points in curves:
        for point in points:
            raw = raw_sigmas[(result.segment.group, point.tau_s)]
            factor = point.sigma_y / raw if raw is not None and raw > 0 and point.sigma_y is not None else None
            stability_rows.append((result.scenario.key, str(result.scenario.coefficient),
                                   result.segment.group, point.tau_s, point.n_pairs, point.sigma_y, factor))
    target.mkdir(parents=True, exist_ok=True)
    with (target / FILENAMES[0]).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(RATIO_FIELDS)
        writer.writerows(ratio_row(r) for r in results)
    with (target / FILENAMES[1]).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(STABILITY_FIELDS)
        writer.writerows(stability_rows)
    (target / FILENAMES[2]).write_text(summary_text + "\n", encoding="utf-8")


@app.command()
def main(output_dir: Annotated[Path, typer.Option(help="Independent output directory; legacy/source roots are protected.")] = DEFAULT_OUTPUT) -> None:
    """Compare raw clocks with fixed A=-1 and A=-0.54 tidal corrections."""
    try:
        target = validate_output_dir(output_dir)
        try:
            times, beat = shared.load_beat()
        except (OSError, ValueError) as error:
            raise AnalysisError(f"raw beat data could not be loaded from {shared.DATA_DIR}: {error}") from error
        segments = select_segments(times, beat)
        try:
            tide = TideGrid(*shared.load_tide())
        except (OSError, ValueError, KeyError) as error:
            raise AnalysisError(f"tide data could not be loaded from {shared.RESULTS_CSV}: {error}") from error
        results: list[SegmentResult] = []
        for segment in segments:
            template = tide.beat_at(segment.times)
            results.extend(analyze_segment(segment, template, scenario) for scenario in SCENARIOS)
        write_outputs(tuple(results), target)
    except (AnalysisError, OSError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Wrote {len(results)} segment/scenario rows and stability/summary to {target}")


if __name__ == "__main__":
    app()
