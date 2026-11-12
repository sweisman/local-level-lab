# SPDX-License-Identifier: AGPL-3.0-or-later
"""Focused checks for the saved-only four-group stopping diagnosis."""
import hashlib

import pytest

from lll.ilvis0_transfer_stopping_diagnostic import (
    POLICY_SOURCES, failed_gates, frozen_policy_sources, render)


def fit(*, cost=2e-8, stationarity=1e-6, reason='fresh_position_probe_not_stable'):
    probe = dict(passed=False, reason=reason)
    if reason != 'not_stationary':
        probe.update(actual_cost_change=cost, fresh_stationarity=stationarity,
                     position_rms_neu_m=[0., 0., 0.],
                     position_max_abs_neu_m=[0., 0., 0.])
    return dict(stability_probe=probe,
                stability_policy=dict(position_rms_tolerance_m=.001,
                                      position_max_tolerance_m=.01),
                stationarity_tolerance=1e-4)


def test_cost_only_failure_does_not_relabel_fit():
    assert failed_gates(fit()) == ['relative_cost_change']


def test_joint_failure_and_early_stationarity_are_distinct():
    assert failed_gates(fit(stationarity=2e-4)) == [
        'relative_cost_change', 'fresh_stationarity']
    assert failed_gates(fit(reason='not_stationary')) == [
        'stationarity_before_probe']


def test_rejects_failed_probe_without_a_failed_original_gate():
    with pytest.raises(ValueError, match='no failed original gate'):
        failed_gates(fit(cost=1e-9))


def test_render_keeps_all_ten_failures_and_no_scientific_decision():
    rows = ([dict(failed_gates=['relative_cost_change']) for _ in range(7)] +
            [dict(failed_gates=['relative_cost_change', 'fresh_stationarity'])
             for _ in range(2)] +
            [dict(failed_gates=['stationarity_before_probe'])])
    page = render(dict(tasks=16, nonpassing=10, rows=rows,
                       relative_cost_tolerance=1e-8))
    assert 'Cost change only | 7' in page
    assert 'failed fits remain failed' in page
    assert 'no model or uncertainty decision' in page


def test_requires_original_stopping_policy_source_hashes(tmp_path):
    sources = {}
    for name in POLICY_SOURCES:
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        sources[name] = hashlib.sha256(name.encode()).hexdigest()
    assert frozen_policy_sources(tmp_path, dict(sources=sources)) == sources
    sources[POLICY_SOURCES[0]] = '0'*64
    with pytest.raises(ValueError, match='source changed'):
        frozen_policy_sources(tmp_path, dict(sources=sources))
