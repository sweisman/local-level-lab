# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def reporter():
    source=Path(__file__).resolve().parents[2]/'docs/ilvis0-prediction-trial-20261011/build_report.py'
    spec=importlib.util.spec_from_file_location('prediction_report',source)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def evidence(directory, duplicate=False, unresolved=False):
    module=reporter()
    cases=[dict(case_id=name,fits=[dict(model=model,converged=True,
        solver_reported_success=True,exact_projected_gradient_relative=1e-6,
        evaluations=10,elapsed_s=2.,residual_sum_squares=1.,
        prediction_diagnostics=dict(training=dict(horizontal_rms_m=.1,vertical_rms_m=.2),
            prediction=dict(horizontal_rms_m=.3,vertical_rms_m=.4,
                primary_conditional_cost=2.,conservative_conditional_cost=.2)))
        for model in module.MODELS]) for name in ('bias1_unsubtracted','bias1_profiled_removal')]
    if duplicate: cases[1]['fits'][2]['model']=module.MODELS[0]
    if unresolved:
        cases[1]['fits'][2].update(converged=False,solver_reported_success=False,
            exact_projected_gradient_relative=.004,evaluations=200,
            message='The maximum number of function evaluations is exceeded.')
    profile=dict(conditional_shape_preference='unresolved' if unresolved else 'globe',
        rotation_withheld_reason='incomplete shape comparison' if unresolved else None,
        shape_profiles=[dict(case_id=c['case_id'],
            conditional_disc_minus_globe_cost=None if unresolved and i==1 else 3.,
            unresolved_optimizations=['flat_still'] if unresolved and i==1 else [])
            for i,c in enumerate(cases)])
    payloads={'summary.json':dict(version=module.VERSION,state='complete',starts=6,
        cases=cases,prediction_profile=profile),
        'manifest.json':dict(version=module.VERSION,maximum_starts=6,
            cases=[dict(case_id=c['case_id']) for c in cases])}
    for name,payload in payloads.items(): (directory/name).write_text(json.dumps(payload))
    (directory/'completion.json').write_text(json.dumps(dict(state='complete',
        summary_sha256=module.sha(directory/'summary.json'),
        manifest_sha256=module.sha(directory/'manifest.json'))))
    (directory/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={
        name:module.sha(directory/name) for name in (*payloads,'completion.json')})))
    return module


def test_changed_prediction_evidence_is_rejected_before_reporting(tmp_path):
    (tmp_path/'summary.json').write_text('{}')
    (tmp_path/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={'summary.json':'0'*64})))
    with pytest.raises(ValueError,match='hash'): reporter().build(tmp_path)
    assert not (tmp_path/'RESULTS.md').exists()


def test_report_rejects_partial_or_duplicate_case_population(tmp_path):
    module=evidence(tmp_path,duplicate=True)
    with pytest.raises(ValueError,match='duplicate prediction population'): module.build(tmp_path)
    assert not (tmp_path/'RESULTS.md').exists()


def test_completed_report_preserves_direct_and_conditioned_errors(tmp_path):
    module=evidence(tmp_path)
    rows=module.build(tmp_path)
    assert len(rows)==6 and all(r['status']=='converged' for r in rows)
    assert rows[0]['prediction_horizontal_m']==.3
    assert rows[0]['prediction_cost']==2.
    report=(tmp_path/'RESULTS.md').read_text()
    assert '6/6 training fits converged' in report and 'Prediction comparison: globe' in report
    assert '0.3 / 0.4' in report and 'not an independent confirmation' in report
    assert 'Rotating globe' in report and 'Stationary flat disc' in report
    assert 'No upstream removal' in report and 'Upstream removal allowed' in report
    receipt=json.loads((tmp_path/'report-receipt.json').read_text())
    assert receipt['optimizer_starts']==receipt['native_predictions']==0
    for name,digest in receipt['artifacts'].items(): assert module.sha(tmp_path/name)==digest
    first={name:(tmp_path/name).read_bytes() for name in (*receipt['artifacts'],'report-receipt.json')}
    module.build(tmp_path)
    assert first=={name:(tmp_path/name).read_bytes() for name in first}


def test_report_distinguishes_completed_case_from_unfinished_comparison(tmp_path):
    module=evidence(tmp_path,unresolved=True)
    rows=module.build(tmp_path)
    assert sum(r['status']=='converged' for r in rows)==5
    report=(tmp_path/'RESULTS.md').read_text()
    assert 'No upstream removal favors globe' in report
    assert 'Upstream removal allowed remains unresolved' in report
    assert 'Stationary flat disc has not converged' in report
    assert 'Rotation comparison is withheld' in report
    assert 'maximum number of function evaluations' in (tmp_path/'fit-comparisons.csv').read_text()
