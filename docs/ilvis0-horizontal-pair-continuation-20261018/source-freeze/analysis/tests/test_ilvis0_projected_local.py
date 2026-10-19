# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local stability checks retain the numerical limits and every weak column."""
import numpy as np
import pytest


def module():
    from lll import ilvis0_projected_local as local
    return local


def physical(delta):return np.column_stack((delta,np.zeros(len(delta)),np.zeros(len(delta))))


def test_local_probe_retains_null_column_and_cannot_cross_its_radius():
    local=module();point=np.array([.9999,-.5]);r=np.array([1e-9,2e-9]);j=np.array([[1.,0.],[2.,0.]])
    points=[]
    def evaluate(u,fresh=False):
        assert fresh;points.append(u.copy());return r+j@(u-point),j,0
    result=local.verify_local(point,r,j,evaluate,physical)
    assert result['passed'] and result['columns']==2
    assert np.max(abs(points[0]-point))<=local.LOCAL_RADIUS
    assert np.all(abs(points[0])<=1.) and points[0][1]==point[1]
    assert result['local_stability_only'] is True


def test_original_stationarity_failure_is_not_relabeled():
    local=module();calls=[]
    def evaluate(u,fresh=False):calls.append(u);return np.zeros(1),np.ones((1,1)),0
    result=local.verify_local(np.zeros(1),np.array([.001]),np.ones((1,1)),evaluate,physical)
    assert not result['passed'] and result['reason']=='not_stationary' and not calls


def test_nonlinear_probe_with_large_actual_change_still_fails():
    local=module();point=np.array([-.49,-.7])
    def evaluate(u,fresh=False):
        x,y=u;return np.array([1000*(x+y*y),.001*(y-.3)]),np.array([[1000.,2000*y],[0.,.001]]),0
    r,j,_=evaluate(point)
    result=local.verify_local(point,r,j,evaluate,physical)
    assert not result['passed']
    assert result['actual_cost_change']>local.STOPPING['relative_cost_tolerance']


def test_known_curved_optimum_passes_without_nuisance_claim():
    local=module();point=np.array([-.09,.3])
    def evaluate(u,fresh=False):
        x,y=u;return np.array([1000*(x+y*y),.001*(y-.3)]),np.array([[1000.,2000*y],[0.,.001]]),0
    r,j,_=evaluate(point)
    result=local.verify_local(point,r,j,evaluate,physical)
    assert result['passed'] and result['local_stability_only']


def test_changed_gate_is_explicit_and_old_policy_is_untouched():
    from lll.ilvis0_solver_position import POLICY
    original=dict(POLICY);local=module();engine=local.engine()
    assert local.VERSION!=engine.position.VERSION or engine.position.verify_stability is local.verify_local
    assert POLICY==original
    assert local.LOCAL_RADIUS==.001
