# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def cells(center=0.):
    return [dict(lower=-1.,upper=center,anchor=(-1+center)/2),
        dict(lower=float(np.nextafter(center,1.)),upper=1.,anchor=(1+center)/2)]


def curve(kind,center=0.,columns=1):
    b=5e-5
    def evaluate(point,*,fresh=False):
        assert fresh
        x=point[0];sign=-1 if x<center else 1
        if kind=='smooth':r=np.array([15.,b*(x-center)]);j=np.zeros((2,columns));j[1,0]=b
        else:
            value=abs(x-center) if kind=='kink' else x
            r=np.array([15.+b*value]);j=np.zeros((1,columns));j[0,0]=b*(sign if kind=='kink' else 1)
        return r,j,0
    return evaluate


@pytest.mark.parametrize('kind,center',[('smooth',0.),('kink',0.),('kink',.25)])
def test_timing_verifier_accepts_known_minima_on_every_side(kind,center):
    from lll.ilvis0_timing_stop import verify
    evaluate=curve(kind,center);point=np.array([center]);r,j,_=evaluate(point,fresh=True);charges=[]
    result=verify(point,r,j,evaluate,lambda d:np.c_[d,d*0,d*0],active=['time_offset'],
        cells=cells(center),reserve_linear=lambda:charges.append(1))
    assert result['passed'] and len(result['cells'])==len(charges)==2
    assert all(row['passed'] for row in result['cells'])
    assert result['fresh_evaluations']==5 and not result['confidence_calibrated']


def test_timing_verifier_rejects_nonminimum_even_if_one_side_looks_stable():
    from lll.ilvis0_timing_stop import verify
    evaluate=curve('nonminimum');point=np.array([0.]);r,j,_=evaluate(point,fresh=True)
    result=verify(point,r,j,evaluate,lambda d:np.c_[d,d*0,d*0],active=['time_offset'],
        cells=cells(),reserve_linear=lambda:None)
    assert not result['passed'] and len(result['cells'])==2
    assert any(row['passed'] for row in result['cells'])
    assert any(not row['passed'] for row in result['cells'])


def test_timing_verifier_retains_all_27_columns_and_fixed_timing_nuisance_solve():
    from lll.ilvis0_timing_stop import verify
    evaluate=curve('kink',columns=27);point=np.zeros(27);r,j,_=evaluate(point,fresh=True)
    one=[dict(lower=0.,upper=0.,anchor=0.)]
    result=verify(point,r,j,evaluate,lambda d:np.c_[d,d*0,d*0],
        active=['time_offset']+['p'+str(i) for i in range(26)],cells=one,reserve_linear=lambda:None)
    assert result['passed'] and len(result['cells'][0]['jacobian'][0])==27
    assert result['cells'][0]['linear']['fixed_parameters']==['time_offset']


def test_timing_verifier_preserves_physical_gate_even_with_small_cost_change():
    from lll.ilvis0_timing_stop import verify
    def evaluate(p,*,fresh=False):return np.array([15.+1e-10*p[0]]),np.array([[1e-10]]),0
    point=np.array([0.]);r,j,_=evaluate(point,fresh=True)
    result=verify(point,r,j,evaluate,lambda d:np.c_[1e9*d,d*0,d*0],
        active=['time_offset'],cells=cells(),reserve_linear=lambda:None)
    assert not result['passed']
    assert any(not v['position_stable'] for v in result['cells'])


def test_timing_verifier_keeps_original_stationarity_gate_even_at_sharp_minimum():
    from lll.ilvis0_timing_stop import verify
    def forbidden(*a,**k):raise AssertionError('nonstationary point must not pass through another exit')
    result=verify(np.array([0.]),np.array([15.]),np.array([[.01]]),forbidden,forbidden,
        active=['time_offset'],cells=cells(),reserve_linear=forbidden)
    assert not result['passed'] and result['reason']=='not_stationary'


@pytest.mark.parametrize('bad',['gap','overflow','columns','repeat','charge'])
def test_timing_verifier_guards_incomplete_cells_repeats_and_charge_before_solve(bad):
    from lll.ilvis0_timing_stop import verify
    evaluate=curve('kink');point=np.array([0.]);r,j,_=evaluate(point,fresh=True);boxes=cells();names=['time_offset']
    if bad=='gap':boxes[1]['lower']=.1
    elif bad=='overflow':boxes*=9
    elif bad=='columns':names=['wrong']
    elif bad=='repeat':
        def evaluate(p,*,fresh=False):return r+1,j,0
    def reserve():
        if bad=='charge':raise RuntimeError('linear allowance exhausted')
    if bad=='repeat':
        result=verify(point,r,j,evaluate,lambda d:np.c_[d,d*0,d*0],active=names,cells=boxes,reserve_linear=reserve)
        assert not result['passed'] and result['reason']=='baseline_not_repeatable'
    else:
        with pytest.raises(RuntimeError if bad=='charge' else ValueError):
            verify(point,r,j,evaluate,lambda d:np.c_[d,d*0,d*0],active=names,cells=boxes,reserve_linear=reserve)


@pytest.mark.parametrize('center',[0.,.25])
@pytest.mark.parametrize('start',[-.8,0.,.6,.9])
def test_complete_timing_optimizer_recovers_independent_kink_predictions(center,start):
    from types import SimpleNamespace
    from lll.ilvis0_timing_stop import fit_candidate
    class Problem:
        calls=0
        bounds=SimpleNamespace(active=['time_offset'],limits={'time_offset':.01},decode=lambda u:dict(time_offset=float(u[0])))
        dt=np.array([.5+.01*center,.5,.5]);gps_times=np.array([.5])
        def residual_tangent(self,u,model):
            self.calls+=1
            return curve('kink',center)(u,fresh=True)
    problem=Problem();charges=[]
    fit=fit_candidate(problem,'control',start=[start],maximum_evaluations=200,
        physical_step=lambda d:np.c_[d,d*0,d*0],reserve_linear=lambda:charges.append(1))
    assert fit['converged'] and problem.calls==fit['evaluations']<=200
    assert fit['residual_sum_squares']==pytest.approx(225.,abs=3e-6)
    assert 5e-5*abs(fit['normalized_parameters'][0]-center)<=1e-7
    assert len(charges)==fit['linear_solves'] and charges
    assert fit['stability_probe']['passed'] and not fit['confidence_calibrated']
