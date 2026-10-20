# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

import ilvis0_history_envelope_worker as worker
from test_ilvis0_channel_envelope import sample


def test_exact_identity_multiplier_and_unique_keys():
    inventories = {'one':dict(groups=[dict(group_index=0,eligible=True),dict(group_index=1,eligible=False)]),
                   'two':dict(groups=[dict(group_index=0,eligible=True)])}
    result = worker.identities(inventories)
    assert len(result) == len({r['identity'] for r in result}) == 8
    assert worker.LIMITS['maximum_receiver_operators'] == worker.LIMITS['maximum_identities']
    assert worker.LIMITS['maximum_force_boxes'] == 3*worker.LIMITS['maximum_identities']
    assert worker.LIMITS['maximum_scalar_comparisons'] == 9*worker.LIMITS['maximum_identities']


def test_identity_cap_is_not_adaptively_expanded():
    groups=[dict(group_index=i,eligible=True) for i in range(841)]
    with pytest.raises(ValueError): worker.identities({'one':dict(groups=groups)})


def test_identity_order_survives_canonical_json_round_trip():
    import json
    inventories={'z':dict(groups=[dict(group_index=0,eligible=True)]),
                 'a':dict(groups=[dict(group_index=1,eligible=True)])}
    restored=json.loads(json.dumps(inventories,sort_keys=True))
    assert worker.identities(inventories) == worker.identities(restored)


def test_deadline_cannot_be_swallowed_by_ordinary_calculation_handler():
    caught = False
    with pytest.raises(worker.Deadline):
        try: worker.require_time(0., worker.LIMITS['maximum_wall_s'])
        except Exception: caught = True
    assert not caught
    assert worker.require_time(0., 1.) == worker.LIMITS['maximum_wall_s']-1


def test_completed_or_terminal_study_cannot_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, 'DATA', tmp_path)
    for filename in ['completion.json','terminal.json']:
        path=tmp_path/filename; path.write_text('{}')
        with pytest.raises(ValueError): worker.require_unfinished()
        path.unlink()


def test_worker_counts_calls_before_evaluation():
    values,times,coordinates=sample()
    task=dict(group=dict(first_packet=2000,packet_count=200,group_index=10,eligible=True),
        clock='nominal',receiver_error_m=1)
    counts=dict(operators=0,force_boxes=0)
    result=worker.evaluate(task,dict(values=values,times=times,coordinates=coordinates,
        provenance=dict(velocity_scale_mps_per_count=1e-8)),counts)
    assert result['supported']
    assert counts == dict(operators=1,force_boxes=3)
    assert len(result['models']) == 3
    assert all(len(r['comparisons'])==3 for r in result['models'].values())
