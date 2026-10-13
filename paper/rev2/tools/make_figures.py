#!/usr/bin/env python3
"""Figure inventory for the rebuilt manuscript (paper/rev2).

All three manuscript figures are now hand-supplied by the collaboration:

    figs/fig1_network.png   -- user-supplied PNG (2026-10-13)
    figs/fig2_ratio.pdf     -- user-supplied SVG (fig_ratio.svg, 2026-10-13),
                               converted to PDF with cairosvg
    figs/fig3_history.pdf   -- user-supplied SVG (fig_history.svg, 2026-10-13),
                               converted to PDF with cairosvg

This script intentionally does not regenerate any figure: running it
prints the inventory and exits. The numbers pipeline
(tools/build_numbers.py) remains the source of all manuscript numerics.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REV2 = TOOLS.parent
FIGS = REV2 / "figs"

SUPPLIED: tuple[tuple[str, str], ...] = (
    ("fig1_network.png", "user-supplied PNG (2026-10-13); network schematic"),
    ("fig2_ratio.pdf", "user-supplied SVG fig_ratio.svg (2026-10-13); "
     "fractional instability of a representative segment"),
    ("fig3_history.pdf", "user-supplied SVG fig_history.svg (2026-10-13); "
     "historical Yb/Sr measurements vs this work"),
)


def main() -> int:
    print(f"Manuscript figures in {FIGS}/ are hand-supplied:")
    missing = False
    for name, note in SUPPLIED:
        path = FIGS / name
        status = "OK " if path.is_file() else "MISSING"
        if not path.is_file():
            missing = True
        print(f"  [{status}] {name} -- {note}")
    if missing:
        print("ERROR: one or more supplied figures are missing", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
