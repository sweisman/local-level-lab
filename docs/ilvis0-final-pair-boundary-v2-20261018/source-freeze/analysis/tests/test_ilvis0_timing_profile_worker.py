# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest
import ilvis0_timing_profile_worker as worker


def inputs():
    tasks=[];results=[]
    for anchor,time in (('primary',-.138126450355649),('repeat',-.43810412716244257)):
        for start in ('primary','repeat'):
            identity=anchor+'::'+start
            tasks.append(dict(identity=identity,anchor_role=anchor,start_role=start,
                task=dict(segment_id='50f24131843071ae9312c082',case_id='bias1_unsubtracted',model='sphere_still'),
                fit=dict(active_parameters=['position_x','time_offset']),
                saved_result=dict(normalized_parameters=[.2 if anchor=='primary' else -.3,time]),
                anchor_normalized=time))
            results.append(dict(identity=identity,status='complete',conditional_verified=True))
    pairs=[dict(anchor_role=a,both_conditional_verified=True,agreement_passed=True) for a in ('primary','repeat')]
    return dict(plan=dict(tasks=tasks)),dict(results=results,pair_repeatability=pairs)


def test_three_interior_offsets_cross_both_verified_nuisance_starts():
    m,s=inputs();before=copy.deepcopy(m);plan=worker.make_plan(m,s)
    assert len(plan['tasks'])==6 and plan['maximum_starts']==6
    assert plan['maximum_native_evaluations']==486
    assert sum(t['maximum_fit_calls']+t['maximum_diagnostic_calls'] for t in plan['tasks'])==486
    assert {(t['fraction'],t['start_role']) for t in plan['tasks']}=={
        (f,r) for f in (.25,.5,.75) for r in ('primary','repeat')}
    for task in plan['tasks']:
        expected=(1-task['fraction'])*m['plan']['tasks'][0]['anchor_normalized']+task['fraction']*m['plan']['tasks'][-1]['anchor_normalized']
        assert task['anchor_normalized']==expected
        assert task['start_full'][1]==expected
        assert task['start_full'][0]==(.2 if task['start_role']=='primary' else -.3)
    assert m==before


@pytest.mark.parametrize('change',['failed','missing','pair','target','layout'])
def test_unverified_or_changed_source_cannot_define_grid(change):
    m,s=inputs()
    if change=='failed':s['results'][0]['conditional_verified']=False
    if change=='missing':s['results'].pop()
    if change=='pair':s['pair_repeatability'][0]['agreement_passed']=False
    if change=='target':m['plan']['tasks'][0]['task']['model']='flat_disc'
    if change=='layout':m['plan']['tasks'][-1]['fit']['active_parameters'].reverse()
    with pytest.raises(ValueError):worker.make_plan(m,s)


def test_real_ledger_accounts_for_fit_and_full_diagnostic(tmp_path):
    import numpy as np
    from types import SimpleNamespace
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_receipt_journal import Ledger
    book=Ledger(tmp_path,'a'*64,['fit'],fit_limit=80,diagnostic_limit=1);book.start('fit')
    calls=[]
    def native(u,model):
        calls.append(np.array(u))
        return np.r_[np.asarray(u)-[.2,-.3,.4],10.],np.vstack((np.eye(3),np.zeros((1,3)))),0
    problem=SimpleNamespace(bounds=Bounds(dict(velocity_x=1.,position_x=1.,time_offset=.15)),residual_tangent=native)
    result=worker.fit_profile(book,'fit',problem,'sphere_still',[0.,0.,.1],.1,
        lambda d:np.column_stack((d,np.zeros((len(d),2)))))
    assert result['conditional_converged'] and result['free_time_converged'] is False
    assert result['normalized_parameters']==pytest.approx([.2,-.3,.1])
    assert result['full_timing_gradient']==pytest.approx(-.3)
    assert book.count('fit','diagnostic')==1
    assert len(calls)==book.count('fit','fit')+1
    assert all(r['kind']=='tangent' for r in book.read('sweeps'))


def test_full_diagnostic_failure_stays_charged(tmp_path):
    import numpy as np
    from types import SimpleNamespace
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_receipt_journal import Ledger
    book=Ledger(tmp_path,'a'*64,['fit'],fit_limit=80,diagnostic_limit=1);book.start('fit')
    def native(u,model):
        if book.count('fit','diagnostic'):raise RuntimeError('full diagnostic failed')
        return np.r_[np.asarray(u)-[.2,-.3,.4],10.],np.vstack((np.eye(3),np.zeros((1,3)))),0
    problem=SimpleNamespace(bounds=Bounds(dict(velocity_x=1.,position_x=1.,time_offset=.15)),residual_tangent=native)
    with pytest.raises(RuntimeError,match='full diagnostic failed'):
        worker.fit_profile(book,'fit',problem,'sphere_still',[.2,-.3,.1],.1,
            lambda d:np.column_stack((d,np.zeros((len(d),2)))))
    assert book.count('fit','diagnostic')==1
