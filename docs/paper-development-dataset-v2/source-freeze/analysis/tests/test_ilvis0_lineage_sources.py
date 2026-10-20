# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

import pytest


def module():
    from lll import ilvis0_lineage_sources
    return ilvis0_lineage_sources


def put(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(root):
    d='docs/review';identity='s::c::m::primary';fit=dict(converged=False,residual_sum_squares=12.5,parameters=dict(x=1),evaluations=4)
    em=dict(environment=dict(python='actual',numpy='actual-numpy',scipy='actual-scipy',thread_settings={'OMP_NUM_THREADS':'2'}),
        plan=dict(tasks=[dict(identity=identity,segment_id='s',case_id='c',model='m',role='primary')]),sources={'kernel.cpp':'a'*64})
    mh=put(root,d+'/evidence-exec-manifest.json',em)
    sh=put(root,d+'/evidence-exec-summary.json',dict(results=[dict(identity=identity,passed=True)]))
    ch=put(root,d+'/evidence-exec-completion.json',dict(state='complete',manifest_sha256=mh,summary_sha256=sh))
    inputs={d+'/evidence-exec-'+name+'.json':digest for name,digest in (('manifest',mh),('summary',sh),('completion',ch))}
    manifest=dict(environment=dict(python='publisher'),inputs=inputs)
    ph=put(root,d+'/manifest.json',manifest)
    payload=dict(attempts=[dict(identity=identity,source_identity='original-point',segment_id='s',case_id='c',model='m',role='primary',
        status='complete',operation='conditional_timing_profile',fit=fit)])
    rh=put(root,d+'/review.json',payload)
    cc=put(root,d+'/completion.json',dict(state='complete',manifest_sha256=ph,review_sha256=rh))
    put(root,d+'/evidence-receipt.json',dict(artifacts={'manifest.json':ph,'review.json':rh,'completion.json':cc}))
    return dict(segment_id='s',case_id='c',model='m',role='primary',identity=identity,result_origin='review',
        converged='False',cost='12.5',parameters='{"x": 1}',evaluations='4',operation='conditional_timing_profile')


def test_review_publisher_is_not_substituted_for_operation_environment(tmp_path):
    row=review(tmp_path);reader=module().Reader(tmp_path)
    records=reader.review_records('docs/review');result=module().index_history([row],{'review':records},reader)
    assert result[0]['execution_python']=='actual'
    assert result[0]['publication_python']=='publisher'
    assert result[0]['published_converged']=='False'
    assert result[0]['operation_class']=='conditional_profile'
    assert result[0]['parameter_point_source_identity']=='original-point'
    assert result[0]['execution_worker_identity']=='s::c::m::primary'


def test_changed_preserved_execution_artifact_is_rejected(tmp_path):
    review(tmp_path);(tmp_path/'docs/review/evidence-exec-summary.json').write_text('{}')
    with pytest.raises(ValueError):module().Reader(tmp_path).review_records('docs/review')


def test_trial_ownership_excludes_reused_results_outside_its_tasks(tmp_path):
    d='docs/trial';identity='s::c::m::primary'
    manifest=dict(environment=dict(python='actual'),proposal=dict(tasks=[dict(identity=identity,segment_id='s',case_id='c',model='m',role='primary')]))
    mh=put(tmp_path,d+'/manifest.json',manifest)
    sh=put(tmp_path,d+'/summary.json',dict(results={identity:dict(converged=True,residual_sum_squares=1.,parameters={}),
        'old-reused':dict(converged=True)}))
    ch=put(tmp_path,d+'/completion.json',dict(state='complete',manifest_sha256=mh,summary_sha256=sh))
    put(tmp_path,d+'/evidence-receipt.json',dict(artifacts={'manifest.json':mh,'summary.json':sh,'completion.json':ch}))
    records=module().Reader(tmp_path).trial_records(d,published_role='recovery')
    assert len(records)==1 and records[0]['identity']==identity and records[0]['role']=='recovery'
    assert records[0]['execution_task_role']=='primary'
    row=dict(segment_id='s',case_id='c',model='m',role='recovery',identity=identity,result_origin='trial',
        converged='True',cost='1.0',parameters='{}',evaluations='',operation='')
    reader=module().Reader(tmp_path);records=reader.trial_records(d,published_role='recovery')
    indexed=module().index_history([row],{'trial':records},reader)
    assert indexed[0]['parameter_point_ancestry_fully_resolved'] is None
