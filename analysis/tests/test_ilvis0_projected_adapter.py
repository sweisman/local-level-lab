# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap routine checks of projection fitting; candidate acceptance is separate."""
import numpy as np
import pytest
from lll.ilvis0_estimator import Bounds,EvaluationLimit
from lll.ilvis0_projected_fitting import ProjectedProblem,ControlBudget,fit_control


class Known:
    def __init__(self):
        self.bounds=Bounds(dict(position_x=1.,position_z=1.));self.cholesky=np.eye(6)
        self.gps=np.zeros((2,3));self.calls=0
        self.jac=np.tile([[1.,0.],[0.,0.],[0.,1.]],(2,1))

    def residual_tangent(self,u,model):
        self.bounds.decode(u);self.calls+=1
        return self.jac@u-np.tile([2.,0.,.4],2),self.jac.copy(),0

    def predict(self,u,model):return (self.jac@u).reshape(2,3)


def test_bounded_solution_keeps_null_column_and_full_prediction():
    base=Known();p=ProjectedProblem(base,('latitude','longitude'))
    result=fit_control(p,'flat_still',start=[0.,-.7],maximum_evaluations=12)
    assert result['converged'] and result['numerical_rank']==1
    assert result['normalized_parameters']==pytest.approx([1.,-.7])
    assert result['active_parameters']==['position_x','position_z']
    assert result['scientific_decision']=='abstain' and not result['archival_stability_qualified']
    assert result['evaluations']==base.calls<=12
    assert p.predict([0.,.7],'flat_still').shape==(2,3)
    assert p.report()['unscored_coordinates_checked'] is False


def test_projected_stability_does_not_claim_unscored_axis_is_checked():
    p=ProjectedProblem(Known(),('height',))
    delta=p.physical_step(np.array([.1,-.2]))
    assert delta[:,:2]==pytest.approx(np.zeros((2,2)))
    assert delta[:,2]==pytest.approx([.1,-.2])
    with pytest.raises(ValueError):p.physical_step(np.ones(6))


@pytest.mark.parametrize('axes',[(),('height','height'),('unknown',)])
def test_bad_axis_selection_fails_closed(axes):
    with pytest.raises(ValueError):ProjectedProblem(Known(),axes)


def test_native_budget_is_charged_before_the_next_call():
    budget=ControlBudget(maximum_native_sweeps=1,maximum_starts=1)
    budget.charge_native();budget.charge_start()
    with pytest.raises(EvaluationLimit):budget.charge_native()
    with pytest.raises(EvaluationLimit):budget.charge_start()
    assert budget.native_sweeps==budget.starts==1


def test_invalid_start_does_not_spend_a_prediction():
    base=Known();p=ProjectedProblem(base,('height',))
    with pytest.raises(ValueError):fit_control(p,'flat_still',start=[2.,0.],maximum_evaluations=12)
    assert base.calls==0
