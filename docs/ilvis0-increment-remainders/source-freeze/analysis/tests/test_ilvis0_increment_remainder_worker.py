# SPDX-License-Identifier: AGPL-3.0-or-later
import time

import numpy as np
import pytest

import ilvis0_increment_remainder_worker as worker


def test_scope_is_finite_without_observed_work():
    assert len(worker.TASKS)==30
    assert sum(t['probes'] for t in worker.TASKS)==1920
    assert sum(t['maximum_calls'] for t in worker.TASKS)==12726
    assert worker.LIMITS['maximum_software_evaluations']==13000
    assert worker.LIMITS['original_reads']==worker.LIMITS['native_evaluations']==worker.LIMITS['optimizer_starts']==0


@pytest.mark.parametrize('kind',['calibration','packet','history'])
def test_small_software_paths_satisfy_analytic_bounds(kind):
    task=next(dict(t) for t in worker.TASKS if t['kind']==kind)
    result=worker.evaluate(task)
    assert result['passed'] and result['probe_count']==64
    assert result['actual_calls']<=task['maximum_calls']


def test_block_matrix_reference_has_known_zero_angle_integrals():
    book=worker.Calls(4);maps,derivatives=worker.reference(np.zeros(3),book,derivatives=True)
    np.testing.assert_allclose(maps[0],np.eye(3),atol=1e-15)
    np.testing.assert_allclose(maps[1],np.eye(3),atol=1e-15)
    np.testing.assert_allclose(maps[2],np.eye(3)/2.,atol=1e-15)
    assert book.count==4


@pytest.mark.parametrize('identity',['packet-position-large-broad','history-31-broad'])
def test_large_rotation_and_shared_broad_calibration(identity):
    task=next(dict(t) for t in worker.TASKS if t['identity']==identity)
    result=worker.evaluate(task)
    assert result['passed'] and result['actual_calls']==task['maximum_calls']


def test_evaluations_are_charged_before_execution_and_cannot_expand():
    book=worker.Calls(1);book.tick()
    with pytest.raises(ValueError):book.tick()
    assert book.count==1


def test_cooperative_deadline_and_restart_protection(tmp_path,monkeypatch):
    with pytest.raises(worker.AllowanceExhausted):worker.check_time(time.monotonic()-1.)
    monkeypatch.setattr(worker,'DATA',tmp_path);(tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):worker.run()
