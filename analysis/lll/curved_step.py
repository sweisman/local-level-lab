# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use an evaluated rejected residual to choose a single fractional step."""
import numpy as np


def residual_decrease(before, after):
    """Squared-norm reduction without subtracting two large costs."""
    return float((before-after)@(before+after))


def curved_fraction(residual, linear_change, full_residual):
    slope = np.asarray(linear_change)
    curvature = full_residual-residual-slope
    # Coefficients of cost(a) - cost(0), in increasing power order.
    coeff = np.array([0., 2*(residual@slope), slope@slope+2*(residual@curvature),
                      2*(slope@curvature), curvature@curvature])
    norm = np.max(abs(coeff))
    if not np.isfinite(norm) or norm == 0:
        return None
    coeff /= norm
    derivative = np.polynomial.polynomial.polyder(coeff)
    candidates = [0., 1., *(float(root.real) for root in np.polynomial.polynomial.polyroots(derivative)
                             if abs(root.imag) <= 1e-10 and 0 < root.real < 1)]
    best = min(candidates, key=lambda a: np.polynomial.polynomial.polyval(a, coeff))
    return best if 0 < best < 1 else None
