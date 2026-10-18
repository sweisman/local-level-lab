# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import numpy as np
import pytest
import ilvis0_profile_seeded_worker as worker


def inputs():
    names=['position_x','time_offset'];vm=dict(plan=dict(tasks=[]));vs=dict(results=[])
    gm=dict(plan=dict(tasks=[]));gs=dict(results=[],pair_repeatability=[])
    task=dict(segment_id='50f24131843071ae9312c082',case_id='bias1_unsubtracted',model='sphere_still')
    for role in ('primary','repeat'):
        for anchor,t in (('primary',-.1),('repeat',-.4)):
            identity=role+'::'+anchor
            vm['plan']['tasks'].append(dict(identity=identity,task=task,fit=dict(active_parameters=names),
                start_role=role,anchor_role=anchor,anchor_normalized=t,saved_result=dict(normalized_parameters=[.2,t])))
            vs['results'].append(dict(identity=identity,status='complete',conditional_verified=True,
                residual_sum_squares=10.+t*t,linearization_file='end.gz',linearization_sha256='x'))
        for fraction in (.25,.5,.75):
            t=(1-fraction)*-.1+fraction*-.4;identity=role+'::'+str(fraction)
            gm['plan']['tasks'].append(dict(identity=identity,task=task,start_role=role,anchor_normalized=t))
            gs['results'].append(dict(identity=identity,status='complete',conditional_converged=True,
                normalized_parameters=[.2,t],active_parameters=names,residual_sum_squares=10.+t*t,
                linearization_file='interior.gz',linearization_sha256='x'))
    gs['pair_repeatability']=[dict(fraction=f,agreement_passed=True,both_conditional_fits_passed=True) for f in (.25,.5,.75)]
    vs['pair_repeatability']=[dict(anchor_role=a,agreement_passed=True,both_conditional_verified=True) for a in ('primary','repeat')]
    controls=dict(plan=dict(tasks=[dict(kind='control',identity='c'+str(i),source_identity='c'+str(i),fit={}) for i in range(2)]))
    return gm,gs,vm,vs,controls


def test_five_sealed_points_per_start_and_two_fresh_controls():
    values=inputs();before=copy.deepcopy(values);plan=worker.make_plan(*values)
    assert plan['maximum_starts']==4 and plan['maximum_native_evaluations']==174
    assert sum(t['maximum_fit_calls']+t['maximum_diagnostic_calls'] for t in plan['tasks'])==174
    assert len(plan['tasks'])==4 and all(len(t['profiles'])==5 for t in plan['tasks'][2:])
    assert values==before


@pytest.mark.parametrize('change',['failed','missing','pair'])
def test_no_target_starts_from_partial_grid_evidence(change):
    values=inputs();gm,gs,vm,vs,controls=values
    if change=='failed':gs['results'][0]['conditional_converged']=False
    if change=='missing':vs['results'].pop()
    if change=='pair':gs['pair_repeatability'][0]['agreement_passed']=False
    with pytest.raises(ValueError):worker.make_plan(*values)


def test_real_ledger_counts_seed_check_free_fit_and_full_gate(tmp_path):
    from types import SimpleNamespace
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_receipt_journal import Ledger
    book=Ledger(tmp_path,'a'*64,['fit'],fit_limit=81,diagnostic_limit=3);book.start('fit')
    bounds=Bounds(dict(velocity_x=1.,position_x=1.,time_offset=.15))
    calls=[]
    def native(u,model):
        calls.append(np.array(u));return np.r_[np.asarray(u)-[.2,-.3,.4],10.],np.vstack((np.eye(3),np.zeros((1,3)))),0
    problem=SimpleNamespace(bounds=bounds,residual_tangent=native);profiles=[]
    for t in (-.6,.1,.8):
        point=[.2,-.3,t];r,_,_=native(point,'sphere_still')
        profiles.append(dict(anchor_normalized=t,normalized_parameters=point,active_parameters=list(bounds.active),
            cost=float(r@r),conditional_passed=True,source_identity=str(t)))
    calls.clear()
    result=worker.fit_and_check(book,'fit',problem,'sphere_still',profiles,[-.6,.1,.8],
        lambda d:np.column_stack((d,np.zeros((len(d),2)))))
    assert result['converged'] and result['full_gate_verified']
    assert result['normalized_parameters']==pytest.approx([.2,-.3,.4])
    assert book.count('fit','diagnostic')==3 and len(calls)==book.count('fit','fit')+3


def test_free_time_repeat_comparison_allows_different_final_offsets():
    a=dict(times_s=[1.],gps=[[.5,.1,1000.]],active_parameters=['time_offset'],residual=[20.,0.,0.],normalized_parameters=[.1])
    b=dict(a,residual=[20.,1e-5,0.],normalized_parameters=[.1001])
    result=worker.repeat_metrics(a,b,lambda d:np.asarray(d).reshape(1,3))
    assert result['agreement_passed'] and not result['global_optimum_proven']
