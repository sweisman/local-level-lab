# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-stretch publication must not promote failed controls or partial fits."""
import copy
import importlib.util
from pathlib import Path

import pytest


path = Path(__file__).resolve().parents[2] / 'docs/ilvis0-position-stability-trial-20261013/build_findings.py'
spec = importlib.util.spec_from_file_location('current_findings', path)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def examples():
    original = dict(results=[dict(segment_id='unfinished', profile=dict(conditional_shape_preference='unresolved')),
                             dict(segment_id='preserved', profile=dict(conditional_shape_preference='globe'))])
    row = dict(segment_id='unfinished', profile=dict(conditional_shape_preference='globe'),
               recovery_checks_passed=True,
               cases=[dict(fits=[dict(converged=True) for _ in range(3)]) for _ in range(2)])
    recovery = dict(state='complete', qualification=dict(qualified=False, controls_passed=True), comparisons=[row])
    return original, recovery


def test_complete_stretch_can_publish_without_whole_corpus_success():
    original, recovery = examples()
    before = copy.deepcopy(original)
    assert set(report.recovery_updates(original, recovery)) == {'unfinished'}
    assert original == before


@pytest.mark.parametrize('failure', ['control', 'repeat', 'primary', 'missing', 'duplicate', 'active'])
def test_invalid_recovery_cannot_promote(failure):
    original, recovery = examples()
    row = recovery['comparisons'][0]
    if failure == 'control':
        recovery['qualification']['controls_passed'] = False
    elif failure == 'repeat':
        row['recovery_checks_passed'] = False
    elif failure == 'primary':
        row['cases'][0]['fits'][0]['converged'] = False
    elif failure == 'missing':
        recovery['comparisons'] = []
    elif failure == 'duplicate':
        recovery['comparisons'].append(copy.deepcopy(row))
    else:
        recovery['state'] = 'fitting'
    with pytest.raises(ValueError):
        report.recovery_updates(original, recovery)


def test_failed_comparison_is_preserved_as_unknown():
    original, recovery = examples()
    row = recovery['comparisons'][0]
    row['profile']['conditional_shape_preference'] = 'unresolved'
    row['recovery_checks_passed'] = False
    row['cases'][0]['fits'][0]['converged'] = False
    assert report.recovery_updates(original, recovery)['unfinished']['profile']['conditional_shape_preference'] == 'unresolved'


def precision_example():
    original, recovery = examples()
    before = report.recovery_updates(original, recovery)
    before['unfinished']['profile']['conditional_shape_preference'] = 'unresolved'
    row = copy.deepcopy(recovery['comparisons'][0])
    row['profile']['conditional_shape_preference'] = 'globe'
    trial = dict(state='complete', comparisons=[row], qualification=dict(
        qualified=True, controls_passed=True,
        repeatability=[dict(identity='unfinished::case::model::repeat', passed=True)]))
    return before, trial


def test_qualified_precision_overlay_preserves_old_results():
    before, trial = precision_example()
    saved = copy.deepcopy(before)
    updates = report.precision_updates(before, trial, ['unfinished'])
    assert updates['unfinished']['profile']['conditional_shape_preference'] == 'globe'
    assert before == saved


@pytest.mark.parametrize('failure', ['control', 'repeat', 'primary', 'missing', 'duplicate', 'active', 'unqualified', 'already_resolved'])
def test_precision_overlay_requires_all_qualification_checks(failure):
    before, trial = precision_example()
    if failure == 'control': trial['qualification']['controls_passed'] = False
    elif failure == 'repeat': trial['qualification']['repeatability'][0]['passed'] = False
    elif failure == 'primary': trial['comparisons'][0]['cases'][0]['fits'][0]['converged'] = False
    elif failure == 'missing': trial['comparisons'] = []
    elif failure == 'duplicate': trial['comparisons'] *= 2
    elif failure == 'active': trial['state'] = 'fitting'
    elif failure == 'unqualified': trial['qualification']['qualified'] = False
    else: before['unfinished']['profile']['conditional_shape_preference'] = 'globe'
    with pytest.raises(ValueError): report.precision_updates(before, trial, ['unfinished'])


def test_cost_recovery_publishes_only_complete_stretches_when_whole_run_fails():
    before, trial = precision_example()
    trial['qualification']['qualified'] = False
    before['other'] = copy.deepcopy(before['unfinished'])
    row = copy.deepcopy(trial['comparisons'][0]); row['segment_id'] = 'other'
    row['cases'][0]['fits'][0]['converged'] = False
    row['profile']['conditional_shape_preference'] = 'unresolved'
    trial['comparisons'].append(row)
    trial['qualification']['repeatability'].append(dict(identity='other::case::model::repeat',passed=True))
    updates = report.cost_precision_updates(before, trial, ['unfinished','other'])
    assert updates['unfinished']['profile']['conditional_shape_preference'] == 'globe'
    assert updates['other']['profile']['conditional_shape_preference'] == 'unresolved'


@pytest.mark.parametrize('failure',['control','repeat','primary','missing','duplicate','active'])
def test_cost_recovery_never_promotes_an_unqualified_stretch(failure):
    before, trial = precision_example()
    trial['qualification']['qualified'] = False
    if failure == 'control': trial['qualification']['controls_passed'] = False
    elif failure == 'repeat': trial['qualification']['repeatability'][0]['passed'] = False
    elif failure == 'primary': trial['comparisons'][0]['cases'][0]['fits'][0]['converged'] = False
    elif failure == 'missing': trial['comparisons'] = []
    elif failure == 'duplicate': trial['comparisons'] *= 2
    else: trial['state'] = 'fitting'
    with pytest.raises(ValueError): report.cost_precision_updates(before, trial, ['unfinished'])
