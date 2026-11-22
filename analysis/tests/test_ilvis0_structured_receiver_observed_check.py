"""Saved-prefix equivalence uses training receiver positions only."""
import gzip
import json

import numpy as np


def test_prefix_loader_never_opens_scoring_input():
    from lll.ilvis0_structured_receiver_observed_check import CASE,load_prefix
    segment=CASE.split('-')[0]
    class Prior:
        def __init__(self):self.inputs=[]
        def input(self,key,*,raw=False):
            self.inputs.append(key)
            assert 'scoring' not in key
            if key=='recipe':return dict(training_weight='formal_only',
                                         independent_neu_m=[.3,.3,.7])
            if key==segment+'-common':
                return gzip.compress(json.dumps(dict(times=[0,1,2],
                    values=[[0]*15]*3)).encode())
            return dict(training_gps=[[.5,.1,1000.],[.5,.1,1000.],
                                      [.5,.1,1000.]],cut_epoch=3)
        def artifact(self,identity,name):
            assert identity==CASE and name=='forecast.json'
            return dict(coordinates=[[.5,.1,1000.]]*3,times=[0,1,2],
                        training_epochs=3)
    prior=Prior()
    result=load_prefix(prior,epochs=3)
    assert prior.inputs==['recipe',segment+'-common',
                          segment+'-outer-training']
    assert result['times'].shape==(3,)
    assert result['receiver'].shape==(3,3)


def test_real_scale_prefix_comparison_has_finite_equivalent_outputs():
    from lll.ilvis0_structured_receiver_observed_check import compare_prefix
    t=np.array([0.,1.,3.,4.])
    receiver=np.array([[.5,.1,1000.],[.50001,.10002,1001.],
                       [.50003,.10005,1001.],[.50004,.10007,1002.]])
    predicted=receiver.copy();predicted[:,0]+=[0,1e-7,2e-7,1e-7]
    result=compare_prefix(t,receiver,predicted,
        independent_neu_m=[.3,.3,.7],assumption_name='h1_v3_tau60')
    assert result['epochs']==4
    assert result['surrogate_columns']==26
    assert result['withheld_positions_read'] is False
    assert result['maximum_whitened_residual_difference']<1e-7
    assert result['maximum_whitened_design_difference']<1e-7
