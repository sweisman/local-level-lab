# SPDX-License-Identifier: AGPL-3.0-or-later
"""Follow the directional curvature observed at a rejected bounded trial."""

import numpy as np


FRACTIONS = (1., .5, .25, .125)
STRONG_RELATIVE = 1e-3


def corrected_trial(point, residual, jacobian, direction, curvature):
    """Propose one box-feasible strong-direction correction to a weak step."""
    left, singular, right = np.linalg.svd(jacobian, full_matrices=False)
    if not len(singular) or singular[0] <= 0.:
        return None
    strong = singular >= STRONG_RELATIVE*singular[0]
    acceleration = -(left[:, strong].T@curvature/singular[strong])@right[strong]
    if not np.any(acceleration):
        return None
    linear = jacobian@direction
    best, best_reduction = None, 0.
    for fraction in FRACTIONS:
        base = point+fraction*direction
        change = fraction*fraction*acceleration
        positive, negative = change > 0, change < 0
        caps = np.ones_like(change)
        caps[positive] = (1.-base[positive])/change[positive]
        caps[negative] = (-1.-base[negative])/change[negative]
        scale = min(1., float(np.min(caps)))
        if scale <= 0.:
            continue
        correction = scale*change
        proposal = np.clip(base+correction, -1., 1.)
        predicted_change = fraction*linear+fraction*fraction*curvature+jacobian@correction
        decrease = -float(predicted_change@(2*residual+predicted_change))
        if decrease > best_reduction and not np.array_equal(proposal, point):
            best, best_reduction = (proposal, decrease, fraction), decrease
    return best
