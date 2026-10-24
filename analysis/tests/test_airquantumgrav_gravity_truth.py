# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated geometry/force checks, without a navigation predictor."""
import math
from pathlib import Path

import numpy as np
import pytest

from lll.airquantumgrav_truth import truth,MODELS


@pytest.mark.parametrize('model',MODELS)
def test_default_truth_is_exactly_the_frozen_constant_gravity_truth(model):
    from lll.studies.closed import ClosedStudy,load_python_reference
    root=Path(__file__).resolve().parents[2];closed=ClosedStudy(root,'docs/esa-development-pilot')
    try:
        key='analysis/lll/airquantumgrav_truth.py';sha=closed.manifest['sources'][key]
        previous=load_python_reference(closed.read('source-freeze/'+key,sha,raw=True),
            name='lll._constant_gravity_truth_reference_'+sha,sha256=sha)
    finally:closed.close()
    times=np.linspace(0.,1200.,17)
    args=dict(latitude_deg=55.,pattern='fast',removal=.35)
    old=previous.truth(model,times,**args);current=truth(model,times,**args)
    assert set(current)==set(old)
    for key in old:np.testing.assert_array_equal(current[key],old[key],err_msg=key)


@pytest.mark.parametrize('profile,heights',(('climb',(1500.,2500.,3500.)),('descend',(3500.,2500.,1500.))))
def test_generated_height_profiles_have_declared_endpoints_and_zero_endpoint_climb(profile,heights):
    case=truth('sphere_still',[0.,600.,1200.],latitude_deg=55.,pattern='slow',removal=0.,height_profile=profile)
    np.testing.assert_allclose(case['coordinates'][:,2],heights,atol=1e-12,rtol=0)
    np.testing.assert_allclose(case['coordinate_rates'][[0,-1],2],0.,atol=1e-14,rtol=0)
    other='climb' if profile=='descend' else 'descend'
    reverse=truth('sphere_still',[0.,600.,1200.],latitude_deg=55.,pattern='slow',removal=0.,height_profile=other)
    np.testing.assert_array_equal(case['coordinate_rates'][:,0],-reverse['coordinate_rates'][:,0])


@pytest.mark.parametrize('model',MODELS)
@pytest.mark.parametrize('profile',('climb','descend'))
def test_height_gravity_changes_only_specific_force_with_independent_sign_and_scale(model,profile):
    times=np.array([0.,300.,600.,900.,1200.]);args=dict(latitude_deg=-55.,pattern='fast',removal=.35,height_profile=profile)
    constant=truth(model,times,**args)
    varied=truth(model,times,gravity_model='inverse_square_height',**args)
    for key in constant:
        if key!='specific_force_mps2':np.testing.assert_array_equal(varied[key],constant[key],err_msg=key)
    delta=np.einsum('nij,nj->ni',varied['attitude_body_to_local'],
        varied['specific_force_mps2']-constant['specific_force_mps2'])
    np.testing.assert_allclose(delta[:,:2],0.,atol=2e-14,rtol=0)
    # Independent first-order free-air gradient, with a tolerance for the
    # second-order term across 2 km; it is not a helper shared with prediction.
    expected=.00000308*(varied['coordinates'][:,2]-varied['coordinates'][0,2])
    np.testing.assert_allclose(delta[:,2],expected,atol=8e-6,rtol=0)


@pytest.mark.parametrize('model',MODELS)
def test_climbing_cartesian_acceleration_matches_independent_position_differences(model):
    args=dict(latitude_deg=55.,pattern='fast',removal=0.,height_profile='climb',gravity_model='inverse_square_height')
    time=421.3;step=.05
    case=truth(model,[time-step,time,time+step],**args)
    second=(case['position_world_m'][0]-2*case['position_world_m'][1]+case['position_world_m'][2])/step**2
    np.testing.assert_allclose(second,case['acceleration_world_mps2'][1],rtol=2e-5,atol=2e-6)


def test_truth_rejects_undeclared_gravity_or_height_profiles():
    for kwargs in (dict(height_profile='unknown'),dict(gravity_model='unknown')):
        with pytest.raises(ValueError):truth('sphere_still',[0.,1.],latitude_deg=55.,pattern='slow',removal=0.,**kwargs)
