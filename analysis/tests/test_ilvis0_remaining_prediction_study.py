# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite twenty-group task and prefit guards."""

from types import SimpleNamespace

import pytest

from lll import ilvis0_remaining_prediction_study as study


def _layout(i):
    return dict(segment_id=f'segment-{i}',group_id=f'group-{i}',
                receiver_epochs=30,training_epochs=20,prediction_epochs=10,
                native_packets=600)


def test_twenty_group_grid_has_eighty_finite_starts():
    rows=study.tasks([_layout(i) for i in range(20)])
    assert len(rows)==80
    assert len({row['identity'] for row in rows})==80
    assert sum(row['limits']['native_calls'] for row in rows)==16080
    assert {row['payload']['origin'] for row in rows}=={'inner','outer'}
    assert {row['payload']['start'] for row in rows}=={0,1}
    assert all(row['payload']['clock']=='header_elapsed'
               and row['payload']['profile'] is False for row in rows)


def test_changed_task_is_rejected_before_established_fit(monkeypatch,tmp_path):
    monkeypatch.setattr('lll.ilvis0_rolling_origin_study.evaluate',
                        lambda *args:pytest.fail('fit ran'))
    layouts=[_layout(i) for i in range(20)]
    path=tmp_path/'layouts.json'
    import json
    path.write_text(json.dumps(layouts))
    task=study.tasks(layouts)[0]
    context=SimpleNamespace(manifest=dict(scope=study.SCOPE),
                            input_path=lambda key:path)
    changed=dict(task,payload=dict(task['payload'],start=2))
    with pytest.raises(ValueError,match='unchanged twenty-group'):
        study.evaluate(changed,context)


def test_changed_established_source_is_rejected(tmp_path):
    source=tmp_path/'established.py'
    source.write_bytes(b'changed')
    with pytest.raises(ValueError,match='unchanged sealed rolling-origin evaluator'):
        study.verify_established_sources(
            tmp_path, {'established.py':'0'*64}, ['established.py'])


def test_historical_science_lock_accepts_only_audited_changes():
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    root=Path(__file__).resolve().parents[2]
    prior=ClosedStudy(root,'data/ilvis0-rolling-origin-development-v1')
    try:
        audited=study.verify_historical_science(root,prior)
    finally:
        prior.close()
    assert len(audited)==12
    assert 'analysis/lll/ilvis0_segments.py' in audited
    assert 'analysis/lll/ilvis0_rolling_origin_study.py' not in audited
