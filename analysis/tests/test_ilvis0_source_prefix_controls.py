# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_fixed_prefix_work_and_cases_are_defined_before_outputs():
    from lll.ilvis0_source_prefix_controls import recipe,case
    r=recipe()
    assert r['identities']==18 and r['packets']==16 and r['prefix_packets']==[2,8]
    assert r['source_steps_per_identity']==174 and r['fork_attempts_per_identity']==9
    for model in range(3):
        for profile in (False,True):
            c,z,lo,hi=case(model,profile)
            assert len(c['dt'])==16 and c['configuration']['model']==model
            assert c['configuration']['profile']==profile
            assert z.shape==lo.shape==hi.shape==(27,) and np.all(lo<=z) and np.all(z<=hi)
            assert lo[25]<z[25]<hi[25]


def test_all_array_columns_and_numeric_metadata_must_match_exactly():
    from lll.ilvis0_source_prefix_controls import compare
    before={'values':np.ones((2,2,3)),'jacobian':np.zeros((2,2,3,27)),
        'state_bytes':100,'packet_index':3}
    after=dict(before,state_bytes=200)
    assert compare(before,after)==2
    after['jacobian']=after['jacobian'].copy();after['jacobian'][1,1,2,26]=1e-100
    with pytest.raises(ValueError):compare(before,after)


def test_actual_source_check_uses_complete_runner_reservations(tmp_path):
    from collections import Counter
    from lll.ilvis0_source_prefix import load_kernels
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_prefix_controls import check,limits
    kernels,_=load_kernels(tmp_path);original,_=load_stream(tmp_path);counts=Counter();calls=[];saved={}
    def reserve(**values):
        counts.update(values)
        assert all(counts[k]<=v for k,v in limits().items())
    def charge(**values):
        # Shared TaskContext requires a complete diagnostic operation, never a
        # standalone packet_visits count with no native or diagnostic call.
        assert values=={'bound_calls':1,'bound_steps':1}
        calls.append(values)
    result=check('reference',0,False,kernels=kernels,cold_kernels={'reference':original},
        reserve=reserve,charge=charge,save=lambda n,v:saved.update({n:v}))
    assert result['passed'] and counts==limits() and len(calls)==174
    assert len(saved['source-comparisons.json'])==6
