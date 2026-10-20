# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_scalar_nonlinear import Problem
from lll import ilvis0_scalar_certificate as candidate
from ilvis0_scalar_nonlinear_controls import fixture,FIXTURES,STARTS,LIMITS


def test_rotation_invariant_feasible_gain_is_certified_without_optimizer():
    time=np.arange(121)/3
    body=np.column_stack((9.8*np.sin(time),np.zeros(121),9.8*np.cos(time)))
    force=np.tile([0.,0.,-9.81],(121,1));problem=Problem(body,force,LIMITS)
    results=[candidate.fit(problem,start) for start in STARTS]
    assert all(r['passed'] and not r['optimizer_started'] for r in results)
    assert all(r['completion_method']=='algebraic_near_zero_certificate' for r in results)
    for result in results:
        assert result['calls']==4 and result['rms_mps2']<=1e-12
        assert result['cost_lower_bound']==0. and result['feasible_cost_upper_bound']>=0.
        assert not result['global_optimum_established']


def test_temporal_disagreement_is_not_hidden_by_matching_a_mean():
    body=np.tile([0.,0.,-9.81],(20,1));body[::2,2]+=.01
    body[1::2,2]-=.01;force=np.tile([0.,0.,-9.81],(20,1))
    result=candidate.fit(Problem(body,force,LIMITS),np.zeros(7))
    assert result['optimizer_started']
    assert result['completion_method']=='bounded_least_squares'
    assert result['calls']<=404 and result['rms_mps2']>1e-4


def test_infeasible_gain_is_rejected_without_clipping():
    problem=Problem(np.tile([0.,0.,-15.],(12,1)),np.tile([0.,0.,-9.81],(12,1)),LIMITS)
    result=candidate.fit(problem,np.zeros(7))
    assert result['optimizer_started'] and result['certificate_rejection']=='gain outside bounds'


@pytest.mark.parametrize('name',FIXTURES)
def test_original_independent_controls_keep_the_same_acceptance(name):
    body,force,_=fixture(name);results=[candidate.fit(Problem(body,force,LIMITS),start) for start in STARTS]
    assert all(r['passed'] and r['rms_mps2']<=1e-7 for r in results)
    assert max(r['calls'] for r in results)<=404


@pytest.mark.parametrize('start',[np.full(7,1.01),np.ones(6),np.full(7,np.nan)])
def test_bad_requested_start_is_rejected_even_if_a_certificate_exists(start):
    force=np.tile([0.,0.,-9.81],(12,1))
    with pytest.raises(ValueError):candidate.fit(Problem(force,force,LIMITS),start)
