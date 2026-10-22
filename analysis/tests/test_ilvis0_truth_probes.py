# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def test_points_are_perturbations_of_the_actual_nonzero_truth_without_clipping():
    from lll.ilvis0_truth_probes import make_point
    truth=[.05]*27;truth[25]=.25
    value=make_point(truth,['1']*27,'1/10')
    assert value['point'][0]==float(F(.05)+F(1,20))
    assert value['point'][25]==.3
    assert value['original_truth']==truth
    with pytest.raises(ValueError):make_point([.99]*27,['1']*27,'1/10')


def test_only_the_three_predeclared_scales_and_all_columns_are_accepted():
    from lll.ilvis0_truth_probes import make_point,recipe,validate_recipe
    with pytest.raises(ValueError):make_point([0]*27,['1']*27,'1/5')
    with pytest.raises(ValueError):make_point([0]*26,['1']*27,'1/10')
    changed=recipe();changed['training_allowance_m']=2
    with pytest.raises(ValueError):validate_recipe(changed)


def test_nonlinear_feasibility_uses_stored_observations_rather_than_zero_or_truth():
    from lll.ilvis0_truth_probes import compare
    obs=[[100,200,1000],[101,201,1000]];future=[102,202,1000]
    actual=[[100.5,200.5,1000],[101.5,201.5,1000],[10000,10000,10000]]
    result=compare(actual,obs,future,[1,1,1],['0']*3)
    assert result['nonlinear_training_feasible']
    assert result['training_max_axis_exact']==['1/2','1/2','0']
    assert result['future_used_for_training_gate'] is False
