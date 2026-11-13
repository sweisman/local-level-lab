"""Finite four-group transfer grid reusing the qualified rolling evaluator."""
import json
from pathlib import Path

import pytest


RECEIPT = Path(__file__).resolve().parents[2] / 'docs/prediction-group-transfer/split-receipt.json'


def _layouts():
    rows = json.loads(RECEIPT.read_bytes())['layouts']
    return [dict(row, native_packets=1000) for row in rows]


def test_fixed_grid_and_charges_have_four_groups_sixteen_starts():
    from lll.ilvis0_group_transfer_study import recipe, tasks
    rule = recipe()
    grid = tasks(_layouts())
    assert len(grid) == 16
    assert len({row['identity'] for row in grid}) == 16
    assert rule['model'] == 'sphere_rotating'
    assert rule['clock'] == 'header_elapsed'
    assert rule['profile'] is False
    assert rule['workers'] == rule['threads'] == 1
    assert sum(row['limits']['native_calls'] for row in grid) == 3216
    assert {row['payload']['origin'] for row in grid} == {'inner', 'outer'}
    assert {row['payload']['start'] for row in grid} == {0, 1}
    assert {row['payload']['segment_id'] for row in grid} == {
        row['segment_id'] for row in _layouts()}


def test_missing_or_duplicate_provenance_group_fails_closed():
    from lll.ilvis0_group_transfer_study import tasks
    rows = _layouts()
    with pytest.raises(ValueError):
        tasks(rows[:3])
    duplicate = [dict(row) for row in rows]
    duplicate[-1]['group_id'] = duplicate[0]['group_id']
    with pytest.raises(ValueError):
        tasks(duplicate)


def test_grid_ignores_scientific_outcome_metadata():
    from lll.ilvis0_group_transfer_study import tasks
    rows = _layouts()
    original = tasks(rows)
    for row in rows:
        row['scientific_decision'] = 'flat'
    assert tasks(rows) == original


def test_adapter_reuses_established_evaluator(monkeypatch):
    from lll import ilvis0_group_transfer_study, ilvis0_rolling_origin_study
    marker = object()
    monkeypatch.setattr(ilvis0_rolling_origin_study, 'evaluate',
                        lambda task, context: marker)
    assert ilvis0_group_transfer_study.evaluate(None, None) is marker


def test_missing_source_qualification_blocks_preparation_before_original_reads():
    from lll.ilvis0_group_transfer_study import prepare
    with pytest.raises((FileNotFoundError, ValueError)):
        prepare(Path(__file__).resolve().parents[2],
                qualification='docs/prediction-group-transfer/missing-request.json')


def test_reused_prediction_source_matches_sealed_three_recording_study():
    from lll.ilvis0_rolling_origin_study import sources
    from lll.studies.artifacts import digest
    from lll.studies.closed import ClosedStudy
    root = Path(__file__).resolve().parents[2]
    try:
        prior = ClosedStudy(root, 'data/ilvis0-rolling-origin-development-v1')
    except ValueError as error:
        if str(error) == 'closed study required':
            pytest.skip('historical closed parent is not in the source checkout')
        raise
    try:
        assert prior.completion['state'] in ('complete', 'terminal')
        assert len(prior.tasks) == len(prior.rows) == 48
        assert all(prior.manifest['sources'][name] ==
                   digest(prior.read('source-freeze/' + name, raw=True))
                   for name in sources(root))
    finally:
        prior.close()
