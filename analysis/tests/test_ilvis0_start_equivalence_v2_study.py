"""Source-bound fresh-geometry start-equivalence study controls."""

from pathlib import Path

import pytest

from lll.ilvis0_start_equivalence_v2_study import (
    assess_group, pair, prepare, recipe, tasks, verify_parent)

ROOT = Path(__file__).resolve().parents[2]


def test_v2_study_freezes_new_geometry_and_finite_limits():
    from lll.ilvis0_near_zero import POLICY
    r = recipe()
    rows = tasks(r)
    assert (r['duration_s'], r['queries'], r['starts']) == (180., 179, 2)
    assert r['absolute_cost_tolerance'] == POLICY['maximum_computed_cost'] == 1e-8
    assert r['workers']*r['threads'] == 4
    assert len(rows) == 12
    assert {row['payload']['model'] for row in rows} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {row['payload']['profile'] for row in rows} == {False, True}
    assert {row['payload']['start'] for row in rows} == {0, 1}
    assert all(row['limits']['native_calls'] == 402 for row in rows)
    assert all(row['limits']['packet_visits'] == 1711750000 for row in rows)


def test_v2_study_requires_complete_group_and_early_only_binding():
    base = dict(training_cost=1e-12, passed=True,
                input_binding={'early': 'a'*64}, times_s=[1., 2.],
                forecast=[[0., 0., 0.], [0., 0., 0.]])
    group = {'wide': {0: dict(base), 1: dict(base)},
             'hybrid': {0: dict(base), 1: dict(base)}}
    assert assess_group(group, model='sphere_rotating',
                        settings=recipe())['equivalent']
    group['hybrid'][1] = dict(base, input_binding={'early': 'b'*64})
    with pytest.raises(ValueError, match='binding'):
        assess_group(group, model='sphere_rotating', settings=recipe())
    del group['hybrid'][1]
    with pytest.raises(ValueError, match='complete'):
        assess_group(group, model='sphere_rotating', settings=recipe())


def test_v2_study_preserves_failed_parent_and_qualification():
    assert verify_parent(ROOT)
    with pytest.raises(ValueError, match='qualification'):
        prepare(ROOT)


def test_v2_study_uses_shared_paired_calculation(monkeypatch):
    from lll import ilvis0_hybrid_fit_study as base
    seen = []

    def recorded(spec, settings, **kwargs):
        seen.append((spec, settings, kwargs['allowed_specs']))
        return {'passed': True}

    monkeypatch.setattr(base, 'pair', recorded)
    selected = tasks()[1]['payload']
    assert pair(selected, recipe())['passed']
    assert seen[0][0] == selected
    assert len(seen[0][2]) == 12
