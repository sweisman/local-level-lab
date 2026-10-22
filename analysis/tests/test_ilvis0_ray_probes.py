# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest


def test_training_only_contraction_recovers_known_linear_scale():
    from lll.ilvis0_ray_probes import choose
    center=np.zeros((2,3));actual=center.copy();actual[:,0]=2
    jac=np.zeros((2,3,27));jac[:,0,0]=2;point=[1]+[0]*26
    result=choose(actual,center,jac,point,[1,1,1])
    assert F(result['scale_exact'])==F(3,8)
    assert result['point'][0]==.375
    assert result['future_used_for_selection'] is False
    assert result['nonlinear_feasibility_established'] is False


def test_quadratic_proposal_model_is_explicitly_not_a_feasibility_certificate():
    from lll.ilvis0_ray_probes import choose
    center=np.zeros((2,3));actual=center.copy();actual[:,0]=4
    result=choose(actual,center,np.zeros((2,3,27)),[1]+[0]*26,[1,1,1])
    alpha=F(result['scale_exact'])
    assert 4*alpha**2<=F(3,4)<4*(alpha+F(1,2**48))**2
    assert result['proposal_model']=='linear plus endpoint quadratic heuristic'
    assert not result['nonlinear_feasibility_established']


def test_endpoint_cancellation_does_not_allow_unchecked_full_scale():
    from lll.ilvis0_ray_probes import choose
    center=np.zeros((2,3));jac=np.zeros((2,3,27));jac[:,0,0]=2
    result=choose(center,center,jac,[1]+[0]*26,[1,1,1])
    assert F(result['scale_exact'])<F(3,8)
    assert F(result['envelope_exact'])<=F(3,4)


def test_incomplete_training_and_out_of_box_original_points_are_rejected():
    from lll.ilvis0_ray_probes import choose,recipe,validate_recipe
    zero=np.zeros((2,3));jac=np.zeros((2,3,27))
    with pytest.raises(ValueError):choose(zero,zero,jac,[0]*26,[1,1,1])
    with pytest.raises(ValueError):choose(zero,zero,jac,[2]+[0]*26,[1,1,1])
    changed=recipe();changed['training_allowance_m']=2
    with pytest.raises(ValueError):validate_recipe(changed)


def record(change,feasible=True):
    return dict(passed=True,nonlinear_training_feasible=feasible,
        training_max_axis_exact=['1/2' if feasible else '2']*3,
        future_change_exact=list(map(str,change)),future_used_for_training_gate=False)


def test_sampled_span_uses_only_actually_feasible_points_and_the_reference():
    from lll.ilvis0_ray_probes import sampled_span
    result=sampled_span([record([-11,0,0]),record([11,2,0]),record([1000,1000,0],False)])
    assert result['feasible_points']==2
    assert result['width_m']==[22.,2.,0.]
    assert result['target_exceeded']==[True,False,False]
    assert not result['outer_enclosure']


def test_span_refuses_inconsistent_feasibility_flags_or_future_selected_gates():
    from lll.ilvis0_ray_probes import sampled_span
    wrong=record([1,2,3]);wrong['training_max_axis_exact']=['2']*3
    with pytest.raises(ValueError):sampled_span([wrong])
    wrong=record([1,2,3]);wrong['future_used_for_training_gate']=True
    with pytest.raises(ValueError):sampled_span([wrong])
