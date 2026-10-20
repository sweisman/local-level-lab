# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll import airquantumgrav_motion as motion


def path(angle=0.,turn=0.,sigma=.01):
    t=np.linspace(-5.,5.,21);phase=np.deg2rad(angle+turn*t)
    velocity=np.column_stack((60*np.cos(phase),60*np.sin(phase)))
    covariance=np.broadcast_to(sigma**2*np.eye(3),(len(t),3,3)).copy()
    return t,velocity,covariance


@pytest.mark.parametrize('heading',[0.,90.,179.9,359.9])
@pytest.mark.parametrize('turn',[-.06,0.,.06])
def test_analytic_turns_and_heading_wrap_preserve_sign(heading,turn):
    t,v,c=path(heading,turn)
    result=motion.assess(t,v,np.zeros(len(t)),c,center_s=0.)
    assert abs(result['course_rate_deg_s']-turn)<1e-6
    assert abs(result['adjacent_median_abs_course_rate_deg_s']-abs(turn))<1e-10
    assert result['median_abs_vertical_speed_mps']==0.
    assert result['observational_coverage_calibrated'] is False


def test_nonuniform_time_linear_velocity_matches_independent_reference():
    t=np.linspace(-5.,5.,23)+.02*np.sin(np.arange(23))
    velocity=np.column_stack((60.+.03*t,10.-.02*t));covariance=np.tile(np.eye(3),(len(t),1,1))*.001
    result=motion.assess(t,velocity,np.full(len(t),-2.),covariance,center_s=0.)
    np.testing.assert_allclose(result['intercept_ne_mps'],[60.,10.],atol=1e-12)
    np.testing.assert_allclose(result['slope_ne_mps2'],[.03,-.02],atol=1e-12)
    assert result['median_abs_vertical_speed_mps']==2.


def test_known_temporal_covariance_matches_dense_reference():
    t,v,c=path();tau=3.
    result=motion.assess(t,v,np.zeros(len(t)),c,center_s=0.,time_constant_s=tau)
    x=np.column_stack((np.ones(len(t)),t));weights=np.linalg.pinv(x)
    corr=np.exp(-abs(t[:,None]-t[None,:])/tau)
    expected=np.array([weights[0]@corr@weights[0],weights[1]@corr@weights[1]])*.01**2
    np.testing.assert_allclose(result['intervals']['supplied_correlation']['coefficient_variance'],
        [expected[0],expected[0],expected[1],expected[1]],atol=1e-17)


def test_arbitrary_correlation_bound_is_at_least_known_variance():
    t,v,c=path();r=motion.assess(t,v,np.zeros(len(t)),c,center_s=0.,time_constant_s=10.)
    assert np.all(np.array(r['intervals']['arbitrary_correlation']['coefficient_variance'])
        >=np.array(r['intervals']['supplied_correlation']['coefficient_variance'])-1e-18)


def test_undefined_speed_and_covariance_are_explicitly_unsupported():
    t,v,c=path();v[:]=0.
    result=motion.assess(t,v,np.zeros(len(t)),c,center_s=0.)
    assert result['course_rate_deg_s'] is None
    assert not result['intervals']['arbitrary_correlation']['supported']
    t,v,c=path();c[0,0,0]=-1.
    result=motion.assess(t,v,np.zeros(len(t)),c,center_s=0.)
    assert not result['intervals']['arbitrary_correlation']['supported']
    assert result['course_rate_deg_s']==0.


def test_rounding_allowance_cannot_shrink_intervals():
    t,v,c=path()
    a=motion.assess(t,v,np.zeros(len(t)),c,center_s=0.,rounding_mps=0.)
    b=motion.assess(t,v,np.zeros(len(t)),c,center_s=0.,rounding_mps=.0005)
    for name in a['intervals']:
        assert b['intervals'][name]['lower_deg_s']<=a['intervals'][name]['lower_deg_s']
        assert b['intervals'][name]['upper_deg_s']>=a['intervals'][name]['upper_deg_s']


@pytest.mark.parametrize('kind',['reversal','gap','nonfinite'])
def test_unsupported_time_geometry_is_rejected(kind):
    t,v,c=path()
    if kind=='reversal':t[10]=t[9]
    elif kind=='gap':t[10:]+=1.
    else:v[0,0]=float('nan')
    with pytest.raises(ValueError):motion.assess(t,v,np.zeros(len(t)),c,center_s=0.)
