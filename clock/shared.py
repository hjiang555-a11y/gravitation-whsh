"""Shared constants, segment definitions and data loaders for the clock project.

This is the SINGLE SOURCE OF TRUTH for things that were previously duplicated
across scripts:
  - the 17 jump-free segment windows (GROUPS) and manual exclusion ranges
  - the ratio-formula constants (N1156, N1397, N1550, N1550_WH, fref, div20,
    b_Yb, delta_g) and the Sr systematic-shift components (shift_a)
  - the beat-frequency data loader (from the 8th-column data files)
  - the tidal 30-s "综合差" loader and its conversion helpers

Import it from any script with, e.g.::

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from clock.shared import GROUPS, EXCLUDE_RANGES, load_beat, ...

See docs/NOTATION.md for the symbol glossary.
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path

import numpy as np

# Decimal arithmetic at 80 significant digits mirrors the MATLAB vpa(...,80):
# the clock ratio R ~ 1.2 and segment-to-segment differences are ~1-5e-18, which
# float64 (abs eps ~2.6e-16) would destroy.
getcontext().prec = 80

# --------------------------------------------------------------------------
# Paths (relative to the repo root)
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "clock" / "data" / "环外数据（第八列数据）"
RESULTS_CSV = REPO_ROOT / "results" / "professional_tidal_delta_30s.csv"
TIDAL_COLUMN = "total_tidal_delta_m2_s2_surface"
PARAMS_JSON = Path(__file__).resolve().parent / "params.json"


def _load_params() -> dict:
    """Load the intermediate parameter document (params.json)."""
    with open(PARAMS_JSON) as f:
        return json.load(f)


def _dec_list(values: list[str]) -> list[Decimal]:
    """Parse a list of string-encoded decimals into Decimal (preserve precision)."""
    return [Decimal(v) for v in values]


_P = _load_params()

# --------------------------------------------------------------------------
# Physical / processing constants (not in params.json — code-level facts)
# --------------------------------------------------------------------------
C = 299792458.0                    # speed of light (m/s)
JUMP_THRESHOLD = 10.0              # Hz, beat deviation from median to drop
UTC_OFFSET = np.timedelta64(8, "h")  # Beijing (UTC+8) -> UTC
COEF = 4.282082163269648e-15       # beat[Hz] -> fractional RATIO offset (Dr formula)
F_1550 = 193399200000000.0         # 1550nm transfer light, N1550_WH × f_rep (Hz)
# -> 1/COEF = 233.53 THz is NOT f_1550; COEF carries a f_Yb/f_Sr = Yb/Sr ~1.2075
#    factor, so the tidal beat template must normalize to F_1550, not 1/COEF.

# --------------------------------------------------------------------------
# Ratio-formula constants (from params.json "ratio_constants")
# --------------------------------------------------------------------------
_RC = _P["ratio_constants"]
N1156 = Decimal(_RC["N1156"])          # Yb 1156 nm comb count
N1397 = Decimal(_RC["N1397"])          # Sr 1397 nm comb count
N1550 = Decimal(_RC["N1550"])          # 1550 nm link count (Shanghai end)
N1550_WH = Decimal(_RC["N1550_WH"])    # 1550 nm link count (Wuhan end)
FREF = Decimal(_RC["FREF"])            # comb repetition base (Hz)
DIV20 = Decimal(_RC["DIV20"])          # divider; fref*div20 = 200 MHz = f_rep
B_YB = Decimal(_RC["b_yb_raw_530"]) - Decimal(_RC["b_yb_raw_700"])  # = -1.7e-18
DELTA_G = Decimal(_RC["DELTA_G"])      # static gravitational redshift correction
COEF1156 = (Decimal(1) + B_YB) / Decimal(2)
D_7_25 = Decimal(7) / Decimal(25)
D_1_25 = Decimal(1) / Decimal(25)

# --------------------------------------------------------------------------
# 17 jump-free segment windows + exclusion ranges (from params.json "segments")
# --------------------------------------------------------------------------
_SG = _P["segments"]
GROUPS = [tuple(g) for g in _SG["groups"]]
EXCLUDE_RANGES = [tuple(e) for e in _SG["exclude_ranges"]]

# --------------------------------------------------------------------------
# Sr systematic shift components (from params.json "shift_a")
# shift_a = a_rou + a_AC + a_SM + a_air + a_BBR  (14 segments; 15/16/17 reuse
# segment 12-14's constant shift). Segment 9's a_SM is -8.925e-17, kept verbatim
# from the source (its 0 in segments 10-14 is flagged "possibly a placeholder").
# --------------------------------------------------------------------------
_SH = _P["shift_a"]
A_ROU = _dec_list(_SH["a_rou"])
A_AC = _dec_list(_SH["a_AC"])
A_SM = _dec_list(_SH["a_SM"])
A_AIR = _dec_list(_SH["a_air"])
A_BBR = _dec_list(_SH["a_BBR"])
SHIFT_A_14 = [A_ROU[i] + A_AC[i] + A_SM[i] + A_AIR[i] + A_BBR[i]
              for i in range(14)]
SHIFT_A = SHIFT_A_14 + [SHIFT_A_14[11]] * 3   # 15/16/17 inherit seg 12-14


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
def first_stamp(path: Path) -> np.datetime64:
    """Parse the first data line's timestamp into datetime64[s] (Beijing time)."""
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            tok = line.split()
            dd, tt = int(tok[0]), float(tok[1])
            yy, mm, day = dd // 10000, (dd // 100) % 100, dd % 100
            hh = int(tt) // 10000
            mi = (int(tt) // 100) % 100
            ss = int(tt) % 100
            return np.datetime64(f"{2000+yy:04d}-{mm:02d}-{day:02d} "
                                 f"{hh:02d}:{mi:02d}:{ss:02d}")
    raise ValueError(f"no data line in {path}")


def load_beat() -> tuple[np.ndarray, np.ndarray]:
    """Load all 1550 nm beat files (8th-column data), sorted by uniform time.

    Returns (t, b): t is a uniform 1-s datetime64 axis (rebuilt from each file's
    first stamp + row index, ignoring the ±1 s label jitter), b is the beat (Hz).
    """
    files = (sorted(DATA_DIR.glob("Freq_B_2_2606*.txt"))
             + sorted(DATA_DIR.glob("Freq_B_2_2607*.txt"))
             + sorted(DATA_DIR.glob("Freq_B_2_2608*.txt")))
    t_all, b_all = [], []
    for f in files:
        b = np.loadtxt(f, usecols=(10,))
        t0 = first_stamp(f)
        t = t0 + np.arange(len(b), dtype="int64").astype("timedelta64[s]")
        t_all.append(t)
        b_all.append(b)
    t = np.concatenate(t_all)
    b = np.concatenate(b_all)
    order = np.argsort(t.astype("int64"))
    return t[order], b[order]


def load_tide() -> tuple[np.ndarray, np.ndarray]:
    """Load the professional 30-s tidal 综合差 (UTC) -> (timestamps, total ΔW)."""
    import csv
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    t = np.array([r["timestamp_utc"].replace("Z", "") for r in rows],
                 dtype="datetime64[s]")
    total = np.array([float(r[TIDAL_COLUMN]) for r in rows])
    return t, total


def longest_valid_span(valid: np.ndarray) -> tuple[int, int] | None:
    """Return (start, stop) inclusive indices of the longest run of True."""
    if not valid.any():
        return None
    padded = np.concatenate([[False], valid, [False]])
    diff = np.diff(padded.astype(int))
    starts = np.where(diff == 1)[0]
    stops = np.where(diff == -1)[0]
    lengths = stops - starts
    i = int(np.argmax(lengths))
    return int(starts[i]), int(stops[i] - 1)


def to_dec(x) -> Decimal:
    """Return x as Decimal: passthrough if already Decimal, else via repr.

    repr(float) preserves full float64 precision; Decimal must NOT be wrapped in
    float() or the E-20 precision carried by params.json is destroyed.
    """
    if isinstance(x, Decimal):
        return x
    return Decimal(repr(float(x)))
