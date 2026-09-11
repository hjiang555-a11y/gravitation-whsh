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

# --------------------------------------------------------------------------
# Physical / processing constants
# --------------------------------------------------------------------------
C = 299792458.0                    # speed of light (m/s)
JUMP_THRESHOLD = 10.0              # Hz, beat deviation from median to drop
UTC_OFFSET = np.timedelta64(8, "h")  # Beijing (UTC+8) -> UTC
COEF = 4.282082163269648e-15       # beat[Hz] -> fractional RATIO offset (Dr formula)
F_1550 = 193399200000000.0         # 1550nm transfer light, N1550_WH × f_rep (Hz)
# -> 1/COEF = 233.53 THz is NOT f_1550; COEF carries a f_Yb/f_Sr = Yb/Sr ~1.2075
#    factor, so the tidal beat template must normalize to F_1550, not 1/COEF.

# --------------------------------------------------------------------------
# Ratio-formula constants (MATLAB YbSr_NISTstyle_14bin, lines 143-151)
# --------------------------------------------------------------------------
N1156 = Decimal(1295739)          # Yb 1156 nm comb count
N1397 = Decimal(858456)           # Sr 1397 nm comb count
N1550 = Decimal(773598)           # 1550 nm link count (Shanghai end)
N1550_WH = Decimal(966996)        # 1550 nm link count (Wuhan end)
FREF = Decimal("1e7")             # comb repetition base (Hz)
DIV20 = Decimal(20)               # divider; fref*div20 = 200 MHz = f_rep
B_YB = Decimal("5.3e-18") - Decimal("7e-18")   # Yb fixed shift = -1.7e-18
DELTA_G = Decimal("-3.116e-15")   # static gravitational redshift correction
COEF1156 = (Decimal(1) + B_YB) / Decimal(2)
D_7_25 = Decimal(7) / Decimal(25)
D_1_25 = Decimal(1) / Decimal(25)

# --------------------------------------------------------------------------
# 17 jump-free segment windows (Beijing time, UTC+8)
# --------------------------------------------------------------------------
GROUPS = [
    ("2026-06-29 10:06:28", "2026-06-30 04:59:59"),
    ("2026-06-30 12:00:00", "2026-06-30 20:11:31"),
    ("2026-07-01 15:58:41", "2026-07-02 03:53:40"),
    ("2026-07-02 14:00:00", "2026-07-03 07:51:26"),
    ("2026-07-03 17:34:22", "2026-07-03 23:00:00"),
    ("2026-07-04 19:30:46", "2026-07-05 10:00:00"),
    ("2026-07-05 13:00:00", "2026-07-06 00:00:00"),
    ("2026-07-06 21:45:16", "2026-07-07 09:52:03"),
    ("2026-08-07 15:15:00", "2026-08-07 21:30:00"),
    ("2026-08-07 22:15:00", "2026-08-08 14:20:59"),
    ("2026-08-09 00:00:00", "2026-08-09 09:57:21"),
    ("2026-08-10 12:47:06", "2026-08-11 00:00:00"),
    ("2026-08-11 05:30:00", "2026-08-13 00:00:00"),
    ("2026-08-13 18:56:58", "2026-08-14 14:00:42"),
    ("2026-08-21 00:40:03", "2026-08-21 16:40:56"),
    ("2026-08-21 23:20:01", "2026-08-23 16:20:51"),
    ("2026-08-25 15:09:41", "2026-08-26 09:29:54"),
]

# Manual exclusion windows (Beijing time), copied from MATLAB exclude_ranges.
EXCLUDE_RANGES = [
    ("2026-06-30 05:00:00", "2026-06-30 12:00:00"),
    ("2026-06-30 20:30:00", "2026-07-01 14:00:00"),
    ("2026-07-02 08:00:00", "2026-07-02 14:00:00"),
    ("2026-07-03 12:00:00", "2026-07-03 16:20:00"),
    ("2026-07-03 23:00:00", "2026-07-04 01:20:00"),
    ("2026-07-05 10:00:00", "2026-07-05 13:00:00"),
    ("2026-07-06 00:00:00", "2026-07-06 20:00:00"),
    ("2026-08-07 21:30:01", "2026-08-07 22:14:59"),
    ("2026-08-08 18:00:01", "2026-08-08 23:59:59"),
    ("2026-08-10 01:00:01", "2026-08-10 11:59:59"),
    ("2026-08-11 00:00:01", "2026-08-11 05:29:59"),
    ("2026-08-13 00:00:01", "2026-08-13 03:29:59"),
]

# --------------------------------------------------------------------------
# Sr systematic shift components (MATLAB a_rou/a_AC/a_SM/a_air/a_BBR)
# shift_a = a_rou + a_AC + a_SM + a_air + a_BBR  (14 segments; 15/16/17 reuse
# segment 12-14's constant shift). Segment 9's a_SM is -8.925e-17, kept verbatim
# from the source (its 0 in segments 10-14 is flagged "possibly a placeholder").
# --------------------------------------------------------------------------
A_ROU = [
    -2.3405897235204027e-19, -1.4762696609004877e-19, -2.447205229168124e-19,
    -2.8193721064244536e-19, -2.722072607303744e-19, -2.6646987912614174e-19,
    -2.530366977034812e-19, -2.334981365086871e-19,
    -3.532e-19, -3.532e-19, -3.532e-19, -3.422e-19, -3.422e-19, -3.422e-19,
]
A_AC = [7.44377658537123e-18] * 8 + [8.929e-18] * 6
A_SM = [
    -1.7854788394394161e-16, -1.786187875083559e-16, -1.7856555448119226e-16,
    -1.7848198533888947e-16, -1.7852307151852717e-16, -1.784782742736454e-16,
    -1.7827511036845825e-16, -1.782675356790445e-16, -8.925e-17, 0.0, 0.0, 0.0,
    0.0, 0.0,
]
A_AIR = [-6.7e-19] * 14
A_BBR = [0.0] * 14
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
    """Convert a float to Decimal via repr (preserves full float64 precision)."""
    return Decimal(repr(float(x)))
