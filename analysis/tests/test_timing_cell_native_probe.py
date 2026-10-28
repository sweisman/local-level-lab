# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import numpy as np
import pytest


def fixture():
    names=['time_offset']+['p'+str(i) for i in range(26)]
    point=np.zeros(27);residual=np.ones(6);jacobian=np.zeros((6,27))
    proposals=[]
    for i in range(6):
        candidate=point.copy();candidate[0]=(.01 if i%2 else -.01)
        proposals.append(dict(index=i,active=list(names),point=candidate.tolist(),
            lower=(-np.ones(27)).tolist(),upper=np.ones(27).tolist(),predicted_cost=6.,
            predicted_residual=residual.tolist()))
    options=dict(active=names,proposals=proposals,expected_cost=6.,
        expected_linearization=dict(residual=residual.tolist(),jacobian=jacobian.tolist()),
        bounds=(-np.ones(27),np.ones(27)),maximum_evaluations=8)
    return point,options


def test_native_proposals_charge_before_every_call_keep_columns_and_convert_actual_difference():
    from lll.timing_cell_native_probe import probe
    point,options=fixture();charged=[];calls=[];converted=[]
    def evaluate(p,*,fresh):
        assert fresh and len(charged)==len(calls)+1
        calls.append(p.copy());r=np.ones(6)+p[0]**2
        j=np.zeros((6,27));j[:,0]=2*p[0]
        return r,j,0
    def physical(delta):
        converted.append(delta.copy());return delta.reshape(2,3)*2
    result=probe(evaluate,point,reserve=lambda **k:charged.append(k),check_continue=lambda:None,
        physical_step=physical,**options)
    assert len(calls)==result['evaluations']==8 and len(converted)==6
    assert len(result['proposals'])==6 and all(len(v['jacobian'][0])==27 for v in result['proposals'])
    assert all(v=={'evaluations':1} for v in charged)
    assert not result['labels_changed'] and result['stopping_probe']['passed'] is None
    row=result['proposals'][0]
    assert row['position_rms_neu_m']==pytest.approx([.0002]*3)
    assert row['cost_stable'] is False and row['position_stable'] is True
    assert row['actual_cost']>row['predicted_cost']
    assert row['residual_remainder_norm']==pytest.approx(np.sqrt(6)*.0001)


@pytest.mark.parametrize('bad',['cap','outside_cell','columns','nonfinite','repeat','baseline','physical'])
def test_native_proposals_reject_incomplete_infeasible_or_nonreproducible_inputs(bad):
    from lll.timing_cell_native_probe import probe
    point,options=fixture();options=copy.deepcopy(options);calls=[]
    if bad=='cap':options['maximum_evaluations']=7
    if bad=='outside_cell':options['proposals'][0]['upper'][0]=-.1
    if bad=='columns':options['proposals'][0]['active'].reverse()
    if bad=='nonfinite':options['proposals'][0]['point'][1]=float('nan')
    if bad=='baseline':options['expected_cost']=5.
    def evaluate(p,*,fresh):
        calls.append(1);r=np.ones(6)
        if bad=='repeat' and len(calls)>1:r[0]+=1
        return r,np.zeros((6,27)),0
    with pytest.raises(ValueError):
        probe(evaluate,point,reserve=lambda **k:None,check_continue=lambda:None,
            physical_step=lambda d:np.zeros((1,2) if bad=='physical' else (2,3)),**options)
    if bad in ('cap','outside_cell','columns','nonfinite'):assert not calls


def test_native_proposals_cooperative_stop_precedes_charge_and_evaluation():
    from lll.timing_cell_native_probe import probe
    point,options=fixture();calls=[]
    def stop():raise RuntimeError('cooperative stop')
    with pytest.raises(RuntimeError,match='cooperative stop'):
        probe(lambda *a,**k:calls.append('evaluate'),point,reserve=lambda **k:calls.append('charge'),
            check_continue=stop,physical_step=lambda d:d,**options)
    assert not calls
