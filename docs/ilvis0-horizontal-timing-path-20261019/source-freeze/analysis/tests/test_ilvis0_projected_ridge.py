# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
from pathlib import Path
import numpy as np
import pytest


def module():
    assert Path(__file__).parents[1].joinpath('lll/ilvis0_projected_ridge.py').exists(), 'ridge candidate missing'
    return importlib.import_module('lll.ilvis0_projected_ridge')


def physical(r):return np.column_stack((r,np.zeros(len(r)),np.zeros(len(r))))


def test_exact_optimum_preserves_every_column_and_gate_limits():
    m=module();calls=[];point=np.array([0.,.3,-.5]);j=np.array([[1.,0.,0.],[0.,.001,0.]])
    def evaluate(u,fresh=False):
        assert fresh;calls.append(u);return j@(u-point),j,0
    result=m.verify_local(point,np.zeros(2),j,evaluate,physical)
    assert result['passed'] and result['columns']==3 and calls[0][2]==point[2]
    assert result['regularization_changes_score'] is False
    assert result['local_stability_only'] and result['ridge_penalty']==1e-6


def test_endpoint_stationarity_is_still_required():
    m=module();calls=[]
    result=m.verify_local(np.zeros(1),np.array([.1]),np.ones((1,1)),lambda *a,**k:calls.append(a),physical)
    assert not result['passed'] and not calls


def test_actual_nonlinear_instability_is_still_rejected():
    m=module();j=np.array([[1.,0.]])
    result=m.verify_local(np.zeros(2),np.array([1e-8]),j,
        lambda u,fresh=False:(np.array([.1]),j,0),physical)
    assert not result['passed'] and result['actual_cost_change']>1e-8


def test_new_candidate_does_not_modify_frozen_engine_or_policy():
    from lll import ilvis0_projected_local as old
    from lll.ilvis0_solver_position import POLICY
    before=dict(POLICY);original=old.engine()
    m=module();new=m.engine()
    assert new.position.verify_stability is m.verify_local
    assert original.position.verify_stability is old.verify_local and POLICY==before
    assert new.VERSION!=original.VERSION


@pytest.mark.parametrize('maximum',[5,601,True])
def test_invalid_budget_is_rejected_before_model_evaluation(maximum):
    with pytest.raises(ValueError):module().fit_control(None,'flat_still',start=[0.],maximum_evaluations=maximum)
