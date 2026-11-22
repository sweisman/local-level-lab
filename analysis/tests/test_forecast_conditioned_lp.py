# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the compact proposal independently of the observed calculation."""

from fractions import Fraction as F

import numpy as np

from lll.calibration_maximum_margin import smooth_rows
from lll.calibration_orthogonal import annihilate_quadratics
from lll.conditioned_position_margin import (conditional_transfer, lower_certificate, propose,
                                             upper_certificate)
from lll.forecast_conditioned_lp import forecast_factors, propose_compact
from test_conditioned_position_margin import factors


def test_forecast_factors_reproduce_the_dense_map_at_each_cut():
    operator = factors()
    for cut in range(1, operator.epoch_count):
        history, projection = forecast_factors(operator, cut=cut)
        np.testing.assert_allclose(projection @ history, conditional_transfer(operator, cut=cut))
        assert history.shape == (1, cut*3)


def test_compact_program_certifies_known_optimum_for_nonzero_cut_state():
    operator = factors()
    for name in ('_transition', '_observation', '_gain'):
        values = getattr(operator, name)
        setattr(operator, name, np.concatenate([values, values[-1:]]))
    operator.epoch_count += 1
    times = [0, 1, 2, 3]
    nominal = [F(0)]*17+[F(8)]
    design = np.zeros((18, 1))
    design[-1, 0] = 1
    args = operator, nominal, design, [1.]*18, [-1.], [1.]
    smooth = smooth_rows(times, len(nominal))
    choice = propose_compact(*args, smooth, cut=2, iterations=200)
    assert choice['status'] == 0
    assert np.any(np.asarray(choice['earlier_error']) != 0)
    proof_upper = upper_certificate(*args, smooth, choice, cut=2)
    proof_lower, _ = lower_certificate(*args, annihilate_quadratics(choice['later_taps'], times), cut=2)
    assert proof_lower <= F(56, 131) <= proof_upper
    assert float(proof_upper-proof_lower) < 1e-10


def test_compact_and_dense_programs_match_with_cross_axis_calibration():
    operator = factors()
    for name in ('_transition', '_observation', '_gain'):
        values = getattr(operator, name)
        setattr(operator, name, np.concatenate([values, values[-2:]]))
    operator.epoch_count += 2
    generator = np.random.default_rng(310)
    design = generator.normal(size=(21, 6))
    nominal = generator.normal(size=21).tolist()
    metric = [1., .4, 7.]*7
    low = [-.2, -.004, -.03, .04, -.12, 0.]
    high = [.18, .19, .05, .09, .16, 0.]
    args = operator, nominal, design, metric, low, high
    smooth = smooth_rows([0, 1, 2, 3, 7], len(nominal))
    dense = propose(*args, smooth, cut=2, iterations=200)
    compact = propose_compact(*args, smooth, cut=2, iterations=200)
    assert dense['status'] == compact['status'] == 0
    np.testing.assert_allclose(compact['objective'], dense['objective'], atol=1e-9)
