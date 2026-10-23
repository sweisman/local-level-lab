# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path
import pytest
from lll.studies.artifacts import encoded,digest


def closed_fixture(root,rejected=False,unchanged=False):
    from test_ilvis0_truth_probes import _witness_fixture
    from lll import ilvis0_truth_probes
    prefix='data/witnesses';base=root/prefix;base.mkdir(parents=True)
    def write(name,value):
        path=base/name;path.parent.mkdir(parents=True,exist_ok=True)
        raw=encoded(value);path.write_bytes(raw);return digest(raw)
    tasks=[];inputs={};records={}
    for m in range(3):
        for p in (False,True):
            name=f'{m}-{int(p)}';problem,a,b=_witness_fixture();problem['numerical_error_m']=[1e-5]*3
            for value in (problem,a,b):value['binding'].update(model=m,profile=p)
            key='bundle-'+name;path='inputs/'+key+'.json';sha=write(path,dict(problem=problem,initial=a['point']))
            inputs[key]=dict(path=path,sha256=sha);inputs['case-'+name]=dict(path='case.json',sha256='a'*64)
            for sign,record in ((-1,a),(1,b)):
                if unchanged:record=a
                identity=name+str(sign);records[identity]=dict(problem=problem,record=record,
                    source_hashes_verified=True,bitwise_native_replay=True)
                tasks.append(dict(identity=identity,payload=dict(model=m,profile=p,sign=sign,
                    bundle_key=key,case_key='case-'+name,compiler='test compiler')))
    manifest_sha=write('manifest.json',dict(tasks=tasks,inputs=inputs,sources={
        'analysis/lll/ilvis0_tangent.cpp':'b'*64,
        'analysis/lll/ilvis0_truth_probes.py':digest(Path(ilvis0_truth_probes.__file__).read_bytes())}))
    rows=[]
    for i,task in enumerate(tasks):
        identity=task['identity'];spec=task['payload'];valid=not(rejected and i==1);artifacts={}
        if valid:
            name='artifacts/'+identity+'/verified-witness.json';artifacts[name]=write(name,records[identity])
            name='artifacts/'+identity+'/kernel.json';artifacts[name]=write(name,dict(compiler='test compiler',source_sha256='b'*64))
        result=dict(passed=valid,model=spec['model'],profile=spec['profile'],sign=spec['sign'],
            source_hashes_verified=valid,bitwise_native_replay=valid,optimizer_success=False,
            stopping_reason='native budget exhausted',native_evaluations=2)
        envelope=dict(identity=identity,manifest_sha256=manifest_sha,result=result,
            result_sha256=digest(encoded(result)),artifacts=artifacts)
        name='results/'+identity+'.json';rows.append(dict(identity=identity,artifact=name,
            artifact_sha256=write(name,envelope),passed=valid))
    state='terminal' if rejected else 'complete'
    summary_sha=write('summary.json',dict(state=state,total=12,completed=12,passed=not rejected,
        results=rows,elapsed_s=1.,charged=dict(native_calls=24)))
    write('completion.json',dict(state=state,manifest_sha256=manifest_sha,summary_sha256=summary_sha))
    return prefix


@pytest.mark.parametrize('rejected',[False,True])
def test_report_checks_actual_pairs_and_keeps_failed_directions_visible(tmp_path,rejected):
    from lll.ilvis0_witness_publication import inspect,render
    prefix=closed_fixture(tmp_path,rejected);report=inspect(tmp_path,prefix)
    assert report['complete_pairs']==6-int(rejected)
    assert report['target_exceedances']==6-int(rejected)
    assert len(report['cases'])==6
    text=render(report)
    assert 'not outer uncertainty bounds' in text and '53-stretch' in text
    assert 'numerical-error allowance' in text
    if rejected:assert 'Incomplete pair' in text


def test_report_refuses_active_or_corrupt_evidence(tmp_path):
    from lll.ilvis0_witness_publication import inspect
    with pytest.raises(ValueError,match='closed'):inspect(tmp_path,'data/active')
    prefix=closed_fixture(tmp_path)
    path=tmp_path/prefix/'artifacts/0-0-1/verified-witness.json';path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash'):inspect(tmp_path,prefix)


def test_witness_report_imports_no_numerical_libraries():
    import subprocess,sys
    subprocess.run([sys.executable,'-c',
        'import lll.ilvis0_witness_publication,sys; assert not {"numpy","scipy"}&set(sys.modules)'],
        check=True,capture_output=True,text=True)


def test_coincident_starting_points_are_not_reported_as_zero_uncertainty(tmp_path):
    from lll.ilvis0_witness_publication import inspect,render
    report=inspect(tmp_path,closed_fixture(tmp_path,unchanged=True))
    assert report['initial_only_pairs']==6 and report['distinct_pairs']==0
    text=render(report)
    assert 'same starting calibration' in text and 'not zero uncertainty' in text


def test_saved_step_diagnosis_separates_linear_and_native_training_errors():
    from lll.ilvis0_witness_publication import step_diagnostics
    from fractions import Fraction as F
    problem=dict(observations=[[0.,0.,0.]],coordinate_scale=[1.,1.,1.])
    jac=[[[100.]+[0.]*26,[0.]*27,[0.]*27],[[10.]+[0.]*26,[0.]*27,[0.]*27]]
    initial=dict(point=[0.]*27,prediction=[[0.,0.,0.],[0.,0.,0.]],jacobian=jac)
    trial=dict(point=[.01]+[0.]*26,prediction=[[2.,0.,0.],[3.,0.,0.]])
    result=step_diagnostics(problem,initial,trial)
    assert F(result['linear_training_max_exact'])==100*F(.01)
    assert F(result['native_training_max_exact'])==2
    assert F(result['linear_north_change_exact'])==10*F(.01)
    assert F(result['native_north_change_exact'])==3


def test_publication_preserves_renderer_and_leaves_saved_numerical_results_unchanged(tmp_path,monkeypatch):
    from lll import ilvis0_witness_publication as publication,ilvis0_control_publication as package
    from lll.studies import publication as archive
    prefix=closed_fixture(tmp_path);calls=[]
    def publish(data,public,text,*,plan):
        public.mkdir(parents=True);(public/'README.md').write_text(text)
        (public/'evidence-receipt.json').write_bytes(encoded(dict(artifacts={'README.md':digest(text.encode())})))
        calls.append('package')
    def compact(root,data,public):
        receipt=json.loads((public/'evidence-receipt.json').read_text())
        name='artifacts/publication/renderer.py'
        assert receipt['artifacts'][name]==digest((public/name).read_bytes())
        calls.append('archive');return dict(numerical_work=0)
    monkeypatch.setattr(package,'publish',publish);monkeypatch.setattr(archive,'archive_publication',compact)
    before=(tmp_path/prefix/'summary.json').read_bytes()
    result=publication.publish(tmp_path,prefix,'docs/witnesses',plan='PLAN.md')
    assert result['numerical_work']==0 and calls==['package','archive']
    assert before==(tmp_path/prefix/'summary.json').read_bytes()
    with pytest.raises(ValueError,match='sealed'):publication.publish(tmp_path,prefix,'docs/witnesses',plan='PLAN.md')
