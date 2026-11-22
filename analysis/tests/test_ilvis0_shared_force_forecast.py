# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_force_witness_must_match_the_actual_forecast_receiver_epochs():
    from lll.ilvis0_shared_force_forecast import aligned_correction

    saved = dict(times=[0., 1., 2.], coordinates=[[0., 0., 1.]]*3, cut=1)
    correction = dict(times_s=saved['times'], axes=['north', 'east', 'up'],
                      correction_m=[[0., 0., .1], [0., 0., .2], [0., 0., .3]])
    later = dict(query_times_s=[1., 2.], coordinates={'onboard': [[0., 0., 1.]]*2})
    np.testing.assert_array_equal(aligned_correction(saved, correction, later), [[0.,0.,.2], [0.,0.,.3]])
    later['coordinates']['onboard'][1] = [0., 0., 1.01]
    with pytest.raises(ValueError, match='same receiver'):
        aligned_correction(saved, correction, later)


def test_fixed_imu_score_uses_one_shared_reference_and_preserves_sign():
    from lll.ilvis0_shared_force_forecast import scores

    f = np.zeros((2, 3))
    g = np.array([[3., 4., 2.], [3., 4., 2.]])
    correction = np.array([[1., 1., 0.], [0., 0., 1.]])
    data = scores(f, g, correction)
    assert data['horizontal']['before_gap_m2'] == 25.
    assert data['horizontal']['after_gap_m2'] == 18.
    assert data['height']['before_gap_m2'] == 4.
    assert data['height']['after_gap_m2'] == 2.
