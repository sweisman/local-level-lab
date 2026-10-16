# SPDX-License-Identifier: AGPL-3.0-or-later
from types import SimpleNamespace
import numpy as np
import pytest


def module():
    from lll import ilvis0_timing_probes
    return ilvis0_timing_probes


class Problem:
    gps=np.zeros((3,3));gps_times=np.array([.013,.023,.033])
    ends=np.cumsum(np.full(12,.005))
    bounds=SimpleNamespace(active=('time_offset',),limits={'time_offset':.15})
    def prediction_tangent(self,u,model):
        t=u[0]*.15
        return np.tile([0.,0.,2*t+t*t],(3,1)),np.tile([[0.],[0.],[(2+2*t)*.15]],(3,1)),0
    def whiten(self,difference):return np.asarray(difference).ravel()


def test_smooth_derivative_and_exact_finite_call_count():
    calls=[]
    def call(fn,*args):calls.append(1);return fn(*args)
    r=module().inspect(Problem(),[0.],'control',call,correction=[.01])
    assert len(calls)==12
    assert r['center_repeat_maximum_neu_m']==[0.,0.,0.]
    assert all(p['centered_derivative_relative_error']<1e-10 for p in r['time_probes'])
    assert r['time_probes'][-1]['minus_changed_packet_epochs']==3
    assert r['time_probes'][-1]['plus_changed_packet_epochs']==3
    assert r['coupled_probes'][0]['fraction']==1.
    assert r['coupled_probes'][1]['fraction']==.5
    assert r['original_labels_changed'] is False


def test_incorrect_derivative_is_exposed_without_relabeling():
    class Wrong(Problem):
        def prediction_tangent(self,u,model):
            y,j,b=super().prediction_tangent(u,model);return y,j*.5,b
    r=module().inspect(Wrong(),[0.],'control',lambda fn,*args:fn(*args))
    assert r['time_probes'][1]['centered_derivative_relative_error']==pytest.approx(1.)
    assert r['scientific_decision']=='abstain'


def test_infeasible_probe_fails_before_any_native_call():
    calls=[]
    with pytest.raises(ValueError,match='feasible'):
        module().inspect(Problem(),[.99],'control',lambda fn,*args:calls.append(1))
    assert calls==[]


def test_boundary_uses_left_interval():
    r=module().packet_context(Problem(),[0.])
    assert r['minimum_boundary_distance_s']==pytest.approx(.002)
    p=Problem();p.gps_times=np.array([.005,.010,.015])
    assert module().packet_context(p,[0.])['packet_indices']==[0,1,2]


def test_small_longitude_differences_preserve_precision():
    a=np.array([[0.,1e-17,0.]])
    assert module().difference(a,np.zeros((1,3)))[0,1]==1e-17
