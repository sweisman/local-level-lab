# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def example():
    tasks={};rows=[]
    for seed in (26102610,26102611):
        for start in (0,1):
            identity=f'{seed}-{start}'
            tasks[identity]=dict(payload=dict(draw_seed=seed,role='method_diagnostic_pilot',
                case=dict(law='increment',model='sphere_rotating',profile=False,start=start)))
            rows.append(dict(identity=identity,draw_seed=seed,role='method_diagnostic_pilot',law='increment',
                model='sphere_rotating',profile=False,start=start,complete=True,converged=seed==26102610,
                accurate=True,training_cost=float(start+1),maximum_standardized_error=9.-8*start,
                prediction=dict(horizontal_rms_m=2.,vertical_rms_m=.2),
                conditional_prediction=dict(horizontal_rms_m=1.9,vertical_rms_m=.1,accuracy={'passed':True})))
    return tasks,rows


def test_fresh_report_requires_closed_study_before_numerical_imports(tmp_path):
    import sys
    from lll.independent_noisy_report import inspect
    before='numpy' in sys.modules
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path,'data/missing')
    assert ('numpy' in sys.modules)==before


def test_fresh_primary_selection_uses_training_cost_and_retains_empty_group():
    from lll.independent_noisy_report import select_primaries
    tasks,rows=example();p=select_primaries(rows,tasks)
    assert len(p)==2 and p[0]['selected_identity']=='26102610-0'
    assert p[1]['selected_identity'] is None
    assert select_primaries([],tasks)[0]['selected_identity'] is None


def summary():
    from lll.independent_noisy_report import select_primaries
    tasks,rows=example()
    return dict(verified=True,total=4,returned_outcomes=4,complete=4,numerically_converged=2,raw_accuracy=4,
        conditional_accuracy=4,rows=rows,primaries=select_primaries(rows,tasks),seeds=[26102610,26102611],
        available_primaries=1,elapsed_s=2.,confidence_calibrated=False)


def test_fresh_report_explains_seed_dependence_and_preserves_failures():
    from lll.independent_noisy_report import render
    text=render(summary())
    assert '2/4' in text and '26102611' in text and 'Unavailable' in text
    assert 'not Earth-model votes' in text and 'two' in text
    assert 'not calibrated' in text


def test_fresh_result_csv_keeps_every_start_and_training_primary():
    import csv,io
    from lll.independent_noisy_report import result_csv
    rows=list(csv.DictReader(io.StringIO(result_csv(summary()))))
    assert len(rows)==4 and sum(r['training_primary']=='True' for r in rows)==1
    assert sum(r['numerical_pass']=='False' for r in rows)==2
    assert rows[1]['maximum_standardized_error']=='1.0'


def test_fresh_publication_requires_qualification_before_any_files(tmp_path):
    from lll.independent_noisy_report import publish
    with pytest.raises(ValueError):publish(tmp_path,'data/missing',qualification=None)
    assert not (tmp_path/'docs').exists()


def test_previous_numeric_replay_after_shared_audit_extraction_is_unchanged():
    from pathlib import Path
    from lll.structured_noisy_publication import inspect
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import encoded
    root=Path(__file__).resolve().parents[2];prefix='docs/structured-noisy-training'
    s=ClosedStudy(root,prefix)
    try:original=s.read('artifacts/publication/verified-report.json')
    finally:s.close()
    assert encoded(inspect(root,prefix))==encoded(original)


def test_closed_pilot_numeric_replay_preserves_all_seeds_and_returned_outcomes():
    import os
    from pathlib import Path
    from lll.independent_noisy_report import inspect
    from lll.studies.closed import ClosedStudy
    root=Path(__file__).resolve().parents[2]
    prefix=os.environ.get('LLL_CLOSED_INDEPENDENT_PILOT','docs/independent-noisy-training-pilot')
    if not (root/prefix/'completion.json').is_file():pytest.skip('closed pilot evidence not published yet')
    r=inspect(root,prefix);s=ClosedStudy(root,prefix)
    try:
        assert r['total']==48 and r['returned_outcomes']==s.summary['completed']
        assert r['seeds']==[26102610,26102611] and len(r['rows'])==48
        assert r['confidence_calibrated'] is False and r['native_calls_during_audit']==0
        assert r['numerically_converged']==sum(v.get('converged',False) for v in r['rows'])
    finally:s.close()
