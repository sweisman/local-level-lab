"""Finite physical-Jacobian receiver whitening gate."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest


def test_native_equivalence_task_has_one_exact_charge():
    from lll.ilvis0_structured_receiver_native_study import tasks
    grid=tasks(dict(packets=24000,epochs=120))
    assert len(grid)==1
    assert grid[0]['limits']['native_calls']==1
    assert grid[0]['limits']['packet_visits']==24000*120
    with pytest.raises(ValueError):tasks(dict(packets=0,epochs=120))


def test_preparation_stages_no_scoring_receiver_positions(monkeypatch):
    from lll.ilvis0_structured_receiver_native_study import CASE,stage_training
    segment=CASE.split('-')[0]
    class Prior:
        def __init__(self):self.keys=[]
        def input(self,key,*,raw=False):
            self.keys.append(key)
            assert 'scoring' not in key
            if key=='recipe':return dict(gyro_offset_dph=1.,
                training_weight='h1_v3_tau60',independent_neu_m=[.3,.3,.7])
            if key.endswith('-common'):
                return gzip.compress(json.dumps(dict(times=[0.,10.,20.],
                    values=[[0.]*15]*3)).encode())
            return dict(training_gps=[[.5,.1,1000.]]*3,cut_epoch=3)
    def fake_training(times,placeholder,values,offset,*,cut):
        assert cut==3
        return times[:cut],placeholder[:cut],values
    monkeypatch.setattr('lll.ilvis0_prediction.training_inputs',fake_training)
    arrays=stage_training(Prior(),epochs=3)
    assert arrays['t'].shape==(3,)
    assert arrays['v'].shape==(3,15)
    assert arrays['source_keys']==['recipe',segment+'-common',
                                   segment+'-outer-training']


def test_native_source_closure_contains_c_and_cpp():
    from lll.ilvis0_structured_receiver_native_study import sources
    names=set(sources(Path(__file__).resolve().parents[2]))
    assert 'analysis/lll/ilvis0_native.c' in names
    assert 'analysis/lll/ilvis0_tangent.cpp' in names


def test_whitening_comparison_rejects_changed_jacobian():
    from lll.ilvis0_structured_receiver_native_study import compare_whitening
    residual=np.array([.1,.2,.3])
    jac=np.eye(3)
    good=compare_whitening(residual,jac,residual.copy(),jac.copy(),
                           dense_logdet=1.,structured_logdet=1.)
    assert good['passed'] is True
    bad=compare_whitening(residual,jac,residual.copy(),jac*2,
                          dense_logdet=1.,structured_logdet=1.)
    assert bad['passed'] is False
