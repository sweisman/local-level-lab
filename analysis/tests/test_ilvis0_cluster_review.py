# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publication checks for the clustered-boundary diagnostic, without native work."""
import copy
import importlib.util
from pathlib import Path

import pytest


def publication():
    path = Path(__file__).resolve().parents[2] / 'docs/ilvis0-cluster-review-20261018/build_report.py'
    spec = importlib.util.spec_from_file_location('cluster_review', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def fixture():
    item = dict(kind='target', source_role='verified_profile_companion',
                task=dict(identity='s::bias1_unsubtracted::sphere_still::primary'))
    result = dict(status='complete', passed=True, source_role=item['source_role'],
                  boundary_check=dict(passed=True, branches=[dict(passed=True, side=s) for s in ('left', 'right')]),
                  source_relocation=dict(passed=True), cumulative_from_source=dict(passed=True))
    return item, result


def test_companion_is_a_new_diagnostic_repeat_not_the_interrupted_fit():
    item, result = fixture()
    assert publication().scientific_identity(item) == 's::bias1_unsubtracted::sphere_still::repeat'
    publication().require_gate(item, result)


@pytest.mark.parametrize('failure', ['boundary', 'branch', 'missing_side', 'movement', 'cumulative', 'status', 'passed'])
def test_incomplete_gate_cannot_publish(failure):
    item, original = fixture(); result = copy.deepcopy(original)
    if failure == 'boundary': result['boundary_check']['passed'] = False
    if failure == 'branch': result['boundary_check']['branches'][0]['passed'] = False
    if failure == 'missing_side': result['boundary_check']['branches'].pop()
    if failure == 'movement': result['source_relocation']['passed'] = False
    if failure == 'cumulative': result['cumulative_from_source']['passed'] = False
    if failure == 'status': result['status'] = 'interrupted'
    if failure == 'passed': result['passed'] = False
    with pytest.raises(ValueError): publication().require_gate(item, result)


def test_primary_keeps_its_primary_identity():
    item, _ = fixture(); item['source_role'] = 'completed_primary'
    assert publication().scientific_identity(item) == item['task']['identity']


def test_unknown_provenance_cannot_be_assigned_a_role():
    item, _ = fixture(); item['source_role'] = 'interrupted_repeat'
    with pytest.raises(ValueError): publication().scientific_identity(item)
