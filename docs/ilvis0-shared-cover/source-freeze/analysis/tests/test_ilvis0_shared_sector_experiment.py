# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from lll import ilvis0_shared_sector_experiment as experiment
from lll.ilvis0_orientation_cover import sector
from lll.ilvis0_shared_reference_terms import ReferenceErrors,SharedCoefficients
from lll.ilvis0_shared_native import SharedEnclosure


def test_fixed_common_block_and_training_then_future_evidence_order():
    box=sector(4);config=dict(initial_c=np.zeros(3),initial_r=np.eye(3),limits=np.ones(27),
        model=0,profile=False,source_id='sector-interface-control')
    reference=ReferenceErrors(config,box['lower'],box['upper'],box['center'])
    task=dict(identity='control',kind='sector',sector=4,model=0,profile=False,packets=400,
        training_times=[0.,1.],future_time=2.)
    events=[];native_calls=[]
    def native(times,point):
        if len(times)==1 and times[0]==2.:assert events==['training','future']
        native_calls.append(np.array(point));jac=np.zeros((len(times),3,27))
        jac[:,0,0]=1/6371000.;jac[:,0,1]=np.array(times)/6371000.
        return np.einsum('tij,j->ti',jac,point),jac
    def bound(t,lo,hi,value):
        np.testing.assert_array_equal(reference.center,box['center'])
        extra=np.zeros((3,6));extra[0,0]=1/6371000.
        return SharedEnclosure(value,np.zeros(3),SharedCoefficients(extra,reference.binding),
            dict(source_id=reference.source_id,time_s=t,normalized_center=reference.center.tolist(),
                bound_lower=box['lower'].tolist(),bound_upper=box['upper'].tolist()))
    def emit(label,value):events.append(label);assert value['parameter_count']==33
    result=experiment.evaluate(task,dict(configuration=config,truth=np.zeros(27)),
        reference=reference,native=native,bound=bound,emit=emit)
    assert result['passed'] and result['known_truth_retained'] and len(native_calls)==3
    np.testing.assert_array_equal(native_calls[1],box['center'])
    assert result['contraction']['lower'].shape==(33,)
