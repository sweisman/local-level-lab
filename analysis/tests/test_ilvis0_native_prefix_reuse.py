# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only checks; no numerical imports or packet integration."""
from copy import deepcopy
import pytest


def reference():
    from lll.studies.artifacts import digest,encoded
    certificate=dict(case_sha256='case',material_sha256='material',conditioning_sha256='proof',
        reference_sha256='reference',original_cold_sha256='original',wrapper_sha256='wrapper',
        compiler='compiler',environment={'python':'fixed'})
    report=dict(time_s=290.,center=[1.,2.,3.])
    record=dict(report=report,certificate=certificate,
        report_sha256=digest(encoded(report)),work=dict(elapsed_s=4500.,peak_rss_bytes=500*1024**2),
        parent='data/closed-attempt',manifest_sha256='manifest',result_sha256='sealed-result')
    return record,certificate


def test_saved_early_reference_requires_same_source_proof_and_environment():
    from lll.ilvis0_native_prefix_long import validate_early_reference
    record,certificate=reference()
    assert validate_early_reference(record,certificate)==record['report']
    for name in certificate:
        bad=deepcopy(record);bad['certificate'][name]='different'
        with pytest.raises(ValueError,match='early reference'):
            validate_early_reference(bad,certificate)


def test_saved_early_reference_rejects_modified_or_incomplete_calculation():
    from lll.ilvis0_native_prefix_long import validate_early_reference
    from lll.studies.artifacts import digest,encoded
    record,certificate=reference()
    bad=deepcopy(record);bad['report']['center'][0]=99.
    with pytest.raises(ValueError,match='early reference'):
        validate_early_reference(bad,certificate)
    bad=deepcopy(record);bad['report']['time_s']=438.;bad['report_sha256']=digest(encoded(bad['report']))
    with pytest.raises(ValueError,match='early reference'):
        validate_early_reference(bad,certificate)
    for field in ('manifest_sha256','result_sha256','parent'):
        bad=deepcopy(record);bad[field]=''
        with pytest.raises(ValueError,match='early reference'):
            validate_early_reference(bad,certificate)
    for field,value in [('elapsed_s',7201.),('elapsed_s',float('nan')),
                        ('peak_rss_bytes',2*1024**3)]:
        bad=deepcopy(record);bad['work'][field]=value
        with pytest.raises(ValueError,match='early reference'):
            validate_early_reference(bad,certificate)


def test_reused_reference_has_no_new_cold_call_allowance():
    from lll.ilvis0_native_prefix_long import limits
    fresh=limits();reused=limits(reused_early=True)
    assert fresh['cold_bound_queries']==1 and fresh['reused_cold_reports']==1
    assert reused['cold_bound_queries']==0 and reused['reused_cold_reports']==2
    assert {k:v for k,v in fresh.items() if k not in ('cold_bound_queries','reused_cold_reports')}=={
        k:v for k,v in reused.items() if k not in ('cold_bound_queries','reused_cold_reports')}


def closed_reference(tmp_path,*,complete=True,extra_unstarted=False,include_cold=True,charged_bounds=1):
    from lll.studies.artifacts import digest,encoded
    from lll.studies.closed import ClosedStudy
    prefix='data/closed-attempt';base=tmp_path/prefix;identity='case'
    def write(name,value,raw=False):
        content=value if raw else encoded(value);p=base/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(content);return digest(content)
    record,certificate=reference();adapter='analysis/lll/ilvis0_native_prefix_long.py'
    adapter_sha=write('source-freeze/'+adapter,b'# trusted test adapter\n',True)
    cold_sha=write('inputs/cold.py',b'# trusted test original\n',True);certificate['original_cold_sha256']=cold_sha
    artifacts={}
    for name,value in [('cold-00.json',record['report']),('cold-work.json',record['work']),
                       ('compatibility.json',certificate)]:
        if name=='cold-00.json' and not include_cold:continue
        path='artifacts/'+identity+'/'+name;artifacts[path]=write(path,value)
    task=dict(identity=identity,payload=dict(model=0,profile=False))
    tasks=[task]+([dict(identity='not-started',payload=dict(model=0,profile=True))] if extra_unstarted else [])
    manifest=dict(tasks=tasks,adapter=adapter,sources={adapter:adapter_sha},
        inputs={'cold':dict(path='inputs/cold.py',sha256=cold_sha)},environment=certificate['environment'])
    manifest_sha=write('manifest.json',manifest);result=dict(passed=False,error_type='BudgetStopped')
    env=dict(identity=identity,manifest_sha256=manifest_sha,result=result,result_sha256=digest(encoded(result)),artifacts=artifacts,
        charged=dict(native_calls=0,packet_visits=0,bound_calls=charged_bounds,bound_steps=charged_bounds*864000))
    result_sha=write('results/case.json',env)
    summary=dict(total=len(tasks),completed=1,state='terminal',results=[dict(identity=identity,passed=False,
        artifact='results/case.json',artifact_sha256=result_sha)])
    summary_sha=write('summary.json',summary)
    if complete:write('completion.json',dict(state='terminal',manifest_sha256=manifest_sha,summary_sha256=summary_sha))
    return (ClosedStudy(tmp_path,prefix) if complete else (tmp_path,prefix)),certificate,adapter_sha


def test_reuse_acquires_only_hash_checked_artifacts_from_closed_attempt(tmp_path):
    from lll.ilvis0_native_prefix_long import early_from_study,validate_early_reference
    study,certificate,sha=closed_reference(tmp_path)
    try:
        record=early_from_study(study,'case',certificate,expected_adapter_sha=sha)
        assert record['parent']==study.prefix and record['result_sha256']==study.rows['case']['artifact_sha256']
        assert validate_early_reference(record,certificate)['time_s']==290.
        with pytest.raises(ValueError,match='source'):
            early_from_study(study,'case',certificate,expected_adapter_sha='wrong')
    finally:study.close()


def test_publication_preserves_unstarted_identities_and_failed_reference_work(tmp_path):
    from lll.ilvis0_native_prefix_long import inspect
    study,_,_=closed_reference(tmp_path,extra_unstarted=True);prefix=study.prefix;study.close()
    report=inspect(tmp_path,prefix)
    assert not report['complete'] and report['completed']==1 and report['not_started']==1
    assert len(report['rows'])==2
    assert report['rows'][0]['saved_cold_report'] and report['rows'][0]['cold_elapsed_s']==4500.
    assert report['rows'][1]['not_started'] and report['rows'][1]['profile'] is True


def test_active_or_corrupt_reference_cannot_be_reused(tmp_path):
    from lll.ilvis0_native_prefix_long import early_from_study
    from lll.studies.closed import ClosedStudy
    location,_,_=closed_reference(tmp_path/'active',complete=False)
    with pytest.raises(ValueError,match='closed'):ClosedStudy(*location)
    study,certificate,sha=closed_reference(tmp_path/'closed')
    path=tmp_path/'closed'/study.prefix/'artifacts/case/cold-00.json';path.write_text('{}')
    try:
        with pytest.raises(ValueError,match='hash'):
            early_from_study(study,'case',certificate,expected_adapter_sha=sha)
    finally:study.close()


def test_missing_charged_cold_reference_cannot_silently_be_retried(tmp_path):
    from lll.ilvis0_native_prefix_long import early_from_study
    study,certificate,sha=closed_reference(tmp_path/'charged',include_cold=False)
    try:
        with pytest.raises(ValueError,match='incomplete.*no retry'):
            early_from_study(study,'case',certificate,expected_adapter_sha=sha)
    finally:study.close()
    study,certificate,sha=closed_reference(tmp_path/'not-charged',include_cold=False,charged_bounds=0)
    try:
        assert early_from_study(study,'case',certificate,expected_adapter_sha=sha) is None
    finally:study.close()
