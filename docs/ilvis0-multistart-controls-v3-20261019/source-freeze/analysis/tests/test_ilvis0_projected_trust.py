# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constructed controls for the isolated projected trust-region candidate."""
import numpy as np
import pytest
from lll.ilvis0_estimator import Bounds


def candidate():
    from lll import ilvis0_projected_trust as module
    return module


class Curved:
    def __init__(self,kind):
        self.kind=kind;self.bounds=Bounds(dict(position_x=1.,position_z=1.))
        self.gps=np.zeros((3,3));self.cholesky=np.eye(9);self.calls=0

    def residual_tangent(self,u,model):
        self.bounds.decode(u);self.calls+=1;x,y=u
        if self.kind=='banana':r=[10*(y-x*x),.8-x,0.];j=[[-20*x,10.],[-1.,0.],[0.,0.]]
        elif self.kind=='exponential':
            v=np.exp(4*x);r=[v-np.exp(3.2),y-.4,0.];j=[[4*v,0.],[0.,1.],[0.,0.]]
        elif self.kind=='null_bound':r=[x-2.,0.,y-.4];j=[[1.,0.],[0.,0.],[0.,1.]]
        else:
            # Narrow curved valley: a full first-order cancellation can make
            # the actual residual worse; no columns are deleted.
            r=[1000*(x+y*y),.001*(y-.3),0.];j=[[1000.,2000*y],[0.,.001],[0.,0.]]
        return np.tile(r,3),np.tile(j,(3,1)),0


@pytest.mark.parametrize('kind',['banana','exponential','narrow'])
def test_trust_candidate_recovers_known_nonlinear_prediction(kind):
    base=Curved(kind);p=candidate().ProjectedProblem(base,('latitude','longitude'))
    fit=candidate().fit_control(p,'flat_still',start=[-.7,-.7],maximum_evaluations=160)
    assert fit['converged'],fit['message']
    assert fit['residual_sum_squares']<1e-8
    assert fit['evaluations']==base.calls<=160
    assert fit['stability_probe']['passed']
    if kind=='narrow':assert any(r.get('method')=='bounded_curvature_correction' and r['accepted'] for r in fit['step_history'])
    assert len(fit['local_linearization']['jacobian'][0])==2
    assert fit['scientific_decision']=='abstain' and fit['unscored_coordinates_checked'] is False


def test_null_column_and_exact_bound_are_preserved():
    base=Curved('null_bound');p=candidate().ProjectedProblem(base,('latitude','longitude'))
    fit=candidate().fit_control(p,'flat_still',start=[0.,-.7],maximum_evaluations=20)
    assert fit['converged'] and fit['normalized_parameters']==pytest.approx([1.,-.7])
    assert fit['numerical_rank']==1 and fit['columns']==2


def test_budget_failure_does_not_become_convergence():
    base=Curved('exponential');p=candidate().ProjectedProblem(base,('latitude','longitude'))
    fit=candidate().fit_control(p,'flat_still',start=[-.8,-.8],maximum_evaluations=6)
    assert not fit['converged'] and fit['evaluations']==base.calls<=6


@pytest.mark.parametrize('limit',[5,161,True])
def test_invalid_budget_stops_before_prediction(limit):
    base=Curved('banana');p=candidate().ProjectedProblem(base,('height',))
    with pytest.raises(ValueError):candidate().fit_control(p,'flat_still',start=[0.,0.],maximum_evaluations=limit)
    assert base.calls==0
