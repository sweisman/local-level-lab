# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def fixture():
    names=['time_offset']+['p'+str(i) for i in range(26)]
    matrix=dict(identity='original-failed',original_fit_converged=False,original_cost=4.,side=1,spacing_s=1e-6,
        active=names,point=[.25]+[0.]*26,lower=[0.]+[-1.]*26,upper=[1.]*27,
        residual=[1.],jacobian=[[1.]+[0.]*26],time_offset_scale=.01)
    proposal=dict(point=[0.]+[0.]*26,active_parameters=names,predicted_cost=.75**2,
        predicted_residual=[.75],anchor_cost=1.,lower=matrix['lower'],upper=matrix['upper'],
        maximum_iterations=100,iterations=1,tolerance=1e-10,linear_success=True,
        parameter_bounds_reached=['time_offset'],native_calls=0,nonlinear_fit_starts=0)
    return matrix,proposal


def test_cell_report_independently_recomputes_objective_and_preserves_original_failure():
    from lll.timing_cell_report import summarize
    matrix,proposal=fixture();row=summarize(matrix,proposal,index=0)
    assert row['original_fit_converged'] is False and row['linear_success']
    assert row['predicted_cost']==pytest.approx(.75**2)
    assert row['proposed_time_offset_s']==0. and row['actual_cost_evaluated'] is False
    assert 'converged' not in row


@pytest.mark.parametrize('change',['cost','point','columns','bounds','iterations'])
def test_cell_report_rejects_forged_or_changed_proposal(change):
    from lll.timing_cell_report import summarize
    matrix,p=fixture();p=copy.deepcopy(p)
    if change=='cost':p['predicted_cost']=0.
    elif change=='point':p['point'][0]=-.1
    elif change=='columns':p['active_parameters']=p['active_parameters'][:-1]
    elif change=='bounds':p['upper'][0]=2.
    else:p['maximum_iterations']=1000
    with pytest.raises(ValueError):summarize(matrix,p,index=0)
