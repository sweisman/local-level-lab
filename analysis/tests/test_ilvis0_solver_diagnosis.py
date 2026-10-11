# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest

from lll import ilvis0_solver_diagnosis as diagnosis


def fit():
    return dict(model='flat_still',converged=False,solver_reported_success=False,
        message='allowance exhausted',evaluations=200,residual_sum_squares=2.,
        exact_projected_gradient_relative=1e-9,stationarity_tolerance=1e-4,
        active_parameters=['gain','offset'],normalized_parameters=[0.,1.],
        gradient=[1e-6,-2.],projected_gradient=[1e-6,0.],
        scaled_projected_gradient=[1e-9,0.],active_bounds=['offset'],
        singular_values=[10.,.001],right_singular_vectors=[[1.,0.],[0.,1.]],
        accepted_step_history=[dict(evaluations=190,cost=2.,stationarity=1e-9,
            relative_cost_change=1e-9,relative_residual_step=1e-7)])


def test_small_final_gradient_does_not_relabel_exhausted_fit():
    f=fit(); original=copy.deepcopy(f)
    row=diagnosis.inspect_fit(f,dict(f,exact_projected_gradient_relative=.004),'case')
    assert row['status']=='unresolved' and row['fresh_stationarity_passed']
    assert row['terminal_stable_callbacks']==1
    assert row['first_three_stable_evaluation'] is None
    assert row['baseline_stationarity_ratio']==40.
    assert f==original


def test_stability_requires_both_step_and_cost_not_gradient_alone():
    h=[dict(evaluations=i+1,cost=2.,stationarity=1e-9,
        relative_cost_change=1e-9,relative_residual_step=1e-7) for i in range(4)]
    h[1]['relative_residual_step']=1e-3
    assert diagnosis.history_summary(h,10)['terminal_stable_callbacks']==2
    h[1]['relative_residual_step']=1e-7
    assert diagnosis.history_summary(h,10)['first_three_stable_evaluation']==3


def test_boundary_projection_and_weak_direction_are_reported_without_covariance_claim():
    p,m=diagnosis.parameter_diagnostics(fit())
    assert p[1]['bound_blocks_descent'] and p[1]['raw_gradient']==-2.
    assert m[0]['singular_value']==.001
    assert not m[0]['positive_direction_feasible']
    assert m[0]['negative_direction_feasible']


@pytest.mark.parametrize('field,value',[
    ('gradient',[1e-6]),('projected_gradient',[1e-6,-2.]),
    ('scaled_projected_gradient',[float('nan'),0.]),
    ('singular_values',[.001,10.]),
    ('right_singular_vectors',[[1.,0.],[1.,0.]]),
    ('active_parameters',['gain','gain']),
])
def test_inconsistent_saved_diagnostics_are_rejected(field,value):
    f=fit(); f[field]=value
    with pytest.raises(ValueError): diagnosis.inspect_fit(f,fit(),'case')


def test_reversed_or_out_of_allowance_history_is_rejected():
    h=fit()['accepted_step_history']
    with pytest.raises(ValueError): diagnosis.history_summary(h,100)
    with pytest.raises(ValueError): diagnosis.history_summary(h+h[:-1]+[dict(h[0],evaluations=180)],200)
