# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def fixture():
    point=np.zeros(27);prediction=np.zeros((6,3));jac=np.zeros((6,3,27))
    for k in range(15):jac.reshape(18,27)[k,k]=1
    jac[5,0,15]=1;target=np.full((5,3),.1)
    return point,prediction,jac,target,[1,1,1]


def test_one_linear_repair_matches_training_and_keeps_future_north_unchanged():
    from lll.ilvis0_training_repair import repair
    result=repair(*fixture())
    assert result['proposal_valid'] and result['rank']==16
    assert result['point'][:15]==pytest.approx([.1]*15)
    assert result['point'][15:]==[0.]*12
    assert result['maximum_linear_residual_m']<=1e-3
    assert not result['nonlinear_feasibility_established']


def test_infeasible_linear_equalities_and_out_of_box_updates_are_not_clipped():
    from lll.ilvis0_training_repair import repair
    args=list(fixture());args[2]=np.zeros((6,3,27))
    assert not repair(*args)['proposal_valid']
    args=list(fixture());args[0]=np.full(27,.99)
    result=repair(*args);assert not result['proposal_valid'] and not result['clipped']


@pytest.mark.parametrize('change',['columns','nan','target','scale'])
def test_complete_finite_inputs_are_required(change):
    from lll.ilvis0_training_repair import repair
    args=list(fixture())
    if change=='columns':args[2]=args[2][:,:,:26]
    if change=='nan':args[1][0,0]=float('nan')
    if change=='target':args[3]=args[3][:4]
    if change=='scale':args[4]=[0,1,1]
    with pytest.raises(ValueError):repair(*args)
