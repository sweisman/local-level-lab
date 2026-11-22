"""Construct matched ESA rate hypotheses without changing the saved baseline."""
import numpy as np
import pytest


def test_three_hypotheses_keep_time_support_and_saved_baseline():
    from lll.esa_fixed_rate_inputs import construct

    samples = construct(
        [0., .001, .002],
        [[0., 0., 0.], [200., 0., 0.], [400., 0., 0.]],
        [[0., 0., 0.], [1000., 0., 0.], [2000., 0., 0.]],
        saved_theta=[[.1, 0., 0.], [.3, 0., 0.]],
        saved_dv=[[.5, 0., 0.], [1.5, 0., 0.]],
        saved_dt=[.001, .001], training_prefix=1)
    assert set(samples) == {'linear_points', 'left_hold', 'right_hold'}
    np.testing.assert_array_equal(samples['linear_points']['theta'],
                                  [[.1, 0., 0.], [.3, 0., 0.]])
    np.testing.assert_allclose(samples['left_hold']['theta'],
                               [[0., 0., 0.], [.2, 0., 0.]])
    np.testing.assert_allclose(samples['right_hold']['dv'],
                               [[1., 0., 0.], [2., 0., 0.]])
    assert all(np.array_equal(value['dt'], samples['linear_points']['dt'])
               for value in samples.values())
    assert all(value['training_prefix'] == 1 for value in samples.values())


def test_changed_saved_increment_prevents_alternative_construction():
    from lll.esa_fixed_rate_inputs import construct

    with pytest.raises(ValueError, match='saved linear'):
        construct([0., .001], [[0., 0., 0.]]*2, [[0., 0., 0.]]*2,
                  saved_theta=[[1., 0., 0.]], saved_dv=[[0., 0., 0.]],
                  saved_dt=[.001], training_prefix=1)
