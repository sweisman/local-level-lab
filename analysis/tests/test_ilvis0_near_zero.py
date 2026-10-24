# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util

import numpy as np
import pytest


def candidate():
    name='lll.ilvis0_near_zero'
    assert importlib.util.find_spec(name) is not None, 'separate near-zero stopping check missing'
    return __import__(name,fromlist=['verify'])


def test_near_zero_redundant_solution_does_not_need_unique_parameters():
    calls=[]
    def evaluate(point,fresh=False):
        calls.append(fresh)
        return np.array([1e-6,-1e-6]),np.ones((2,2)),0
    result=candidate().verify(np.zeros(2),evaluate,lambda d:np.c_[d,d*0,d*0])
    assert result['passed'] and calls==[True,True]
    assert result['computed_objective_gap_upper']<=1e-8
    assert result['parameter_identification_established'] is False
    assert result['scientific_decision']=='abstain'


@pytest.mark.parametrize('mode',['nonzero_cost','changed_cost','changed_prediction'])
def test_nonzero_or_unrepeatable_values_do_not_pass(mode):
    calls=[]
    def evaluate(point,fresh=False):
        calls.append(fresh)
        level=.1 if mode=='nonzero_cost' else (2e-4 if mode=='changed_cost' and len(calls)==2 else 1e-6)
        if mode=='changed_prediction' and len(calls)==2:level=-level
        return np.array([level]),np.zeros((1,2)),0
    scale=1e7 if mode=='changed_prediction' else 1.
    result=candidate().verify(np.zeros(2),evaluate,lambda d:np.c_[d,d*0,d*0]*scale)
    assert not result['passed']


def test_repeat_cannot_change_the_observation_vector_length():
    calls=[]
    def evaluate(point,fresh=False):
        calls.append(fresh);n=len(calls)
        return np.full(n,1e-6),np.zeros((n,2)),0
    with pytest.raises(ValueError,match='shape'):
        candidate().verify(np.zeros(2),evaluate,lambda d:np.c_[d,d*0,d*0])


@pytest.mark.parametrize('argument',['evaluate','physical_step'])
def test_invalid_callbacks_are_rejected_before_any_evaluation(argument):
    calls=[]
    def evaluate(point,fresh=False):calls.append(fresh);return np.zeros(1),np.zeros((1,2)),0
    args=dict(evaluate=evaluate,physical_step=lambda d:np.c_[d,d*0,d*0]);args[argument]=None
    with pytest.raises(ValueError,match='callable'):candidate().verify(np.zeros(2),**args)
    assert not calls


def meters(delta):return np.c_[delta,delta*0,delta*0]


class NearZeroCurve:
    """Independent nonlinear example with a misleading large linear correction."""
    def __init__(self):
        from lll.ilvis0_solver_controls import ControlBounds
        self.bounds=ControlBounds(1);self.calls=0
    def residual_tangent(self,point,model):
        self.calls+=1;x=point[0]
        return np.array([1e-7*(x-1)+.1*x*x]),np.array([[1e-7+.2*x]]),0


def test_new_composition_checks_near_zero_without_relabeling_the_ordinary_solver():
    from lll.ilvis0_solver_trust_v2 import fit_candidate as ordinary
    module=candidate();assert hasattr(module,'fit_candidate'), 'near-zero solver composition missing'
    old=NearZeroCurve();baseline=ordinary(old,'control',start=[0.],maximum_evaluations=18,physical_step=meters)
    assert not baseline['converged']
    problem=NearZeroCurve();fit=module.fit_candidate(problem,'control',start=[0.],maximum_evaluations=20,physical_step=meters)
    assert fit['converged'] and not fit['ordinary_converged']
    assert fit['near_zero_probe']['passed'] and fit['near_zero_probe']['fresh_evaluations']==2
    assert fit['evaluations']==problem.calls<=20
    assert fit['ordinary_maximum_evaluations']==18
    assert fit['scientific_decision']=='abstain' and not fit['scientific_eligible']
    assert not baseline['converged']


@pytest.mark.parametrize('name',['interior','boundary','redundant','scaled','nonlinear','gain_offset',
    'curved_boundary','exponential','curved_redundant','nonlinear27'])
@pytest.mark.parametrize('index',range(4))
def test_nonzero_known_optima_and_bounds_keep_the_original_gate(name,index):
    module=candidate();assert hasattr(module,'fit_candidate'), 'near-zero solver composition missing'
    from lll.ilvis0_boundary_controls import problem_for,starts
    problem,optimum,expected,unique=problem_for(name)
    fit=module.fit_candidate(problem,'control',start=starts(len(optimum))[index],maximum_evaluations=200,physical_step=meters)
    point=np.array(fit['normalized_parameters'])
    assert fit['converged'] and fit['ordinary_converged']
    assert fit['near_zero_probe'] is None
    assert fit['residual_sum_squares']==pytest.approx(expected,abs=1e-7)
    assert np.linalg.norm(problem.residual(point)-problem.residual(optimum))<=1e-4
    if unique:assert point==pytest.approx(optimum,abs=1e-5)
    assert np.all(abs(point)<=1) and fit['evaluations']==problem.calls<=200


def test_near_zero_repeat_failure_and_nonzero_budget_exhaustion_remain_failures():
    module=candidate();assert hasattr(module,'fit_candidate'), 'near-zero solver composition missing'
    problem=NearZeroCurve()
    fit=module.fit_candidate(problem,'control',start=[0.],maximum_evaluations=20,
        physical_step=lambda d:np.ones((len(d),3)))
    assert not fit['converged'] and not fit['near_zero_probe']['passed']
    assert fit['evaluations']==problem.calls<=20
    from lll.ilvis0_boundary_controls import problem_for
    problem,_,_,_=problem_for('exponential')
    fit=module.fit_candidate(problem,'control',start=[-.8,-.8],maximum_evaluations=8,physical_step=meters)
    assert not fit['converged'] and fit['near_zero_probe'] is None
    assert fit['evaluations']==problem.calls<=8
