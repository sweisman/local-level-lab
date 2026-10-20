# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

import ilvis0_structured_error_worker as worker


def test_benchmark_scope_is_finite_and_contains_no_observed_work():
    assert len(worker.TASKS)==3
    assert max(r['epochs'] for r in worker.TASKS)==worker.LIMITS['maximum_epochs']==64080
    assert max(r['columns'] for r in worker.TASKS)==worker.LIMITS['maximum_columns']==27
    assert worker.LIMITS['original_reads']==worker.LIMITS['optimizer_starts']==worker.LIMITS['native_evaluations']==0


def test_generated_blocks_reproduce_the_same_full_input():
    np.testing.assert_array_equal(worker.values(0,9,4),np.vstack((worker.values(0,3,4),worker.values(3,9,4))))


def test_worker_dense_gate_and_small_scaling_path_pass():
    dense=worker.evaluate(dict(identity='dense-equivalence',epochs=6,columns=2))
    small=worker.evaluate(dict(identity='unit-scaling',epochs=20,columns=3))
    assert dense['passed'] and small['passed']
    assert small['cache_bytes_per_epoch']>0
    assert small['block_max_error']==0.
    assert small['inverse_max_error']<1e-10


def test_charged_benchmark_cannot_restart(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path)
    (tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):worker.run()


def test_deadline_escapes_ordinary_calculation_failure_handler():
    with pytest.raises(worker.Deadline):
        try:raise worker.Deadline('test')
        except Exception:pytest.fail('deadline was swallowed')
