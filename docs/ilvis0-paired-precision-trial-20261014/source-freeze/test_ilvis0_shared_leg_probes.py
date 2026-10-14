# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer linear controls for the finite diagnostic, without archive data."""
import numpy as np
import pytest

import ilvis0_shared_leg_probes as probes


class LinearProblem:
    gps = np.zeros((4,3))
    cholesky = np.eye(12)

    def whiten(self, difference):
        return np.asarray(difference).ravel()

    def predict(self, point, model):
        return np.tile(point,(4,1))

    def prediction_tangent(self, point, model):
        return self.predict(point,model),np.tile(np.eye(3),(4,1)),0


def test_exactly_ten_calls_and_fixed_probe_fractions():
    calls=[]
    def call(kind,function,*args):
        calls.append(kind)
        return function(*args)
    result=probes.probe_endpoint(LinearProblem(),np.array([.2,-.3,.4]),'control',call)
    assert len(calls)==10
    assert calls.count('tangent')==5
    assert calls.count('value')==5
    assert [r['fraction'] for r in result['probes']]==[1.,.5,.25]
    assert result['probes'][0]['tangent_cost']==pytest.approx(0.,abs=1e-25)
    assert result['probes'][1]['tangent_cost']==pytest.approx(result['center_tangent_cost']*.25)
    assert result['probes'][2]['tangent_cost']==pytest.approx(result['center_tangent_cost']*.75**2)
    assert result['value_tangent_difference']['maximum_neu_m']==[0.,0.,0.]
    assert result['tangent_repeat']['maximum_neu_m']==[0.,0.,0.]


def test_value_disagreement_is_reported_not_hidden():
    class DifferentValue(LinearProblem):
        def prediction_tangent(self,point,model):
            return np.tile(point,(4,1)),np.tile(np.eye(3),(4,1)),0
        def predict(self,point,model):
            answer=np.tile(point,(4,1));answer[:,2]+=1e-5
            return answer
    result=probes.probe_endpoint(DifferentValue(),np.array([.2,-.3,.4]),'control',lambda kind,fn,*args:fn(*args))
    assert result['value_tangent_difference']['maximum_neu_m'][2]==pytest.approx(1e-5)
    assert result['center_value_tangent_cost_relative_difference']>0


def test_pre_call_budget_stops_work_before_evaluation():
    count=0
    def call(kind,function,*args):
        nonlocal count
        if count==4:
            raise RuntimeError('budget')
        count+=1
        return function(*args)
    with pytest.raises(RuntimeError,match='budget'):
        probes.probe_endpoint(LinearProblem(),np.array([.2,-.3,.4]),'control',call)
    assert count==4
