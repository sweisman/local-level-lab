# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata/report checks only; no numerical packages or scientific calculations."""
import json
import pytest
from lll.studies.artifacts import encoded,digest


def test_report_helper_loads_without_numerical_libraries():
    import subprocess,sys
    code="import sys;import lll.ilvis0_prediction_publication;assert not {'numpy','scipy'}&set(sys.modules)"
    subprocess.run([sys.executable,'-c',code],check=True,capture_output=True,text=True)


def closed_fixture(root,*,useful=0,rejected=0):
    prefix='data/prediction';directory=root/prefix;directory.mkdir(parents=True)
    def write(name,value):
        path=directory/name;path.parent.mkdir(parents=True,exist_ok=True)
        raw=encoded(value);path.write_bytes(raw);return digest(raw)
    tasks=[];rows=[]
    for index in range(6):
        identity=f'case-{index}';model=index//2;profile=bool(index%2)
        tasks.append(dict(identity=identity,payload=dict(model=model,profile=profile,width_target_m=[20.,20.,50.])))
    manifest_sha=write('manifest.json',dict(tasks=tasks,limits=dict(bound_calls=6)))
    for index,task in enumerate(tasks):
        passed=index<useful;checked=index>=rejected
        result=dict(identity=task['identity'],model=task['payload']['model'],profile=task['payload']['profile'],
            passed=passed and checked,useful=passed,numerical_checks_passed=checked,
            future_width_m=[10.,10.,10.] if passed else [100.,100.,100.],
            previous_width_m=[1000.]*3,width_target_m=[20.,20.,50.],scientific_decision='abstain')
        if not checked:result=dict(passed=False,error_type='ValueError',reason='preserved rejection')
        envelope=dict(identity=task['identity'],manifest_sha256=manifest_sha,result=result,
            result_sha256=digest(encoded(result)),artifacts={})
        name='results/'+task['identity']+'.json'
        rows.append(dict(identity=task['identity'],artifact=name,artifact_sha256=write(name,envelope),passed=result['passed']))
    summary=dict(state='complete' if useful==6 else 'terminal',total=6,completed=6,
        passed=useful==6,results=rows,elapsed_s=3600.,charged=dict(bound_calls=6,native_calls=0))
    summary_sha=write('summary.json',summary)
    write('completion.json',dict(state=summary['state'],manifest_sha256=manifest_sha,summary_sha256=summary_sha))
    return prefix


@pytest.mark.parametrize('useful,rejected',[(0,0),(2,1),(6,0)])
def test_report_keeps_numerical_completion_separate_from_endpoint_usefulness(tmp_path,useful,rejected):
    from lll.ilvis0_prediction_publication import inspect,render
    prefix=closed_fixture(tmp_path,useful=useful,rejected=rejected)
    report=inspect(tmp_path,prefix);text=render(report)
    assert report['numerical_checks']==6-rejected
    assert report['useful_cases']==max(0,useful-rejected)
    assert str(report['useful_cases'])+'/6' in text
    assert 'generated software cases' in text and '53-stretch' in text
    assert len(report['cases'])==6 and text.count('| Globe, specified field')==2
    if useful!=6:assert 'remains unqualified' in text


def test_report_refuses_an_active_study_and_changed_closed_artifact(tmp_path):
    from lll.ilvis0_prediction_publication import inspect
    directory=tmp_path/'data/active';directory.mkdir(parents=True)
    with pytest.raises(ValueError,match='closed'):inspect(tmp_path,'data/active')
    prefix=closed_fixture(tmp_path)
    path=tmp_path/prefix/'results/case-0.json';path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash'):inspect(tmp_path,prefix)


def test_report_rejects_a_matrix_with_duplicate_model_processing_cases(tmp_path):
    from lll.ilvis0_prediction_publication import inspect
    prefix=closed_fixture(tmp_path);directory=tmp_path/prefix
    path=directory/'manifest.json';manifest=json.loads(path.read_text())
    manifest['tasks'][-1]['payload']['model']=0;manifest['tasks'][-1]['payload']['profile']=False
    path.write_bytes(encoded(manifest));completion=json.loads((directory/'completion.json').read_text())
    completion['manifest_sha256']=digest(path.read_bytes());(directory/'completion.json').write_bytes(encoded(completion))
    with pytest.raises(ValueError,match='matrix'):inspect(tmp_path,prefix)


def test_report_keeps_planned_cases_that_never_completed(tmp_path):
    from lll.ilvis0_prediction_publication import inspect,render
    prefix=closed_fixture(tmp_path);directory=tmp_path/prefix
    path=directory/'summary.json';summary=json.loads(path.read_text())
    summary['results']=summary['results'][:4];summary['completed']=4;path.write_bytes(encoded(summary))
    completion=json.loads((directory/'completion.json').read_text());completion['summary_sha256']=digest(path.read_bytes())
    (directory/'completion.json').write_bytes(encoded(completion))
    report=inspect(tmp_path,prefix)
    assert len(report['cases'])==6 and report['completed']==4
    assert render(report).count('No completed calculation')==2


def test_publication_archives_its_renderer_without_touching_numerical_evidence(tmp_path,monkeypatch):
    from lll import ilvis0_prediction_publication as publication
    from lll import ilvis0_control_publication as packaging
    from lll.studies import publication as archive
    prefix=closed_fixture(tmp_path);output='docs/comparison';calls=[]
    def package(data,public,text,*,plan):
        public.mkdir(parents=True);(public/'README.md').write_text(text)
        (public/'evidence-receipt.json').write_bytes(encoded(dict(artifacts={'README.md':digest(text.encode())})))
        calls.append('package')
    def compact(root,data,public):
        receipt=json.loads((public/'evidence-receipt.json').read_text())
        source=(public/'artifacts/publication/renderer.py').read_bytes()
        provenance=json.loads((public/'artifacts/publication/report-provenance.json').read_text())
        assert provenance['renderer_sha256']==digest(source) and provenance['numerical_work']==0
        assert receipt['artifacts']['artifacts/publication/renderer.py']==digest(source)
        calls.append('archive');return dict(numerical_work=0)
    monkeypatch.setattr(packaging,'publish',package);monkeypatch.setattr(archive,'archive_publication',compact)
    before=(tmp_path/prefix/'summary.json').read_bytes()
    result=publication.publish(tmp_path,prefix,output,plan='PLAN.md')
    assert result['numerical_work']==0 and calls==['package','archive']
    assert (tmp_path/prefix/'summary.json').read_bytes()==before
    with pytest.raises(ValueError,match='sealed'):publication.publish(tmp_path,prefix,output,plan='PLAN.md')
