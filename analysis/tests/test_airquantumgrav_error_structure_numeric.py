# SPDX-License-Identifier: AGPL-3.0-or-later
"""Whole saved-data pipeline control; no motion kernel is available to it."""
def test_saved_error_structure_preserves_parent_outcomes_choices_and_exact_work(tmp_path):
    import gzip
    import itertools
    import json
    from types import SimpleNamespace
    import numpy as np
    from lll.airquantumgrav_error_structure import evaluate,environment,recipe,tasks,work_limits,SCOPE
    from lll.airquantumgrav_error_structure_report import verify_statistics,csv_bytes
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.studies.artifacts import digest,encoded

    r=recipe();task=tasks()[0];identity=task['identity'];curves={};rows=[];primaries=[]
    times=np.arange(1.,1201.).tolist()
    for model,profile,policy in itertools.product(('sphere_rotating','sphere_still','flat_still'),
            (False,True),('reported-short-v1','reported-persistent-v1')):
        members=[]
        for start in (0,1):
            name=f'{model}-{int(profile)}-{policy}-{start}'
            complete=not (model=='flat_still' and profile and policy=='reported-short-v1')
            row=dict(identity=name,model=model,profile=profile,policy_id=policy,start=start,
                complete=complete,passed=complete,last_training_cost=2400. if complete else None,
                reason=None if complete else 'original cooperative deadline exhausted')
            rows.append(row);members.append(row)
            if complete:
                t=np.array(times);errors=np.column_stack((np.sin(t/30),t/100,2*np.cos(t/60)))
                scores=dict(times_s=times,errors_neu_m=errors.tolist())
                curves[name]=dict(scores=scores,source_sha256=digest(encoded(scores)))
        primaries.append(dict(model=model,profile=profile,policy_id=policy,selected_training_start=1,
            primary=members[1] if complete else None))
    manifest_raw=encoded(dict(tasks='synthetic saved-output fixture'))
    report=dict(verified=True,total=24,expected_primaries=12,complete_predictions=22,numerically_converged=22,
        original_reads=0,protected_reads=0,native_calls_during_audit=0,rows=rows,primaries=primaries,
        manifest_sha256=digest(manifest_raw),summary_sha256='b'*64,
        source=dict(source_references=dict(imu=dict(filename='187_rqh01.txt'))))
    receipt=dict(artifacts={'artifacts/publication/verified-report.json':digest(encoded(report)),
        **{'artifacts/'+k+'/scores.json':v['source_sha256'] for k,v in curves.items()}})
    completion=dict(manifest_sha256=report['manifest_sha256'],summary_sha256=report['summary_sha256'])
    materials={'recipe':encoded(r),'qualification-environment':encoded(environment()),'parent-report':encoded(report),
        'parent-manifest':manifest_raw,'parent-completion':encoded(completion),'parent-receipt':encoded(receipt),
        'curves':gzip.compress(encoded(curves),mtime=0)}
    inputs={}
    for i,(key,raw) in enumerate(materials.items()):
        path=tmp_path/f'input-{i}';path.write_bytes(raw);inputs[key]=path
    manifest=dict(scope=SCOPE,limits=dict(maximum_wall_s=300.))
    (tmp_path/'manifest.json').write_bytes(encoded(manifest))
    directory=tmp_path/'artifacts'/identity;directory.mkdir(parents=True)
    def save(name,value):(directory/name).write_bytes(encoded(value))
    def save_bytes(name,value):(directory/name).write_bytes(value)
    context=SimpleNamespace(root=tmp_path,directory=directory,manifest=manifest,
        input_path=lambda key:inputs[key],save=save,save_bytes=save_bytes,note_file=lambda path:None)
    before=encoded(curves);result=evaluate(task,context)
    statistics=json.loads((directory/'statistics.json').read_bytes())
    assert result['passed'] and (result['records'],result['missing_records'],result['selected_primaries'])==(22,2,11)
    assert all(result[k]==0 for k in ('native_calls','observed_starts','new_propagations','original_reads','protected_reads'))
    assert not result['forecasts_changed'] and not result['model_decisions_changed'] and not result['error_law_calibrated']
    assert len(statistics)==24 and sum(v['statistics'] is not None for v in statistics)==22
    assert [v['parent_reason'] for v in statistics if not v['complete']]==['original cooperative deadline exhausted']*2
    assert all(v['start']==1 for v in statistics if v['selected_primary'])
    assert all(v['weighted_training_rms']==1. for v in statistics if v['complete'])
    assert encoded(curves)==before and (directory/'error-growth.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    counts=construction_counts((directory/'statistics-work.sqlite').read_bytes(),
        digest((tmp_path/'manifest.json').read_bytes()),identity,work_limits(r),complete=False)
    assert counts==dict(records=22,saved_error_epochs=26400,statistics_sections=88,spectra=264,
        correlation_pairs=22*34698,plotted_epochs=13200)==result['charged_work']
    verify_statistics(report,curves,statistics,result)
    import csv
    import io
    table=list(csv.DictReader(io.StringIO(csv_bytes(dict(statistics=statistics)).decode())))
    assert len(table)==264 and {v['units'] for v in table}=={'m','m/s'}
    statistics[0]['statistics']['training']['axes'][0]['distribution']['rms']+=1.
    import pytest
    with pytest.raises(ValueError,match='statistics'):verify_statistics(report,curves,statistics,result)
