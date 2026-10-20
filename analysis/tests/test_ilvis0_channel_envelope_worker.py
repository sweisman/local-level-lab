# SPDX-License-Identifier: AGPL-3.0-or-later
import json

import numpy as np
import pytest

import ilvis0_channel_envelope_worker as worker
from lll.ilvis0_channel_envelope import prepare_jets, assess
from test_ilvis0_channel_envelope import sample


def test_finite_plan_has_exact_unique_identity_counts():
    selected = [dict(segment=dict(segment_id='one')), dict(segment=dict(segment_id='two'))]
    tasks = worker.tasks(selected)
    assert len(tasks) == len({row['identity'] for row in tasks}) == 170
    for kind, number in [('extract', 2), ('batch', 24), ('candidate', 144)]:
        assert sum(row['kind'] == kind for row in tasks) == number
    assert worker.LIMITS['maximum_receiver_operators'] == 24*256
    assert worker.LIMITS['maximum_force_boxes'] == 144*256


def test_reloaded_numeric_batch_matches_in_memory_calculation():
    values, times, points = sample()
    batch = prepare_jets(values, times, points, 0., 'nominal', 1.)
    restored = json.loads(json.dumps(worker.plain(batch)))
    before = assess(values, batch, model='sphere_still', velocity_scale=1e-8, calibration='broad')
    after = assess(values, restored, model='sphere_still', velocity_scale=1e-8, calibration='broad')
    assert before == after


def test_deterministic_compression_and_no_overwrite(tmp_path):
    a, b = tmp_path/'a.json.gz', tmp_path/'b.json.gz'
    worker.write(a, dict(values=np.array([1., 2.]), flag=np.bool_(True)))
    worker.write(b, dict(values=np.array([1., 2.]), flag=np.bool_(True)))
    assert a.read_bytes() == b.read_bytes()
    assert worker.load(a) == dict(values=[1., 2.], flag=True)
    with pytest.raises(FileExistsError): worker.write(a, dict(other=True))


def test_completed_work_cannot_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, 'DATA', tmp_path)
    worker.write(tmp_path/'completion.json', dict(done=True))
    with pytest.raises(ValueError, match='cannot restart'): worker.run()
