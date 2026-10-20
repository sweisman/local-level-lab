# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from lll import ilvis0_sector_experiment as experiment


def run(oracle_shift):
    calls=[];emitted={};matrix=np.zeros((3,27));matrix[:,:3]=np.eye(3)/6371000.
    config=dict(initial_c=[0.,0.,0.]);case=dict(configuration=config,truth=np.zeros(27))
    task=dict(identity='fake',kind='orientation-sector',model=0,profile=False,sector=4,packets=400,
        training_times=[.2,.35,.6,.9,1.2,1.5],future_time=1.8)
    def native(times,point):
        calls.append(('native',len(calls)))
        result=np.asarray(times)[:,None]*np.array([1e-5,2e-5,.1])+matrix@point
        if sum(name=='native' for name,_ in calls)==4:
            assert 'future' in emitted
            result=result+np.array([oracle_shift/6371000.,0.,0.])
        return result,np.tile(matrix,(len(times),1,1))
    def bound(*args):return np.zeros(3)
    def emit(name,value):emitted[name]=value;calls.append((name,len(calls)))
    return experiment.evaluate(task,case,native=native,bound=bound,emit=emit),emitted,calls


def test_future_truth_cannot_change_region_center_constraints_or_bounds():
    normal,first,calls=run(0.);changed,second,_=run(100.)
    assert normal['passed'] and not changed['passed']
    for name in ('future_lower_m','future_upper_m','future_center'):
        np.testing.assert_array_equal(normal[name],changed[name])
    for name in ('design','lower','upper','inequality_design','inequality_upper'):
        np.testing.assert_array_equal(first['training']['constraints'][name],second['training']['constraints'][name])
    assert calls[-2][0]=='future' and calls[-1][0]=='native'
    assert first['future']['jacobian_m'].shape==(3,27)
    assert normal['parameter_count']==27 and normal['future_truth_evaluated_after_bounds']
