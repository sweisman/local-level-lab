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
