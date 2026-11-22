"""Cross-interval rate comparison keeps vector and magnitude distinct."""

import pytest


def test_equal_magnitude_can_hide_changed_instrument_axis_vector():
    from lll.esa_second_ground_imu import compare_vectors
    result=compare_vectors([3.,4.,0.],[0.,5.,0.])
    assert result['first_magnitude_deg_per_hour']==5.
    assert result['second_magnitude_deg_per_hour']==5.
    assert result['magnitude_difference_deg_per_hour']==0.
    assert result['component_difference_deg_per_hour']==[-3.,1.,0.]
    assert result['vector_difference_magnitude_deg_per_hour']==pytest.approx(10**.5)
