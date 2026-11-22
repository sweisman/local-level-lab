# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_exact_packet_calibration import exact_terms, refine
from lll.ilvis0_packet_calibration import packet_intervals


def test_exact_interval_derivatives_match_independent_packet_correction():
    counts = np.array([[0, 21, -154], [10, -7, -156], [-3, 5, -161], [-9, 0, -155]])
    dt = np.array([.005, .004, .006, .005])
    slices = np.array([[0, 2], [1, 4]])
    point = np.array([.01, -.02, .03, -.02, .01, .05])
    kwargs = dict(counts=counts, periods=dt, scale=.0003, slices=slices, count_error=.5)
    model, jacobian = exact_terms(correction=point, **kwargs)
    np.testing.assert_allclose(model, packet_intervals(correction=point, **kwargs), rtol=0., atol=1e-12)
    eps = 1e-5
    for k, step in enumerate(eps*np.eye(6)):
        left = packet_intervals(correction=point-step, **kwargs)
        right = packet_intervals(correction=point+step, **kwargs)
        np.testing.assert_allclose(jacobian[..., k], (right-left)/(2.*eps), rtol=1e-6, atol=1e-8)


def test_exact_update_rejects_overshoot_before_accepting_a_smaller_step():
    def assess(point):
        shift = point[3]-.05
        value = np.full((1, 2), 2.+shift**2)
        jacobian = np.zeros((1, 2, 6))
        jacobian[..., 3] = 2.*shift
        return value, jacobian

    charged, audits = [], []
    result = refine(np.zeros(6), [.1]*3+[.5]*3, np.ones((1, 2)), assess,
                    reserve=charged.append, save=audits.append, trials=2)
    assert charged == [1, 2]
    assert [trial['accepted'] for trial in audits] == [False, True]
    assert result['gap_mps2'] < result['initial_gap_mps2']
    assert result['correction'][3] == .0625
