"""Check that GPS force contrasts use shared support and isolate height swaps."""

import numpy as np

from lll import ilvis0_gps_force_comparison as comparison


def test_height_only_controls_keep_onboard_latitude_and_longitude():
    times = np.arange(-5., 6.)
    raw = np.column_stack((-.7+2e-6*times, -.8+4e-5*times, 2500.+.1*times))
    l1 = raw.copy()
    l1[:, 2] += .01*times**2
    dual = l1.copy()
    dual[:, 0] += 1e-6*times
    results = comparison.window_forces(times, {'onboard': raw, 'l1_broadcast': l1,
                                               'dual_frequency': dual})
    for model in comparison.MATCHED_MODELS:
        np.testing.assert_array_equal(results['l1_broadcast'][model], results['l1_height_only'][model])
        np.testing.assert_array_equal(results['l1_broadcast'][model], results['dual_height_only'][model])
        assert not np.allclose(results['dual_frequency'][model], results['dual_height_only'][model])
        assert abs(results['l1_broadcast'][model][2]-results['onboard'][model][2]+.02) < 1e-10


def test_fixed_support_abstains_instead_of_bridging_a_two_second_gap():
    tags = np.arange(10000, 22000, 1000)
    qualified, _, _ = comparison.support(tags, 15000, 5.)
    assert qualified == 'evaluated'
    missing = tags[tags != 14000]
    state, _, _ = comparison.support(missing, 15000, 5.)
    assert state == 'unsupported'
