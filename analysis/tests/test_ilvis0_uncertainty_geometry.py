# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def api():
    from lll import ilvis0_uncertainty_geometry as g
    return g


def linear_case(center=(0.,0.),bounds=((-10.,-10.),(10.,10.))):
    g=api();j=np.diag([1.,.5]);points=np.array([center,np.asarray(center)+[.1,0.],np.asarray(center)+[0.,.1]])
    return g.assess(center,*bounds,j,np.eye(2),points,points@j.T,np.array(center)@j.T)


def test_interior_linear_geometry_has_known_covariance_and_no_remainder():
    out=linear_case()
    assert out['rank']==2 and out['active_bounds']==[]
    np.testing.assert_allclose(out['unconstrained_local_covariance'],np.diag([1.,4.]))
    assert out['maximum_whitened_remainder']==pytest.approx(0.)
    assert out['minimum_bound_distance_in_local_sd']==pytest.approx(5.)
    assert out['confidence_calibrated'] is False


def test_bound_parameters_remain_in_rank_and_are_not_given_zero_variance():
    out=linear_case(bounds=((0.,-10.),(10.,10.)))
    assert out['active_bounds']==[{'parameter':0,'side':'lower'}]
    assert out['rank']==2
    np.testing.assert_allclose(out['unconstrained_local_covariance'],np.diag([1.,4.]))
    assert not out['local_gaussian_boundary_compatible']
    assert out['minimum_bound_distance_in_local_sd']==0.


def test_nonlinear_remainder_uses_noise_units_without_fit_residual_rescaling():
    g=api();points=np.array([[1.],[.9],[1.1]])
    out=g.assess([1.],[0.],[2.],[[2.]],[[.01]],points,points**2,[1.])
    assert out['maximum_whitened_remainder']==pytest.approx(.1)
    np.testing.assert_allclose(out['unconstrained_local_covariance'],[[.0025]])
    assert out['probe_count']==3


def test_zero_derivative_rejects_spurious_precision_for_quadratic_observation():
    g=api();out=g.assess([0.],[-2.],[2.],[[0.]],[[1.]],[[0.],[1.]],[[0.],[1.]],[0.])
    assert out['rank']==0
    assert out['unconstrained_local_covariance'] is None
    assert out['maximum_whitened_remainder']==pytest.approx(1.)


def test_redundant_columns_have_no_pseudoinverse_covariance_claim():
    g=api();out=g.assess([0.,0.],[-1.,-1.],[1.,1.],[[1.,1.]],[[1.]],
        [[0.,0.],[.1,-.1]],[[0.],[0.]],[0.])
    assert out['rank']==1 and out['unidentifiable_dimensions']==1
    assert out['unconstrained_local_covariance'] is None


def test_parameter_units_preserve_rank_covariance_and_whitened_remainder():
    g=api();a=linear_case();scale=np.array([1e9,1e-9]);j=np.diag([1.,.5])
    points=np.array([[0.,0.],[.1,0.],[0.,.1]])
    b=g.assess([0.,0.],-10*scale,10*scale,j/scale,np.eye(2),points*scale,points@j.T,[0.,0.])
    assert b['rank']==a['rank']
    np.testing.assert_allclose(np.array(b['unconstrained_local_covariance'])/np.outer(scale,scale),a['unconstrained_local_covariance'])
    assert b['maximum_whitened_remainder']==pytest.approx(0.)


def test_cost_support_keeps_disconnected_nonlinear_solutions_and_prediction_spread():
    g=api();points=np.array([[-1.],[0.],[1.]])
    out=g.grid_support(points,[0.,1.,0.],points,[-2.],[2.],cost_allowance=.1)
    assert out['accepted_indices']==[0,2]
    assert out['prediction_minimum']==[-1.] and out['prediction_maximum']==[1.]
    assert out['sampled_support_only'] and not out['confidence_calibrated']
    assert not out['continuous_extrema_established']


def test_cost_allowance_is_relative_to_grid_minimum_and_not_an_absolute_cutoff():
    out=api().grid_support([[0.],[1.],[2.]],[10.,10.1,11.],[[3.],[4.],[100.]],
        [0.],[2.],cost_allowance=.2)
    assert out['accepted_indices']==[0,1]
    assert out['prediction_maximum']==[4.]
    assert out['grid_minimum_cost']==10.


def test_incomplete_probe_directions_do_not_claim_full_nonlinear_examination():
    g=api();out=g.assess([0.,0.],[-1.,-1.],[1.,1.],np.eye(2),np.eye(2),
        [[0.,0.],[.1,0.]],[[0.,0.],[.1,0.]],[0.,0.])
    assert out['rank']==2 and out['probed_parameter_rank']==1


def test_upper_bound_is_not_silently_dropped_from_geometry():
    g=api();out=g.assess([1.],[0.],[1.],[[1.]],[[1.]],[[1.],[.9]],[[1.],[.9]],[1.])
    assert out['active_bounds']==[{'parameter':0,'side':'upper'}]
    assert out['rank']==1 and not out['local_gaussian_boundary_compatible']


@pytest.mark.parametrize('case',['outside_center','outside_probe','reversed_bounds','nonfinite',
    'bad_jacobian','bad_predictions','bad_covariance','empty_probes','missing_center'])
def test_invalid_geometry_is_not_repaired(case):
    g=api();center=np.array([0.]);lo=np.array([-1.]);hi=np.array([1.]);j=np.ones((1,1))
    c=np.eye(1);points=np.array([[0.],[.1]]);pred=points.copy()
    if case=='outside_center':center[:]=2.
    if case=='outside_probe':points[1]=2.
    if case=='reversed_bounds':hi[:]=-2.
    if case=='nonfinite':pred[0]=np.nan
    if case=='bad_jacobian':j=np.ones((2,1))
    if case=='bad_predictions':pred=np.ones((1,2))
    if case=='bad_covariance':c[:]=0.
    if case=='empty_probes':points=np.zeros((0,1));pred=np.zeros((0,1))
    if case=='missing_center':points+=.2
    with pytest.raises(ValueError):g.assess(center,lo,hi,j,c,points,pred,[0.])


@pytest.mark.parametrize('case',['negative_allowance','negative_cost','nonfinite_cost','outside',
    'wrong_predictions','empty'])
def test_invalid_grid_is_rejected(case):
    g=api();points=np.array([[0.],[1.]]);costs=np.array([1.,2.]);pred=points.copy();allowance=1.
    if case=='negative_allowance':allowance=-1.
    if case=='negative_cost':costs[0]=-1.
    if case=='nonfinite_cost':costs[0]=np.nan
    if case=='outside':points[1]=2.
    if case=='wrong_predictions':pred=pred[:1]
    if case=='empty':points=points[:0];costs=costs[:0];pred=pred[:0]
    with pytest.raises(ValueError):g.grid_support(points,costs,pred,[0.],[1.],cost_allowance=allowance)
