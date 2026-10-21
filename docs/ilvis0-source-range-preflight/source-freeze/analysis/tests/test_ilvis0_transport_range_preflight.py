# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import numpy as np


def test_saved_bound_comparison_exists():
    assert importlib.util.find_spec('lll.ilvis0_transport_range_preflight') is not None


def fixture():
    value=dict(center=[.1,.2,3000.],previous_coefficients=np.zeros((3,6)).tolist(),
        acceleration_coefficients=np.zeros((3,9)).tolist(),transform_coefficients=np.zeros((3,9)).tolist(),
        source_id='source',reference_binding='reference',shared_binding='shared',
        acceleration_binding='acceleration',transform_binding='transform',time_s=7.2,
        conditioning=dict(input_binding='training'),unshared_remainder=[.1,.2,.3])
    return value


def test_only_compatible_bounds_can_be_intersected():
    from copy import deepcopy
    from lll.ilvis0_transport_range_preflight import compare_bounds
    old=fixture();new=deepcopy(old);new['unshared_remainder']=[.08,.25,.15]
    result=compare_bounds(old,new,[10.,20.,1.])
    assert result['passed'] and result['improved_axes']==[True,False,True]
    np.testing.assert_allclose(result['retained_remainder_m'],[.8,4.,.15])
    new['previous_coefficients'][0][0]=.001
    assert not compare_bounds(old,new,[10.,20.,1.])['passed']
    new=deepcopy(old);new['center'][0]+=1e-12
    assert not compare_bounds(old,new,[10.,20.,1.])['passed']


def test_invalid_error_bounds_are_rejected():
    import pytest
    from lll.ilvis0_transport_range_preflight import compare_bounds
    for invalid in ([.1,-.2,.3],[.1,.2,float('nan')],[.1,.2]):
        old=fixture();new=fixture();new['unshared_remainder']=invalid
        with pytest.raises(ValueError):compare_bounds(old,new,[1.,1.,1.])
