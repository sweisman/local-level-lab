# SPDX-License-Identifier: AGPL-3.0-or-later
import time

import numpy as np
import pytest

import esa_motion_worker as worker


def test_finite_scope_and_protection():
    assert len(worker.TASKS)==11
    assert sum(t.get('realizations',0) for t in worker.TASKS)==2304
    assert worker.LIMITS['maximum_observed_windows']==2048
    assert worker.LIMITS['raw_imu_reads']==worker.LIMITS['native_evaluations']==worker.LIMITS['optimizer_starts']==0


def test_exact_paths_use_independent_reference():
    result=worker.exact_controls()
    assert result['passed'] and result['exact_paths']==24
    assert result['maximum_coefficient_error']<1e-10


def test_generated_noise_is_reproducible_and_preserves_truth():
    case=worker.coverage_fixture(.05,.8)
    a=worker.generated(case,3);b=worker.generated(case,3)
    np.testing.assert_array_equal(a['observed_velocity_ne'],b['observed_velocity_ne'])
    assert not np.array_equal(a['observed_velocity_ne'],worker.generated(case,4)['observed_velocity_ne'])
    assert abs(a['true_window_rate_deg_s']-a['instantaneous_rate_deg_s'])<1e-6


def test_full_coverage_lower_bound_passes_and_missing_counts_as_miss():
    assert worker.coverage_bound(256,256)['passed']
    assert not worker.coverage_bound(256,0)['passed']


def test_candidate_centers_are_fixed_before_outcomes():
    assert worker.center_indices(5,3)==[0,2,4]
    assert worker.center_indices(3,10)==[0,1,2]


def test_window_does_not_bridge_gaps():
    times=np.arange(41)*.5;sequence=np.arange(41);times[21:]+=1.
    assert worker.window_indices(times,sequence,20) is None
    assert worker.window_indices(times,sequence,0) is None


def test_study_cannot_restart(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path)
    (tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):worker.run()


def test_deadline_is_cooperative():
    with pytest.raises(worker.AllowanceExhausted):worker.check_time(time.monotonic()-1.)
