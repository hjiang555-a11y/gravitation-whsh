from __future__ import annotations

from decimal import Decimal

from clock.shared import COEF1156, D_1_25, D_7_25, DELTA_G, DIV20, FREF, N1156, N1397, N1550, N1550_WH


def full_ratio(mean_dm: Decimal, shift_a: Decimal, global_median: Decimal) -> Decimal:
    """Invert the legacy Decimal80 full ratio formula without changing any terms."""
    coef1397 = (Decimal(1) + shift_a) / Decimal(2)
    denominator = coef1397 / N1397 * (N1550 + D_7_25 + D_1_25)
    delta_ratio = COEF1156 / N1156 * (mean_dm / FREF / DIV20) / denominator
    numerator = N1550_WH + Decimal(26) / Decimal(20) + global_median / FREF / DIV20
    denominator_base = N1550 + Decimal(8) / Decimal(25)
    ratio_base = COEF1156 / N1156 * numerator / (coef1397 / N1397 * denominator_base)
    sr_yb_raw = ratio_base + delta_ratio
    return (Decimal(1) / sr_yb_raw) * (Decimal(1) + DELTA_G)
