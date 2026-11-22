# SPDX-License-Identifier: AGPL-3.0-or-later
"""Status publication checks use metadata only, with no numerical imports."""
import importlib.util
from pathlib import Path

import pytest


def builder():
    path=Path(__file__).resolve().parents[2]/'docs/build_current_status.py'
    assert path.exists(), 'shared status generator is missing'
    spec=importlib.util.spec_from_file_location('current_status_builder',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_verified_inputs_use_published_ledgers_without_runtime_data(tmp_path):
    module=builder();p=tmp_path/'docs/study/ledger.json';p.parent.mkdir(parents=True);p.write_text('{}')
    module.verify_inputs(tmp_path,{'data/study/ledger.json':module.sha(p)})
    p.write_text('{"changed":true}')
    with pytest.raises(ValueError,match='hash mismatch'):
        module.verify_inputs(tmp_path,{'data/study/ledger.json':module.sha_bytes(b'{}')})


def test_missing_ledger_and_paths_outside_repo_are_rejected(tmp_path):
    module=builder()
    for path in ('docs/missing.json','../private.json','/tmp/private.json'):
        with pytest.raises(ValueError): module.verify_inputs(tmp_path,{path:'0'*64})


def row(sid,shape,background='False'):
    return dict(segment_id=sid,shape_preference=shape,specified_background_preferred=background,
                duration_s='240',imu_type='8')


def test_counts_are_derived_and_unresolved_is_not_flat_support():
    snapshot=builder().summarize([row('a','globe','True'),row('b','unresolved')])
    assert snapshot['tally']==dict(globe=1,flat=0,unresolved=1,ambiguous=0)
    assert snapshot['total']==2 and snapshot['background']==1 and snapshot['minutes']==8


def test_completed_cohorts_distinguish_saved_repeats_from_missing_evidence():
    module=builder()
    first=dict(row('a','globe','True'),result_origin='original_first_pass',
               latest_repeat_status='not_saved_or_not_scheduled')
    later=dict(row('b','globe','True'),result_origin='completed_recovery',
               latest_repeat_status='passed')
    snapshot=module.summarize([first,later])
    snapshot['receipt_sha256']='a'*64
    report=module.render(snapshot)
    assert '| Original pass | 1 | 0 | 1 |' in report
    assert '| Later numerical studies | 1 | 1 | 0 |' in report
    assert 'All selected comparisons have passed' not in module.status_block(snapshot,'')


def test_cost_contrast_requires_preference_under_both_processing_cases():
    cases = ('bias1_unsubtracted', 'bias1_profiled_removal')
    models = ('sphere_rotating', 'sphere_still', 'flat_still')

    def costs(first, second):
        return {f'{case}__{model}__cost': str(value)
                for case, values in zip(cases, (first, second), strict=True)
                for model, value in zip(models, values, strict=True)}

    assert builder().verified_cost_contrasts([
        costs((1, 9, 4), (1, 10, 6)),
        costs((1, 3, 2), (1, 2, 3)),
        costs((2, 3, 2), (1, 3, 2)),
    ]) == dict(field_globe=2, zero_field_disc=2)


@pytest.mark.parametrize('rows',[
    [row('a','globe'),row('a','unresolved')],
    [row('a','unknown_label')],
    [row('a','unresolved','True')],
])
def test_bad_inventory_cannot_publish(rows):
    with pytest.raises(ValueError): builder().summarize(rows)


def test_missing_or_duplicate_generated_markers_fail():
    module=builder()
    for text in ('no markers',module.START+module.START+module.END):
        with pytest.raises(ValueError,match='markers'): module.replace_block(text,'replacement')


def test_stale_excerpt_is_detected_without_writing(tmp_path,monkeypatch):
    module=builder();snapshot=module.summarize([row('a','globe','True')]);snapshot['receipt_sha256']='a'*64
    monkeypatch.setattr(module,'load_snapshot',lambda root:snapshot)
    for name in module.PAGES:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(module.START+'\n'+module.END+'\n')
    module.generate(tmp_path)
    assert module.generate(tmp_path,check=True)==[]
    path=tmp_path/'README.md';stale=path.read_text().replace('1 of 1 selected stretches','99 of 1 selected stretches');path.write_text(stale)
    assert module.generate(tmp_path,check=True)==['README.md']
    assert path.read_text()==stale


def test_committed_landing_pages_match_verified_evidence():
    module=builder()
    assert module.generate(module.ROOT,check=True)==[]
