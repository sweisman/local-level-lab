# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import io

import numpy as np
import pytest


def fixture(columns=26,*,initial=0.,nonstationary=False):
    point=np.zeros(columns);point[0]=initial
    fit=dict(normalized_parameters=point.tolist(),active_parameters=[f'p{i}' for i in range(columns)],
        converged=False,residual_sum_squares=1.)
    weight=1. if nonstationary else 1e-6
    def evaluate(u):
        residual=np.zeros(3*(columns+1));residual[0]=1.;residual[1]=.9*weight+weight*u[0]
        jac=np.zeros((len(residual),columns));jac[1,0]=weight
        return residual,jac,0
    return fit,evaluate


@pytest.mark.parametrize('columns',(26,27))
def test_resolution_probe_preserves_fixed_point_labels_columns_and_exact_charge_order(columns):
    from lll.stopping_resolution import probe
    fit,evaluate=fixture(columns);before=copy.deepcopy(fit);events=[];saved={};binary={}
    def reserve(**v):events.append(('charge',v))
    def counted(u):
        assert events and events[-1][0]=='charge'
        events.append(('evaluate',u.copy()));return evaluate(u)
    r=probe(fit,evaluate=counted,physical_step=lambda d:d.reshape(-1,3),packet_count=600,epoch_count=columns+1,
        reserve=reserve,save=lambda k,v:saved.__setitem__(k,v),save_bytes=lambda k,v:binary.__setitem__(k,v),check_continue=lambda:None)
    assert r['native_calls']==10 and r['optimizer_starts']==0 and not r['labels_changed']
    assert r['saved_converged'] is False and r['scientific_decision']=='abstain'
    assert fit==before and r['correction_available'] and r['all_columns_retained']
    assert len(events)==20
    assert all(events[i][1]==dict(native_calls=1,packet_visits=600*(columns+1)) for i in range(0,20,2))
    assert [v['fraction'] for v in saved['probe.json']['sweeps']]==[None,None,1.,.5,.25,.125,-.125,-.25,-.5,-1.]
    assert len(binary)==10
    with np.load(io.BytesIO(binary['sweep-00.npz']),allow_pickle=False) as a, np.load(io.BytesIO(binary['sweep-01.npz']),allow_pickle=False) as b:
        assert a['point'].shape==(columns,)
        assert a['jacobian'].shape==(3*(columns+1),columns)
        assert np.array_equal(a['point'],b['point']) and np.array_equal(a['residual'],b['residual'])


def test_resolution_probe_records_feasible_clipping_and_duplicate_points():
    from lll.stopping_resolution import probe
    fit,evaluate=fixture(initial=1.);saved={};binary={}
    probe(fit,evaluate=evaluate,physical_step=lambda d:d.reshape(-1,3),packet_count=600,epoch_count=27,
        reserve=lambda **v:None,save=lambda k,v:saved.__setitem__(k,v),save_bytes=lambda k,v:binary.__setitem__(k,v),check_continue=lambda:None)
    with np.load(io.BytesIO(binary['sweep-09.npz']),allow_pickle=False) as a, np.load(io.BytesIO(binary['sweep-00.npz']),allow_pickle=False) as b:
        assert np.all(abs(a['point'])<=1.) and np.array_equal(a['point'],b['point'])
    assert saved['probe.json']['sweeps'][-1]['clipped']


def test_resolution_probe_preserves_unavailable_correction_without_extra_sweeps():
    from lll.stopping_resolution import probe
    fit,evaluate=fixture(nonstationary=True);calls=[];saved={}
    r=probe(fit,evaluate=evaluate,physical_step=lambda d:d.reshape(-1,3),packet_count=600,epoch_count=27,
        reserve=lambda **v:calls.append(v),save=lambda k,v:saved.__setitem__(k,v),save_bytes=lambda k,v:None,check_continue=lambda:None)
    assert len(calls)==r['native_calls']==2 and not r['correction_available']
    assert saved['probe.json']['shared_probe']['reason']=='not_stationary'
    assert not r['saved_converged'] and not r['labels_changed']


@pytest.mark.parametrize('bad',('nonfinite','missing_column'))
def test_resolution_probe_charges_and_rejects_malformed_native_results(bad):
    from lll.stopping_resolution import probe
    fit,evaluate=fixture();calls=[]
    def broken(u):
        assert len(calls)==1
        r,j,b=evaluate(u)
        if bad=='nonfinite':r[0]=np.nan
        else:j=j[:,:-1]
        return r,j,b
    with pytest.raises(ValueError):
        probe(fit,evaluate=broken,physical_step=lambda d:d.reshape(-1,3),packet_count=600,epoch_count=27,
            reserve=lambda **v:calls.append(v),save=lambda k,v:None,save_bytes=lambda k,v:None,check_continue=lambda:None)
    assert len(calls)==1


@pytest.mark.parametrize('bad',('point','duplicate_columns','cost'))
def test_resolution_probe_rejects_invalid_saved_fit_before_charging(bad):
    from lll.stopping_resolution import probe
    fit,evaluate=fixture();calls=[]
    if bad=='point':fit['normalized_parameters'][0]=1.1
    elif bad=='duplicate_columns':fit['active_parameters'][1]=fit['active_parameters'][0]
    else:fit['residual_sum_squares']=float('inf')
    with pytest.raises(ValueError):
        probe(fit,evaluate=evaluate,physical_step=lambda d:d.reshape(-1,3),packet_count=600,epoch_count=27,
            reserve=lambda **v:calls.append(v),save=lambda k,v:None,save_bytes=lambda k,v:None,check_continue=lambda:None)
    assert not calls
