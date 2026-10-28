# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer bounded probes, with failures preserved and no optimization."""
import numpy as np
import pytest


def test_matched_probe_keeps_all_columns_and_charges_each_evaluation():
    from lll.timing_arithmetic_probe import probe,MODES
    active=['extra','gyro_bias_z','time_offset'];point=np.array([.2,1.,-1.]);mode=[];charged=[]
    matrix=np.array([[1.,2.,3.],[4.,5.,6.],[7.,8.,10.],[1.,3.,5.]])
    def evaluate(p,fresh=False):return matrix@p,matrix,0
    value=matrix@point
    result=probe(evaluate,point,active=active,saved_cost=float(value@value),
        select=mode.append,reserve=lambda **v:charged.append(v),check_continue=lambda:None,
        bounds=(-np.ones(3),np.ones(3)))
    assert mode==list(MODES)
    assert result['evaluations']==len(charged)==52
    assert result['stopping_probe']['not_executed']
    assert result['labels_changed'] is False
    assert all(len(v['jacobian'][0])==3 for v in result['settings'])
    assert max(s['error_norm'] for v in result['settings'] for c in v['derivatives'] for s in c['steps'])<1e-8
    assert {c['steps'][0]['stencil'] for c in result['settings'][0]['derivatives']}=={'forward','backward'}


def test_probe_keeps_mismatch_as_an_outcome():
    from lll.timing_arithmetic_probe import probe
    matrix=np.eye(2);point=np.zeros(2)
    result=probe(lambda u,fresh=False:(u,2*matrix,0),point,
        active=['gyro_bias_z','time_offset'],saved_cost=0.,select=lambda v:None,
        reserve=lambda **v:None,check_continue=lambda:None,bounds=(-np.ones(2),np.ones(2)))
    assert all(c['steps'][0]['error_norm']>.9 for s in result['settings'] for c in s['derivatives'])
    assert result['nonlinear_fit_starts']==0


@pytest.mark.parametrize('bad',('cost','columns','budget','infeasible','charge'))
def test_probe_rejects_invalid_work_before_an_extra_evaluation(bad):
    from lll.timing_arithmetic_probe import probe
    point=np.array([0.,-1.]);calls=[]
    def evaluate(u,fresh=False):calls.append(u);return u,np.eye(2),0
    def reserve(**v):
        if bad=='charge':raise RuntimeError('denied')
    if bad=='infeasible':point[0]=2.
    with pytest.raises((ValueError,RuntimeError)):
        probe(evaluate,point,active=['gyro_bias_z','wrong' if bad=='columns' else 'time_offset'],
            saved_cost=2. if bad=='cost' else 1.,select=lambda v:None,
            reserve=reserve,check_continue=lambda:None,bounds=(-np.ones(2),np.ones(2)),
            maximum_evaluations=1 if bad=='budget' else 64)
    assert len(calls)<=1


@pytest.mark.parametrize('columns',(26,27))
def test_full_precision_probe_retains_every_column_and_original_failed_label(columns):
    from lll.timing_arithmetic_probe import full_precision_probe
    point=np.zeros(columns);names=[f'p{i}' for i in range(columns)];mode=[];charges=[];calls=[]
    def evaluate(u,fresh=False):
        calls.append(u.copy());return u.copy(),np.eye(columns),0
    def frozen(u,r,j,e):
        e(u.copy(),fresh=True)
        return dict(passed=False,actual_cost_change=1e-6)
    result=full_precision_probe(evaluate,point,active=names,saved_cost=0.,select=mode.append,
        reserve=lambda **v:charges.append(v),check_continue=lambda:None,
        bounds=(-np.ones(columns),np.ones(columns)),frozen_probe=frozen)
    assert mode==['baseline','compensated']
    assert result['evaluations']==len(charges)==len(calls)==5+6*columns
    assert len(result['derivatives'])==columns and result['columns']==columns
    assert result['stopping_probe']['passed'] is False and result['labels_changed'] is False
    assert result['baseline']['cost']==0. and len(result['baseline']['jacobian'][0])==columns
    assert result['maximum_evaluations']==171


def test_full_precision_probe_denial_and_bad_replay_stop_before_candidate():
    from lll.timing_arithmetic_probe import full_precision_probe
    u=np.zeros(2);modes=[];calls=[]
    def evaluate(v,fresh=False):calls.append(v);return v,np.eye(2),0
    options=dict(active=['a','b'],select=modes.append,check_continue=lambda:None,
        bounds=(-np.ones(2),np.ones(2)),frozen_probe=lambda *a:None)
    def deny(**v):raise RuntimeError('denied')
    with pytest.raises(RuntimeError,match='denied'):
        full_precision_probe(evaluate,u,saved_cost=0.,reserve=deny,**options)
    assert not calls
    modes.clear()
    with pytest.raises(ValueError,match='baseline'):
        full_precision_probe(evaluate,u,saved_cost=1.,reserve=lambda **v:None,**options)
    assert modes==['baseline'] and len(calls)==1
