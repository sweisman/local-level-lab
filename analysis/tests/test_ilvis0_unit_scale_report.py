# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path

import pytest


def report():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-unit-scale-trial-20261011/build_report.py'
    spec=importlib.util.spec_from_file_location('unit_report',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def fit(cost=1.,converged=True):
    return dict(model='sphere_rotating',converged=converged,solver_reported_success=converged,
        exact_projected_gradient_relative=1e-6,residual_sum_squares=cost,
        prediction_diagnostics={'prediction':{'horizontal_rms_m':2.,'vertical_rms_m':3.}})


def test_comparison_accepts_improvement_but_not_success_with_worse_objective():
    module=report()
    row=module.matched_fit(fit(.9),fit(1.),'retained')
    assert row['completed_baseline_preserved'] and row['objective_qualified']
    assert not module.matched_fit(fit(1.01),fit(1.),'retained')['objective_qualified']
    assert not module.matched_fit(fit(.9,False),fit(1.),'retained')['completed_baseline_preserved']


def test_unfinished_baseline_is_preserved_without_inventing_objective_reference():
    row=report().matched_fit(fit(.9),fit(1.,False),'retained')
    assert row['baseline_status']=='unresolved'
    assert row['objective_qualified'] is None
    assert row['new_status']=='converged'


def test_changed_baseline_hash_is_rejected_before_publication(tmp_path):
    p=tmp_path/'baseline'; p.mkdir()
    (p/'evidence-receipt.json').write_text('{"artifacts":{"summary.json":"bad"}}')
    (p/'summary.json').write_text('{}')
    with pytest.raises(ValueError,match='hash'): report().build(tmp_path/'new',p)
    assert not (tmp_path/'new'/'RESULTS.md').exists()


def publications(tmp_path):
    from test_ilvis0_prediction_report import evidence
    module=report(); folders=[tmp_path/'baseline',tmp_path/'new']
    for i,p in enumerate(folders):
        p.mkdir(); helper=evidence(p)
        summary=json.loads((p/'summary.json').read_text())
        summary['split']={'training_epochs':292,'prediction_epochs':147}
        manifest=json.loads((p/'manifest.json').read_text())
        if i: summary['version']=manifest['version']=module.VERSION
        for name,payload in (('summary.json',summary),('manifest.json',manifest)):
            (p/name).write_text(json.dumps(payload))
        (p/'completion.json').write_text(json.dumps(dict(state='complete',
            summary_sha256=helper.sha(p/'summary.json'),manifest_sha256=helper.sha(p/'manifest.json'))))
        (p/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={
            n:helper.sha(p/n) for n in ('summary.json','manifest.json','completion.json')})))
    return module,folders[1],folders[0]


def test_complete_matching_publications_generate_verified_comparison(tmp_path):
    module,new,old=publications(tmp_path)
    assert len(module.build(new,old))==6
    assert 'Comparison qualification: passed' in (new/'RESULTS.md').read_text()
    receipt=json.loads((new/'report-receipt.json').read_text())
    assert receipt['comparison_qualification_passed']
    from lll import ilvis0_saved_audit
    ilvis0_saved_audit.verify_artifacts(new,receipt)


def test_changed_physical_scope_is_rejected_even_with_valid_hashes(tmp_path):
    module,new,old=publications(tmp_path)
    from test_ilvis0_prediction_report import reporter
    helper=reporter(); manifest=json.loads((new/'manifest.json').read_text())
    manifest['cases'][0]['profile']=True
    (new/'manifest.json').write_text(json.dumps(manifest))
    completion=json.loads((new/'completion.json').read_text())
    completion['manifest_sha256']=helper.sha(new/'manifest.json')
    (new/'completion.json').write_text(json.dumps(completion))
    receipt=json.loads((new/'evidence-receipt.json').read_text())
    for n in ('manifest.json','completion.json'): receipt['artifacts'][n]=helper.sha(new/n)
    (new/'evidence-receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='scientific scope differs'): module.build(new,old)
    assert not (new/'RESULTS.md').exists()
