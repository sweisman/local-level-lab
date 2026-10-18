# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest
import ilvis0_profile_boundary_worker as worker


def inputs():
    names=['position_x','time_offset'];tasks=[];saved=[]
    for i in range(2):
        identity='c'+str(i)
        tasks.append(dict(identity=identity,source_identity=identity,kind='control',
            fit=dict(active_parameters=names),task={}))
        saved.append(dict(identity=identity,kind='control',status='complete',converged=True,
            normalized_parameters=[0.,.1],residual_sum_squares=1.,linearization_file='c.gz',linearization_sha256='x'))
    identity='50f24131843071ae9312c082::bias1_unsubtracted::sphere_still::profile_seeded_primary'
    task=dict(segment_id='50f24131843071ae9312c082',case_id='bias1_unsubtracted',model='sphere_still')
    tasks.append(dict(identity=identity,kind='target',task=task,fit=dict(active_parameters=names)))
    saved.append(dict(identity=identity,kind='target',status='complete',converged=False,active_parameters=names,
        normalized_parameters=[0.,.1],residual_sum_squares=2.,linearization_file='p.gz',linearization_sha256='x'))
    vm=dict(plan=dict(tasks=[dict(identity='verified_repeat',anchor_role='primary',start_role='repeat',task=task,
        fit=dict(active_parameters=names),saved_result=dict(normalized_parameters=[.001,.1]))]))
    vs=dict(results=[dict(identity='verified_repeat',status='complete',conditional_verified=True,
        residual_sum_squares=2.,linearization_file='r.gz',linearization_sha256='x')])
    audit=dict(target=dict(identity=identity),clock_geometry=dict(side_geometry_supported=True,
        original_point=.1,point=.1-1e-9,center_relocation_s=-1.5e-10))
    return dict(plan=dict(tasks=tasks)),saved,vm,vs,audit


def test_four_diagnostic_identities_preserve_sources_and_use_no_fit_allowance():
    values=inputs();before=copy.deepcopy(values);plan=worker.make_plan(*values)
    assert len(plan['tasks'])==4 and plan['maximum_optimizer_starts']==0
    assert plan['maximum_native_evaluations']==66
    assert sum(t['maximum_diagnostic_calls'] for t in plan['tasks'])==66
    assert values==before
    assert {t['source_role'] for t in plan['tasks'][2:]}=={'completed_primary','verified_profile_companion'}
    assert all(t['exact_point'][-1]==values[-1]['clock_geometry']['point'] for t in plan['tasks'][2:])


@pytest.mark.parametrize('change',['missing_primary','unsupported','different_clock'])
def test_changed_or_incomplete_target_evidence_blocks_new_plan(change):
    values=inputs()
    if change=='missing_primary':values[1].pop()
    if change=='unsupported':values[-1]['clock_geometry']['side_geometry_supported']=False
    if change=='different_clock':values[2]['plan']['tasks'][0]['saved_result']['normalized_parameters'][-1]=.2
    with pytest.raises(ValueError):worker.make_plan(*values)


def test_both_sealed_control_results_are_required():
    values=inputs();values[1][0]['converged']=False
    with pytest.raises(ValueError):worker.make_plan(*values)


def test_call_scope_forbids_fit_calls_and_charges_only_its_finite_identity(tmp_path):
    from lll.ilvis0_receipt_journal import Ledger
    book=Ledger(tmp_path,'a'*64,['control'],fit_limit=1,diagnostic_limit=30);book.start('control')
    scope=worker.CallScope(book,'control',1)
    assert scope.call('control','diagnostic','tangent',lambda:7)==7
    for identity,phase in [('control','diagnostic'),('control','fit'),('another','diagnostic')]:
        with pytest.raises(ValueError,match='scope'):
            scope.call(identity,phase,'tangent',lambda:None)
    assert book.count('control','diagnostic')==1 and book.count('control','fit')==0
