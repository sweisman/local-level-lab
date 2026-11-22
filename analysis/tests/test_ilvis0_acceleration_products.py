# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np

from lll.esa_direct_training_score import feasible_box_and_cuts
from lll.ilvis0_acceleration_products import build, lift
from lll.ilvis0_calibration_consistency import build as consistency
from lll.ilvis0_saved_prediction_audit import endpoint
from test_ilvis0_calibration_consistency import components


def setup():
    acceleration, transform = components()
    ref = transform.reference
    delta = lambda endpoint_values, up: [
        endpoint(F(value)-F(center), up) for value,center in zip(endpoint_values, ref.center, strict=True)
    ]
    cuts = build(acceleration, transform, consistency(acceleration, transform),
                 delta(ref.lower, False)+[-1.]*24, delta(ref.upper, True)+[1.]*24,
                 allowance=3e-10)
    return acceleration, transform, cuts


def test_coupled_force_and_bias_products_retain_mixed_calibrations():
    acceleration, transform, cuts = setup()
    ref = transform.reference
    assert len(cuts['design']) == 42
    assert len(cuts['lower']) == 60
    choices = np.random.default_rng(612).uniform(ref.lower, ref.upper, (8,27))
    for point in [ref.center, ref.lower, ref.upper, *choices]:
        values = np.r_[ref.normalized_values_at(point), acceleration.normalized_values_at(point),
                       transform.normalized_values_at(point)]
        delta = [F(a)-F(b) for a,b in zip(point, ref.center, strict=True)]
        lifted = lift(cuts, delta+list(values))
        assert feasible_box_and_cuts(lifted, cuts['lower'], cuts['upper'], cuts['design'], cuts['limits'])


def test_cannot_move_acceleration_remainder_at_unchanged_force_and_bias():
    _, _, cuts = setup()
    point = [F(0)]*51
    point[39] = F(1,2)
    assert not feasible_box_and_cuts(lift(cuts, point), cuts['lower'], cuts['upper'],
                                    cuts['design'], cuts['limits'])
