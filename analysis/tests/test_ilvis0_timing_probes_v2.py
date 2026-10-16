# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from test_ilvis0_timing_probes import Problem


def module():
    from lll import ilvis0_timing_probes_v2
    return ilvis0_timing_probes_v2


class BoundProblem(Problem):
    def prediction_tangent(self,u,model):
        assert np.all(abs(u)<=1), 'native input outside unchanged bounds'
        return super().prediction_tangent(u,model)


def test_one_ulp_coupled_overshoot_is_recorded_and_snapped():
    calls=[]
    def call(fn,*args):calls.append(1);return fn(*args)
    # The roundoff is on a separate nuisance coordinate, never on the time probes.
    p=BoundProblem()
    from types import SimpleNamespace
    p.bounds=SimpleNamespace(active=('time_offset','gyro_bias_x'),limits={'time_offset':.15})
    original=p.prediction_tangent
    def tangent(u,model):
        y,j,b=original(u,model);return y,np.column_stack((j,np.zeros(len(j)))),b
    p.prediction_tangent=tangent
    r=module().inspect(p,[0.,-1.],'control',call,correction=[.01,-np.finfo(float).eps])
    assert len(calls)==12
    assert len(r['coupled_roundoff_adjustments'])==1
    adjustment=r['coupled_roundoff_adjustments'][0]
    assert adjustment['parameter']=='gyro_bias_x'
    assert adjustment['computed_value']==-1.-np.finfo(float).eps
    assert adjustment['evaluated_value']==-1.
    assert adjustment['fraction']==1.
    assert r['original_labels_changed'] is False


@pytest.mark.parametrize('step',[1e-10,float('nan')])
def test_material_or_nonfinite_coupled_overshoot_remains_rejected(step):
    calls=[]
    with pytest.raises(ValueError,match='feasible'):
        module().inspect(Problem(),[0.],'control',lambda fn,*args:calls.append(1),correction=[1.+step])
    assert not calls


def test_infeasible_center_is_never_snapped():
    calls=[]
    with pytest.raises(ValueError,match='feasible'):
        module().inspect(Problem(),[1.+np.finfo(float).eps],'control',lambda fn,*args:calls.append(1))
    assert not calls
